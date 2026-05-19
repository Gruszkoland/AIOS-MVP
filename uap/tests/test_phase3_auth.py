"""
Phase 3 Auth Module — pytest tests
Verify JWT, RBAC, Rate Limiting, SQL injection guard
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Inject test credentials before importing auth (avoids sys.exit in production check)
os.environ.setdefault("UAP_ADMIN_EMAIL", "admin@test.local")
os.environ.setdefault("UAP_ADMIN_PASSWORD", "test-password-for-unit-tests")
# Ensure we're not in production mode
os.environ.pop("ENVIRONMENT", None)


@pytest.fixture()
def auth():
    from backend.auth import AuthManager
    return AuthManager()


@pytest.fixture()
def auth_with_user(auth):
    """AuthManager pre-populated with a regular test user."""
    ok, _user_id = auth.create_user(
        org_id="00000000-0000-0000-0000-000000000001",
        email="testuser@test.local",
        password="correct-password",
        role="operator",
    )
    assert ok, "create_user failed in fixture"
    return auth


# ── Test 1: empty password is rejected ───────────────────────────────────────

def test_authenticate_empty_password_returns_false(auth):
    success, token, error = auth.authenticate_user("", "admin@test.local", "")
    assert success is False
    assert token is None
    assert error is not None


# ── Test 2: wrong password is rejected ───────────────────────────────────────

def test_authenticate_wrong_password_returns_false(auth_with_user):
    success, token, error = auth_with_user.authenticate_user(
        "00000000-0000-0000-0000-000000000001",
        "testuser@test.local",
        "wrong-password",
    )
    assert success is False
    assert token is None
    assert error is not None


# ── Test 3: correct credentials return True + valid JWT ──────────────────────

def test_authenticate_correct_credentials_returns_jwt(auth_with_user):
    success, token, error = auth_with_user.authenticate_user(
        "00000000-0000-0000-0000-000000000001",
        "testuser@test.local",
        "correct-password",
    )
    assert success is True
    assert token is not None
    assert error is None

    # The returned token must be verifiable
    is_valid, payload, _ = auth_with_user.validate_jwt(token)
    assert is_valid is True
    assert payload["email"] == "testuser@test.local"
    assert payload["role"] == "operator"


# ── Test 4: forged JWT is rejected ───────────────────────────────────────────

def test_validate_forged_jwt_returns_false(auth):
    forged = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiJoYWNrZXIiLCJyb2xlIjoiYWRtaW4ifQ"
        ".FAKE_SIGNATURE_XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    )
    is_valid, payload, error = auth.validate_jwt(forged)
    assert is_valid is False
    assert payload is None
    assert error is not None


# ── Test 5: non-UUID org_id raises ValueError ─────────────────────────────────

def test_scope_query_non_uuid_raises(auth):
    with pytest.raises(ValueError, match="Invalid org_id"):
        auth.scope_query_to_tenant("'; DROP TABLE users; --", "SELECT 1")


def test_scope_query_valid_uuid_appends_clause(auth):
    valid_uuid = "12345678-1234-1234-1234-123456789abc"
    query, params = auth.scope_query_to_tenant(
        valid_uuid, "SELECT * FROM tasks WHERE active = true"
    )
    assert "AND org_id = %s" in query
    assert params == [valid_uuid]


# ── Test 6: rate limiter blocks after user_limit requests ────────────────────

def test_rate_limiter_blocks_after_limit():
    from backend.auth import RateLimiter
    limiter = RateLimiter()
    limiter.user_limit = 5  # lower limit for fast test

    results = [limiter.check_user_limit("test-user-999") for _ in range(6)]
    allowed_flags = [allowed for allowed, _ in results]

    # First 5 should be allowed, 6th should be blocked
    assert all(allowed_flags[:5]), "Expected first 5 requests to be allowed"
    assert allowed_flags[5] is False, "Expected 6th request to be blocked"
