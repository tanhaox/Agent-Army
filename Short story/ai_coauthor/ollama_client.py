"""Ollama HTTP client — talks to local Ollama service via REST API.

Default model: qwen2.5-novelist:latest (Stage A MVP).

Key API:
  - is_ollama_running()
  - list_models()
  - chat(prompt, model=None, system=None, temperature=None, num_predict=None, timeout=60)
"""

from __future__ import annotations

import json
from typing import Any
from urllib import request as urllib_request
from urllib.error import URLError

from .exceptions import OllamaResponseError, OllamaTimeoutError, OllamaUnavailableError

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5-novelist:latest"
DEFAULT_TIMEOUT = 60


def is_ollama_running(base_url: str = DEFAULT_BASE_URL) -> bool:
    """Return True iff Ollama responds to GET /api/version."""
    try:
        with urllib_request.urlopen(f"{base_url}/api/version", timeout=5) as resp:
            return 200 <= resp.status < 300
    except (URLError, OSError, TimeoutError):
        return False


def list_models(base_url: str = DEFAULT_BASE_URL) -> list[str]:
    """Return list of available model names."""
    req = urllib_request.Request(f"{base_url}/api/tags", method="GET")
    try:
        with urllib_request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read())
    except (URLError, OSError, TimeoutError) as e:
        raise OllamaUnavailableError(f"Ollama not reachable at {base_url}: {e}") from e
    models = payload.get("models") or []
    return [m["name"] for m in models if "name" in m]


def chat(
    prompt: str,
    model: str | None = None,
    system: str | None = None,
    temperature: float | None = None,
    num_predict: int | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    base_url: str = DEFAULT_BASE_URL,
) -> dict[str, Any]:
    """Send a single-turn chat completion to Ollama.

    Returns the raw response dict (always includes 'response', 'eval_count', etc.).
    Raises Ollama*Error on network / response failures.
    """
    payload: dict[str, Any] = {
        "model": model or DEFAULT_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system
    options: dict[str, Any] = {}
    if temperature is not None:
        options["temperature"] = float(temperature)
    if num_predict is not None:
        options["num_predict"] = int(num_predict)
    if options:
        payload["options"] = options

    req = urllib_request.Request(
        f"{base_url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except TimeoutError as e:
        raise OllamaTimeoutError(f"Ollama timed out after {timeout}s") from e
    except (URLError, OSError) as e:
        raise OllamaUnavailableError(f"Ollama unreachable: {e}") from e


def chat_text(
    prompt: str,
    model: str | None = None,
    system: str | None = None,
    temperature: float | None = None,
    num_predict: int | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    base_url: str = DEFAULT_BASE_URL,
) -> str:
    """Like chat() but returns just the response text. Raises OllamaResponseError if missing."""
    result = chat(
        prompt=prompt,
        model=model,
        system=system,
        temperature=temperature,
        num_predict=num_predict,
        timeout=timeout,
        base_url=base_url,
    )
    if "response" not in result:
        raise OllamaResponseError(f"Ollama response missing 'response' field: {result!r}")
    return str(result["response"])
