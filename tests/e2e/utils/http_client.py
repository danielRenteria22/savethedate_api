import requests
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.session.hooks['response'] = [self._log_request]

    def _log_request(self, response, *args, **kwargs):
        """Log request and response details"""
        req = response.request
        logger.info(f"Request: {req.method} {req.url}")
        
        # Format request body as JSON if possible
        if req.body:
            try:
                req_data = json.loads(req.body)
                req_data = self._redact_sensitive_data(req_data)
                logger.info(f"Request Data: {json.dumps(req_data, indent=2)}")
            except (json.JSONDecodeError, TypeError):
                logger.info(f"Request Data: {req.body}")
        
        logger.info(f"Response Status: {response.status_code}")
        
        # Format response as JSON if possible
        try:
            resp_data = response.json()
            resp_data = self._redact_sensitive_data(resp_data)
            logger.info(f"Response Data: {json.dumps(resp_data, indent=2)}")
        except (json.JSONDecodeError, ValueError):
            logger.info(f"Response Data: {response.text}")

    def _redact_sensitive_data(self, data):
        """Redact sensitive information from logs"""
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = {'password', 'token', 'access_token', 'refresh_token', 'newPassword', 'session'}
        redacted = data.copy()
        
        for key in redacted:
            if key in sensitive_keys:
                redacted[key] = "***REDACTED***"
            elif isinstance(redacted[key], dict):
                redacted[key] = self._redact_sensitive_data(redacted[key])
        
        return redacted

    def login(self, username: str, password: str):
        """Login and store access token"""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        return data

    def create_event(self, subdomain: str, guests_name: str, datetime_utc: str, 
                     food_options: list, password: str, message: str):
        """POST /events - Create event (admin only)"""
        return self.session.post(
            f"{self.base_url}/api/admin/event",
            json={
                "subdomain": subdomain,
                "guests_name": guests_name,
                "datetime_utc": datetime_utc,
                "food_options": food_options,
                "password": password,
                "message": message
            }
        )

    def list_events(self):
        """GET /events - List all events (admin only)"""
        return self.session.get(f"{self.base_url}/api/admin/event")

    def update_event(self, subdomain: str, updates: dict):
        """PUT /events/{subdomain} - Update event (admin only)"""
        return self.session.put(f"{self.base_url}/api/admin/event/{subdomain}", json=updates)

    def delete_event(self, subdomain: str):
        """DELETE /events/{subdomain} - Delete event (admin only)"""
        return self.session.delete(f"{self.base_url}/api/admin/event/{subdomain}")

    def change_password(self, username: str, session: str, new_password: str):
        """POST /auth/change-password - Change password"""
        return self.session.post(
            f"{self.base_url}/auth/change-password",
            json={"username": username, "session": session, "newPassword": new_password}
        )

    def get_public_data(self):
        """GET /api/data - Public endpoint (authenticated users)"""
        return self.session.get(f"{self.base_url}/api/data")

    def get_admin_users(self):
        """GET /api/admin/users - Admin endpoint (admin only)"""
        return self.session.get(f"{self.base_url}/api/admin/users")

    def add_guest(self, name: str, phone_code: str, phone_number: str, num_guests: int):
        """POST /host/guests - Add guest"""
        return self.session.post(
            f"{self.base_url}/host/guests",
            json={
                "name": name,
                "phone_code": phone_code,
                "phone_number": phone_number,
                "num_guests": num_guests
            }
        )

    def list_guests(self):
        """GET /host/guests - List guests"""
        return self.session.get(f"{self.base_url}/host/guests")

    def update_guest(self, guest_id: str, updates: dict):
        """PUT /host/guests/{guest_id} - Update guest"""
        return self.session.put(f"{self.base_url}/host/guests/{guest_id}", json=updates)

    def delete_guest(self, guest_id: str):
        """DELETE /host/guests/{guest_id} - Delete guest"""
        return self.session.delete(f"{self.base_url}/host/guests/{guest_id}")
