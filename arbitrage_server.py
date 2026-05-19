"""DEPRECATED: Use wsgi.py → arbitrage.app.create_app() instead.

This file will be removed in v5.0 (planned Q3 2026).
See CHANGELOG.md for details.
"""
import warnings

warnings.warn(
    "arbitrage_server.py is deprecated. Use wsgi.py → arbitrage.app.create_app() instead. "
    "This file will be removed in v5.0.",
    DeprecationWarning,
    stacklevel=2,
)

from arbitrage.app import create_app

app = create_app()

if __name__ == "__main__":
    print("WARNING: arbitrage_server.py is deprecated. Use: python wsgi.py")
    app.run(host="0.0.0.0", port=8003, debug=False)
