"""WSGI entrypoint for production servers (waitress/gunicorn)."""
from arbitrage.database import init_db
from arbitrage.app import create_app

# Ensure tables are created before serving traffic.
init_db()
app = create_app()
