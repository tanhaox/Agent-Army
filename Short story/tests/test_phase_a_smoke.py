"""Stage A smoke tests — verify CLI entry + Ollama connectivity.

Run: pytest tests/test_phase_a_smoke.py -v
or:   python -m pytest tests/test_phase_a_smoke.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# Ensure the parent process uses UTF-8 stdout/stderr on Windows
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

import pytest

from ai_coauthor import __version__
from ai_coauthor.cli import main
from ai_coauthor.ollama_client import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    chat_text,
    is_ollama_running,
)


# ───── helper ─────────────────────────────────────────────────────────
def _run(args: list[str], timeout: int = 30):
    """subprocess.run that always uses utf-8 to avoid Windows gbk issues."""
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.run(
        [sys.executable, "-m", "ai_coauthor", *args],
        capture_output=True,
        timeout=timeout,
        encoding="utf-8",  # critical: don't let Windows pick gbk
        errors="replace",
        env=env,
    )


# ───── pure unit tests (no Ollama needed) ─────────────────────────────


def test_version_string_is_set():
    assert __version__ == "0.1.0"
    assert isinstance(__version__, str)


def test_is_ollama_running_returns_bool():
    result = is_ollama_running()
    assert isinstance(result, bool)


def test_cli_help_runs():
    """`python -m ai_coauthor --help` exits 0 and prints help text."""
    result = _run(["--help"], timeout=15)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "ai-coauthor" in result.stdout.lower()
    assert "ollama_chat" in result.stdout
    # should list all stubs (by name; help text is ASCII-only)
    for stub in [
        "setup_consult",
        "character_card",
        "kickoff_meeting",
        "plan_chapter",
        "consistency_check",
        "foreshadow_track",
        "cumulative_audit",
        "diff_check",
    ]:
        assert stub in result.stdout, f"missing {stub} in help"


def test_cli_version_runs():
    result = _run(["--version"], timeout=10)
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_cli_stub_command_runs():
    """Running a stub command succeeds and prints the placeholder JSON."""
    result = _run(["kickoff_meeting", "--book", "fake"], timeout=10)
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert data["command"] == "kickoff_meeting"
    assert data["status"] == "not_implemented_yet"


# ───── integration test (needs local Ollama + qwen2.5-novelist) ─────────

OLLAMA_AVAILABLE = is_ollama_running()


@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not reachable")
def test_ollama_chat_real_call():
    """Real call to Ollama with qwen2.5-novelist — model must be pulled."""
    text = chat_text(
        prompt="Say just OK",
        model=DEFAULT_MODEL,
        temperature=0.0,
        num_predict=20,
        timeout=30,
    )
    assert text.strip()  # non-empty
    # qwen2.5-novelist may respond in Chinese or English; both fine
    # we just need *any* response
    assert len(text) > 0


@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not reachable")
def test_cli_ollama_chat_e2e():
    """End-to-end CLI invocation: ollama_chat command."""
    result = _run(
        [
            "ollama_chat",
            "--model", DEFAULT_MODEL,
            "--prompt", "ping",
            "--temperature", "0.0",
            "--num-predict", "20",
            "--timeout", "30",
        ],
        timeout=60,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert "response" in data
    assert data["model"] == DEFAULT_MODEL
    assert data["prompt"] == "ping"
    assert data["backend"] == "ollama_local"


def test_cli_handles_missing_prompt_arg():
    """--prompt is required → argparse exits with code 2."""
    result = _run(["ollama_chat"], timeout=10)
    # argparse exits with 2 on missing required arg
    assert result.returncode == 2


def test_unreachable_ollama_url_emits_error():
    """When --base-url points to nowhere, get exit code 4 with error JSON."""
    # Use a port that's definitely not Ollama (random high port)
    bad_url = "http://127.0.0.1:1"
    result = _run(
        [
            "ollama_chat",
            "--prompt", "x",
            "--base-url", bad_url,
            "--timeout", "5",
        ],
        timeout=15,
    )
    # Either connection refused quickly OR our is_ollama_running() returns False → exit 4
    assert result.returncode != 0
    # the error should appear in stderr or stdout
    combined = result.stdout + result.stderr
    assert "ollama_unavailable" in combined or "error" in combined.lower()


# ───── module-level sanity (for direct python -m import) ──────────────

def test_module_imports_clean():
    """No circular imports / missing attrs."""
    from ai_coauthor import cli, exceptions, ollama_client
    assert hasattr(cli, "main")
    assert hasattr(exceptions, "OllamaUnavailableError")
    assert hasattr(ollama_client, "chat")
