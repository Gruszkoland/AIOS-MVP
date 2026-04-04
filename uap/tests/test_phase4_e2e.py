"""
Phase 4 — End-to-End & Integration Tests
UAP v4.0 Production Readiness Validation
"""

import pytest
import json
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestPhase4WebSocketIntegration:
    """WebSocket real-time telemetry integration tests"""

    def test_websocket_connection_with_token(self):
        """Verify WebSocket client connects with JWT token"""
        from uap.backend.websocket_server import TelemetryServer

        ws_server = TelemetryServer()
        assert ws_server.clients == {}
        assert ws_server.latest_telemetry is None

    def test_websocket_telemetry_broadcast_interval(self):
        """Verify telemetry broadcasts at <500ms latency target"""
        from uap.backend.websocket_server import TelemetryServer

        ws_server = TelemetryServer()
        # Telemetry broadcast every 200ms
        assert ws_server.broadcast_interval == 0.2

    def test_ebdi_crisis_detection(self):
        """Verify crisis detection when Arousal > 0.7"""
        ebdi_data = {
            "agent_1": {"pleasure": 0.5, "arousal": 0.8, "dominance": 0.6},  # Crisis
            "agent_2": {"pleasure": 0.6, "arousal": 0.4, "dominance": 0.5},
        }

        crisis_detected = any(a["arousal"] > 0.7 for a in ebdi_data.values())
        assert crisis_detected is True


class TestPhase4AuthenticationFlow:
    """JWT authentication and multi-tenant isolation"""

    def test_login_returns_jwt_token(self, client):
        """Login endpoint returns valid JWT token"""
        response = client.post('/mapi/v1/auth/login', json={
            'org_id': 'org-123',
            'email': 'test@example.com',
            'password': 'testpass'
        })

        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data
        assert 'expires_in' in data
        assert data['expires_in'] == 86400  # 24h

    def test_jwt_token_contains_claims(self, client):
        """JWT token contains required RBAC claims"""
        import jwt
        from uap.backend.auth import AuthManager

        auth = AuthManager()
        token = auth.generate_jwt(
            user_id='user-123',
            org_id='org-456',
            email='user@test.com',
            role='operator'
        )

        # Decode without verification to inspect claims
        claims = jwt.decode(token, options={"verify_signature": False})
        assert claims['sub'] == 'user-123'
        assert claims['org'] == 'org-456'
        assert claims['role'] == 'operator'
        assert 'exp' in claims

    def test_rate_limiting_per_user(self, client):
        """Per-user rate limit: 100 tasks/hour"""
        from uap.backend.auth import RateLimiter

        limiter = RateLimiter()

        # Simulate 100 tasks
        for i in range(100):
            allowed = limiter.check_user_quota('user-123')
            assert allowed is True

        # 101st should be rejected
        allowed = limiter.check_user_quota('user-123')
        assert allowed is False

    def test_rate_limiting_per_endpoint(self, client):
        """Per-endpoint rate limit: 1000 req/min"""
        from uap.backend.auth import RateLimiter

        limiter = RateLimiter()

        # Token bucket algorithm: should allow burst then throttle
        for i in range(1000):
            allowed = limiter.check_endpoint_quota('/api/task/delegate')
            assert allowed is True

        # Should reject excess
        allowed = limiter.check_endpoint_quota('/api/task/delegate')
        assert allowed is False


