import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import arbitrage.api as api


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8011
    api.ARB_PORT = port
    api.run_api_server()


if __name__ == "__main__":
    main()
