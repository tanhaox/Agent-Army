"""Shared pytest configuration."""

from __future__ import annotations

import os
import sys

# Ensure Windows terminals can encode whatever we print
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

# Re-open stdout/stderr in UTF-8 on Windows to prevent gbk codec errors
# when argparse help prints non-ASCII chars (e.g. emoji or arrows).
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