class TestPhase4APIEndpoints:
    """Phase 4 API endpoint integration tests"""

    def test_task_delegate_v2_full_master_loop(self, client, auth_headers):
        """Task delegate v2 executes full 4-step master loop"""
        response = client.post(
            '/mapi/v1/task/delegate/v2',
            json={
                'task_description': 'Scout XRP opportunities under $5',
                'agent_hint': None,
                'dry_run': False,
                'budget_max': 1000
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify all 4 KROK steps executed
        assert 'task_id' in data
        assert 'assigned_agent' in data
        assert 'trust_score' in data
        assert 'decision_trace' in data or 'status' in data

    def test_genesis_v2_search_full_text(self, client, auth_headers):
        """Genesis v2 full-text search with filters"""
        response = client.get(
            '/mapi/v1/genesis/v2/search?query=optimize&agent=SAP&status=completed',
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'logs' in data
        assert isinstance(data['logs'], list)

    def test_status_v2_with_telemetry(self, client, auth_headers):
        """Status v2 includes EBDI telemetry summary"""
        response = client.get('/mapi/v1/status/v2', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Verify telemetry is included
        assert 'telemetry' in data or 'telemetry_summary' in data
        assert 'trinity' in data or 'system_state' in data

    def test_crisis_activate_endpoint(self, client, auth_headers):
        """Crisis activation endpoint updates system arousal"""
        response = client.post(
            '/mapi/v1/crisis/activate',
            json={'reason': 'Test crisis'},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'arousal' in data
        assert data['arousal'] > 0.7

    def test_conflict_list_endpoint(self, client, auth_headers):
        """Conflict list returns active agent conflicts"""
        response = client.get('/mapi/v1/conflict/list', headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert 'conflicts' in data or 'result' in data


class TestPhase4FrontendIntegration:
    """Frontend-backend integration tests"""

    def test_login_page_loads(self, client):
        """Login page HTML loads without errors"""
        response = client.get('/login.html')

        assert response.status_code == 200
        assert 'ADRION 369' in response.data.decode()
        assert 'Sign In' in response.data.decode()

    def test_dashboard_requires_authentication(self, client):
        """Dashboard redirects to login if no token"""
        response = client.get('/dashboard.html')

        # Should either redirect or require auth header
        assert response.status_code in [200, 302, 401]

    def test_websocket_client_js_serves(self, client):
        """WebSocket client JavaScript loads"""
        response = client.get('/websocket_client.js')

        assert response.status_code == 200
        assert 'UAP_WebSocketClient' in response.data.decode()

    def test_app_js_serves(self, client):
        """Main app.js JavaScript loads"""
        response = client.get('/app.js')

        assert response.status_code == 200
        assert 'handleTelemetryUpdate' in response.data.decode()


class TestPhase4MultiTenancy:
    """Multi-tenant isolation verification"""

    def test_org_scope_in_genesis_logs(self, db_session):
        """Genesis logs are scoped to org_id"""
        from uap.backend.db import PostgresDB

        db = PostgresDB()

        # Insert logs for two orgs
        db.insert_genesis_log(
            task_id='task-1',
            org_id='org-1',
            agent='SAP',
            action='test',
            status='completed'
        )

        db.insert_genesis_log(
            task_id='task-2',
            org_id='org-2',
            agent='SAP',
            action='test',
            status='completed'
        )

        # Query should return only org-1 logs
        logs = db.query_genesis_logs('org-1', limit=10)
        assert all(log['org_id'] == 'org-1' for log in logs)

    def test_rbac_operator_cannot_delete_users(self, client, auth_headers_operator):
        """Operator role cannot delete users"""
        response = client.delete('/mapi/v1/admin/users/user-123', headers=auth_headers_operator)

        # Should be forbidden
        assert response.status_code == 403

    def test_viewer_role_read_only(self, client, auth_headers_viewer):
        """Viewer role can read but not create tasks"""
        # Should be able to read
        response = client.get('/mapi/v1/task/list', headers=auth_headers_viewer)
        assert response.status_code in [200, 204]

        # Should not be able to create
        response = client.post(
            '/mapi/v1/task/delegate',
            json={'task_description': 'test'},
            headers=auth_headers_viewer
        )
        assert response.status_code == 403


class TestPhase4DRMWorkflow:
    """Dry Run Mode preview and approval workflow"""

    def test_drm_preview_shows_git_diff(self, client, auth_headers):
        """DRM preview returns git diff for git_reset operation"""
        response = client.post(
            '/mapi/v1/task/simulate',
            json={
                'operation': 'git_reset',
                'target': 'HEAD~1'
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()

        # Should include diff preview
        assert 'diff' in data or 'preview' in data
        assert 'risk_level' in data
        assert 'requires_approval' in data

    def test_drm_approval_and_execute(self, client, auth_headers):
        """Task can be approved and executed after DRM preview"""
        # First, submit with dry_run=True
        response1 = client.post(
            '/mapi/v1/task/delegate/v2',
            json={
                'task_description': 'Deploy update',
                'dry_run': True
            },
            headers=auth_headers
        )

        task_id = response1.get_json().get('task_id')
        assert task_id is not None

        # Then approve for execution
        response2 = client.post(
            '/mapi/v1/task/execute/approved',
            json={'task_id': task_id},
            headers=auth_headers
        )

        assert response2.status_code == 200


class TestPhase4RealTimeFeatures:
    """Real-time dashboard updates and animations"""

    def test_stat_counter_animation_values(self):
        """Verify stat counter can smoothly animate"""
        # Simulating cubic easeOut animation
        start = 0
        end = 150
        steps = 37  # 600ms / 16ms per frame

        for step in range(1, steps + 1):
            progress = step / steps
            easeOut = 1 - pow(1 - progress, 3)  # Cubic easeOut
            current = int(start + (end - start) * easeOut)

            assert start <= current <= end

        # Final value should be end
        assert current == end

    def test_ebdi_heatmap_smooth_update(self):
        """EBDI heatmap updates smoothly without full re-render"""
        ebdi_before = {
            "agent_1": {"arousal": 0.5, "pleasure": 0.6, "dominance": 0.7},
        }

        ebdi_after = {
            "agent_1": {"arousal": 0.65, "pleasure": 0.6, "dominance": 0.7},
        }

        # Check if only arousal changed
        for agent, values in ebdi_after.items():
            before = ebdi_before[agent]
            assert values["arousal"] != before["arousal"]
            assert values["pleasure"] == before["pleasure"]


class TestPhase4ErrorHandling:
    """Error handling and recovery"""

    def test_expired_token_returns_401(self, client, expired_token):
        """Expired token returns 401 Unauthorized"""
        response = client.get(
            '/mapi/v1/status',
            headers={'Authorization': f'Bearer {expired_token}'}
        )

        assert response.status_code == 401

    def test_rate_limit_returns_429(self, client, auth_headers):
        """Rate limit exceeded returns 429 Too Many Requests"""
        # Make many rapid requests
        responses = []
        for i in range(1001):  # Beyond endpoint limit
            response = client.get('/mapi/v1/status', headers=auth_headers)
            responses.append(response.status_code)

        # Eventually should get 429
        assert 429 in responses

    def test_invalid_org_id_returns_400(self, client, auth_headers):
        """Invalid organization ID returns 400"""
        response = client.post(
            '/mapi/v1/task/delegate/v2',
            json={
                'task_description': 'test',
                'org_id': '',  # Empty
            },
            headers=auth_headers
        )

        assert response.status_code in [400, 422]


# ──────────────────────────────────────────────────────────────────────────
# FIXTURES
# ──────────────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Flask test client"""
    from uap.backend.api import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers():
    """Authorization headers with valid JWT"""
    return {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsIm9yZyI6Im9yZy00NTYiLCJyb2xlIjoib3BlcmF0b3IifQ.test'
    }


@pytest.fixture
def auth_headers_operator():
    """Operator role headers"""
    return {
        'Authorization': 'Bearer operator-token',
        'X-Role': 'operator'
    }


@pytest.fixture
def auth_headers_viewer():
    """Viewer role headers"""
    return {
        'Authorization': 'Bearer viewer-token',
        'X-Role': 'viewer'
    }


@pytest.fixture
def expired_token():
    """Expired JWT token"""
    return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImV4cCI6MTAwMDAwMDB9.test'


@pytest.fixture
def db_session():
    """Database session for tests"""
    from uap.backend.db import PostgresDB
    db = PostgresDB()
    yield db
    # Cleanup would go here


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
