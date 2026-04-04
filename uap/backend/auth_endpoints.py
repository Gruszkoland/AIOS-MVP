"""
Unified Admin Panel (UAP) — Phase 3
Authentication & Authorization Endpoints
"""
import sys
from pathlib import Path

from flask import Flask, request, jsonify, g

sys.path.insert(0, str(Path(__file__).parent))

from auth import get_auth, get_rate_limiter
from middleware import auth_required, require_permission, scope_to_tenant, rate_limit_user_tasks


def register_auth_endpoints(app: Flask):
    """Register Phase 3 authentication endpoints."""

    auth = get_auth()

    # ────────────────────────────────────────────────────────────────────
    # PUBLIC ENDPOINTS (No auth required)
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/auth/login", methods=["POST"])
    def login():
        """
        User login endpoint.

        Request:
        {
          "org_id": "org-123",
          "email": "user@example.com",
          "password": "secret"
        }

        Response:
        {
          "token": "eyJhbGc...",
          "expires_in": 86400,
          "role": "operator",
          "user_id": "user-123"
        }
        """
        body = request.get_json(silent=True) or {}
        org_id = body.get("org_id", "").strip()
        email = body.get("email", "").strip()
        password = body.get("password", "")

        if not all([org_id, email, password]):
            return jsonify({"error": "Missing org_id, email, or password"}), 400

        success, token, error = auth.authenticate_user(org_id, email, password)

        if not success:
            return jsonify({"error": error}), 401

        return jsonify({
            "token": token,
            "expires_in": 24 * 3600,  # 24 hours
            "token_type": "Bearer",
            "org_id": org_id,
        }), 200

    @app.route("/mapi/v1/auth/refresh", methods=["POST"])
    def refresh():
        """
        Refresh JWT token.

        Request:
        {
          "token": "eyJhbGc..."
        }

        Response:
        {
          "token": "eyJhbGc...",
          "expires_in": 86400
        }
        """
        body = request.get_json(silent=True) or {}
        old_token = body.get("token", "").strip()

        if not old_token:
            return jsonify({"error": "Missing token"}), 400

        success, new_token, error = auth.refresh_jwt(old_token)

        if not success:
            return jsonify({"error": error}), 401

        return jsonify({
            "token": new_token,
            "expires_in": 24 * 3600,
        }), 200

    @app.route("/mapi/v1/auth/register", methods=["POST"])
    def register():
        """
        Register new user (admin-only in production).

        Request:
        {
          "org_id": "org-123",
          "email": "newuser@example.com",
          "password": "secret",
          "role": "operator"  # operator, viewer, healer
        }

        Response:
        {
          "user_id": "user-123",
          "email": "newuser@example.com",
          "role": "operator"
        }
        """
        body = request.get_json(silent=True) or {}
        org_id = body.get("org_id", "").strip()
        email = body.get("email", "").strip()
        password = body.get("password", "")
        role = body.get("role", "operator")

        if not all([org_id, email, password]):
            return jsonify({"error": "Missing required fields"}), 400

        success, user_id = auth.create_user(org_id, email, password, role)

        if not success:
            return jsonify({"error": user_id}), 400

        return jsonify({
            "user_id": user_id,
            "email": email,
            "role": role,
            "org_id": org_id,
        }), 201

    # ────────────────────────────────────────────────────────────────────
    # PROTECTED ENDPOINTS (Require valid JWT)
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/auth/me", methods=["GET"])
    @auth_required
    def get_current_user():
        """Get current user info from JWT."""
        return jsonify({
            "user_id": g.user_id,
            "org_id": g.org_id,
            "email": g.email,
            "role": g.role,
        }), 200

    @app.route("/mapi/v1/auth/permissions", methods=["GET"])
    @auth_required
    def get_user_permissions():
        """Get permissions for current user's role."""
        permissions = auth.get_role_permissions(g.role)

        return jsonify({
            "role": g.role,
            "permissions": permissions.get("permissions", []),
            "description": permissions.get("description", ""),
        }), 200

    @app.route("/mapi/v1/auth/check-permission", methods=["POST"])
    @auth_required
    def check_permission_endpoint():
        """Check if user has specific permission."""
        body = request.get_json(silent=True) or {}
        action = body.get("action", "").strip()

        if not action:
            return jsonify({"error": "Missing action"}), 400

        has_permission = auth.check_permission(g.role, action)

        return jsonify({
            "action": action,
            "role": g.role,
            "has_permission": has_permission,
        }), 200

    @app.route("/mapi/v1/auth/validate-token", methods=["POST"])
    def validate_token():
        """Validate JWT token (used by frontend)."""
        body = request.get_json(silent=True) or {}
        token = body.get("token", "").strip()

        if not token:
            return jsonify({"error": "Missing token"}), 400

        is_valid, payload, error = auth.validate_jwt(token)

        return jsonify({
            "valid": is_valid,
            "error": error,
            "payload": payload if is_valid else None,
        }), 200

    # ────────────────────────────────────────────────────────────────────
    # RATE LIMITING STATUS (Debug endpoint)
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/auth/rate-limit-status", methods=["GET"])
    @auth_required
    def rate_limit_status():
        """Check current rate limit status."""
        limiter = get_rate_limiter()

        user_allowed, user_remaining = limiter.check_user_limit(g.user_id)
        endpoint_allowed, endpoint_remaining = limiter.check_endpoint_limit(request.path)

        return jsonify({
            "user": {
                "allowed": user_allowed,
                "remaining_tasks": user_remaining,
                "limit_per_hour": 100,
            },
            "endpoint": {
                "allowed": endpoint_allowed,
                "remaining_tokens": endpoint_remaining,
                "limit_per_minute": 1000,
            },
            "crisis_mode_active": False,  # TODO: get from WebSocket
        }), 200

    # ────────────────────────────────────────────────────────────────────
    # ROLES & PERMISSIONS MANAGEMENT (Admin-only)
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/admin/roles", methods=["GET"])
    @auth_required
    @require_permission("manage_roles")
    def list_roles():
        """List all available roles and their permissions."""
        from auth import ROLE_PERMISSIONS

        roles = []
        for role, info in ROLE_PERMISSIONS.items():
            roles.append({
                "role": role,
                "permissions": info.get("permissions", []),
                "description": info.get("description", ""),
            })

        return jsonify({"roles": roles}), 200

    @app.route("/mapi/v1/admin/users", methods=["GET"])
    @auth_required
    @require_permission("manage_users")
    def list_users():
        """List users in organization (admin-only)."""
        # TODO: Query PostgreSQL for users where org_id == g.org_id
        return jsonify({
            "org_id": g.org_id,
            "users": []  # Mock
        }), 200

    print("✅ Phase 3 Auth Endpoints registered:")
    print("   POST /mapi/v1/auth/login                   — User login")
    print("   POST /mapi/v1/auth/refresh                 — Refresh token")
    print("   POST /mapi/v1/auth/register                — New user registration")
    print("   GET  /mapi/v1/auth/me                      — Current user info")
    print("   GET  /mapi/v1/auth/permissions             — User permissions")
    print("   POST /mapi/v1/auth/check-permission        — Check specific permission")
    print("   POST /mapi/v1/auth/validate-token          — Validate JWT")
    print("   GET  /mapi/v1/auth/rate-limit-status       — Rate limit info")
    print("   GET  /mapi/v1/admin/roles                  — List roles (admin)")
    print("   GET  /mapi/v1/admin/users                  — List users (admin)")
