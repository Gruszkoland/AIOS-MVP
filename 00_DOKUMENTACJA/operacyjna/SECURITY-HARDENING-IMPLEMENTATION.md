# 🔒 Security Hardening Sprint - Implementation Plan

**Data:** 14.05.2026  
**Sprint:** Sprint 1 / 3  
**Effort:** 9 godzin  

---

## 1️⃣ CRITICAL FIX #1: Remove Hardcoded Secrets

### Problem
```yaml
# config/prod.yaml (lines 12-15) - EXPOSED
database:
  user: "admin"
  password: "prod_secret_2024!"
  host: "db.prod.adrion.dev"
  
api:
  stripe_key: "sk_live_abcd1234xyz"
  sendgrid_key: "SG_key_production_xyz"
```

### Solution
**Approach:** Environment variables + AWS Secrets Manager

```yaml
# config/prod.yaml (SAFE)
database:
  user: "${DB_USER}"
  password: "${DB_PASSWORD}"
  host: "${DB_HOST}"
  
api:
  stripe_key: "${STRIPE_KEY}"
  sendgrid_key: "${SENDGRID_KEY}"
```

### Implementation Steps
1. **Create env var templates** (.env.example)
2. **Update config loader** (use os.getenv with validation)
3. **Migrate to AWS Secrets Manager** (optional, for prod)
4. **Update CI/CD secrets** (GitHub Actions)
5. **Document** (SECURITY.md)

### Code Changes

#### File: `config/prod.yaml`
```yaml
# BEFORE
database:
  user: admin
  password: prod_secret_2024!

# AFTER
database:
  user: ${DB_USER}
  password: ${DB_PASSWORD}
```

#### File: `config/loader.py` (NEW/UPDATED)
```python
import os
from typing import Dict, Any

class ConfigLoader:
    @staticmethod
    def load_prod_config() -> Dict[str, Any]:
        """Load production config from environment variables."""
        return {
            "database": {
                "user": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD"),
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", 5432)),
            },
            "api": {
                "stripe_key": os.getenv("STRIPE_KEY"),
                "sendgrid_key": os.getenv("SENDGRID_KEY"),
            }
        }
    
    @staticmethod
    def validate() -> bool:
        """Validate all required env vars are set."""
        required = ["DB_USER", "DB_PASSWORD", "DB_HOST", "STRIPE_KEY"]
        missing = [v for v in required if not os.getenv(v)]
        if missing:
            raise ValueError(f"Missing env vars: {missing}")
        return True
```

#### File: `.env.example` (NEW)
```env
# Database
DB_USER=admin
DB_PASSWORD=your-secure-password-here
DB_HOST=db.prod.adrion.dev
DB_PORT=5432

# API Keys
STRIPE_KEY=sk_live_your_key_here
SENDGRID_KEY=SG_your_key_here
```

### Testing
```bash
# Test config loading
pytest tests/test_config.py::test_prod_config_loads

# Test env var validation
pytest tests/test_config.py::test_missing_env_var_raises
```

### Effort: **2 hours**

---

## 2️⃣ CRITICAL FIX #2: SQL Injection Prevention

### Problem
```python
# core/queries.py (lines 45-52) - VULNERABLE
def get_user_by_id(user_id: str) -> Dict:
    """Get user by ID - VULNERABLE TO INJECTION."""
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    result = db.execute(query)
    return result.to_dict()

# Attack: user_id = "'; DROP TABLE users; --"
# Result: SELECT * FROM users WHERE id = ''; DROP TABLE users; --'
```

### Solution
**Approach:** Parameterized queries (prepared statements)

```python
def get_user_by_id(user_id: str) -> Dict:
    """Get user by ID - SAFE."""
    query = "SELECT * FROM users WHERE id = %s"
    result = db.execute(query, (user_id,))
    return result.to_dict()
```

### Implementation Steps
1. **Scan all SQL queries** in core/queries.py
2. **Convert to parameterized** queries
3. **Add input validation** (types, lengths)
4. **Test with SQLi payloads** (OWASP list)
5. **Code review** security-focused

### Code Changes

