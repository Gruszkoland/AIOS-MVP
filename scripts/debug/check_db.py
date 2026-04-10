#!/usr/bin/env python3
"""Check database schema"""
import sqlite3

db_path = "db/adrion_local.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = {row[0] for row in cursor.fetchall()}

print(f"✓ Database exists: {db_path}")
print(f"✓ Found {len(tables)} tables: {sorted(tables)}")

# Check for 'agents' table
if 'agents' in tables:
    cursor.execute("SELECT COUNT(*) FROM agents")
    count = cursor.fetchone()[0]
    print(f"✓ agents table has {count} records")
else:
    print("✗ agents table NOT FOUND - this is the problem!")
    print("\nAvailable tables:")
    for table in sorted(tables):
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        cnt = cursor.fetchone()[0]
        print(f"  - {table}: {cnt} records")

conn.close()
