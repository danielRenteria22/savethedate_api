"""
Admin Lambda Token Authorizer
Requires user to have 'admin' group in cognito:groups claim.
"""

import json
import os
import time
import base64
import urllib.request
from functools import lru_cache

def _b64decode(s: str) -> bytes:
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)

@lru_cache(maxsize=1)
def _get_jwks() -> dict:
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
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise ValueError("Malformed token")

    header  = json.loads(_b64decode(header_b64))
    payload = json.loads(_b64decode(payload_b64))

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

    return payload

def handler(event, context):
    token = event.get("authorizationToken", "")
    method_arn: str = event["methodArn"]

    if token.startswith("Bearer "):
        token = token[7:]

    try:
        payload = _verify_jwt(token)
    except Exception as exc:
        print(f"Token validation failed: {exc}")
        raise Exception("Unauthorized")

    groups: list[str] = payload.get("cognito:groups", [])
    
    if "admin" not in groups:
        print(f"Access denied: user lacks admin group")
        raise Exception("Unauthorized")

    resource_wildcard = method_arn.split("/")[0] + "/*"
    
    policy = {
        "principalId": payload["sub"],
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": "Allow",
                "Resource": resource_wildcard,
            }],
        },
        "context": {
            "userId": payload["sub"],
            "username": payload.get("username", payload.get("cognito:username", "")),
            "isAdmin": "true",
            "groups": ",".join(groups),
        },
    }

    return policy
