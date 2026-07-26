"""Launch script for digital human pipeline web UI."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on path for local imports.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn

from app.config import load_config


def main() -> int:
    config_path = PROJECT_ROOT / "config" / "app.yaml"
    if not config_path.exists():
        print(f"Config not found: {config_path}", file=sys.stderr)
        print("Copy config/app.example.yaml to config/app.yaml and fill in your DeepSeek key.", file=sys.stderr)
        return 1

    cfg = load_config(config_path)
    uvicorn.run("app.main:app", host=cfg.app.host, port=cfg.app.port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
