# Ensure project root is on sys.path so 'game' package imports resolve when running tests from repo root.
import sys
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Signal test environment to application entrypoint
os.environ.setdefault("PYTEST_RUNNING", "1")
