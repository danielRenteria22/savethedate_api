# WhatsApp Invitation Feature

## Overview
This feature allows hosts to send WhatsApp invitations to guests via Twilio with automatic retry logic and status tracking.

## Architecture

### Flow
1. Host calls `POST /host/send-invitation` with `confirmation_code`
2. Message is queued to SQS
3. `process-invitation` Lambda consumes SQS messages and sends via Twilio
4. Twilio calls back to `POST /callback/twilio` with delivery status
5. Guest record is updated with final status

### Components

#### 1. Send Invitation Lambda (`send_invitation/index.py`)
- **Endpoint**: `POST /host/send-invitation`
- **Auth**: User group (host)
- **Input**: `{ "confirmation_code": "ABC12345" }`
- **Action**: Queues message to SQS
- **Response**: `202 Accepted`

#### 2. SQS Queue (`invitation-queue`)
- **Visibility Timeout**: 90 seconds
- **Max Receive Count**: 3 (retries)
- **Dead Letter Queue**: `invitation-dlq`

#### 3. Process Invitation Lambda (`process_invitation/index.py`)
- **Trigger**: SQS messages (batch of 10)
- **Action**: 
  - Retrieves Twilio credentials from Secrets Manager
  - Sends WhatsApp message via Twilio
  - Checks message status (queued/sent/delivered)
  - Marks `invitation_sent: true` if successful
  - Returns failed messages for retry
  - Marks `invitation_sent_fatal_error: true` after 3 failed attempts
- **Timeout**: 60 seconds

#### 4. Twilio Callback Lambda (`twilio_callback/index.py`)
- **Endpoint**: `POST /callback/twilio`
- **Auth**: Public (no auth)
- **Input**: Twilio webhook with `MessageStatus` and query params
- **Action**: Updates guest record based on final delivery status
  - `sent`/`delivered` → `invitation_sent: true`
  - `failed`/`undelivered` → `invitation_sent_fatal_error: true`

### Guest Model Updates
Added two new properties:
- `invitation_sent` (bool): True when message successfully sent/delivered
- `invitation_sent_fatal_error` (bool): True when sending failed after 3 retries

## Setup Instructions

### 1. Create Twilio Secret in AWS Secrets Manager
```bash
aws secretsmanager create-secret \
  --name twilio-credentials \
  --secret-string '{
    "account_sid": "YOUR_TWILIO_ACCOUNT_SID",
    "auth_token": "YOUR_TWILIO_AUTH_TOKEN",
    "whatsapp_from": "whatsapp:+14155238886"
  }'
```

### 2. Deploy Stack
```bash
npm run build
npx cdk deploy
```

### 3. Configure Twilio Webhook
After deployment, configure your Twilio WhatsApp number to use the callback URL from stack outputs.

## Usage Example

```bash
# Send invitation
curl -X POST https://api-url/host/send-invitation \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"confirmation_code": "ABC12345"}'
```

## Retry Logic
- SQS automatically retries failed messages up to 3 times
- Lambda returns `batchItemFailures` for messages that need retry
- After 3 attempts, message moves to DLQ and guest is marked with `invitation_sent_fatal_error: true`
