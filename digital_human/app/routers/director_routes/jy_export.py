"""J 线草稿导出端点 — 导演 job → 剪映草稿 (J1)."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.director_routes.common import _job_or_404
from app.services.jy_draft_service import export_job_draft

logger = logging.getLogger(__name__)

jy_router = APIRouter(tags=["director"])

__all__ = ["jy_router"]


@jy_router.post("/jobs/{job_id}/export-jy-draft")
def export_jy_draft(job_id: str, db: Session = Depends(get_db)):
    """导出当前 job 为剪映草稿 (同步, 纯写盘). 前置: job 存在 (可用性在 service 内校验)."""
    _job_or_404(db, job_id)  # 统一 404 语义
    try:
        return export_job_draft(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
