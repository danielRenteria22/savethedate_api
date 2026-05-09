#!/usr/bin/env python3
"""Delete all events from the API."""
import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tests', 'e2e'))

from utils.http_client import ApiClient

API_URL = os.getenv("API_URL", "https://22tp7n0qdg.execute-api.us-east-2.amazonaws.com/v1")
USERNAME = os.getenv("ADMIN_USERNAME", "foo1")
PASSWORD = os.getenv("ADMIN_PASSWORD", "Pa$$word2")

client = ApiClient(API_URL)
client.login(USERNAME, PASSWORD)

events = client.list_events().json().get("events", [])
print(f"Found {len(events)} event(s).")

for event in events:
    print('event',json.dumps(event, indent=4))
    subdomain = event["subdomain"]
    r = client.delete_event(subdomain)
    status = "OK" if r.status_code == 200 else f"FAILED ({r.status_code})"
    print(f"  Deleted {subdomain}: {status}")
