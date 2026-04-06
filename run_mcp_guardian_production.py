#!/usr/bin/env python3
"""Enhanced GUARDIAN MCP with Waitress production server"""
from mcp_guardian_app import app
from waitress import serve

if __name__ == "__main__":
    print("🚀 GUARDIAN-MCP (PRODUCTION MODE) — Port 9002")
    print("   Server: Waitress (multi-threaded)")
    print("   Workers: 4 threads")
    serve(app, host="0.0.0.0", port=9002, threads=4)
