import sys
from pathlib import Path
from socket import error as SocketError

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import arbitrage.api as api


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8011
    api.ARB_PORT = port
    try:
        api.run_api_server()
    except OSError as exc:
        if "Address already in use" in str(exc):
            print(
                f"[OK] Arbitrage API already running on http://localhost:{port}",
                flush=True,
            )
            return
        raise
    except SocketError as exc:
        if "Address already in use" in str(exc):
            print(
                f"[OK] Arbitrage API already running on http://localhost:{port}",
                flush=True,
            )
            return
        raise


if __name__ == "__main__":
    main()
