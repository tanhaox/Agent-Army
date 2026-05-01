import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import get_db
from app.core.security import check_ownership, get_current_user, set_owner
from app.core.limiter import limiter
from app.models.persona import Persona
from app.models.persona_slice import PersonaSlice
from app.models.user import User
from app.services.persona_analyzer import persona_analyzer

import asyncio
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/persona", tags=["Persona"])


class SliceInput(BaseModel):
    text: str
    source_url: str | None = None


class AnalyzeRequest(BaseModel):
    persona_name: str | None = None
    slices: list[SliceInput]
    force_new: bool = False


class AppendRequest(BaseModel):
    texts: list[str]
    emotion_tag: str | None = None
    action_desc: str | None = None


class PersonaResponse(BaseModel):
    id: str
    name: str
    global_style: str
    catchphrases: list | None
    reaction_patterns: dict | None
    sentence_templates: list | None
    core_values: list | None
    language_style: dict | None
    tone_adaptation: dict | None
    version: int
    is_active: bool

    model_config = {"from_attributes": True}


@router.post("/analyze")
@limiter.limit("10/minute")
async def analyze_persona(
    request: Request,
    req: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not req.slices:
        raise HTTPException(status_code=400, detail="At least one slice is required")

    try:
        texts = [s.text for s in req.slices]
        analysis, narrative = await asyncio.gather(
            persona_analyzer.analyze_slices(texts),
            persona_analyzer.analyze_narrative(texts),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    name = req.persona_name or analysis.get("name", "Unnamed Persona")

    if not req.force_new:
        existing = await db.execute(select(Persona).where(Persona.name == name))
        persona = existing.scalar_one_or_none()
        if persona:
            persona.global_style = analysis.get("global_style", persona.global_style)
            persona.catchphrases = analysis.get("catchphrases", persona.catchphrases)
            persona.reaction_patterns = analysis.get("reaction_patterns", persona.reaction_patterns)
            persona.sentence_templates = analysis.get("sentence_templates", persona.sentence_templates)
            persona.core_values = analysis.get("core_values", persona.core_values)
            persona.language_style = analysis.get("language_style", persona.language_style)
            persona.tone_adaptation = analysis.get("tone_adaptation", persona.tone_adaptation)
            persona.narrative_style = narrative
            persona.version += 1
            await db.commit()
            await db.refresh(persona)

            for s in req.slices:
                slice_obj = PersonaSlice(
                    persona_id=persona.id,
                    original_text=s.text,
                    source_url=s.source_url,
                    analyzed=True,
                )
                db.add(slice_obj)
            await db.commit()

            return {"action": "updated", "persona_id": str(persona.id), "version": persona.version, "narrative_style": narrative}

    persona = Persona(
        name=name,
        global_style=analysis.get("global_style", ""),
        catchphrases=analysis.get("catchphrases", []),
        reaction_patterns=analysis.get("reaction_patterns", {}),
        sentence_templates=analysis.get("sentence_templates", []),
        core_values=analysis.get("core_values", []),
        language_style=analysis.get("language_style", {}),
        tone_adaptation=analysis.get("tone_adaptation", {}),
        narrative_style=narrative,
    )
    set_owner(persona, current_user)
    db.add(persona)
    await db.flush()

    for s in req.slices:
        slice_obj = PersonaSlice(
            persona_id=persona.id,
            original_text=s.text,
            source_url=s.source_url,
            analyzed=True,
        )
        db.add(slice_obj)

    await db.commit()
    await db.refresh(persona)

    return {"action": "created", "persona_id": str(persona.id), "version": 1, "narrative_style": narrative}


@router.post("/{persona_id}/append")
async def append_slices_to_persona(
    persona_id: str,
    req: AppendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not req.texts:
        raise HTTPException(status_code=400, detail="At least one text is required")

    try:
        pid = uuid.UUID(persona_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(
        select(Persona).where(Persona.id == pid, Persona.is_active.is_(True))
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    check_ownership(persona, current_user)

    slices_result = await db.execute(
        select(func.count()).select_from(PersonaSlice).where(PersonaSlice.persona_id == pid)
    )
    existing_slice_count = slices_result.scalar() or 0

    existing_persona = {
        "name": persona.name,
        "global_style": persona.global_style,
        "language_style": persona.language_style or {},
        "catchphrases": persona.catchphrases or [],
        "reaction_patterns": persona.reaction_patterns or {},
        "sentence_templates": persona.sentence_templates or [],
        "core_values": persona.core_values or [],
        "tone_adaptation": persona.tone_adaptation or {},
    }

    try:
        analysis, narrative = await asyncio.gather(
            persona_analyzer.incremental_analyze(
                existing_persona, req.texts, existing_slice_count
            ),
            persona_analyzer.analyze_narrative(req.texts),
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incremental analysis failed: {e}")

    old_catchphrases = set(persona.catchphrases or [])
    new_catchphrases = set(analysis.get("catchphrases", []))
    added_catchphrases = new_catchphrases - old_catchphrases

    persona.global_style = analysis.get("global_style", persona.global_style)
    persona.catchphrases = analysis.get("catchphrases", persona.catchphrases)
    persona.reaction_patterns = analysis.get("reaction_patterns", persona.reaction_patterns)
    persona.sentence_templates = analysis.get("sentence_templates", persona.sentence_templates)
    persona.core_values = analysis.get("core_values", persona.core_values)
    persona.language_style = analysis.get("language_style", persona.language_style)
    persona.tone_adaptation = analysis.get("tone_adaptation", persona.tone_adaptation)
    persona.narrative_style = narrative
    persona.version += 1

    flag_modified(persona, "catchphrases")
    flag_modified(persona, "reaction_patterns")
    flag_modified(persona, "sentence_templates")
    flag_modified(persona, "core_values")
    flag_modified(persona, "language_style")
    flag_modified(persona, "tone_adaptation")
    flag_modified(persona, "narrative_style")

    changes = []
    if added_catchphrases:
        changes.append(f"新增口头禅：{', '.join(added_catchphrases)}")
    if analysis.get("global_style") != persona.global_style:
        changes.append("风格综述已更新")

    note = {
        "version": persona.version,
        "summary": "; ".join(changes) if changes else "特征微调",
        "added_slices": len(req.texts),
    }

    notes = list(persona.version_notes or [])
    notes.append(note)
    persona.version_notes = notes
    flag_modified(persona, "version_notes")

    for text in req.texts:
        slice_obj = PersonaSlice(
            persona_id=pid,
            original_text=text,
            emotion_tag=req.emotion_tag,
            action_desc=req.action_desc,
            analyzed=True,
        )
        db.add(slice_obj)

    await db.commit()
    await db.refresh(persona)

    logger.info("Appended %d slices to persona %s (v%d)", len(req.texts), persona.name, persona.version)

    return {
        "action": "updated",
        "persona_id": str(persona.id),
        "version": persona.version,
        "changes_summary": note,
    }


@router.get("/{persona_id}/slices")
async def get_persona_slices(
    persona_id: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        pid = uuid.UUID(persona_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(
        select(PersonaSlice)
        .where(PersonaSlice.persona_id == pid)
        .order_by(PersonaSlice.created_at.desc())
    )
    slices = result.scalars().all()

    return {
        "total": len(slices),
        "items": [
            {
                "id": str(s.id),
                "original_text": s.original_text,
                "preview": s.original_text[:100] + "..." if len(s.original_text) > 100 else s.original_text,
                "emotion_tag": s.emotion_tag,
                "action_desc": s.action_desc,
                "source_url": s.source_url,
                "analyzed": s.analyzed,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in slices
        ],
    }


@router.get("/{persona_id}")
async def get_persona(persona_id: str, db: AsyncSession = Depends(get_db)):
    try:
        pid = uuid.UUID(persona_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(
        select(Persona).where(Persona.id == pid, Persona.is_active.is_(True))
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    slices_result = await db.execute(
        select(PersonaSlice).where(PersonaSlice.persona_id == pid)
    )
    slices = slices_result.scalars().all()

    return {
        "id": str(persona.id),
        "name": persona.name,
        "global_style": persona.global_style,
        "catchphrases": persona.catchphrases,
        "reaction_patterns": persona.reaction_patterns,
        "sentence_templates": persona.sentence_templates,
        "core_values": persona.core_values,
        "language_style": persona.language_style,
        "tone_adaptation": persona.tone_adaptation,
        "narrative_style": persona.narrative_style,
        "version": persona.version,
        "is_active": persona.is_active,
        "version_notes": persona.version_notes,
        "created_at": persona.created_at.isoformat() if persona.created_at else None,
        "slice_count": len(slices),
    }


@router.get("/")
async def list_personas(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(
        select(func.count()).select_from(Persona).where(Persona.is_active.is_(True))
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Persona)
        .where(Persona.is_active.is_(True))
        .order_by(Persona.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    personas = result.scalars().all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": str(p.id),
                "name": p.name,
                "global_style": p.global_style[:100] if p.global_style else "",
                "version": p.version,
                "is_active": p.is_active,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in personas
        ],
    }


@router.delete("/{persona_id}")
async def delete_persona(
    persona_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        pid = uuid.UUID(persona_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(
        select(Persona).where(Persona.id == pid, Persona.is_active.is_(True))
    )
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    check_ownership(persona, current_user)
    persona.is_active = False
    await db.commit()
    logger.info("Deleted persona: %s (%s)", persona.name, persona_id)
    return {"id": str(persona.id), "name": persona.name, "status": "deleted"}
