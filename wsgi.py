"""WSGI entrypoint for production servers (waitress/gunicorn)."""
from arbitrage.database import init_db
from arbitrage_server import app

# Ensure tables are created before serving traffic.
init_db()
