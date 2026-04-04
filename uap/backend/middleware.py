"""
Unified Admin Panel (UAP) — Phase 3
Middleware for JWT validation & Rate Limiting
"""
import sys
import os
import logging
from functools import wraps
from pathlib import Path
from typing import Callable, Tuple

from flask import request, jsonify, g

sys.path.insert(0, str(Path(__file__).parent))

from auth import get_auth, get_rate_limiter

logger = logging.getLogger("adrion.uap.middleware")

# ────────────────────────────────────────────────────────────────────────────
# JWT AUTH MIDDLEWARE
# ────────────────────────────────────────────────────────────────────────────

def auth_required(f: Callable) -> Callable:
    """
    Decorator: Require valid JWT token in Authorization header.

    Usage:
        @app.route("/api/protected")
        @auth_required
        def protected_endpoint():
            org_id = g.org_id
            user_id = g.user_id
            role = g.role
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header[7:]  # Remove "Bearer " prefix

        auth = get_auth()
        is_valid, payload, error = auth.validate_jwt(token)

        if not is_valid:
            return jsonify({"error": error}), 401

        # Inject into Flask g object
        g.user_id = payload.get("sub")
        g.org_id = payload.get("org")
        g.email = payload.get("email")
        g.role = payload.get("role")
        g.token = token
        g.token_payload = payload  # PRIORITY 8 FIX: Store full payload for crisis mode check

        return f(*args, **kwargs)

    return decorated_function


def require_permission(action: str) -> Callable:
    """
    Decorator: Require specific permission.

    Usage:
        @app.route("/api/create-task")
        @auth_required
        @require_permission("create_task")
        def create_task():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if JWT was validated (auth_required runs first)
            if not hasattr(g, "role"):
                return jsonify({"error": "Authentication required"}), 401

            auth = get_auth()
            if not auth.check_permission(g.role, action):
                return jsonify({
                    "error": f"Permission denied for role {g.role}",
                    "required_permission": action,
                    "user_role": g.role
                }), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def scope_to_tenant(f: Callable) -> Callable:
    """
    Decorator: Automatically scope queries to user's org_id.

    Inject org_id filter into database queries.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, "org_id"):
            return jsonify({"error": "Authentication required"}), 401

        # Store org_id globally so db queries can filter
        g.current_org_id = g.org_id

        return f(*args, **kwargs)

    return decorated_function


# ────────────────────────────────────────────────────────────────────────────
# RATE LIMITING MIDDLEWARE
# ────────────────────────────────────────────────────────────────────────────

def rate_limit_user_tasks(f: Callable) -> Callable:
    """
    Decorator: Enforce per-user task limit (100/hour).

    Applied to task delegation endpoints.
    Crisis mode exemption: Arousal > 0.7 (from JWT payload, NOT user input)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, "user_id"):
            return jsonify({"error": "Authentication required"}), 401

        limiter = get_rate_limiter()

        # PRIORITY 8 FIX: Get arousal from JWT payload (trusted source), NOT from request args
        # Never trust user-supplied arousal value for security decisions
        arousal = g.token_payload.get("arousal", 0.0) if hasattr(g, "token_payload") else 0.0

        if limiter.check_crisis_mode_exemption(g.user_id, arousal):
            # Crisis mode: bypass limit only for authenticated users with high arousal in JWT
            logger.info(f"[PRIORITY 8] Crisis mode exemption granted for user {g.user_id} (arousal={arousal})")
            return f(*args, **kwargs)

        # Normal rate limiting
        allowed, remaining = limiter.check_user_limit(g.user_id)

        if not allowed:
            return jsonify({
                "error": "Task quota exceeded (100 tasks/hour)",
                "reset_in_seconds": 3600,
            }), 429

        # Add rate limit info to response headers (will be set in after_request)
        g.rate_limit_remaining = remaining

        return f(*args, **kwargs)

    return decorated_function


def rate_limit_endpoint(f: Callable) -> Callable:
    """
    Decorator: Enforce per-endpoint request limit (1000/min).

    Applied to all sensitive endpoints.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        endpoint = request.path
        limiter = get_rate_limiter()

        allowed, remaining = limiter.check_endpoint_limit(endpoint)

        if not allowed:
            return jsonify({
                "error": "Endpoint rate limit exceeded (1000 req/min)",
                "reset_in_seconds": 60,
            }), 429

        g.endpoint_rate_limit_remaining = remaining

        return f(*args, **kwargs)

    return decorated_function


# ────────────────────────────────────────────────────────────────────────────
# RESPONSE HEADERS (Add rate limit info)
# ────────────────────────────────────────────────────────────────────────────

def add_rate_limit_headers(response):
    """Add rate limit headers to response."""
    if hasattr(g, "rate_limit_remaining"):
        response.headers["X-RateLimit-Remaining"] = str(g.rate_limit_remaining)
    if hasattr(g, "endpoint_rate_limit_remaining"):
        response.headers["X-RateLimit-Endpoint-Remaining"] = str(g.endpoint_rate_limit_remaining)
    if hasattr(g, "user_id"):
        response.headers["X-User-ID"] = g.user_id
    if hasattr(g, "org_id"):
        response.headers["X-Org-ID"] = g.org_id

    return response


# ────────────────────────────────────────────────────────────────────────────
# REGISTRATION HELPER
# ────────────────────────────────────────────────────────────────────────────

def register_auth_middleware(app):
    """
    Register auth & rate limit middleware with Flask app.

    Usage in main api.py:
        from middleware import register_auth_middleware
        register_auth_middleware(app)
    """
    app.after_request(add_rate_limit_headers)

    print("✅ Auth & Rate Limit Middleware registered:")
    print("   - @auth_required for JWT validation")
    print("   - @require_permission for RBAC")
    print("   - @scope_to_tenant for multi-tenant isolation")
    print("   - @rate_limit_user_tasks for task quota (100/hour)")
    print("   - @rate_limit_endpoint for endpoint limit (1000/min)")
    print("   - Crisis mode exemption (Arousal > 0.7)")