#### File: `core/queries.py` (UPDATED)
```python
from typing import Dict, Any, List, Optional

class UserQueries:
    """Safe SQL queries using parameterized statements."""
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict]:
        """Get user by ID - SAFE parameterized query."""
        query = "SELECT id, email, name, role FROM users WHERE id = %s"
        result = db.execute(query, (user_id,))
        return result.to_dict() if result else None
    
    @staticmethod
    def get_users_by_role(role: str, limit: int = 100) -> List[Dict]:
        """Get users by role - SAFE parameterized."""
        if limit > 1000:
            limit = 1000  # Prevent denial of service
        query = "SELECT id, email, name FROM users WHERE role = %s LIMIT %s"
        results = db.execute(query, (role, limit))
        return [r.to_dict() for r in results]
    
    @staticmethod
    def search_users(search_term: str) -> List[Dict]:
        """Search users - SAFE with parameterized query."""
        # Use LIKE with parameterized query
        query = "SELECT id, email, name FROM users WHERE email LIKE %s OR name LIKE %s"
        # Escape wildcards manually to prevent bypass
        search_pattern = f"%{search_term.replace('%', '\\%').replace('_', '\\_')}%"
        results = db.execute(query, (search_pattern, search_pattern))
        return [r.to_dict() for r in results]
    
    @staticmethod
    def update_user(user_id: str, email: str, name: str) -> bool:
        """Update user - SAFE parameterized."""
        query = "UPDATE users SET email = %s, name = %s WHERE id = %s"
        return db.execute(query, (email, name, user_id)).affected_rows > 0
    
    @staticmethod
    def delete_user(user_id: str) -> bool:
        """Delete user - SAFE parameterized."""
        query = "DELETE FROM users WHERE id = %s"
        return db.execute(query, (user_id,)).affected_rows > 0
```

#### File: `core/validators.py` (NEW)
```python
import re
from typing import Tuple

class InputValidators:
    """Input validation to complement parameterized queries."""
    
    @staticmethod
    def validate_user_id(user_id: str) -> Tuple[bool, str]:
        """Validate user ID format."""
        if not user_id:
            return False, "User ID cannot be empty"
        if not re.match(r'^[a-zA-Z0-9_\-]{1,64}$', user_id):
            return False, "Invalid user ID format"
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format."""
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return False, "Invalid email format"
        return True, ""
    
    @staticmethod
    def validate_sql_search_term(term: str, max_length: int = 100) -> Tuple[bool, str]:
        """Validate search term."""
        if len(term) > max_length:
            return False, f"Search term too long (max {max_length})"
        if re.search(r'[;\'"\-\-]', term):
            return False, "Invalid characters in search term"
        return True, ""
```

### Testing
```python
# tests/test_queries.py
import pytest
from core.queries import UserQueries

class TestSQLInjectionPrevention:
    
    def test_sql_injection_in_id(self, db):
        """Test that SQL injection is prevented."""
        # This should NOT drop table
        result = UserQueries.get_user_by_id("'; DROP TABLE users; --")
        assert result is None  # User not found
        
        # Verify table still exists
        count = db.execute("SELECT COUNT(*) FROM users").scalar()
        assert count >= 0
    
    def test_sql_injection_in_search(self, db):
        """Test search protection."""
        result = UserQueries.search_users("% OR 1=1 --")
        # Should search for literal string, not return all users
        assert all("% OR 1=1 --" in r['email'] or "% OR 1=1 --" in r['name'] 
                  for r in result)
    
    def test_valid_queries_work(self, db):
        """Test legitimate queries still work."""
        user = UserQueries.get_user_by_id("user123")
        assert user is not None
        assert user['id'] == "user123"
```

### Effort: **2 hours**

---

## 3️⃣ HIGH FIX #1: API Authentication

### Problem
```python
# mcp_servers/router.py (lines 78-85) - NO AUTHENTICATION
@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json()
    return oracle_service.predict(data)

# Anyone can call this endpoint!
```

### Solution
**Approach:** API Key authentication middleware

```python
@app.route('/api/predict', methods=['POST'])
@require_api_key
def predict():
    data = request.get_json()
    return oracle_service.predict(data)
```

### Implementation Steps
1. **Create API key management** (database table)
2. **Implement auth middleware** (decorator)
3. **Generate test keys** (for clients)
4. **Update all endpoints** with @require_api_key
5. **Document for clients** (how to use keys)

### Code Changes

#### File: `mcp_servers/auth.py` (NEW)
```python
from functools import wraps
from flask import request, jsonify
import hashlib
import os

class APIKeyManager:
    """Manage API keys for authentication."""
    
    @staticmethod
    def verify_api_key(api_key: str) -> bool:
        """Verify API key from database."""
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Hash the key before looking it up
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Query database
        from core.models import APIKey
        key_record = APIKey.query.filter_by(key_hash=key_hash, active=True).first()
        
        return key_record is not None
    
    @staticmethod
    def generate_api_key(client_name: str) -> str:
        """Generate new API key for client."""
        import secrets
        from core.models import APIKey
        
        # Generate random key
        raw_key = f"sk_{client_name}_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # Store hash in database
        key_record = APIKey(name=client_name, key_hash=key_hash, active=True)
        db.session.add(key_record)
        db.session.commit()
        
        return raw_key  # Return only once


def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({"error": "Missing X-API-Key header"}), 401
        
        if not APIKeyManager.verify_api_key(api_key):
            return jsonify({"error": "Invalid API key"}), 401
        
        # Add key info to request context for logging
        request.api_key = api_key[:10] + "..." # For logging
        
        return f(*args, **kwargs)
    
    return decorated_function
```

