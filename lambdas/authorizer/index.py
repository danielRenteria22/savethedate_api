"""
Lambda Token Authorizer
- Validates the Cognito JWT (access token) without an external library
  by fetching the JWKS from Cognito's public endpoint and verifying the
  RS256 signature using only Python standard library + cryptography (available
  in the Lambda runtime via the included 'cryptography' package).
- Extracts the cognito:groups claim to determine admin status.
- Passes user context (userId, username, isAdmin) to downstream lambdas
  via the authorizer context object.

Admin routes: any method ARN whose path contains /admin/
"""

import json
import os
import time
import base64
import urllib.request
from functools import lru_cache

# ---- JWT verification helpers (no third-party deps) ----------------------

def _b64decode(s: str) -> bytes:
    """Base64url decode with padding."""
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    """Fetch and cache JWKS from Cognito. LRU cache survives warm Lambda invocations."""
    region = os.environ["REGION"]
    pool_id = os.environ["USER_POOL_ID"]
    url = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read())


def _find_key(kid: str) -> dict:
    jwks = _get_jwks()
    for key in jwks["keys"]:
        if key["kid"] == kid:
            return key
    raise ValueError(f"Key {kid!r} not found in JWKS")


def _verify_jwt(token: str) -> dict:
    """
    Verify a Cognito JWT and return its payload.
    Raises ValueError on any failure.
    """
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise ValueError("Malformed token")

    header  = json.loads(_b64decode(header_b64))
    payload = json.loads(_b64decode(payload_b64))

    # ---- Basic claims validation ----
    now = int(time.time())
    if payload.get("exp", 0) < now:
        raise ValueError("Token expired")

    expected_iss = (
        f"https://cognito-idp.{os.environ['REGION']}.amazonaws.com/"
        f"{os.environ['USER_POOL_ID']}"
    )
    if payload.get("iss") != expected_iss:
        raise ValueError("Invalid issuer")

    if payload.get("token_use") != "access":
        raise ValueError("Not an access token")

    if payload.get("client_id") != os.environ["CLIENT_ID"]:
        raise ValueError("Invalid client_id")

    # ---- Signature verification ----
    # Import here so cold start cost is paid only once
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend

    jwk = _find_key(header["kid"])

    n = int.from_bytes(_b64decode(jwk["n"]), "big")
    e = int.from_bytes(_b64decode(jwk["e"]), "big")
    public_key = RSAPublicNumbers(e, n).public_key(default_backend())

    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = _b64decode(sig_b64)

    public_key.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
    # verify() raises InvalidSignature on failure — let it bubble up

    return payload


# ---- Authorizer handler --------------------------------------------------

def handler(event, context):
    token = event.get("authorizationToken", "")
    method_arn: str = event["methodArn"]

    if token.startswith("Bearer "):
        token = token[7:]

    try:
        payload = _verify_jwt(token)
    except Exception as exc:
        print(f"Token validation failed: {exc}")
        # API Gateway interprets "Unauthorized" string as a 401
        raise Exception("Unauthorized")

    groups: list[str] = payload.get("cognito:groups", [])
    is_admin = "admin" in groups

    # Deny admin routes for non-admin users
    # Method ARN format: arn:aws:execute-api:region:acct:api-id/stage/METHOD/resource/path
    path_part = method_arn.split(":")[-1]  # api-id/stage/METHOD/resource/path
    path_segments = path_part.split("/")[3:]  # everything after stage/METHOD
    is_admin_route = "admin" in path_segments

    effect = "Allow"
    if is_admin_route and not is_admin:
        effect = "Deny"

    policy = _generate_policy(
        principal_id=payload["sub"],
        effect=effect,
        resource=method_arn,
    )

    # Context fields are passed to the Lambda integration as
    # $context.authorizer.<key>  in API Gateway mapping templates,
    # or event["requestContext"]["authorizer"] inside the Lambda.
    policy["context"] = {
        "userId":   payload["sub"],
        "username": payload.get("username", payload.get("cognito:username", "")),
        "isAdmin":  str(is_admin).lower(),   # context values must be strings
        "groups":   ",".join(groups),
    }

    return policy


def _generate_policy(principal_id: str, effect: str, resource: str) -> dict:
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action":   "execute-api:Invoke",
                    "Effect":   effect,
                    "Resource": resource,
                }
            ],
        },
    }