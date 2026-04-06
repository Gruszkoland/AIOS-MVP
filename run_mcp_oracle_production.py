#!/usr/bin/env python3
"""Enhanced ORACLE MCP with Waitress production server"""
from mcp_oracle_app import app
from waitress import serve

if __name__ == "__main__":
    print("🚀 ORACLE-MCP (PRODUCTION MODE) — Port 9003")
    print("   Server: Waitress (multi-threaded)")
    print("   Workers: 4 threads")
    serve(app, host="0.0.0.0", port=9003, threads=4)
