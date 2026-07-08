---
name: lambda_development
description: Helps with creating, editing, testing, and debugging Python Lambda functions, database DAO layers, and requirements in the savethedate_api project.
---

# Python Lambda Development Skill

This skill provides context and instructions for developing, updating, and debugging backend Python Lambda functions in the `savethedate_api` project.

## When to use this skill
Use this skill when:
- Creating new API endpoints or back-end worker logic.
- Modifying existing Python Lambda functions in the `lambdas/` folder.
- Updating database access logic (DAOs) under `lambdas/utils/`.
- Managing Python package dependencies in `lambdas/requirements.txt`.
- Running pytest E2E integrations.

## Core Architecture Guidelines

### 1. Handler Structure
All Lambda functions should reside in their own subdirectory inside [lambdas/](file:///Users/danielrenteria/projects/savethedate_api/lambdas/).
By default, the Lambda handler configuration expects:
- **File**: `index.py` (e.g. `lambdas/add_guest/index.py`)
- **Function**: `handler(event, context)`

### 2. Standard Responses (CORS)
For API Gateway endpoints, always import and return `cors_response` from `utils.response` to handle serialization and CORS headers:
```python
from utils.response import cors_response

def handler(event, context):
    try:
        # business logic...
        return cors_response(200, {"success": True, "data": result})
    except Exception as e:
        return cors_response(500, {"error": str(e)})
```

### 3. Database Access (DAOs)
Never initialize raw DynamoDB clients inside handlers. Use the shared DAOs in `lambdas/utils/`:
- **Events**: Use `EventDAO` from `utils.event_dao`
- **Guests**: Use `GuestDAO` from `utils.guest_dao`
Example usage:
```python
import os
from utils.guest_dao import GuestDAO

table_name = os.environ['TABLE_NAME']
guest_dao = GuestDAO(table_name)

# Get guest details
guest = guest_dao.get_guest(event_id, confirmation_code)
```

### 4. SQS Queue & Retry Logic
- SQS queue for invitations triggers the `process_invitation` Lambda in batches of 10.
- If individual messages fail, return the failed message IDs in `batchItemFailures` so SQS can retry.
- After 3 retries, the message moves to DLQ, and the Guest record is marked `invitation_sent_fatal_error: true`.

## Testing Backend Changes
Always run E2E pytest tests to verify your changes:
1. Ensure dependencies are installed: `pip install -r tests/requirements.txt`
2. Export the environment variables:
   ```bash
   export API_URL="https://<api-id>.execute-api.<region>.amazonaws.com/prod"
   export ADMIN_USERNAME="admin"
   export ADMIN_PASSWORD="your-admin-password"
   ```
3. Run tests: `pytest tests/e2e`
