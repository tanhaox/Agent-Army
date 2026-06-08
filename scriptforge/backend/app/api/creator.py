import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, set_owner
from app.core.limiter import limiter
from app.models.persona import Persona
from app.models.user import User
from app.services.creator import creator_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/creator", tags=["Creator"])


class CreatePersonaRequest(BaseModel):
    requirements: str = Field(..., description="风格要求描述")


class CreateGuestsRequest(BaseModel):
    topic: str = Field(..., description="主题")
    count: int = Field(default=20, ge=1, le=50)


class FusionRequest(BaseModel):
    persona_id_a: str
    persona_id_b: str
    ratio: float = Field(default=0.5, ge=0.1, le=0.9)


class SavePersonaRequest(BaseModel):
    generated_data: dict


@router.post("/persona")
@limiter.limit("10/minute")
async def create_persona(request: Request, req: CreatePersonaRequest):
    try:
        result = await creator_service.create_persona(req.requirements)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"status": "success", "persona": result}


@router.post("/guests")
@limiter.limit("10/minute")
async def create_guests(request: Request, req: CreateGuestsRequest):
    try:
        guests = await creator_service.create_guests(req.topic, req.count)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"status": "success", "count": len(guests), "guests": guests}


@router.post("/fusion")
@limiter.limit("10/minute")
async def fuse_personas(request: Request, req: FusionRequest):
    try:
        result = await creator_service.fuse_personas(
            req.persona_id_a, req.persona_id_b, req.ratio
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"status": "success", "persona": result}


@router.post("/save")
async def save_created_persona(
    request: SavePersonaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = request.generated_data
    for field in ["persona_name", "catchphrases"]:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"缺少必要字段: {field}")

    name = data["persona_name"]
    existing = await db.execute(select(Persona).where(Persona.name == name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"人设名称已存在: {name}")

    now = datetime.now(timezone.utc).isoformat()
    persona = Persona(
        name=name,
        global_style=data.get("global_style") or data.get("style_summary") or "",
        catchphrases=data.get("catchphrases", []),
        reaction_patterns=data.get("reaction_patterns", {}),
        sentence_templates=data.get("sentence_templates", []),
        core_values=data.get("core_values", []),
        language_style=data.get("language_style", {}),
        tone_adaptation=data.get("tone_adaptation", {}),
        lingo_map=data.get("lingo_map") or {},
        version=1,
        version_notes=[{"version": 1, "summary": "由角色生成器创建", "created_at": now}],
    )
    set_owner(persona, current_user)
    db.add(persona)
    await db.commit()
    await db.refresh(persona)
    return {"status": "saved", "persona_id": str(persona.id)}
