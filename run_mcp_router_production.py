#!/usr/bin/env python3
"""Enhanced MCP Router with Waitress production server"""
from mcp_router_app import app
from waitress import serve

if __name__ == "__main__":
    print("🚀 MCP Router (PRODUCTION MODE) — Port 9000")
    print("   Server: Waitress (multi-threaded)")
    print("   Workers: 4 threads")
    serve(app, host="0.0.0.0", port=9000, threads=4)
