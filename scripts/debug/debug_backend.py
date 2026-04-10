#!/usr/bin/env python3
"""Debug backend startup"""
import sys
sys.path.insert(0, 'uap/backend')

print("1. Starting backend initialization...")

try:
    print("2. Importing db module...")
    from db import DatabaseEngine
    print(f"✓ DatabaseEngine initialized: {DatabaseEngine}")

    print("3. Importing Flask app...")
    from api import app, logger
    print(f"✓ Flask app created")

    print("4. Starting Flask server...")
    logger.info("Starting flask development server on 0.0.0.0:8002")
    app.run(host="0.0.0.0", port=8002, debug=False, use_reloader=False)
except Exception as e:
    import traceback
    print(f"✗ ERROR: {e}")
    traceback.print_exc()
