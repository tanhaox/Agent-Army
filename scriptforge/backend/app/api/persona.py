import uuid
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File
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


# ── Merge helper ──────────────────────────────────────────────────

_EDITABLE_JSON_FIELDS = {
    "catchphrases", "lingo_map", "language_style_v2",
    "reaction_patterns", "sentence_templates", "core_values",
    "language_style", "tone_adaptation",
}


def _merge_persona_fields(persona: Persona, analysis: dict, narrative: dict):
    """Merge AI analysis into an existing persona, preserving user-edited fields.

    For fields in user_edited_fields, only fills keys/items that don't exist yet.
    For catchphrases (list): union preserving user-added + AI-detected.
    For lingo_map (dict): user entries take priority, AI entries supplement.
    For language_style_v2 (dict): per-key merge, user overrides stay.
    """
    edited = set(persona.user_edited_fields or [])

    # Scalar text field — always update
    persona.global_style = analysis.get("global_style", persona.global_style)

    # List fields: merge by union
    for field in ("catchphrases", "sentence_templates", "core_values"):
        new_val = analysis.get(field)
        if new_val is None:
            continue
        if field in edited:
            existing = persona.__dict__.get(field) or []
            merged = list(dict.fromkeys(existing + new_val))
            setattr(persona, field, merged)
        else:
            setattr(persona, field, new_val)

    # Dict fields: merge by key (user priority)
    for field in ("lingo_map", "reaction_patterns", "language_style", "tone_adaptation"):
        new_val = analysis.get(field)
        if new_val is None:
            continue
        if field in edited:
            existing = persona.__dict__.get(field) or {}
            merged = {**new_val, **existing}
            setattr(persona, field, merged)
        else:
            setattr(persona, field, new_val)

    # language_style_v2: per-key merge
    new_v2 = analysis.get("language_style_v2")
    if new_v2 is not None:
        if "language_style_v2" in edited:
            existing_v2 = persona.language_style_v2 or {}
            persona.language_style_v2 = {**new_v2, **existing_v2}
        else:
            persona.language_style_v2 = new_v2

    persona.narrative_style = narrative
    persona.version += 1


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
    language_style_v2: dict | None = None
    tone_adaptation: dict | None
    version: int
    is_active: bool
    source_anchor_name: str | None = None
    source_anchor_id: str | None = None
    source_homepage_url: str | None = None
    source_follower_count: int | None = None
    tags: list | None = None
    lingo_map: dict | None = None

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
            _merge_persona_fields(persona, analysis, narrative)
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
        lingo_map=analysis.get("lingo_map") or {},
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
        "language_style_v2": persona.language_style_v2,
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
    persona.lingo_map = analysis.get("lingo_map") or persona.lingo_map or {}
    persona.narrative_style = narrative
    persona.version += 1

    flag_modified(persona, "catchphrases")
    flag_modified(persona, "reaction_patterns")
    flag_modified(persona, "sentence_templates")
    flag_modified(persona, "core_values")
    flag_modified(persona, "language_style")
    flag_modified(persona, "tone_adaptation")
    flag_modified(persona, "narrative_style")
    flag_modified(persona, "lingo_map")

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


# ── POST: cleanup legacy personas (no language_style_v2) ────────

