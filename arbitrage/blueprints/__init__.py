"""ADRION 369 - Flask Blueprints for Arbitrage API."""


def safe_float(val, default: float = 0.0) -> float:
    """Safely convert value to float, returning default on failure."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def safe_int(val, default: int = 0) -> int:
    """Safely convert value to int, returning default on failure."""
    try:
        return int(val)
    except (TypeError, ValueError):
        return default
