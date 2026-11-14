import sys
from pathlib import Path

# Enable resolution of 'backend' when working directory is inside 'backend'
_parent = Path(__file__).resolve().parent.parent
__path__ = [str(_parent)]
