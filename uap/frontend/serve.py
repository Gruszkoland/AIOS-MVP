#!/usr/bin/env python3
"""
Unified Admin Panel (UAP) — Frontend Server
Port 8003, serves static files (HTML/CSS/JS)
"""
import os
import sys
import http.server
import socketserver
from pathlib import Path

FRONTEND_HOST = os.getenv("FRONTEND_HOST", "localhost")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "8003"))

frontend_dir = Path(__file__).parent

os.chdir(frontend_dir)

class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

if __name__ == "__main__":
    print("╔════════════════════════════════════════════╗")
    print("║  Unified Admin Panel (UAP) Frontend Server ║")
    print(f"║  http://{FRONTEND_HOST}:{FRONTEND_PORT}                      ║")
    print("╚════════════════════════════════════════════╝\n")

    server = socketserver.TCPServer((FRONTEND_HOST, FRONTEND_PORT), QuietHTTPRequestHandler)
    print(f"✅ Serving from: {frontend_dir}")
    print(f"📖 Open: http://{FRONTEND_HOST}:{FRONTEND_PORT}\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Shutdown complete")
        server.shutdown()
