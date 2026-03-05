"""
Login Lambda
POST /auth/login
Body: { "username": "...", "password": "..." }
Returns: { "access_token": "...", "id_token": "...", "refresh_token": "...", "expires_in": 3600 }
"""

import json
import os
import boto3
from botocore.exceptions import ClientError

cognito = boto3.client("cognito-idp", region_name=os.environ["REGION"])
CLIENT_ID = os.environ["CLIENT_ID"]


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
        username = body.get("username", "").strip()
        password = body.get("password", "")

        if not username or not password:
            return _response(400, {"error": "username and password are required"})

        result = cognito.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            ClientId=CLIENT_ID,
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": password,
            },
        )

        if 'ChallengeParameters' in result and 'AuthenticationResult' not in result:
            return _response(403, {
                "error": "Additional authentication challenge required", 
                "challenge_name": result["ChallengeName"],
                "challenge_parameters": result["ChallengeParameters"],
                "session": result.get("Session")
            })

        auth = result["AuthenticationResult"]
        return _response(200, {
            "access_token":  auth["AccessToken"],
            "id_token":      auth["IdToken"],
            "refresh_token": auth["RefreshToken"],
            "expires_in":    auth["ExpiresIn"],
            "token_type":    auth["TokenType"],
        })

    except ClientError as e:
        code = e.response["Error"]["Code"]

        if code in ("NotAuthorizedException", "UserNotFoundException"):
            return _response(401, {"error": "Invalid username or password"})
        if code == "UserNotConfirmedException":
            return _response(403, {"error": "User account is not confirmed"})
        if code == "PasswordResetRequiredException":
            return _response(403, {"error": "Password reset required"})

        print(f"Unexpected Cognito error: {e}")
        return _response(500, {"error": "Authentication service error"})

    except Exception as e:
        print(f"Unexpected error: {e}")
        return _response(500, {"error": "Internal server error"})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }