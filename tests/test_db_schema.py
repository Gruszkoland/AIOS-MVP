#!/usr/bin/env python3
"""Quick database schema check"""
import sqlite3
from pathlib import Path

db_path = Path("data/uap.db")
if not db_path.exists():
    print(f"✗ Database file not found: {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get list of all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"✓ Found {len(tables)} tables:")
for table in tables:
    print(f"  - {table}")

# Check agents table specifically
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents'")
if cursor.fetchone():
    print("\n✓ agents table EXISTS")
    # Count agents
    cursor.execute("SELECT COUNT(*) FROM agents")
    count = cursor.fetchone()[0]
    print(f"  - Contains {count} agent records")
    
    # Check columns
    cursor.execute("PRAGMA table_info(agents)")
    cols = cursor.fetchall()
    print(f"  - Columns: {', '.join([col[1] for col in cols])}")
else:
    print("\n✗ agents table NOT FOUND")

conn.close()
