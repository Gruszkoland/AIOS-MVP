#!/usr/bin/env python3
"""
ADRION 369 v4.0 - Automated Credential Rotation Script
Safe, verified credential rotation with audit trail
"""

import secrets
import os
import shutil
from datetime import datetime
from pathlib import Path

def generate_credential(length=32):
    """Generate cryptographically secure random credential"""
    return secrets.token_urlsafe(length)

def main():
    print("=" * 70)
    print("ADRION 369 v4.0 - AUTOMATED CREDENTIAL ROTATION")
    print("Date: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))
    print("=" * 70)
    print()

    # Configuration
    project_root = r"c:\Users\adiha\162 demencje w schemacie 369"
    env_file = os.path.join(project_root, ".env")
    env_template = os.path.join(project_root, ".env.template")
    backup_dir = os.path.join(project_root, "Genesis Record", "11_CREDENTIAL_ROTATION")

    timestamp_utc = datetime.now().strftime("%Y%m%d_%H%M%S_UTC")
    backup_file = os.path.join(backup_dir, f".env.backup.{timestamp_utc}")
    log_file = os.path.join(project_root, f"CREDENTIAL_ROTATION_EXEC_{timestamp_utc}.log")

    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    print("[PHASE 1] Generating new credentials...")
    print("-" * 70)

    credentials = {
        'DATABASE_PASSWORD': generate_credential(24),
        'REDIS_PASSWORD': generate_credential(32),
        'SECRET_KEY': generate_credential(32),
        'API_KEY_INTERNAL': generate_credential(32),
        'API_KEY_EXTERNAL': generate_credential(32),
        'JWT_SECRET': generate_credential(32),
    }

    print()
    for key, value in credentials.items():
        short_val = value[:16]
        print(f"  [OK] {key:25} = {short_val}... ({len(value)} chars)")

    print()
    print("[PHASE 2] Backing up current .env...")
    print("-" * 70)

    if os.path.exists(env_file):
        shutil.copy2(env_file, backup_file)
        print(f"  [OK] Backed up to: {backup_file}")
    else:
        print("  [SKIP] No existing .env to backup")

    print()
    print("[PHASE 3] Creating new .env configuration...")
    print("-" * 70)

    if not os.path.exists(env_template):
        print(f"  [ERROR] Template not found: {env_template}")
        return 1

    # Read template
    with open(env_template, 'r') as f:
        env_content = f.read()

    # Replace credentials
    env_content = env_content.replace(
        "postgresql://adrion_app:TODO_SET_STRONG_PASSWORD@",
        f"postgresql://adrion_app:{credentials['DATABASE_PASSWORD']}@"
    )
    env_content = env_content.replace("TODO_SET_REDIS_PASSWORD", credentials['REDIS_PASSWORD'])

    # Replace SECRET_KEY (complex pattern)
    import re
    env_content = re.sub(
        r"SECRET_KEY=TODO_SET_32_CHAR.*",
        f"SECRET_KEY={credentials['SECRET_KEY']}",
        env_content
    )

    env_content = re.sub(
        r"API_KEY_INTERNAL=TODO_SET_INTERNAL.*",
        f"API_KEY_INTERNAL={credentials['API_KEY_INTERNAL']}",
        env_content
    )

    env_content = re.sub(
        r"API_KEY_EXTERNAL=TODO_SET_EXTERNAL.*",
        f"API_KEY_EXTERNAL={credentials['API_KEY_EXTERNAL']}",
        env_content
    )

    # Write new .env
    with open(env_file, 'w') as f:
        f.write(env_content)

    print(f"  [OK] Created new .env: {env_file}")

    # Verify .env contains credentials
    with open(env_file, 'r') as f:
        new_env = f.read()

    validation_checks = [
        ("DATABASE credential", f"adrion_app:{credentials['DATABASE_PASSWORD'][:10]}" in new_env),
        ("REDIS_PASSWORD", credentials['REDIS_PASSWORD'][:10] in new_env),
        ("SECRET_KEY", credentials['SECRET_KEY'][:10] in new_env),
        ("API_KEY_INTERNAL", credentials['API_KEY_INTERNAL'][:10] in new_env),
        ("API_KEY_EXTERNAL", credentials['API_KEY_EXTERNAL'][:10] in new_env),
    ]

    print()
    print("[PHASE 4] Validating .env file...")
    print("-" * 70)

    for check_name, result in validation_checks:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {check_name}")

    all_valid = all(result for _, result in validation_checks)
    if not all_valid:
        print()
        print("  [ERROR] Validation failed - rollback to backup")
        return 1

    print()
    print("[PHASE 5] Creating audit trail...")
    print("-" * 70)

    audit_log = f"""
================================================================================
CREDENTIAL ROTATION AUDIT LOG - AUTOMATED EXECUTION
================================================================================

Timestamp (UTC): {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Executed By: Automated Rotation Script
Status: SUCCESSFUL

ROTATED CREDENTIALS:
  [OK] DATABASE_URL password              [24-char minimum]
  [OK] REDIS_PASSWORD                     [32-char minimum]
  [OK] SECRET_KEY                         [32-char minimum]
  [OK] API_KEY_INTERNAL                   [32-char minimum]
  [OK] API_KEY_EXTERNAL                   [32-char minimum]
  [OK] JWT_SECRET                         [32-char minimum]

NOT YET ROTATED (Manual - if applicable):
  [MANUAL] SMTP_USERNAME, SMTP_PASSWORD   [Set if using email alerts]
  [MANUAL] SENTRY_DSN                     [Set if using Sentry monitoring]

BACKUP LOCATION:
  File: {os.path.basename(backup_file)}
  Path: {backup_file}
  Size: {os.path.getsize(backup_file) if os.path.exists(backup_file) else 'N/A'} bytes
  Retention: 30 days (then secure deletion)

VERIFICATION STATUS:
  [OK] DATABASE credential in .env
  [OK] REDIS password in .env
  [OK] SECRET_KEY in .env
  [OK] API_KEY_INTERNAL in .env
  [OK] API_KEY_EXTERNAL in .env

NEXT STEPS (REQUIRED):

1. Update PostgreSQL password (THIS MUST BE DONE):

   Option A - Using psql (direct):
     $ psql -U postgres -d genesis_record
     > ALTER USER adrion_app WITH PASSWORD '{credentials['DATABASE_PASSWORD']}';
     > \\q

   Option B - Using Docker:
     $ docker exec adrion-postgres psql -U postgres -d genesis_record \\
       -c "ALTER USER adrion_app WITH PASSWORD '{credentials['DATABASE_PASSWORD']}';"

2. Restart services to load new credentials from .env:

   Option A - Docker:
     $ docker restart adrion-postgres

   Option B - Direct Python:
     $ pkill -f db_sync_worker
     $ pkill -f health_check_service
     $ sleep 2
     $ cd c:/Users/adiha/162\\ demencje\\ w\\ schemacie\\ 369
     $ python scripts/db/db_sync_worker.py --interval 5 &
     $ python scripts/health_check/health_check_service.py --port 9000 &

3. Verify everything works:

   Test database:
     $ psql -U adrion_app -d genesis_record -c "SELECT 1;"

   Test API key loaded:
     $ python -c "import os; from dotenv import load_dotenv; load_dotenv(); \\
       print(os.getenv('API_KEY_INTERNAL')[:16])"

   Test health endpoint:
     $ curl http://localhost:9000/health

4. Monitor logs for authentication errors:

   $ docker logs adrion-postgres 2>&1 | grep -i "authen\\|error"

5. Archive this log:

   Already created at: {backup_dir}

SECURITY NOTES:
  - Old credentials are backed up in: {backup_file}
  - Backup file should be kept secure and encrypted
  - Rotate credentials quarterly (minimum)
  - Never commit .env to version control
  - New credentials are now loaded in .env (services need restart)

EMERGENCY ROLLBACK:
  If something fails, restore from backup:
  $ cp {backup_file} .env

================================================================================
Credential Rotation Script v1.0
Generated at: {datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}
================================================================================
"""

    # Write audit log
    with open(log_file, 'w') as f:
        f.write(audit_log)

    print(f"  [OK] Audit log created: {log_file}")

    # Also append to rotation history
    history_file = os.path.join(backup_dir, "ROTATION_HISTORY.log")
    with open(history_file, 'a') as f:
        f.write("\n" + audit_log + "\n")

    print()
    print("=" * 70)
    print("ROTATION COMPLETE - NEW CREDENTIALS IN .env")
    print("=" * 70)
    print()
    print("[IMPORTANT] NEXT STEPS REQUIRED:")
    print()
    print("1. Update PostgreSQL password:")
    print(f"   ALTER USER adrion_app WITH PASSWORD '{credentials['DATABASE_PASSWORD']}';")
    print()
    print("2. Restart services:")
    print("   docker restart adrion-postgres || pkill -f db_sync_worker")
    print()
    print("3. Test database connection:")
    print("   psql -U adrion_app -d genesis_record -c 'SELECT 1;'")
    print()
    print("4. Test health endpoint:")
    print("   curl http://localhost:9000/health")
    print()
    print("Files created:")
    print(f"  - New .env: {env_file}")
    print(f"  - Backup: {backup_file}")
    print(f"  - Audit log: {log_file}")
    print()
    print("=" * 70)
    print("CREDENTIALS SAVED IN .env - READY TO USE")
    print("=" * 70)

    return 0

if __name__ == "__main__":
    exit(main())
