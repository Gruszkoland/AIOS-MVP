#!/usr/bin/env python3
"""Enhanced VORTEX MCP with Waitress production server"""
from mcp_vortex_app import app
from waitress import serve

if __name__ == "__main__":
    print("🚀 VORTEX-MCP (PRODUCTION MODE) — Port 9001")
    print("   Server: Waitress (multi-threaded)")
    print("   Workers: 4 threads")
    serve(app, host="0.0.0.0", port=9001, threads=4)
