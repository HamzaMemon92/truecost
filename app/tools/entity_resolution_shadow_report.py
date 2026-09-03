from __future__ import annotations

import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
SCRIPT = BACKEND / "app" / "tools" / "entity_resolution_shadow_report.py"

sys.path.insert(0, str(BACKEND))
runpy.run_path(str(SCRIPT), run_name="__main__")
