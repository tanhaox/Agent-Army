"""Director 产物下载 + 打开产物文件夹端点."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.director_routes.common import _find_composition_mp4, _job_or_404

logger = logging.getLogger(__name__)

download_router = APIRouter(tags=["director"])

__all__ = ["download_router"]


@download_router.get("/jobs/{job_id}/download")
def download_job(job_id: str, db: Session = Depends(get_db)):
    job = _job_or_404(db, job_id)
    if job.status != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"job 状态 {job.status}, 暂未产出 (需 status=completed)",
        )
    # 优先从 composition manifest 文件读取, 其次 plan_json, 最后 fallback 搜索
    out = _find_composition_mp4(job_id)
    if not out:
        raise HTTPException(status_code=404, detail="未找到合成产物路径")
    p = Path(out)
    if not p.exists():
        raise HTTPException(status_code=410, detail=f"产物文件丢失: {p}")
    return FileResponse(str(p), media_type="video/mp4", filename=p.name)


@download_router.post("/jobs/{job_id}/open-folder")
def open_output_folder(job_id: str, db: Session = Depends(get_db)):
    """打开合成产物所在的文件夹（仅 Windows 本地环境）."""
    job = _job_or_404(db, job_id)
    out = _find_composition_mp4(job_id)
    if not out:
        raise HTTPException(status_code=404, detail="未找到合成产物路径")
    folder = str(Path(out).parent)
    if not Path(folder).exists():
        raise HTTPException(status_code=410, detail=f"产物目录不存在: {folder}")
    try:
        os.startfile(folder)
        return {"status": "ok", "folder": folder}
    except Exception as exc:
        logger.exception("open folder failed")
        raise HTTPException(status_code=500, detail=f"打开文件夹失败: {exc}")
