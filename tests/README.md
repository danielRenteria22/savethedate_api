# Save the Date API - E2E Tests

## Setup

```bash
pip install -r tests/requirements.txt
```

## Configuration

Set environment variables:
```bash
export API_URL="https://your-api-gateway-url.amazonaws.com/prod"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="your-admin-password"
```

## Run Tests

```bash
# All tests
pytest tests/e2e

# Specific test file
pytest tests/e2e/tests/test_auth.py

# With verbose output
pytest tests/e2e -v
```
