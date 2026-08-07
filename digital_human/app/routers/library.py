"""Video Library router — 素材库 + 成品库 CRUD / 搜索 / 标签 / 偏好."""
from __future__ import annotations

import logging
import mimetypes
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import or_, func, String, case
from sqlalchemy.orm import Session

from ..config import get_config
from ..database import get_db
from ..models import VideoAsset, VideoOutput
from ..services.asset_tagging import generate_asset_no
from ..services.video_validator import ffprobe_metadata
from ..schemas import (
    VideoAssetOut,
    VideoAssetPreferenceRequest,
    VideoAssetUpdate,
    VIDEO_LOCATION_CHOICES,
    VIDEO_ORIENTATION_CHOICES,
    VIDEO_PEOPLE_CHOICES,
    VIDEO_PREFERENCE_CHOICES,
    VIDEO_SCENE_CHOICES,
    VIDEO_SHOT_TYPE_CHOICES,
    VIDEO_SOURCE_TYPE_CHOICES,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/library", tags=["library"])


def _recycle_file(path: str) -> bool:
    r"""Move a single file to the Windows recycle bin (never permanent delete).

    CLAUDE.md 红线: 禁止直接删除用户数据, 必须走回收站.
    与 scripts.py::_recycle_file 同一实现 (PowerShell Microsoft.VisualBasic).
    `app/services/file_utils.py::safe_trash` 不可用 — send2trash 未安装时它
    回退到 shutil.rmtree 永久删除. 这里用 PowerShell 实现, 满足红线且不引入新依赖.

    Args:
        path: Windows 绝对路径 (可为 E:\数字人计划\... 或 F:\AI-Agent-Local\...).

    Returns:
        True 若文件已移入回收站 (或路径不存在视为无需处理), False 若失败.
    """
    if not path or not os.path.exists(path):
        return False
    # PowerShell 单引号字面量内唯一需要转义的字符是单引号本身 ('' 转义)
    escaped = path.replace("'", "''")
    cmd = (
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        "[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile("
        f"'{escaped}', 'OnlyErrorDialogs', 'SendToRecycleBin')"
    )
    try:
        # 列表传参 (shell=False) 不经 cmd.exe, 反斜杠/中文路径均为字面量
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            capture_output=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return True
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("recycle failed for %s: %s", path, exc)
        return False


def _parse_range(range_header: str, file_size: int) -> tuple[int, int] | None:
    """Parse 'bytes=start-end' into (start, end) inclusive."""
    if not range_header.startswith("bytes="):
        return None
    spec = range_header[6:].strip()
    if "-" not in spec:
        return None
    start_str, end_str = spec.split("-", 1)
    try:
        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1
    except ValueError:
        return None
    if start < 0 or end >= file_size or start > end:
        return None
    return start, end


def _video_file_response(request: Request, file_path: Path, media_type: str) -> FileResponse | StreamingResponse:
    """Return video with optional HTTP Range support for browser seeking."""
    if not file_path.exists():
        raise HTTPException(404, "file missing on disk")
    file_size = file_path.stat().st_size
    range_header = request.headers.get("range")
    if not range_header:
        return FileResponse(
            str(file_path),
            media_type=media_type,
            filename=file_path.name,
            content_disposition_type="inline",
        )
    rng = _parse_range(range_header, file_size)
    if rng is None:
        return FileResponse(
            str(file_path),
            media_type=media_type,
            filename=file_path.name,
            content_disposition_type="inline",
        )
    start, end = rng
    length = end - start + 1

    def iter_file():
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(8192, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    return StreamingResponse(
        iter_file(),
        media_type=media_type,
        status_code=206,
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
            "Content-Disposition": f'inline; filename="{file_path.name}"',
        },
    )


# ---------------------------------------------------------------------------
# 素材库 (VideoAsset)
# ---------------------------------------------------------------------------

@router.get("/assets")
def list_assets(
    q: str | None = Query(None, description="搜索编号/描述/query/摄影师/标签"),
    orientation: str | None = Query(None, description="landscape / portrait"),
    source_type: str | None = Query(None, description="footage / creative"),
    location: str | None = Query(None, description="domestic / foreign"),
    people: str | None = Query(None, description="people / none"),
    preference: str | None = Query(None, description="like / neutral / dislike"),
    scenes: str | None = Query(None, description="逗号分隔, OR 匹配"),
    shot_types: str | None = Query(None, description="逗号分隔, OR 匹配"),
    tags: str | None = Query(None, description="逗号分隔标签过滤"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """搜索/筛选素材库. 喜欢的素材排序置顶."""
    query = db.query(VideoAsset)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                VideoAsset.asset_no.ilike(like),
                VideoAsset.description_en.ilike(like),
                VideoAsset.description_zh.ilike(like),
                VideoAsset.raw_query.ilike(like),
                VideoAsset.photographer.ilike(like),
                VideoAsset.tags.cast(String).ilike(like),
                VideoAsset.scenes.cast(String).ilike(like),
                VideoAsset.shot_types.cast(String).ilike(like),
            )
        )
    if orientation:
        query = query.filter(VideoAsset.orientation == orientation)
    if source_type:
        query = query.filter(VideoAsset.source_type == source_type)
    if location:
        query = query.filter(VideoAsset.location == location)
    if people:
        query = query.filter(VideoAsset.people == people)
    if preference:
        query = query.filter(VideoAsset.preference == preference)
    if scenes:
        scene_list = [t.strip() for t in scenes.split(",") if t.strip()]
        for s in scene_list:
            query = query.filter(VideoAsset.scenes.cast(String).ilike(f"%{s}%"))
    if shot_types:
        shot_list = [t.strip() for t in shot_types.split(",") if t.strip()]
        for s in shot_list:
            query = query.filter(VideoAsset.shot_types.cast(String).ilike(f"%{s}%"))
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        for t in tag_list:
            query = query.filter(VideoAsset.tags.cast(String).ilike(f"%{t}%"))

    total = query.count()
    items = (
        query.order_by(
            # 喜欢的置顶, 厌恶的沉底
            case(
                (VideoAsset.preference == "like", 0),
                (VideoAsset.preference == "neutral", 1),
                (VideoAsset.preference == "dislike", 2),
                else_=1,
            ),
            VideoAsset.used_count.desc(),
            VideoAsset.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "items": [VideoAssetOut.model_validate(a).model_dump() for a in items],
    }


@router.get("/assets/{asset_id}")
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    a = db.get(VideoAsset, asset_id)
    if not a:
        raise HTTPException(404, "asset not found")
    return VideoAssetOut.model_validate(a).model_dump()


@router.api_route("/assets/{asset_id}/file", methods=["GET", "HEAD"])
def get_asset_file(asset_id: str, request: Request, db: Session = Depends(get_db)):
    """返回素材视频文件，支持 HTTP Range 请求 (GET/HEAD).

    HEAD 由 uvicorn 在协议层抑制 body, 仅返回头 (Content-Type/Length) —
    浏览器 <video> 探测文件存在性与元数据依赖 HEAD, 缺它则 405.
    """
    a = db.get(VideoAsset, asset_id)
    if not a:
        raise HTTPException(404, "asset not found")
    p = Path(a.file_path)
    media_type = mimetypes.guess_type(str(p))[0] or "video/mp4"
    return _video_file_response(request, p, media_type)


@router.put("/assets/{asset_id}")
def update_asset(
    asset_id: str,
    body: VideoAssetUpdate,
    db: Session = Depends(get_db),
):
    """更新素材元数据(asset_no 不可改)."""
    a = db.get(VideoAsset, asset_id)
    if not a:
        raise HTTPException(404, "asset not found")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(a, key, value)
    db.commit()
    db.refresh(a)
    return VideoAssetOut.model_validate(a).model_dump()


@router.post("/assets/{asset_id}/preference")
def set_preference(
    asset_id: str,
    body: VideoAssetPreferenceRequest,
    db: Session = Depends(get_db),
):
    """设置素材偏好 like / neutral / dislike. dislike 会进入黑名单, 后续 resolve 不再下载/返回."""
    a = db.get(VideoAsset, asset_id)
    if not a:
        raise HTTPException(404, "asset not found")
    a.preference = body.preference
    db.commit()
    return {"id": a.id, "preference": a.preference}


@router.delete("/assets/{asset_id}")
def delete_asset(asset_id: str, remove_file: bool = True, db: Session = Depends(get_db)):
    """删除素材记录，可选同时移物理文件到回收站."""
    a = db.get(VideoAsset, asset_id)
    if not a:
        raise HTTPException(404, "asset not found")
    if remove_file:
        p = Path(a.file_path)
        if p.exists():
            _recycle_file(str(p))
    db.delete(a)
    db.commit()
    return {"status": "ok", "deleted": asset_id}


@router.get("/dimensions")
def list_dimensions():
    """返回所有筛选维度枚举值(前端下拉框用)."""
    return {
        "orientation": list(VIDEO_ORIENTATION_CHOICES),
        "source_type": list(VIDEO_SOURCE_TYPE_CHOICES),
        "location": list(VIDEO_LOCATION_CHOICES),
        "people": list(VIDEO_PEOPLE_CHOICES),
        "preference": list(VIDEO_PREFERENCE_CHOICES),
        "scenes": list(VIDEO_SCENE_CHOICES),
        "shot_types": list(VIDEO_SHOT_TYPE_CHOICES),
    }


@router.get("/tags")
def list_all_tags(db: Session = Depends(get_db)):
    """获取所有已使用的老 tags 去重(兼容旧素材)."""
    rows = db.query(VideoAsset.tags).filter(VideoAsset.tags.isnot(None)).all()
    tag_set: set[str] = set()
    for (tags_list,) in rows:
        if isinstance(tags_list, list):
            tag_set.update(tags_list)
    return sorted(tag_set)


VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm"}


@router.post("/scan")
def scan_materials(db: Session = Depends(get_db)):
    """扫描 materials_dir 下未入库的视频文件，自动创建 VideoAsset 记录.

    对每个新文件自动:
    - 生成 asset_no (V{日期}-{序号})
    - 调用 ffprobe 提取 width/height/duration
    - 自动推断 orientation (landscape/portrait)
    - source 设为 "local"

    Returns:
        {"scanned": N, "imported": N, "skipped": N, "items": [...]}
    """
    cfg = get_config()
    materials_dir = Path(cfg.defaults.materials_dir)
    if not materials_dir.is_dir():
        raise HTTPException(400, f"materials_dir 不存在: {materials_dir}")

    # 收集所有已入库 file_path — 统一归一化为正斜杠，避免 Windows 反斜杠 vs forward slash 去重失效
    materials_prefix = materials_dir.resolve().as_posix()
    existing_paths: set[str] = set()
    for (fp,) in db.query(VideoAsset.file_path).all():
        normalized = fp.replace("\\", "/")
        if normalized.startswith(materials_prefix):
            existing_paths.add(normalized)

    scanned = 0
    imported = 0
    skipped = 0
    items: list[dict[str, Any]] = []

    for entry in sorted(materials_dir.rglob("*")):
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in VIDEO_EXTS:
            continue
        scanned += 1
        abs_path = entry.resolve().as_posix()

        if abs_path in existing_paths:
            skipped += 1
            continue

        # 新文件 → 创建 VideoAsset
        try:
            asset_no = generate_asset_no(db, "V")
            meta = ffprobe_metadata(entry)
            width = 0
            height = 0
            duration = 0.0
            if meta.get("available") and meta.get("streams"):
                for s in meta["streams"]:
                    if s.get("codec_type") == "video":
                        width = s.get("width", 0) or 0
                        height = s.get("height", 0) or 0
                        dur_str = s.get("duration")
                        if dur_str is not None:
                            try:
                                duration = float(dur_str)
                            except (ValueError, TypeError):
                                pass
                        break
            if not duration and meta.get("format", {}).get("duration"):
                try:
                    duration = float(meta["format"]["duration"])
                except (ValueError, TypeError):
                    pass

            orientation = "portrait" if (height > width) else "landscape"

            asset = VideoAsset(
                id=uuid.uuid4().hex,
                asset_no=asset_no,
                source="local",
                file_path=abs_path,
                orientation=orientation,
                width=width,
                height=height,
                duration_sec=duration,
                source_type="footage",
                location="foreign",
                people="none",
            )
            db.add(asset)
            db.flush()  # 让 generate_asset_no 的下次调用能看到最新记录
            imported += 1
            items.append({
                "id": asset.id,
                "asset_no": asset_no,
                "file_path": abs_path,
                "file_name": entry.name,
                "orientation": orientation,
                "width": width,
                "height": height,
                "duration_sec": round(duration, 2),
            })
        except Exception as exc:
            logger.warning("scan: failed to import %s: %s", entry.name, exc)

    db.commit()
    return {"scanned": scanned, "imported": imported, "skipped": skipped, "items": items}


# ---------------------------------------------------------------------------
# 成品库 (VideoOutput)
# ---------------------------------------------------------------------------

@router.get("/outputs")
def list_outputs(
    q: str | None = Query(None),
    orientation: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(VideoOutput)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(VideoOutput.title.ilike(like), VideoOutput.description.ilike(like)))
    if orientation:
        query = query.filter(VideoOutput.orientation == orientation)
    total = query.count()
    items = query.order_by(VideoOutput.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [_output_to_dict(o) for o in items]}


@router.api_route("/outputs/{output_id}/file", methods=["GET", "HEAD"])
def get_output_file(output_id: str, request: Request, db: Session = Depends(get_db)):
    """返回成品视频文件，支持 HTTP Range 请求 (GET/HEAD)."""
    o = db.get(VideoOutput, output_id)
    if not o:
        raise HTTPException(404, "output not found")
    p = Path(o.file_path)
    media_type = mimetypes.guess_type(str(p))[0] or "video/mp4"
    return _video_file_response(request, p, media_type)


@router.delete("/outputs/{output_id}")
def delete_output(output_id: str, remove_file: bool = True, db: Session = Depends(get_db)):
    o = db.get(VideoOutput, output_id)
    if not o:
        raise HTTPException(404, "output not found")
    if remove_file:
        p = Path(o.file_path)
        if p.exists():
            _recycle_file(str(p))
    db.delete(o)
    db.commit()
    return {"status": "ok", "deleted": output_id}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _output_to_dict(o: VideoOutput) -> dict[str, Any]:
    return {
        "id": o.id,
        "job_id": o.job_id,
        "title": o.title,
        "file_path": o.file_path,
        "orientation": o.orientation,
        "duration_sec": o.duration_sec,
        "video_format": o.video_format,
        "description": o.description,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }
