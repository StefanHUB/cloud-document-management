"""
Authentication module with role-based access control.

Design rationale:
- The system implements role-based authentication as described in the project proposal.
- Two roles are supported:
  - 'manager': Can upload, download, and view engineering documents
  - 'admin': Can review, approve, and reject documents submitted by managers

- For development/demo, a simplified token-based auth is used.
- For production, this would integrate with Firebase Authentication,
  which provides secure JWT-based authentication with custom claims for roles.
  Firebase Admin SDK would verify ID tokens server-side.

Cloud Justification:
- Firebase Authentication is a cloud-native identity management service that
  scales automatically and integrates with GCP services. Using cloud-managed
  auth reduces security maintenance overhead and provides enterprise-grade
  features like multi-factor authentication and anomaly detection.
"""

import os
import hashlib
import hmac
import secrets
import time
import json
import base64
import logging

logger = logging.getLogger(__name__)

# Secret key for token signing (in production, this would be a Firebase Admin key)
SECRET_KEY = os.environ.get("AUTH_SECRET", "dev-secret-key-change-in-production")
TOKEN_EXPIRY_SECONDS = 86400  # 24 hours


# Pre-defined demo users with their roles
# In production, these would be managed through Firebase Authentication
DEMO_USERS = {
    "manager_user": {
        "password": "manager123",
        "email": "manager@example.com",
        "role": "manager",
        "name": "Document Manager",
    },
    "admin_user": {
        "password": "admin123",
        "email": "admin@example.com",
        "role": "admin",
        "name": "Document Administrator",
    },
}


def _sign(payload: str) -> str:
    """Sign a payload using HMAC-SHA256."""
    return hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()


def create_token(username: str, role: str, name: str) -> str:
    """
    Create a signed JWT-like token for the user.
    This simulates the Firebase ID token that would be issued in production.
    """
    payload = {
        "username": username,
        "role": role,
        "name": name,
        "exp": int(time.time()) + TOKEN_EXPIRY_SECONDS,
        "iat": int(time.time()),
    }
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()
    signature = _sign(payload_b64)
    return f"{payload_b64}.{signature}"


def verify_token(token: str) -> dict:
    """
    Verify a token and return the user payload.
    In production, this would use firebase_admin.auth.verify_id_token().
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            raise ValueError("Invalid token format")

        payload_b64, signature = parts
        expected_sig = _sign(payload_b64)

        if not hmac.compare_digest(signature, expected_sig):
            raise ValueError("Invalid token signature")

        payload_json = base64.urlsafe_b64decode(payload_b64).decode()
        payload = json.loads(payload_json)

        if payload["exp"] < time.time():
            raise ValueError("Token expired")

        return payload
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        raise ValueError(f"Authentication failed: {e}")


def authenticate(username: str, password: str) -> dict:
    """
    Authenticate a user with username/password.
    Returns user info and token if successful.

    In production, this would be replaced by Firebase Authentication:
    - Frontend signs in with Firebase SDK (email/password or OAuth)
    - Firebase returns an ID token
    - Backend verifies the token using Firebase Admin SDK
    - Custom claims determine the user's role (manager/admin)
    """
    user = DEMO_USERS.get(username)
    if not user or user["password"] != password:
        raise ValueError("Invalid credentials")

    token = create_token(username, user["role"], user["name"])
    return {
        "token": token,
        "username": username,
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
    }


def get_user_from_token(auth_header: str) -> dict:
    """Extract and verify user from Authorization header."""
    if not auth_header or not auth_header.startswith("Bearer "):
        raise ValueError("Missing or invalid Authorization header")

    token = auth_header.split("Bearer ")[1]
    return verify_token(token)
