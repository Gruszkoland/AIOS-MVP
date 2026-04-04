"""
Unified Admin Panel (UAP) — Phase 3
Multi-Tenant Authentication Module (JWT + RBAC)

JWT tokens with role-based access control
Multi-tenant organization isolation
"""
import os
import re
import sys
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

import jwt

sys.path.insert(0, str(Path(__file__).parent))

from db import get_db

_JWT_SECRET_DEFAULT = "uap-secret-key-change-in-production"
JWT_SECRET = os.getenv("JWT_SECRET", _JWT_SECRET_DEFAULT)
if JWT_SECRET == _JWT_SECRET_DEFAULT:
    import logging as _logging
    _logging.getLogger("adrion.uap.auth").warning(
        "[SECURITY] JWT_SECRET is not set — using insecure default. "
        "Set JWT_SECRET env var (min 32 chars) before exposing this service on a network."
    )
    if os.getenv("ENVIRONMENT") == "production":
        import logging as _logging2
        _logging2.getLogger("adrion.uap.auth").critical(
            "[SECURITY] JWT_SECRET is default in PRODUCTION — refusing to start."
        )
        sys.exit(1)
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

# RBAC Role Definitions
ROLE_PERMISSIONS = {
    "admin": {
        "permissions": [
            "create_task", "view_task", "execute_task", "delete_task",
            "view_genesis", "export_genesis",
            "manage_users", "manage_roles", "manage_org",
            "create_checkpoint", "restore_checkpoint"
        ],
        "description": "Full access to all features"
    },
    "operator": {
        "permissions": [
            "create_task", "view_task", "execute_task",
            "view_genesis", "export_genesis",
            "create_checkpoint", "restore_checkpoint"
        ],
        "description": "Can delegate tasks, view logs, manage checkpoints"
    },
    "viewer": {
        "permissions": [
            "view_task", "view_genesis",
        ],
        "description": "Read-only access to tasks and logs"
    },
    "healer": {
        "permissions": [
            "view_task", "view_genesis",
            "execute_healing_suggestions",  # Auto-optimization
            "update_agent_metrics"
        ],
        "description": "Automated system optimization",
    }
}

_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I
)