#### File: `core/models.py` (ADD APIKey model)
```python
from datetime import datetime

class APIKey(db.Model):
    """API Key for client authentication."""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Client name
    key_hash = db.Column(db.String(64), unique=True, nullable=False)  # SHA256 hash
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    
    def __repr__(self):
        return f"<APIKey {self.name}>"
```

#### File: `mcp_servers/router.py` (UPDATE endpoints)
```python
from auth import require_api_key

# All endpoints that were public now require auth
@app.route('/api/predict', methods=['POST'])
@require_api_key
def predict():
    """ML prediction endpoint."""
    data = request.get_json()
    return oracle_service.predict(data)

@app.route('/api/analyze', methods=['POST'])
@require_api_key
def analyze():
    """Data analysis endpoint."""
    data = request.get_json()
    return guardian_service.analyze(data)

@app.route('/api/health', methods=['GET'])
# Health check can be public
def health():
    """Service health endpoint (no auth required)."""
    return {"status": "ok"}
```

### Documentation

#### File: `docs/API-AUTHENTICATION.md` (NEW)
```markdown
# API Authentication Guide

## Getting an API Key

1. Contact: api@adrion.dev
2. Request: Provide client name
3. Receive: Your API key (store securely!)

Example response:
```
sk_yourcompany_abc123def456xyz789...
```

## Using Your API Key

Add header to all requests:

```bash
curl -X POST http://api.adrion.dev/api/predict \
  -H "X-API-Key: sk_yourcompany_abc123def456xyz789..." \
  -H "Content-Type: application/json" \
  -d '{"data": [...]}' 
```

## Security

- Store keys securely (use env vars, not hardcoded)
- Never commit keys to git
- Rotate keys regularly
- Contact us if key is exposed
```

### Testing
```bash
# Test missing key
curl -X POST http://localhost:8000/api/predict # Should return 401

# Test invalid key
curl -X POST http://localhost:8000/api/predict \
  -H "X-API-Key: invalid_key" # Should return 401

# Test valid key
curl -X POST http://localhost:8000/api/predict \
  -H "X-API-Key: sk_test_valid_key" # Should work
```

### Effort: **2 hours**

---

## 4️⃣ HIGH FIX #2: Audit Logging

### Problem
```python
# guardian_mcp.py (lines 120-135) - NO AUDIT LOGGING
def validate_request(request):
    """Validate incoming request - NO LOGGING."""
    if not is_valid(request):
        return False
    # No record of who validated what
    return True
```

### Solution
**Approach:** Comprehensive audit logging middleware

```python
def validate_request(request):
    """Validate incoming request with audit logging."""
    is_valid = check_validity(request)
    
    logger.audit(
        event="request_validation",
        user_id=request.user_id,
        endpoint=request.path,
        status="success" if is_valid else "failure",
        timestamp=datetime.utcnow()
    )
    
    return is_valid
```

### Implementation Steps
1. **Create audit logger** (custom handler)
2. **Add audit table** to database (90-day retention)
3. **Middleware integration** for auto-logging
4. **Monitoring dashboard** in Grafana
5. **Alert rules** for suspicious activity

### Code Changes

#### File: `core/audit.py` (NEW)
```python
import logging
from datetime import datetime
from core.models import AuditLog

class AuditLogger:
    """Structured audit logging."""
    
    def __init__(self, logger_name: str = "audit"):
        self.logger = logging.getLogger(logger_name)
    
    def log(self, event: str, **kwargs):
        """Log audit event to database and file."""
        # Database record
        audit_record = AuditLog(
            event=event,
            user_id=kwargs.get('user_id'),
            endpoint=kwargs.get('endpoint'),
            status=kwargs.get('status'),
            details=kwargs.get('details', {}),
            timestamp=datetime.utcnow()
        )
        db.session.add(audit_record)
        db.session.commit()
        
        # File logging (for immediate visibility)
        log_msg = f"AUDIT: {event} | User: {kwargs.get('user_id')} | Status: {kwargs.get('status')}"
        self.logger.info(log_msg)

# Global audit logger
audit = AuditLogger()
```

