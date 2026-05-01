"""Centralized exception hierarchy for ScriptForge.

All service-level exceptions inherit from ScriptForgeError.
This lets middleware and error handlers catch a single base type.
"""


class ScriptForgeError(Exception):
    """Base exception for all ScriptForge service errors."""
    status_code: int = 500
    detail: str = "Internal server error"


class AIServiceError(ScriptForgeError):
    """Base for AI/LLM provider errors."""
    status_code = 503
    detail = "AI service temporarily unavailable"


class AIServiceRateLimitError(AIServiceError):
    """429 Too Many Requests from the AI provider."""
    status_code = 429
    detail = "AI service rate limit exceeded, please retry later"


class AIServiceAuthError(AIServiceError):
    """401 Unauthorized from the AI provider (bad API key)."""
    status_code = 500  # Hide provider auth failures from clients
    detail = "AI service configuration error"


class AIServiceTimeoutError(AIServiceError):
    """Request to AI provider timed out after all retries."""
    status_code = 504
    detail = "AI service request timed out"


class AIServiceServerError(AIServiceError):
    """5xx errors from the AI provider."""
    status_code = 503
    detail = "AI service experiencing issues"


class DatabaseError(ScriptForgeError):
    """Database operation failures."""
    status_code = 503
    detail = "Database service unavailable"


class RedisError(ScriptForgeError):
    """Redis/Celery broker failures."""
    status_code = 503
    detail = "Task queue service unavailable"


class ChromaDBError(ScriptForgeError):
    """Vector store failures."""
    status_code = 503
    detail = "Vector store service unavailable"


class ResourceNotFoundError(ScriptForgeError):
    """Requested resource does not exist."""
    status_code = 404
    detail = "Resource not found"


class PermissionDeniedError(ScriptForgeError):
    """User does not have permission for the requested action."""
    status_code = 403
    detail = "Permission denied"


class RateLimitExceededError(ScriptForgeError):
    """Client has exceeded rate limits."""
    status_code = 429
    detail = "Too many requests, please slow down"