class AuthManager:
    """Multi-tenant authentication & RBAC."""

    def __init__(self):
        self.db = get_db()
        self.jwt_secret = JWT_SECRET
        self.jwt_algorithm = JWT_ALGORITHM
        self._users: Dict[str, Dict[str, Any]] = {}
        self._init_users()

    def _init_users(self):
        """Initialize default admin user from environment."""
        admin_email = os.getenv("UAP_ADMIN_EMAIL", "admin@adrion.local")
        admin_pw = os.getenv("UAP_ADMIN_PASSWORD", "")
        if not admin_pw:
            import logging as _l
            _l.getLogger("adrion.uap.auth").critical(
                "[SECURITY] UAP_ADMIN_PASSWORD not set — authentication is disabled. "
                "Set UAP_ADMIN_PASSWORD env var to enable login."
            )
            return
        self._users[admin_email] = {
            "user_id": str(uuid.uuid4()),
            "role": "admin",
            "password_hash": self._hash_password(admin_pw),
            "org_id": "default",
        }

    # ────────────────────────────────────────────────────────────────────
    # USER MANAGEMENT
    # ────────────────────────────────────────────────────────────────────

    def create_user(self, org_id: str, email: str, password: str,
                    role: str = "operator") -> Tuple[bool, str]:
        """Create new user. Returns: (success, user_id or error_message)"""
        if role not in ROLE_PERMISSIONS:
            return False, f"Invalid role: {role}"
        if not self._validate_email(email):
            return False, "Invalid email format"
        if not password:
            return False, "Password cannot be empty"
        if email in self._users:
            return False, "User already exists"
        user_id = str(uuid.uuid4())
        self._users[email] = {
            "user_id": user_id,
            "role": role,
            "password_hash": self._hash_password(password),
            "org_id": org_id,
        }
        return True, user_id

    def authenticate_user(self, org_id: str, email: str,
                         password: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Authenticate user and return JWT token. Returns: (success, token, error_message)"""
        if not email or not password:
            return False, None, "Missing email or password"
        user = self._users.get(email)
        if user is None:
            return False, None, "Invalid email or password"
        if not self._verify_password(password, user["password_hash"]):
            return False, None, "Invalid email or password"
        token = self.generate_jwt(
            user_id=user["user_id"],
            org_id=user["org_id"],
            email=email,
            role=user["role"],
        )
        return True, token, None

    def validate_jwt(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate JWT token.

        Returns: (is_valid, payload, error_message)
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return True, payload, None
        except jwt.ExpiredSignatureError:
            return False, None, "Token expired"
        except jwt.InvalidSignatureError:
            return False, None, "Invalid signature"
        except jwt.DecodeError:
            return False, None, "Invalid token format"

    # ────────────────────────────────────────────────────────────────────
    # JWT OPERATIONS
    # ────────────────────────────────────────────────────────────────────

    def generate_jwt(self, user_id: str, org_id: str, email: str,
                     role: str, expires_in_hours: int = JWT_EXPIRY_HOURS) -> str:
        """Generate JWT token."""
        now = datetime.utcnow()
        expiry = now + timedelta(hours=expires_in_hours)

        payload = {
            "sub": user_id,  # Subject (user ID)
            "org": org_id,   # Organization
            "email": email,
            "role": role,
            "iat": int(now.timestamp()),
            "exp": int(expiry.timestamp()),
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return token

    def refresh_jwt(self, token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Refresh expiring JWT token."""
        is_valid, payload, error = self.validate_jwt(token)

        if not is_valid:
            return False, None, error

        # Generate new token with same claims
        new_token = self.generate_jwt(
            user_id=payload["sub"],
            org_id=payload["org"],
            email=payload["email"],
            role=payload["role"]
        )

        return True, new_token, None

    # ────────────────────────────────────────────────────────────────────
    # RBAC OPERATIONS
    # ────────────────────────────────────────────────────────────────────

    def check_permission(self, role: str, action: str) -> bool:
        """Check if role has permission for action."""
        if role not in ROLE_PERMISSIONS:
            return False

        permissions = ROLE_PERMISSIONS[role].get("permissions", [])
        return action in permissions

    def get_role_permissions(self, role: str) -> Dict[str, Any]:
        """Get all permissions for a role."""
        return ROLE_PERMISSIONS.get(role, {})

    def authorize_action(self, token: str, action: str) -> Tuple[bool, str]:
        """
        Authorize action for user in token.

        Returns: (is_authorized, tenant_org_id)
        """
        is_valid, payload, error = self.validate_jwt(token)

        if not is_valid:
            return False, error

        role = payload.get("role", "viewer")
        org_id = payload.get("org", "")

        if not self.check_permission(role, action):
            return False, f"Permission denied for role {role}"

        return True, org_id

    # ────────────────────────────────────────────────────────────────────
    # TENANT ISOLATION
    # ────────────────────────────────────────────────────────────────────

    def scope_query_to_tenant(self, org_id: str, base_query: str) -> Tuple[str, List[str]]:
        """Return (query_with_placeholder, [org_id]) — NEVER concatenate org_id directly."""
        if not _UUID_RE.match(org_id):
            raise ValueError(f"Invalid org_id format: {org_id!r}")
        placeholder = "AND org_id = %s" if "WHERE" in base_query.upper() else "WHERE org_id = %s"
        return base_query + f" {placeholder}", [org_id]

    def filter_tasks_by_tenant(self, org_id: str,
                              filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get tasks for specific tenant."""
        # TODO: Query PostgreSQL using scope_query_to_tenant result
        return []

    def filter_genesis_logs_by_tenant(self, org_id: str,
                                      filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get Genesis logs for specific tenant."""
        # TODO: Query PostgreSQL using scope_query_to_tenant result
        return []

    # ────────────────────────────────────────────────────────────────────
    # UTILITY
    # ────────────────────────────────────────────────────────────────────

    @staticmethod
    def _hash_password(password: str, salt: bytes = None) -> str:
        """Hash password with salt."""
        if not salt:
            salt = os.urandom(16)

        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return salt.hex() + pwd_hash.hex()

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        salt = bytes.fromhex(password_hash[:32])
        stored_hash = password_hash[32:]

        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return pwd_hash.hex() == stored_hash

    @staticmethod
    def _validate_email(email: str) -> bool:
        """Validate email format."""
        return "@" in email and "." in email.split("@")[1]


class RateLimiter:
    """Token bucket rate limiter per user & endpoint."""

    def __init__(self):
        self.db = get_db()
        # In-memory buckets (Phase 3: move to Redis)
        self.buckets: Dict[str, Dict[str, Any]] = {}

        # Limits
        self.user_limit = 100  # tasks/hour
        self.endpoint_limit = 1000  # req/min
        self.burst_allowance = 100  # tokens

    def check_user_limit(self, user_id: str) -> Tuple[bool, int]:
        """
        Check if user hit task limit (100/hour).

        Returns: (allowed, remaining_tasks)
        """
        key = f"user:{user_id}:tasks"

        if key not in self.buckets:
            self.buckets[key] = {
                "count": 0,
                "window_start": datetime.utcnow(),
            }

        bucket = self.buckets[key]

        # Reset window if older than 1 hour
        if (datetime.utcnow() - bucket["window_start"]).total_seconds() > 3600:
            bucket["count"] = 0
            bucket["window_start"] = datetime.utcnow()

        remaining = self.user_limit - bucket["count"]

        if bucket["count"] >= self.user_limit:
            return False, 0

        bucket["count"] += 1
        return True, remaining - 1

    def check_endpoint_limit(self, endpoint: str) -> Tuple[bool, int]:
        """
        Check if endpoint hit request limit (1000/min).

        Returns: (allowed, remaining_tokens)
        """
        key = f"endpoint:{endpoint}:tokens"

        if key not in self.buckets:
            self.buckets[key] = {
                "tokens": self.burst_allowance,
                "window_start": datetime.utcnow(),
            }

        bucket = self.buckets[key]

        # Reset window if older than 1 minute
        if (datetime.utcnow() - bucket["window_start"]).total_seconds() > 60:
            bucket["tokens"] = self.burst_allowance
            bucket["window_start"] = datetime.utcnow()

        if bucket["tokens"] <= 0:
            return False, 0

        bucket["tokens"] -= 1
        return True, bucket["tokens"]

    def check_crisis_mode_exemption(self, user_id: str, arousal: float) -> bool:
        """
        Crisis mode: bypass rate limits when Arousal > 0.7

        Returns: True if in crisis (exempt from limits)
        """
        return arousal > 0.7


# Singleton instances
_auth = None
_rate_limiter = None

def get_auth() -> AuthManager:
    global _auth
    if _auth is None:
        _auth = AuthManager()
    return _auth

def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
