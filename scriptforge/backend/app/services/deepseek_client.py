"""Shared DeepSeek API client — HTTP client, retry logic, error classification.

All AI-facing services use this client instead of duplicating httpx call logic.
Connection pooling enables reuse across requests. Tenacity provides exponential
backoff retry on transient failures (5xx, 429, connection errors).
"""
import json
import logging
import re

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.exceptions import (
    AIServiceAuthError,
    AIServiceError,
    AIServiceRateLimitError,
    AIServiceServerError,
    AIServiceTimeoutError,
)

logger = logging.getLogger(__name__)

# Module-level connection pool — reused across all requests
_client: httpx.AsyncClient | None = None


def _get_client(timeout: float = 60.0) -> httpx.AsyncClient:
    """Return or create the shared httpx.AsyncClient with connection pooling."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )
    return _client


async def close_deepseek_client() -> None:
    """Close the shared connection pool. Call during app shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("DeepSeek client connection pool closed")


def reset_client_sync() -> None:
    """Reset the module-level client so it can be reused in a fresh asyncio.run()."""
    global _client
    if _client is not None:
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_client.aclose())
            loop.close()
        except Exception:
            pass
        _client = None
        logger.debug("DeepSeek client reset for new event loop")


@retry(
    retry=retry_if_exception_type((
        AIServiceServerError,
        AIServiceRateLimitError,
        httpx.ConnectError,
        httpx.ReadError,
        httpx.RemoteProtocolError,
    )),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _retryable_request(
    api_key: str,
    base_url: str,
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    timeout: float,
    response_format: dict | None,
) -> httpx.Response:
    """HTTP request with tenacity retry on transient failures."""
    client = _get_client(timeout)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    try:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        detail = e.response.text[:300] if e.response else str(e)
        logger.error("DeepSeek API HTTP %s: %s", status, detail)

        if status == 401:
            raise AIServiceAuthError("Invalid DeepSeek API key") from e
        elif status == 429:
            raise AIServiceRateLimitError(
                "DeepSeek rate limit exceeded"
            ) from e
        elif status >= 500:
            raise AIServiceServerError(
                f"DeepSeek server error (HTTP {status})"
            ) from e
        else:
            raise AIServiceError(f"DeepSeek API error (HTTP {status})") from e
    except httpx.TimeoutException:
        raise AIServiceTimeoutError("DeepSeek request timed out") from None
    except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError):
        # Let tenacity retry these
        raise


class DeepSeekClient:
    """Wrapper around DeepSeek chat/completions endpoint.

    Handles: auth, retry, error classification, JSON parsing.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "deepseek-chat",
    ):
        self._api_key = api_key
        self.base_url = base_url or settings.DEEPSEEK_BASE_URL
        self.model = model

    @property
    def api_key(self) -> str:
        return self._api_key or settings.DEEPSEEK_API_KEY

    async def chat(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        timeout: float = 60.0,
        response_format: dict | None = None,
    ) -> dict:
        """Send a chat completion request and return parsed JSON.

        Raises:
            AIServiceAuthError: Invalid API key.
            AIServiceRateLimitError: Rate limited after retries.
            AIServiceTimeoutError: Request timed out after retries.
            AIServiceServerError: Persistent 5xx from provider.
            AIServiceError: Other API or parsing failures.
        """
        if not self.api_key:
            raise AIServiceAuthError("DEEPSEEK_API_KEY is not configured")

        response = await _retryable_request(
            self.api_key,
            self.base_url,
            self.model,
            messages,
            temperature,
            max_tokens,
            timeout,
            response_format,
        )

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback 1: extract JSON from markdown-wrapped content
            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            # Fallback 2: repair with json_repair
            try:
                from json_repair import repair_json
                repaired = repair_json(content)
                return json.loads(repaired) if isinstance(repaired, str) else repaired
            except Exception:
                pass
            # Fallback 3: repair the regex-extracted block
            if match:
                try:
                    from json_repair import repair_json
                    repaired = repair_json(match.group())
                    return json.loads(repaired) if isinstance(repaired, str) else repaired
                except Exception:
                    pass
            logger.error("All JSON repair attempts failed. Content preview: %s", content[:200])
            raise AIServiceError("Failed to parse AI response as JSON")

    @staticmethod
    def build_messages(system: str, user: str) -> list[dict]:
        """Build a system+user message list."""
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]


# Module-level singleton for dependency injection
deepseek = DeepSeekClient()
