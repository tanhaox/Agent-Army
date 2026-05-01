"""Frontend error reporting endpoint."""
import logging
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger("scriptforge.frontend")

router = APIRouter(prefix="/logs", tags=["Logs"])


class ClientError(BaseModel):
    message: str = Field(..., description="Error message")
    stack: str | None = Field(default=None, description="Stack trace")
    url: str | None = Field(default=None, description="Page URL where error occurred")
    line: int | None = Field(default=None, description="Line number")
    col: int | None = Field(default=None, description="Column number")
    userAgent: str | None = Field(default=None, description="Browser user agent")
    timestamp: str | None = Field(default=None, description="Error timestamp from client")


@router.post("/client")
async def report_client_error(err: ClientError):
    logger.error(
        "Frontend error: %s | url=%s stack=%s",
        err.message,
        err.url,
        (err.stack or "")[:500],
    )
    return {"logged": True}
