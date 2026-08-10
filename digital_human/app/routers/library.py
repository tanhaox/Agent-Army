"""Video Library router — 素材库 + 成品库 CRUD / 搜索 / 标签 / 偏好."""
from __future__ import annotations

import logging
import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import get_config
from app.database import get_db
from app.models import VideoAsset, VideoOutput
from app.schemas import (
    ImportFolderRequest,
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
from app.services import library_scan_service, library_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/library", tags=["library"])


@router.get("/assets")
def list_assets(
    q: str | None = Query(None, description="搜索编号/描述/query/摄影师/标签"),
    orientation: str | None = Query(None),
    source_type: str | None = Query(None),
    location: str | None = Query(None),
    people: str | None = Query(None),
    preference: str | None = Query(None),
    scenes: str | None = Query(None, description="逗号分隔, OR 匹配"),
    shot_types: str | None = Query(None, description="逗号分隔, OR 匹配"),
    tags: str | None = Query(None, description="逗号分隔标签过滤"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """搜索/筛选素材库. 喜欢的素材排序置顶."""
    result = library_service.search_assets(
        db,
        q=q, orientation=orientation, source_type=source_type, location=location,
        people=people, preference=preference, scenes=scenes,
        shot_types=shot_types, tags=tags, limit=limit, offset=offset,
    )
    return {
        "total": result["total"],
        "items": [VideoAssetOut.model_validate(a).model_dump() for a in result["items"]],
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
    return library_service.video_file_response(request, p, media_type)


@router.put("/assets/{asset_id}")
def update_asset(asset_id: str, body: VideoAssetUpdate, db: Session = Depends(get_db)):
    """更新素材元数据(asset_no 不可改)."""
    a = db.get(VideoAsset, asset_id)
    if not a:
        raise HTTPException(404, "asset not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(a, key, value)
    db.commit()
    db.refresh(a)
    return VideoAssetOut.model_validate(a).model_dump()


@router.post("/assets/{asset_id}/preference")
def set_preference(asset_id: str, body: VideoAssetPreferenceRequest, db: Session = Depends(get_db)):
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
            library_service.recycle_file(str(p))
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
    tag_set: set[str] = set()
    for (tags_list,) in db.query(VideoAsset.tags).filter(VideoAsset.tags.isnot(None)).all():
        if isinstance(tags_list, list):
            tag_set.update(tags_list)
    return sorted(tag_set)


@router.get("/folders")
def list_material_folders(db: Session = Depends(get_db)):
    """列出 materials_dir 下的一级子文件夹 (供导入弹窗选择)."""
    cfg = get_config()
    base = Path(cfg.defaults.materials_dir).resolve()
    if not base.is_dir():
        return {"materials_dir": str(base), "folders": []}
    folders = sorted(
        p.name for p in base.iterdir() if p.is_dir()
    )
    return {"materials_dir": str(base), "folders": folders}


@router.post("/import-folder")
def import_folder(body: ImportFolderRequest, db: Session = Depends(get_db)):
    """导入 materials_dir 下指定子文件夹并批量附加标签.

    为该文件夹下未入库的视频建立 VideoAsset 记录, 并统一附加 scenes /
    shot_types (合并去重). 标签可用库内既有枚举 (航拍/空镜/城市…), 也可新建.
    已入库素材跳过, 不追加标签.
    """
    cfg = get_config()
    materials_dir = Path(cfg.defaults.materials_dir)
    if not materials_dir.is_dir():
        raise HTTPException(400, f"materials_dir 不存在: {materials_dir}")
    try:
        result = library_scan_service.scan_materials_subdir(
            db,
            materials_dir,
            body.folder,
            scenes=body.scenes,
            shot_types=body.shot_types,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    db.commit()
    return result


@router.post("/scan")
def scan_materials(db: Session = Depends(get_db)):
    """扫描 materials_dir 下未入库的视频文件，自动创建 VideoAsset 记录.

    对每个新文件自动: 生成 asset_no (V{日期}-{序号}) / ffprobe 提取尺寸时长 /
    推断 orientation / source 设为 "local".
    """
    cfg = get_config()
    materials_dir = Path(cfg.defaults.materials_dir)
    if not materials_dir.is_dir():
        raise HTTPException(400, f"materials_dir 不存在: {materials_dir}")
    result = library_scan_service.scan_materials_dir(db, materials_dir)
    db.commit()
    return result


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
    return {"total": total, "items": [library_service.output_to_dict(o) for o in items]}


@router.api_route("/outputs/{output_id}/file", methods=["GET", "HEAD"])
def get_output_file(output_id: str, request: Request, db: Session = Depends(get_db)):
    """返回成品视频文件，支持 HTTP Range 请求 (GET/HEAD)."""
    o = db.get(VideoOutput, output_id)
    if not o:
        raise HTTPException(404, "output not found")
    p = Path(o.file_path)
    media_type = mimetypes.guess_type(str(p))[0] or "video/mp4"
    return library_service.video_file_response(request, p, media_type)


@router.delete("/outputs/{output_id}")
def delete_output(output_id: str, remove_file: bool = True, db: Session = Depends(get_db)):
    o = db.get(VideoOutput, output_id)
    if not o:
        raise HTTPException(404, "output not found")
    if remove_file:
        p = Path(o.file_path)
        if p.exists():
            library_service.recycle_file(str(p))
    db.delete(o)
    db.commit()
    return {"status": "ok", "deleted": output_id}
