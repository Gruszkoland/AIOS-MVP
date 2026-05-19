"""UAP test configuration — sets up import paths for uap/backend."""
import sys
from pathlib import Path

# Allow `from backend.xxx import` in uap/tests/
UAP_ROOT = Path(__file__).parent
if str(UAP_ROOT) not in sys.path:
    sys.path.insert(0, str(UAP_ROOT))
