"""Fleet Rental Automation Backend Application Package."""

import sys
from pathlib import Path

# Ensure project root is in sys.path regardless of whether command is run from root or backend/
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

