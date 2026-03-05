"""
Admin endpoint — accessible only by users in the 'admin' Cognito group.
GET /api/admin/users

Access control is enforced by the Lambda Authorizer (Deny policy for
non-admins). This Lambda adds a second layer of validation as defence-in-depth.
"""

import json
import os
import boto3

cognito = boto3.client("cognito-idp", region_name=os.environ["REGION"])
USER_POOL_ID = os.environ["USER_POOL_ID"]


def handler(event, context):
    # Defence-in-depth: double-check the caller is really an admin
    authorizer_ctx = event.get("requestContext", {}).get("authorizer", {})
    is_admin = authorizer_ctx.get("isAdmin", "false") == "true"

    if not is_admin:
        # Should never reach here (authorizer denies first), but just in case
        return _response(403, {"error": "Forbidden: admin access required"})

    caller_username = authorizer_ctx.get("username", "unknown")

    # Example: list all users in the pool
    users = _list_users()

    return _response(200, {
        "message": "Hello from the admin endpoint!",
        "calledBy": caller_username,
        "userCount": len(users),
        "users": users,
    })


def _list_users() -> list[dict]:
    """List all users in the Cognito User Pool."""
    users = []
    paginator = cognito.get_paginator("list_users")

    for page in paginator.paginate(UserPoolId=USER_POOL_ID):
        for u in page["Users"]:
            attrs = {a["Name"]: a["Value"] for a in u["Attributes"]}
            users.append({
                "username":  u["Username"],
                "email":     attrs.get("email", ""),
                "status":    u["UserStatus"],
                "enabled":   u["Enabled"],
                "createdAt": u["UserCreateDate"].isoformat(),
            })

    return users


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }