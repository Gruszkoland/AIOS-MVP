"""pytest configuration for mcp-servers test suite.

Adds the mcp-servers directory to sys.path so that server modules
can be imported without installing the mcp-servers package.
Tests run without the mcp SDK — only the business logic classes are tested.
"""

import sys
from pathlib import Path

# Insert the mcp-servers/ directory so imports like `from shared import ...`
# and `from router.server import RouterLogic` work without any package install.
_MCP_DIR = Path(__file__).parent.parent  # .../mcp-servers/
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))
