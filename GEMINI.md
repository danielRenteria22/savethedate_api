# SaveTheDate API - Project Rules & Context

Welcome to the **SaveTheDate API** project! This file provides the essential context, rules, and guidelines for working on this codebase. Antigravity reads this file automatically on startup to understand the workspace structure and guidelines.

---

## 1. Project Overview & Tech Stack
SaveTheDate API is a serverless backend service for managing event invitations and guest RSVPs.
*   **Infrastructure**: AWS CDK (Cloud Development Kit) written in **TypeScript**.
*   **Backend Code**: AWS Lambda functions written in **Python 3.12**.
*   **Database**: AWS DynamoDB using Single-Table Design.
*   **Authentication & Authorization**: AWS Cognito User Pool with custom Lambda Authorizers.
*   **Async Processing**: Amazon SQS for queueing WhatsApp invitation tasks, processed by a worker Lambda.
*   **External Integration**: Twilio API for sending WhatsApp invitations.

---

## 2. Directory Structure & Key Files
*   [lib/savethedate_api-stack.ts](file:///Users/danielrenteria/projects/savethedate_api/lib/savethedate_api-stack.ts): The main CDK stack definition where all AWS resources (Cognito, DynamoDB, SQS, Lambdas, API Gateway) are defined.
*   [lambdas/](file:///Users/danielrenteria/projects/savethedate_api/lambdas/): Contains all python Lambda functions. Each subdirectory (e.g., [lambdas/add_guest/](file:///Users/danielrenteria/projects/savethedate_api/lambdas/add_guest/)) contains a Lambda function handler.
*   [lambdas/utils/](file:///Users/danielrenteria/projects/savethedate_api/lambdas/utils/): Shared Python helper code, including:
    *   [enums.py](file:///Users/danielrenteria/projects/savethedate_api/lambdas/utils/enums.py): Shared enumeration types.
    *   [event_dao.py](file:///Users/danielrenteria/projects/savethedate_api/lambdas/utils/event_dao.py): Data Access Object (DAO) for Event entities.
    *   [guest_dao.py](file:///Users/danielrenteria/projects/savethedate_api/lambdas/utils/guest_dao.py): DAO for Guest entities.
    *   [response.py](file:///Users/danielrenteria/projects/savethedate_api/lambdas/utils/response.py): Helper function for standardized API Gateway JSON responses with CORS headers.
*   [lambdas/requirements.txt](file:///Users/danielrenteria/projects/savethedate_api/lambdas/requirements.txt): External Python package dependencies bundled as a Lambda Layer.
*   [openapi.yaml](file:///Users/danielrenteria/projects/savethedate_api/openapi.yaml): Swagger / OpenAPI 3.0 specification file defining the API Gateway routes.
*   [tests/](file:///Users/danielrenteria/projects/savethedate_api/tests/): Python E2E integration tests (runs with `pytest`).
*   [test/](file:///Users/danielrenteria/projects/savethedate_api/test/): TypeScript CDK stack tests (runs with Jest).

---

## 3. Database Architecture (DynamoDB Single-Table Design)
All data is stored in a single DynamoDB table named `invitations-table` using the following partition key (`PK`) and sort key (`SK`) design:

| Entity Type | PK Pattern | SK Pattern | Fields & Description |
|---|---|---|---|
| **Event** | `EVENT#{subdomain}` | `EVENT#{subdomain}` | `subdomain`, `guests_name`, `datetime_utc`, `food_options`, `message`, `created_at` |
| **Guest** | `EVENT#{event_id}` | `GUEST#{confirmation_code}` | `confirmation_code`, `event_id`, `name`, `phone_code`, `phone_number`, `num_guests`, `invitation_status`, `confirmed_assistance`, `civil_wedding_invitation`, `after_party_invitation`, `table`, `checked_in`, `created_at` |

---

## 4. Development & Operation Commands
Always run commands from the workspace root directory:

*   **Compile TypeScript (CDK)**: `npm run build`
*   **Synthesize CloudFormation Template**: `npx cdk synth`
*   **Show CDK Diff**: `npx cdk diff`
*   **Deploy Stack to AWS**: `npx cdk deploy`
*   **Run Jest CDK Stack Tests**: `npm run test`
*   **Run Pytest E2E Tests**:
    1. Install requirements: `pip install -r tests/requirements.txt`
    2. Set environment variables: `API_URL`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`
    3. Run: `pytest tests/e2e`

---

## 5. Coding Standards & Best Practices

### CDK & Infrastructure (TypeScript)
*   Define all environment variables in the `commonEnv` object inside [savethedate_api-stack.ts](file:///Users/danielrenteria/projects/savethedate_api/lib/savethedate_api-stack.ts) so they are systematically passed to Lambdas.
*   Keep Lambda definitions unified. Most Lambdas share `defaultLambdaProps` and are compiled using the `RequirementsLayer` defined in the stack.

### Lambda Code (Python)
*   Do not query DynamoDB directly in Lambda handlers if possible. Use the DAOs: `EventDAO` and `GuestDAO` imported from `utils.event_dao` and `utils.guest_dao`.
*   Ensure all Lambda functions return standard CORS responses using `cors_response` from `utils.response`.
*   Handle errors gracefully and return appropriate HTTP status codes (e.g., `400 Bad Request`, `404 Not Found`, etc.).
*   Dependencies should be appended to `lambdas/requirements.txt` instead of vendorizing.

---

## 6. Related Skills
This project contains custom skills that you can activate or reference when performing specific tasks:
*   [cdk_operations](file:///Users/danielrenteria/projects/savethedate_api/.agents/skills/cdk_operations/SKILL.md) for compiling, synthesizing, testing, and deploying infrastructure.
*   [lambda_development](file:///Users/danielrenteria/projects/savethedate_api/.agents/skills/lambda_development/SKILL.md) for creating, modifying, and debugging Python Lambda functions and backend logic.