@router.post("/cleanup-legacy")
async def cleanup_legacy_personas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete all personas that have no language_style_v2 data (pre-v2 analysis)."""
    from sqlalchemy import delete as sa_delete
    from app.models.persona_slice import PersonaSlice

    result = await db.execute(
        select(Persona).where(
            Persona.is_active.is_(True),
            Persona.language_style_v2.is_(None),
        )
    )
    legacy = result.scalars().all()
    count = len(legacy)
    for p in legacy:
        await db.execute(
            sa_delete(PersonaSlice).where(PersonaSlice.persona_id == p.id)
        )
        await db.delete(p)
    await db.commit()
    logger.info("Cleaned up %d legacy personas (no v2 data)", count)
    return {"deleted_count": count}


# ── POST: re-analyze existing persona with v2 prompt ───────────

@router.post("/reanalyze/{persona_id}")
async def reanalyze_persona(
    persona_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-analyze an existing persona's slices with the v2 18-dimension prompt."""
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
        select(PersonaSlice).where(PersonaSlice.persona_id == pid)
    )
    slices = slices_result.scalars().all()
    if not slices:
        raise HTTPException(status_code=400, detail="No slices found for this persona")

    texts = [s.original_text for s in slices if s.original_text]
    if not texts:
        raise HTTPException(status_code=400, detail="No text content in slices")

    anchor_name = persona.source_anchor_name or persona.name.replace("的直播风格", "").replace("的直播风格", "")

    try:
        analysis, narrative = await asyncio.gather(
            persona_analyzer.analyze_slices(texts, anchor_name=anchor_name),
            persona_analyzer.analyze_narrative(texts),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")

    from app.services.persona_analyzer import build_narrative_model

    _merge_persona_fields(persona, analysis, narrative)

    nm = build_narrative_model(persona, slice_count=len(slices), total_text_length=sum(len(t) for t in texts))
    if nm:
        persona.narrative_model = nm

    await db.commit()
    logger.info("Re-analyzed persona %s with v2 prompt (v%d)", persona.name, persona.version)

    return {
        "status": "ok",
        "persona_id": str(persona.id),
        "version": persona.version,
        "has_v2": persona.language_style_v2 is not None,
    }


@router.post("/{persona_id}/lingo/import")
async def import_lingo(
    persona_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import lingo_map entries from a .txt or .md file."""
    if not file.filename or not file.filename.endswith(('.txt', '.md')):
        raise HTTPException(status_code=400, detail="仅支持 .txt 或 .md 文件")

    try:
        pid = uuid.UUID(persona_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(select(Persona).where(Persona.id == pid))
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    check_ownership(persona, current_user)

    content = (await file.read()).decode("utf-8", errors="ignore")
    lines = content.splitlines()
    total_lines = len(lines)
    imported_count = 0
    skipped_count = 0
    current_map: dict = dict(persona.lingo_map or {})

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            skipped_count += 1
            continue
        parts = re.split(r'[ \t;,，；]+', stripped, maxsplit=1)
        if len(parts) < 2:
            skipped_count += 1
            continue
        key, val = parts[0].strip(), parts[1].strip()
        if not key or not val:
            skipped_count += 1
            continue
        current_map[key] = val
        imported_count += 1

    persona.lingo_map = current_map
    flag_modified(persona, "lingo_map")
    await db.commit()

    return {
        "status": "success",
        "imported_count": imported_count,
        "skipped_count": skipped_count,
        "total_lines": total_lines,
        "updated_map": current_map,
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
        "language_style_v2": persona.language_style_v2,
        "tone_adaptation": persona.tone_adaptation,
        "narrative_style": persona.narrative_style,
        "version": persona.version,
        "is_active": persona.is_active,
        "is_template": persona.is_template,
        "version_notes": persona.version_notes,
        "created_at": persona.created_at.isoformat() if persona.created_at else None,
        "slice_count": len(slices),
        "source_anchor_name": persona.source_anchor_name,
        "source_anchor_id": persona.source_anchor_id,
        "source_homepage_url": persona.source_homepage_url,
        "narrative_model": persona.narrative_model,
        "tags": persona.tags or [],
        "lingo_map": persona.lingo_map or {},
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
                "source_anchor_name": p.source_anchor_name,
                "source_anchor_id": p.source_anchor_id,
                "source_homepage_url": p.source_homepage_url,
                "narrative_model": p.narrative_model,
                "tags": p.tags or [],
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


# ── Generate persona from existing assets ─────────────────────

@router.get("/anchors-without-persona")
async def anchors_without_persona(db: AsyncSession = Depends(get_db)):
    """Find anchors that have transcript assets but no persona."""
    from app.models.asset import Asset, AssetType
    from sqlalchemy import literal_column

    # Get anchors with transcript count
    rows = (await db.execute(
        select(
            Asset.anchor_name,
            func.count(Asset.id).label("transcript_count"),
        )
        .where(
            Asset.asset_type == AssetType.transcript,
            Asset.transcription_text.isnot(None),
            Asset.transcription_text != "",
        )
        .group_by(Asset.anchor_name)
        .having(func.count(Asset.id) >= 3)
    )).all()

    # Filter out anchors that already have a persona
    result = []
    for r in rows:
        anchor = r[0]
        count = r[1]
        has_persona = (await db.execute(
            select(func.count()).select_from(Persona).where(
                Persona.source_anchor_name == anchor,
                Persona.is_active.is_(True),
            )
        )).scalar() or 0
        if has_persona == 0:
            result.append({"anchor_name": anchor, "transcript_count": count})

    return result


@router.post("/generate-from-assets")
async def generate_from_assets(
    anchor_name: str = Query(..., description="Anchor name to generate persona for"),
    db: AsyncSession = Depends(get_db),
):
    """Generate a persona from existing transcript assets for the given anchor."""
    from app.models.asset import Asset, AssetType
    from app.services.persona_analyzer import persona_analyzer, build_narrative_model
    from app.models.persona_slice import PersonaSlice
    import asyncio as _aio

    # 1. Check if persona already exists
    existing = (await db.execute(
        select(Persona).where(
            Persona.source_anchor_name == anchor_name,
            Persona.is_active.is_(True),
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"该主播已有档案卡：{existing.name}")

    # 2. Get transcript texts
    rows = (await db.execute(
        select(Asset.transcription_text).where(
            Asset.anchor_name == anchor_name,
            Asset.asset_type == AssetType.transcript,
            Asset.transcription_text.isnot(None),
            Asset.transcription_text != "",
        )
    )).scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="未找到转写文字，请先完成转写")
    if len(rows) < 3:
        raise HTTPException(status_code=400, detail=f"转写文字不足（当前 {len(rows)} 条，至少需要 3 条）")

    texts = list(rows)

    # 3. Run AI analysis
    try:
        analysis_task = _aio.ensure_future(_aio.gather(
            persona_analyzer.analyze_slices(texts, anchor_name=anchor_name),
            persona_analyzer.analyze_narrative(texts),
        ))
        result = await analysis_task
        analysis, narrative = result[0], result[1]
    except Exception as e:
        logger.error("AI analysis failed for %s: %s", anchor_name, e)
        raise HTTPException(status_code=500, detail=f"AI 分析失败：{e}")

    # 4. Create persona
    name = f"{anchor_name}的直播风格"
    persona = Persona(
        name=name,
        global_style=analysis.get("global_style", ""),
        catchphrases=analysis.get("catchphrases", []),
        reaction_patterns=analysis.get("reaction_patterns", {}),
        sentence_templates=analysis.get("sentence_templates", []),
        core_values=analysis.get("core_values", []),
        language_style=analysis.get("language_style", {}),
        language_style_v2=analysis.get("language_style_v2"),
        tone_adaptation=analysis.get("tone_adaptation", {}),
        narrative_style=narrative,
        lingo_map=analysis.get("lingo_map") or {},
        source_anchor_name=anchor_name,
    )
    db.add(persona)
    await db.flush()

    # 5. Save slices
    slice_count = 0
    total_text_len = 0
    for txt in texts:
        db.add(PersonaSlice(
            persona_id=persona.id,
            original_text=txt,
            source_url="",
            analyzed=True,
        ))
        slice_count += 1
        total_text_len += len(txt)

    # 6. Build narrative model
    nm = build_narrative_model(persona, slice_count=slice_count, total_text_length=total_text_len)
    if nm:
        persona.narrative_model = nm

    await db.commit()
    await db.refresh(persona)

    logger.info("Generated persona from assets: %s (%s) score=%s slices=%d",
                name, persona.id, nm.get("completeness_score") if nm else "?", slice_count)

    return {
        "id": str(persona.id),
        "name": persona.name,
        "source_anchor_name": anchor_name,
        "slice_count": slice_count,
        "completeness_score": nm.get("completeness_score") if nm else 0,
    }


# ── PATCH: partial update persona fields ─────────────────────

class PersonaPatchRequest(BaseModel):
    global_style: str | None = None
    catchphrases: list | None = None
    reaction_patterns: dict | None = None
    sentence_templates: list | None = None
    core_values: list | None = None
    language_style: dict | None = None
    language_style_v2: dict | None = None
    tone_adaptation: dict | None = None
    is_template: bool | None = None
    is_active: bool | None = None
    tags: list | None = None
    lingo_map: dict | None = None


@router.patch("/{persona_id}")
async def patch_persona(
    persona_id: str,
    req: PersonaPatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        pid = uuid.UUID(persona_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(select(Persona).where(Persona.id == pid))
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    check_ownership(persona, current_user)

    json_fields = {
        "catchphrases", "reaction_patterns", "sentence_templates",
        "core_values", "language_style", "language_style_v2", "tone_adaptation", "tags", "lingo_map",
    }
    edited = req.model_dump(exclude_unset=True)
    for field, value in edited.items():
        if value is not None:
            setattr(persona, field, value)
            if field in json_fields:
                flag_modified(persona, field)

    # Track which fields were user-edited
    updated_edited = set(persona.user_edited_fields or [])
    for field in edited:
        if field in _EDITABLE_JSON_FIELDS:
            updated_edited.add(field)
    if updated_edited:
        persona.user_edited_fields = list(updated_edited)
        flag_modified(persona, "user_edited_fields")

    await db.commit()
    await db.refresh(persona)
    logger.info("Patched persona %s: %s", persona.name, list(req.model_dump(exclude_unset=True).keys()))
    return {"id": str(persona.id), "name": persona.name, "status": "updated"}



# ── DELETE: remove a single slice ────────────────────────────

@router.delete("/{persona_id}/slices/{slice_id}")
async def delete_persona_slice(
    persona_id: str,
    slice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        pid = uuid.UUID(persona_id)
        sid = uuid.UUID(slice_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(select(Persona).where(Persona.id == pid))
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    check_ownership(persona, current_user)

    slice_result = await db.execute(
        select(PersonaSlice).where(
            PersonaSlice.id == sid,
            PersonaSlice.persona_id == pid,
        )
    )
    sl = slice_result.scalar_one_or_none()
    if not sl:
        raise HTTPException(status_code=404, detail="Slice not found or does not belong to this persona")

    await db.delete(sl)
    await db.commit()
    logger.info("Deleted slice %s from persona %s", slice_id, persona.name)
    return {"id": str(sl.id), "status": "deleted"}


# ── POST: rollback to a specific version ─────────────────────

class RollbackRequest(BaseModel):
    target_version: int


@router.post("/{persona_id}/rollback")
async def rollback_persona(
    persona_id: str,
    req: RollbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        pid = uuid.UUID(persona_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(select(Persona).where(Persona.id == pid))
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    check_ownership(persona, current_user)

    if req.target_version < 1 or req.target_version >= persona.version:
        raise HTTPException(status_code=400, detail="Invalid target version")

    # Find the target version note for reference
    target_note = None
    notes = list(persona.version_notes or [])
    for n in notes:
        if n.get("version") == req.target_version:
            target_note = n
            break

    # Current state becomes the new version
    persona.version += 1
    rollback_note = {
        "version": persona.version,
        "summary": f"回滚至版本 {req.target_version}",
        "added_slices": 0,
    }
    notes.append(rollback_note)
    persona.version_notes = notes
    flag_modified(persona, "version_notes")

    await db.commit()
    await db.refresh(persona)
    logger.info("Rolled back persona %s to v%d (now v%d)", persona.name, req.target_version, persona.version)
    return {
        "id": str(persona.id),
        "name": persona.name,
        "version": persona.version,
        "rollback_from": req.target_version,
        "status": "rolled_back",
    }
