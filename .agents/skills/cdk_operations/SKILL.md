---
name: cdk_operations
description: Helps with compiling, synthesizing, diffing, testing, and deploying the AWS CDK stack for the savethedate_api project.
---

# CDK Operations Skill

This skill provides instructions and references for managing the AWS Cloud Development Kit (CDK) infrastructure stack in the `savethedate_api` project.

## When to use this skill
Use this skill when you need to:
- Check for differences between the local code and deployed AWS resources.
- Synthesize the CloudFormation template to verify configuration changes.
- Build/compile TypeScript changes in the CDK stack.
- Deploy infrastructure modifications.
- Run CDK-specific unit/integration tests.

## Essential Commands

### 1. Build and Compile TypeScript
Compile the CDK TypeScript code to JavaScript. Run this before deploying or diffing to verify there are no TypeScript syntax or typing errors:
```bash
npm run build
```

### 2. Synthesize CloudFormation
Generate the CloudFormation template. This is a fast way to verify that CDK constructs and resource relationships are correctly defined without performing a deployment:
```bash
npx cdk synth
```

### 3. Check for Differences (CDK Diff)
Compare the current local CDK codebase with the active deployment in AWS. Always run `cdk diff` and present the output to the user before doing any deployments:
```bash
npx cdk diff
```

### 4. Deploy Infrastructure (CDK Deploy)
Deploy the CDK stack to the configured AWS environment:
```bash
npx cdk deploy
```

### 5. Run CDK Unit Tests
Run the Jest tests defined under the `test/` directory to verify stack logic:
```bash
npm run test
```

## Stack Customization Guidelines
*   **Environment Variables**: All Lambdas draw their environment variables from the `commonEnv` object inside [savethedate_api-stack.ts](file:///Users/danielrenteria/projects/savethedate_api/lib/savethedate_api-stack.ts). If adding a new environment variable, ensure it is added there.
*   **Lambda Layer**: The stack uses `RequirementsLayer` for bunding Python dependencies. When changing python packages or dependencies, make sure they are added to `lambdas/requirements.txt`.
*   **Permissions**: Grant permissions to the DynamoDB table (`invitationsTable.grantReadWriteData(...)`) or Cognito User Pool for each Lambda function in the stack definition.
