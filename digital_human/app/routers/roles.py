"""角色管理路由 — ComfyUI 多视图定型 + 数字人主流水线入参.

7 端点:
- GET    /api/roles
- POST   /api/roles
- GET    /api/roles/{id}
- PUT    /api/roles/{id}
- DELETE /api/roles/{id}
- POST   /api/roles/{id}/generate-views
- POST   /api/roles/{id}/apply
"""
from __future__ import annotations

import asyncio
import logging
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import get_config
from ..database import get_db
from ..models import Role
from ..schemas import (
    ApplyRoleResponse,
    GenerateViewsRequest,
    GenerateViewsResponse,
    RoleCreate,
    RoleOut,
    RoleUpdate,
)
from .comfyui import _find_workflow, _load_workflow_json, _inject_inputs, submit_and_wait

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db)):
    return db.query(Role).order_by(Role.created_at.desc()).all()


@router.get("/{role_id}", response_model=RoleOut)
def get_role(role_id: str, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.post("", response_model=RoleOut, status_code=201)
async def create_role(
    name: str = Form(...),
    description: str = Form(""),
    workflow_used: str = Form("character_three_view"),
    seed: int | None = Form(None),
    reference: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传参考图 + 创建角色记录.

    reference → E:/数字人计划/roles/<id>/ref.<ext>
    """
    cfg = get_config()
    role_id = str(uuid.uuid4())
    role_dir = Path(cfg.defaults.roles_output_root) / role_id
    role_dir.mkdir(parents=True, exist_ok=True)

    # 保存参考图
    suffix = Path(reference.filename or "ref.png").suffix or ".png"
    ref_path = role_dir / f"ref{suffix}"
    blob = await reference.read()
    if not blob:
        raise HTTPException(status_code=400, detail="Empty reference image")
    if len(blob) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Reference image > 10MB")
    ref_path.write_bytes(blob)

    role = Role(
        id=role_id,
        name=name,
        reference_image=str(ref_path),
        description=description,
        workflow_used=workflow_used,
        seed=seed,
        views={},
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.put("/{role_id}", response_model=RoleOut)
def update_role(role_id: str, body: RoleUpdate, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(role, k, v)
    db.commit()
    db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=204)
def delete_role(role_id: str, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    # 不删磁盘,只删 DB 行 — 用户手动清理角色目录
    db.delete(role)
    db.commit()
    return None


@router.post("/{role_id}/generate-views", response_model=GenerateViewsResponse)
async def generate_views(
    role_id: str,
    body: GenerateViewsRequest | None = None,
    db: Session = Depends(get_db),
):
    """调 ComfyUI 出 3 张视图 (正脸/侧脸/全身).

    - body=None → 使用角色当前 description / reference_image / seed
    - body.seed / body.description_override / body.reference_image 可覆盖

    阻塞调用 (客户端拿 200 + views 字典);SSE 留给后续 backlog (ID-008).
    """
    cfg = get_config()
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    body = body or GenerateViewsRequest()
    description = body.description_override or role.description
    reference_image = body.reference_image or role.reference_image
    seed = body.seed if body.seed is not None else role.seed

    # 锁 seed: 若用户传 seed → 覆盖角色; 否则保持角色 seed
    if body.seed is not None and role.seed != body.seed:
        role.seed = body.seed
        db.commit()
        db.refresh(role)

    wf_meta = _find_workflow(role.workflow_used)
    if not wf_meta:
        raise HTTPException(
            status_code=400,
            detail=f"workflow not in manifest: {role.workflow_used}",
        )

    try:
        wf_json = _load_workflow_json(wf_meta["source"])
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    payload = _inject_inputs(
        wf_json,
        {
            "description": description,
            "reference_image": reference_image,
            "seed": seed,
        },
    )

    result = await submit_and_wait(
        workflow_payload=payload,
        role_id=role_id,
        base_url=cfg.defaults.base_url_comfyui,
        timeout_sec=cfg.defaults.comfyui_timeout_sec,
        output_view_order=wf_meta.get("output_view_order"),
    )

    status = result["status"]
    if status == "completed":
        role.views = result["views"]
        db.commit()
        db.refresh(role)
    elif status == "failed":
        raise HTTPException(status_code=502, detail=result.get("error") or "ComfyUI failed")
    elif status == "timeout":
        raise HTTPException(status_code=504, detail=result.get("error") or "ComfyUI timeout")

    return GenerateViewsResponse(
        role_id=role_id,
        prompt_id=result["prompt_id"],
        status=status,
        views=result["views"],
        error=result.get("error"),
    )


@router.post("/{role_id}/apply", response_model=ApplyRoleResponse)
def apply_role(role_id: str, db: Session = Depends(get_db)):
    """把角色应用到主流水线 — 当前仅返回入参结构 (留接口位).

    真正接 A 管线分镜待 ID-007 backlog.
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if not role.views:
        raise HTTPException(
            status_code=400,
            detail="Role has no views yet — 请先生成多视图",
        )

    mainstream_input: dict[str, Any] = {
        "host_name": role.name,
        "host_reference": role.reference_image,
        "host_views": role.views,
        "host_description": role.description,
        "workflow_used": role.workflow_used,
        "seed": role.seed,
    }
    return ApplyRoleResponse(
        applied=True,
        role_id=role_id,
        mainstream_input=mainstream_input,
        note="主流水线分镜接入待 ID-007 backlog",
    )