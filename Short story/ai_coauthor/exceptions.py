"""Custom exceptions for Short story AI coauthor."""


class AICoauthorError(Exception):
    """Base exception."""


class OllamaUnavailableError(AICoauthorError):
    """Ollama service is not reachable (e.g. not started)."""


class OllamaTimeoutError(AICoauthorError):
    """Ollama inference exceeded timeout."""


class OllamaResponseError(AICoauthorError):
    """Ollama returned malformed/unexpected response."""
