#!/usr/bin/env python3
"""Enhanced HEALER MCP with Waitress production server"""
from mcp_healer_app import app
from waitress import serve

if __name__ == "__main__":
    print("🚀 HEALER-MCP (PRODUCTION MODE) — Port 9005")
    print("   Server: Waitress (multi-threaded)")
    print("   Workers: 4 threads")
    serve(app, host="0.0.0.0", port=9005, threads=4)
