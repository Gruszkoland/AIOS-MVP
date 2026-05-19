#!/usr/bin/env python3
"""Enhanced GENESIS MCP with Waitress production server"""
from mcp_genesis_app import app
from waitress import serve

if __name__ == "__main__":
    print("🚀 GENESIS-MCP (PRODUCTION MODE) — Port 9004")
    print("   Server: Waitress (multi-threaded)")
    print("   Workers: 4 threads")
    serve(app, host="0.0.0.0", port=9004, threads=4)
