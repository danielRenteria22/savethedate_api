"""
Public endpoint — accessible by any authenticated user.
GET /api/data

The authorizer injects user context into event["requestContext"]["authorizer"].
"""

import json


def handler(event, context):
    # Read authorizer context
    authorizer_ctx = event.get("requestContext", {}).get("authorizer", {})
    user_id  = authorizer_ctx.get("userId", "unknown")
    username = authorizer_ctx.get("username", "unknown")
    is_admin = authorizer_ctx.get("isAdmin", "false") == "true"

    return _response(200, {
        "message": "Hello from the public endpoint!",
        "user": {
            "id":       user_id,
            "username": username,
            "isAdmin":  is_admin,
        },
        "data": [
            {"id": 1, "name": "Item A"},
            {"id": 2, "name": "Item B"},
            {"id": 3, "name": "Item C"},
        ],
    })


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }