import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.limiter import limiter
from app.models.strategy_entry import StrategyEntry
from app.models.user import User
from app.services.strategy_extractor import strategy_extractor
from app.services.vector_store import store_pgvector, vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategies", tags=["Strategies"])


class ExtractRequest(BaseModel):
    text: str
    category: str
    material_id: str | None = None


class BatchExtractItem(BaseModel):
    text: str
    category: str
    material_id: str | None = None


class BatchExtractRequest(BaseModel):
    items: list[BatchExtractItem]


class StrategyResponse(BaseModel):
    id: str
    title: str
    category: str
    pattern_type: str | None
    extracted_pattern: str
    emotional_curve: dict | None
    sentence_templates: list | None
    tags: list | None
    quality_score: float
    usage_count: int
    source_text: str | None
    created_at: str | None


@router.post("/extract")
@limiter.limit("10/minute")
async def extract_strategies(
    request: Request,
    req: ExtractRequest, db: AsyncSession = Depends(get_db)
):
    try:
        raw_strategies = await strategy_extractor.extract_strategies(
            req.text, req.category
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if not raw_strategies:
        return {"extracted": 0, "strategies": []}

    saved = []
    ids_for_chroma = []
    docs_for_chroma = []
    metas_for_chroma = []

    for s in raw_strategies:
        sid = str(uuid.uuid4())
        pattern_type = s.get("pattern_type", "unknown")
        description = s.get("description", "")
        templates = s.get("sentence_templates", [])
        tags = s.get("tags", [])
        curve = s.get("emotional_curve", "")
        score = s.get("quality_score", 5.0)

        entry = StrategyEntry(
            id=uuid.UUID(sid),
            title=f"{pattern_type}: {description[:50]}",
            category=req.category,
            source_text=req.text[:2000] if req.text else None,
            extracted_pattern=description,
            pattern_type=pattern_type,
            emotional_curve={"curve": curve} if curve else None,
            sentence_templates=templates,
            tags=tags,
            embedding_id=sid,
            quality_score=score,
        )
        db.add(entry)
        saved.append(sid)

        chroma_doc = f"{pattern_type}: {description} {' '.join(templates)} {' '.join(tags)}"
        ids_for_chroma.append(sid)
        docs_for_chroma.append(chroma_doc)
        metas_for_chroma.append({
            "pattern_type": pattern_type,
            "category": req.category,
            "quality_score": score,
        })

    try:
        vector_store.add_vectors(ids_for_chroma, docs_for_chroma, metas_for_chroma)
    except Exception as e:
        logger.warning("ChromaDB write failed: %s", e)

    await db.commit()

    # Store vectors in pgvector as well (non-blocking, best-effort)
    for sid, chroma_doc in zip(saved, docs_for_chroma):
        try:
            await store_pgvector(db, uuid.UUID(sid), chroma_doc)
        except Exception as e:
            logger.warning("pgvector write failed for %s: %s", sid, e)

    return {
        "extracted": len(saved),
        "strategies": [
            {
                "id": sid,
                "pattern_type": s.get("pattern_type"),
                "description": s.get("description"),
                "sentence_templates": s.get("sentence_templates", []),
                "emotional_curve": s.get("emotional_curve"),
                "tags": s.get("tags", []),
                "quality_score": s.get("quality_score", 5.0),
            }
            for sid, s in zip(saved, raw_strategies)
        ],
    }


@router.post("/batch-extract")
@limiter.limit("5/minute")
async def batch_extract_strategies(
    request: Request,
    req: BatchExtractRequest, db: AsyncSession = Depends(get_db)
):
    all_results = []
    for item in req.items:
        try:
            result = await extract_strategies(
                request,
                ExtractRequest(
                    text=item.text,
                    category=item.category,
                    material_id=item.material_id,
                ),
                db=db,
            )
            all_results.append(result)
        except Exception as e:
            all_results.append({"extracted": 0, "strategies": [], "error": str(e)})

    total = sum(r.get("extracted", 0) for r in all_results)
    return {"total_extracted": total, "results": all_results}


@router.get("/")
async def list_strategies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    pattern_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(StrategyEntry).order_by(StrategyEntry.created_at.desc())
    count_query = select(func.count()).select_from(StrategyEntry)

    if category:
        query = query.where(StrategyEntry.category == category)
        count_query = count_query.where(StrategyEntry.category == category)
    if pattern_type:
        query = query.where(StrategyEntry.pattern_type == pattern_type)
        count_query = count_query.where(StrategyEntry.pattern_type == pattern_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    entries = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": str(e.id),
                "title": e.title,
                "category": e.category,
                "pattern_type": e.pattern_type,
                "extracted_pattern": e.extracted_pattern,
                "tags": e.tags,
                "quality_score": e.quality_score,
                "usage_count": e.usage_count,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ],
    }


@router.get("/{strategy_id}")
async def get_strategy(
    strategy_id: str, db: AsyncSession = Depends(get_db)
):
    try:
        sid = uuid.UUID(strategy_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    entry = await db.get(StrategyEntry, sid)
    if not entry:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return {
        "id": str(entry.id),
        "title": entry.title,
        "category": entry.category,
        "pattern_type": entry.pattern_type,
        "extracted_pattern": entry.extracted_pattern,
        "emotional_curve": entry.emotional_curve,
        "sentence_templates": entry.sentence_templates,
        "tags": entry.tags,
        "quality_score": entry.quality_score,
        "usage_count": entry.usage_count,
        "source_text": entry.source_text,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a strategy entry. NOTE: StrategyEntry has no created_by FK;
    ownership is not enforced. For future multi-user, add created_by column."""
    try:
        sid = uuid.UUID(strategy_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    entry = await db.get(StrategyEntry, sid)
    if not entry:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if entry.embedding_id:
        try:
            vector_store.delete_vectors([entry.embedding_id])
        except Exception as e:
            logger.warning("ChromaDB delete failed: %s", e)

    await db.delete(entry)
    await db.commit()
    return {"deleted": str(sid)}
