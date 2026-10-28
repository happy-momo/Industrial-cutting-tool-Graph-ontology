"""Ensure the repository root is importable so `src`, `scripts` and `contract`
are reachable regardless of how pytest is launched."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))