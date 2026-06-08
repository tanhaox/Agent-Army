import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.director_role import DirectorRole
from app.models.director_act import DirectorAct
from app.models.script_project import ScriptProject
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scripts/{script_id}/director", tags=["Director"])


# ── Request / Response schemas ──────────────────────────────────────────

class RoleInput(BaseModel):
    role_type: str = Field(..., pattern="^(anchor|caller|extra)$")
    name: str = Field(..., max_length=100)
    position: str | None = None
    function: str | None = None
    persona_id: str | None = None
    storyline: str | None = None
    perspective: str | None = None
    sort_order: int = 0


class ActInput(BaseModel):
    title: str = Field(..., max_length=200)
    task: str
    participants: list[str] = Field(default_factory=list)
    sort_order: int = 0


class BatchRolesRequest(BaseModel):
    roles: list[RoleInput]


class BatchActsRequest(BaseModel):
    acts: list[ActInput]


# ── Helpers ─────────────────────────────────────────────────────────────

async def _get_script_or_404(
    script_id: str, db: AsyncSession, current_user: User
) -> ScriptProject:
    try:
        sid = uuid.UUID(script_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的脚本 ID")
    result = await db.execute(select(ScriptProject).where(ScriptProject.id == sid))
    sp = result.scalar_one_or_none()
    if not sp:
        raise HTTPException(status_code=404, detail="脚本项目不存在")
    return sp


# ── Role endpoints ──────────────────────────────────────────────────────

@router.post("/roles")
async def batch_save_roles(
    script_id: str,
    req: BatchRolesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量替换该脚本的所有编导角色。"""
    sp = await _get_script_or_404(script_id, db, current_user)

    await db.execute(
        delete(DirectorRole).where(DirectorRole.script_project_id == sp.id)
    )

    for i, r in enumerate(req.roles):
        persona_id = uuid.UUID(r.persona_id) if r.persona_id else None
        db.add(DirectorRole(
            script_project_id=sp.id,
            role_type=r.role_type,
            name=r.name,
            position=r.position,
            function=r.function,
            persona_id=persona_id,
            storyline=r.storyline,
            perspective=r.perspective,
            sort_order=r.sort_order or i,
        ))

    await db.commit()
    logger.info("Saved %d director roles for script %s", len(req.roles), script_id)
    return {"status": "success", "count": len(req.roles)}


@router.get("/roles")
async def list_roles(
    script_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取该脚本的所有编导角色，按 sort_order 排序。"""
    sp = await _get_script_or_404(script_id, db, current_user)

    result = await db.execute(
        select(DirectorRole)
        .where(DirectorRole.script_project_id == sp.id)
        .order_by(DirectorRole.sort_order)
    )
    roles = result.scalars().all()

    return {
        "script_id": str(sp.id),
        "roles": [
            {
                "id": str(r.id),
                "role_type": r.role_type,
                "name": r.name,
                "position": r.position,
                "function": r.function,
                "persona_id": str(r.persona_id) if r.persona_id else None,
                "storyline": r.storyline,
                "perspective": r.perspective,
                "sort_order": r.sort_order,
            }
            for r in roles
        ],
    }


# ── Act endpoints ───────────────────────────────────────────────────────

@router.post("/acts")
async def batch_save_acts(
    script_id: str,
    req: BatchActsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量替换该脚本的所有编导麦序。"""
    sp = await _get_script_or_404(script_id, db, current_user)

    await db.execute(
        delete(DirectorAct).where(DirectorAct.script_project_id == sp.id)
    )

    for i, a in enumerate(req.acts):
        db.add(DirectorAct(
            script_project_id=sp.id,
            title=a.title,
            task=a.task,
            participants=a.participants,
            sort_order=a.sort_order or i,
        ))

    await db.commit()
    logger.info("Saved %d director acts for script %s", len(req.acts), script_id)
    return {"status": "success", "count": len(req.acts)}


@router.get("/acts")
async def list_acts(
    script_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取该脚本的所有编导麦序，按 sort_order 排序。"""
    sp = await _get_script_or_404(script_id, db, current_user)

    result = await db.execute(
        select(DirectorAct)
        .where(DirectorAct.script_project_id == sp.id)
        .order_by(DirectorAct.sort_order)
    )
    acts = result.scalars().all()

    return {
        "script_id": str(sp.id),
        "acts": [
            {
                "id": str(a.id),
                "title": a.title,
                "task": a.task,
                "participants": a.participants,
                "sort_order": a.sort_order,
            }
            for a in acts
        ],
    }


# ── Clear all ───────────────────────────────────────────────────────────

@router.delete("/all")
async def clear_all(
    script_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除该脚本的所有编导要求（角色 + 麦序）。"""
    sp = await _get_script_or_404(script_id, db, current_user)

    r_result = await db.execute(
        delete(DirectorRole).where(DirectorRole.script_project_id == sp.id)
    )
    a_result = await db.execute(
        delete(DirectorAct).where(DirectorAct.script_project_id == sp.id)
    )
    await db.commit()

    deleted = r_result.rowcount + a_result.rowcount
    logger.info("Cleared %d director items for script %s", deleted, script_id)
    return {"status": "success", "deleted": deleted}
