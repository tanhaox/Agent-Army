"""CLI entry: argparse router.

Stage A registers only `ollama_chat` (a real command) plus 8 stub commands.

Stub commands will be filled in by Stage C (commands/) and Stage B (state, router).
For Stage A they print a short placeholder so `python -m ai_coauthor --help`
is realistic and shows the 9-command shape MVP plans for.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Force UTF-8 stdout/stderr on Windows (avoid gbk codec errors in --help
# and JSON dumps that may contain non-ASCII characters).
# Must be set BEFORE argparse writes its first byte.
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from . import __version__
from .exceptions import AICoauthorError
from .ollama_client import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    chat,
    is_ollama_running,
    list_models,
)


def cmd_ollama_chat(args: argparse.Namespace) -> int:
    """Real command (Stage A). Calls Ollama and prints JSON to stdout."""
    payload = {
        "model": args.model,
        "prompt": args.prompt,
    }
    if args.system is not None:
        payload["system"] = args.system
    if args.temperature is not None:
        payload["temperature"] = float(args.temperature)
    if args.num_predict is not None:
        payload["num_predict"] = int(args.num_predict)
    payload["base_url"] = args.base_url
    payload["timeout"] = int(args.timeout)

    if not is_ollama_running(args.base_url):
        return _emit_error(
            "ollama_unavailable",
            f"Ollama is not reachable at {args.base_url}. Try: ollama serve",
            code=4,
        )

    try:
        result = chat(
            prompt=args.prompt,
            model=args.model,
            system=args.system,
            temperature=args.temperature,
            num_predict=args.num_predict,
            timeout=args.timeout,
            base_url=args.base_url,
        )
    except AICoauthorError as e:
        return _emit_error("ollama_error", str(e), code=5)

    # success — print response as JSON to stdout
    payload.update({
        "response": result.get("response", ""),
        "eval_count": result.get("eval_count", 0),
        "prompt_eval_count": result.get("prompt_eval_count", 0),
        "total_duration_ms": round(result.get("total_duration", 0) / 1e6, 2),
        "backend": "ollama_local",
    })
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return 0


# ───── Stubs (8) — to be filled in Stage B/C ─────────────────────────────
# These print a short placeholder so the help screen shows the right command
# shape; the exit code 0 means "this is a recognised command but not yet
# implemented in Stage A — run it via the right stage instead."
#
# Note: help text must be ASCII only (Windows gbk console).

STUB_COMMANDS: dict[str, str] = {
    "setup_consult":     "Stage C: fill in 6 dimensions (settings/01..06)",
    "character_card":    "Stage C: display character card + voice-print",
    "kickoff_meeting":   "Stage C: multi-agent kickoff (= P10 starter)",
    "plan_chapter":      "Stage C: chapter planning using voice-print",
    "consistency_check": "Stage C: anti-nonsense guard (P0 blocker)",
    "foreshadow_track":  "Stage C: foreshadow half-loop (= F3)",
    "cumulative_audit":  "Stage C: gantt 6+ swimlane audit",
    "diff_check":        "Stage C: git-diff to kickoff-meeting trigger (no special chars)",
}


def _make_stub(name: str):
    def _stub(args: argparse.Namespace) -> int:
        msg = {
            "command": name,
            "status": "not_implemented_yet",
            "stage": STUB_COMMANDS[name],
            "hint": "See docs/MVP_AUTHORITY.md §四 (Phase 1.D)",
        }
        sys.stdout.write(json.dumps(msg, ensure_ascii=False, indent=2) + "\n")
        return 0
    return _stub


def _emit_error(error_type: str, message: str, code: int = 1) -> int:
    """Emit structured JSON error to stderr and return exit code."""
    payload = {"error": error_type, "message": message}
    sys.stderr.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return code


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ai-coauthor",
        description=f"Short story AI coauthor v{__version__}",
        # Windows gbk console can't encode emoji in --help; use ASCII-only.
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    # ── real commands ────────────────────────────────────────────────
    chat_p = sub.add_parser("ollama_chat", help="(Stage A) Send a single prompt to Ollama")
    chat_p.add_argument("--prompt", required=True)
    chat_p.add_argument("--model", default=DEFAULT_MODEL)
    chat_p.add_argument("--system", default=None)
    chat_p.add_argument("--temperature", type=float, default=None)
    chat_p.add_argument("--num-predict", type=int, default=None)
    chat_p.add_argument("--timeout", type=int, default=60)
    chat_p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    chat_p.set_defaults(func=cmd_ollama_chat)

    # ── stub commands (placeholders for Stage C) ────────────────────
    # Each stub accepts an optional --book arg so help runs cleanly.
    for name in STUB_COMMANDS:
        sp = sub.add_parser(name, help=f"(Stage A stub) {STUB_COMMANDS[name]}")
        sp.add_argument("--book", default=None, help="(stub) book name ignored")
        sp.add_argument("--chapter-n", type=int, default=None, help="(stub) ignored")
        sp.add_argument("--target", default=None, help="(stub) ignored")
        sp.add_argument("--since", default=None, help="(stub) ignored")
        sp.add_argument("--action", default="list", help="(stub) ignored")
        sp.add_argument("--mode", default="fill", help="(stub) ignored")
        sp.add_argument("--dimension", default="all", help="(stub) ignored")
        sp.set_defaults(func=_make_stub(name))

    # ── top-level meta ──────────────────────────────────────────────
    doctor = sub.add_parser("doctor", help="Check Ollama availability")
    doctor.set_defaults(func=_cmd_doctor)

    return p


def _cmd_doctor(args: argparse.Namespace) -> int:
    info = {
        "ollama_running": is_ollama_running(),
        "available_models": list_models() if is_ollama_running() else [],
        "default_model": DEFAULT_MODEL,
        "version": __version__,
    }
    sys.stdout.write(json.dumps(info, ensure_ascii=False, indent=2) + "\n")
    return 0 if info["ollama_running"] else 4


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except AICoauthorError as e:
        return _emit_error("coauthor_error", str(e), code=3)
    except KeyboardInterrupt:
        return _emit_error("interrupted", "user cancelled (Ctrl+C)", code=130)


if __name__ == "__main__":
    raise SystemExit(main())
