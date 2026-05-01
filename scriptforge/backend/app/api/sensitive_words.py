import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.sensitive_word import SensitiveWord
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sensitive-words", tags=["SensitiveWords"])


class AddWordRequest(BaseModel):
    word: str
    category: str = "其他"
    severity: str = "medium"


class BatchImportRequest(BaseModel):
    words: list[AddWordRequest]


class WordResponse(BaseModel):
    id: str
    word: str
    category: str | None
    severity: str
    is_active: bool
    created_at: str | None


@router.get("/")
async def list_sensitive_words(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    category: str | None = None,
    severity: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(SensitiveWord).where(SensitiveWord.is_active == True).order_by(SensitiveWord.created_at.desc())
    count_query = select(func.count()).select_from(SensitiveWord).where(SensitiveWord.is_active == True)

    if category:
        query = query.where(SensitiveWord.category == category)
        count_query = count_query.where(SensitiveWord.category == category)
    if severity:
        query = query.where(SensitiveWord.severity == severity)
        count_query = count_query.where(SensitiveWord.severity == severity)
    if search:
        pattern = f"%{search}%"
        query = query.where(SensitiveWord.word.ilike(pattern))
        count_query = count_query.where(SensitiveWord.word.ilike(pattern))

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
                "word": e.word,
                "category": e.category,
                "severity": e.severity,
                "is_active": e.is_active,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in entries
        ],
    }


@router.post("/")
async def add_sensitive_word(req: AddWordRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(SensitiveWord).where(SensitiveWord.word == req.word)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"词条已存在: {req.word}")

    entry = SensitiveWord(
        word=req.word,
        category=req.category,
        severity=req.severity,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return {
        "id": str(entry.id),
        "word": entry.word,
        "category": entry.category,
        "severity": entry.severity,
    }


@router.post("/batch-import")
async def batch_import_words(req: BatchImportRequest, db: AsyncSession = Depends(get_db)):
    added = 0
    skipped = 0
    for item in req.words:
        existing = await db.execute(
            select(SensitiveWord).where(SensitiveWord.word == item.word)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue
        entry = SensitiveWord(
            word=item.word,
            category=item.category,
            severity=item.severity,
        )
        db.add(entry)
        added += 1

    await db.commit()
    return {"added": added, "skipped": skipped}


@router.delete("/{word_id}")
async def delete_sensitive_word(
    word_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a sensitive word. NOTE: SensitiveWord has no created_by FK;
    ownership is not enforced. For future multi-user, add created_by column."""
    try:
        wid = uuid.UUID(word_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    entry = await db.get(SensitiveWord, wid)
    if not entry:
        raise HTTPException(status_code=404, detail="词条不存在")

    entry.is_active = False
    await db.commit()
    return {"deleted": str(wid)}
