import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import check_ownership, get_current_user, set_owner
from app.models.room_tone import RoomTone
from app.models.user import User

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/room-tones", tags=["RoomTones"])


class CreateRoomToneRequest(BaseModel):
    name: str
    description: str | None = None
    core_rules: str
    forbidden_topics: str | None = None
    is_preset: bool = False


@router.get("/")
async def list_room_tones(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(func.count()).select_from(RoomTone).where(RoomTone.is_active.is_(True))
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(RoomTone)
        .where(RoomTone.is_active.is_(True))
        .order_by(RoomTone.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    tones = result.scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": str(t.id),
                "name": t.name,
                "description": t.description,
                "core_rules": t.core_rules,
                "forbidden_topics": t.forbidden_topics,
                "is_preset": t.is_preset,
            }
            for t in tones
        ],
    }


@router.get("/{tone_id}")
async def get_room_tone(tone_id: str, db: AsyncSession = Depends(get_db)):
    try:
        tid = uuid.UUID(tone_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    tone = await db.get(RoomTone, tid)
    if not tone or not tone.is_active:
        raise HTTPException(status_code=404, detail="RoomTone not found")

    return {
        "id": str(tone.id),
        "name": tone.name,
        "description": tone.description,
        "core_rules": tone.core_rules,
        "forbidden_topics": tone.forbidden_topics,
        "is_preset": tone.is_preset,
        "created_at": tone.created_at.isoformat() if tone.created_at else None,
    }


@router.post("/")
async def create_room_tone(
    req: CreateRoomToneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tone = RoomTone(
        name=req.name,
        description=req.description,
        core_rules=req.core_rules,
        forbidden_topics=req.forbidden_topics,
        is_preset=req.is_preset,
    )
    set_owner(tone, current_user)
    db.add(tone)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="调性名称已存在")
    await db.refresh(tone)

    return {
        "id": str(tone.id),
        "name": tone.name,
        "description": tone.description,
        "core_rules": tone.core_rules,
    }


@router.delete("/{tone_id}")
async def delete_room_tone(
    tone_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        tid = uuid.UUID(tone_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    tone = await db.get(RoomTone, tid)
    if not tone or not tone.is_active:
        raise HTTPException(status_code=404, detail="RoomTone not found")
    if tone.is_preset:
        raise HTTPException(status_code=403, detail="预设调性不可删除")
    check_ownership(tone, current_user)

    tone.is_active = False
    await db.commit()
    logger.info("Deleted room tone: %s (%s)", tone.name, tone_id)
    return {"id": str(tone.id), "name": tone.name, "status": "deleted"}
