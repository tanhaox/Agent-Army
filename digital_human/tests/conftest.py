"""conftest.py for digital_human pytest discovery.

Adds the scripts/ directory to sys.path so `import tts_client` works
without installing the package. Also exposes shared fixtures.
"""
from __future__ import annotations

import sys
from pathlib import Path

# digital_human/scripts/tts_client.py is importable as `tts_client`
_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))