#### File: `core/models.py` (ADD AuditLog model)
```python
from datetime import datetime, timedelta

class AuditLog(db.Model):
    """Audit trail for compliance and security."""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.String(100))
    endpoint = db.Column(db.String(255))
    status = db.Column(db.String(20))  # success, failure, warning
    details = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.event} at {self.timestamp}>"
    
    @classmethod
    def cleanup_old_records(cls, days=90):
        """Delete audit logs older than N days (GDPR compliance)."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cls.query.filter(cls.timestamp < cutoff_date).delete()
        db.session.commit()
```

#### File: `mcp_servers/guardian_mcp.py` (UPDATE)
```python
from core.audit import audit

def validate_request(request):
    """Validate incoming request with audit logging."""
    try:
        is_valid = _validate_internal(request)
        
        # Audit the validation
        audit.log(
            event="request_validation",
            user_id=request.user_id,
            endpoint=request.path,
            status="success" if is_valid else "failure",
            details={
                "method": request.method,
                "content_type": request.content_type,
                "size": len(request.data)
            }
        )
        
        return is_valid
        
    except Exception as e:
        # Log failures too
        audit.log(
            event="validation_error",
            user_id=request.user_id,
            endpoint=request.path,
            status="error",
            details={"error": str(e)}
        )
        raise
```

### Database Maintenance

#### Script: `scripts/cleanup_audit_logs.py` (NEW)
```python
#!/usr/bin/env python
"""Cleanup old audit logs for GDPR compliance."""

from core.models import AuditLog, db

if __name__ == "__main__":
    # Keep 90 days of audit logs
    AuditLog.cleanup_old_records(days=90)
    print("Old audit logs cleaned up")
```

### Monitoring

#### Grafana Dashboard: Audit Events
```
Queries:
  1. Failed validations (last 24h)
  2. Most active users
  3. Suspicious patterns (5+ failures in 5 min)
  4. API endpoint usage
```

### Testing
```python
def test_audit_logging(db):
    """Test that events are logged."""
    audit.log(
        event="test_event",
        user_id="test_user",
        endpoint="/api/test",
        status="success"
    )
    
    # Verify in database
    record = AuditLog.query.filter_by(event="test_event").first()
    assert record is not None
    assert record.user_id == "test_user"
```

### Effort: **1.5 hours**

---

## 5️⃣ MEDIUM FIX: Update Dependencies

### Problem
```
OUTDATED PACKAGES:
  flask==1.1.2 (released 2019)
  requests==2.20.0 (released 2018)
  [12 packages with known CVEs]
```

### Solution
**Approach:** Update to latest secure versions

```
flask==1.1.2     →  flask==2.3.2
requests==2.20.0 →  requests==2.31.0
```

### Implementation Steps
1. **Audit current deps** (pip list, safety check)
2. **Check compatibility** (test suite)
3. **Update requirements.txt**
4. **Run full test suite**
5. **Verify performance** (no regressions)

### Code Changes

#### File: `requirements.txt` (UPDATED)
```
# Core
Flask==2.3.2
requests==2.31.0
python-dotenv==1.0.0
PyYAML==6.0

# Database
SQLAlchemy==2.0.19
psycopg2-binary==2.9.6

# Testing
pytest==7.3.1
pytest-cov==4.1.0

# Production
gunicorn==20.1.0
```

### Testing Strategy
```bash
# Run full test suite
pytest --cov=core --cov=mcp_servers

# Security check
safety check

# Performance baseline
python -m pytest tests/benchmarks/ --benchmark-only
```

### Effort: **1.5 hours**

---

## 📊 Summary

| Fix | Type | Effort | Status |
|-----|------|--------|--------|
| Remove secrets | CRITICAL | 2h | ⏳ PENDING |
| SQL injection | CRITICAL | 2h | ⏳ PENDING |
| API auth | HIGH | 2h | ⏳ PENDING |
| Audit logging | HIGH | 1.5h | ⏳ PENDING |
| Dependencies | MEDIUM | 1.5h | ⏳ PENDING |
| **TOTAL** | - | **9h** | ⏳ PENDING |

---

## 🚀 Next Steps

1. ✅ Review implementation plan
2. ✅ Get security team approval
3. ⏳ Clone ADRION-369 repository
4. ⏳ Create security-hardening branch
5. ⏳ Implement all 5 fixes
6. ⏳ Test comprehensively
7. ⏳ Create pull request
8. ⏳ Deploy to staging
9. ⏳ Deploy to production

---

*Plan prepared: 14.05.2026*  
*Version: 1.0*  
*Ready for implementation*
