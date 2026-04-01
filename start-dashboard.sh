#!/bin/bash
# ADRION 369 Dashboard - Quick Start Script

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         ADRION 369 Dashboard - macOS/Linux Quick Start         ║"
echo "║              🚀 Start dashboard on http://localhost:8000       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo ""
    echo "Install Python from: https://www.python.org/downloads/"
    echo "Then run: pip3 install -r requirements.txt"
    exit 1
fi

echo "✅ Python found"
python3 --version

echo ""
echo "🚀 Starting Dashboard Server on http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 server.py
