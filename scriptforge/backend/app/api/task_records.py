"""Task Records API — persistent history of import/analysis tasks."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.task_record import TaskRecord

router = APIRouter(prefix="/task-records", tags=["Task Records"])


# ── Schemas ──

class TaskRecordItem(BaseModel):
    id: str
    task_id: str
    trigger: str
    url: str
    anchor_name: str
    anchor_avatar: str | None = None
    follower_count: int
    status: str
    error_message: str | None = None
    video_count: int
    downloaded_count: int
    transcribed_count: int
    persona_id: str | None = None
    persona_name: str | None = None
    result_summary: dict | None = None
    created_at: str

    class Config:
        from_attributes = True


class TaskRecordDetail(TaskRecordItem):
    result_summary: dict | None = None


class TaskRecordListResponse(BaseModel):
    items: list[TaskRecordItem]
    total: int
    page: int
    page_size: int


# ── Endpoints ──

@router.get("", response_model=TaskRecordListResponse)
async def list_task_records(
    status: str = Query(default="", description="Filter: running / completed / failed"),
    anchor_name: str = Query(default="", description="Filter by anchor name (partial match)"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List task records with optional filters, newest first."""
    q = select(TaskRecord)
    count_q = select(func.count(TaskRecord.id))

    if status:
        q = q.where(TaskRecord.status == status)
        count_q = count_q.where(TaskRecord.status == status)
    if anchor_name:
        q = q.where(TaskRecord.anchor_name.ilike(f"%{anchor_name}%"))
        count_q = count_q.where(TaskRecord.anchor_name.ilike(f"%{anchor_name}%"))

    total = (await db.execute(count_q)).scalar() or 0

    rows = (
        (await db.execute(
            q.order_by(TaskRecord.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ))
        .scalars()
        .all()
    )

    items = [
        TaskRecordItem(
            id=str(r.id),
            task_id=r.task_id,
            trigger=r.trigger,
            url=r.url,
            anchor_name=r.anchor_name,
            anchor_avatar=r.anchor_avatar,
            follower_count=r.follower_count,
            status=r.status,
            error_message=r.error_message,
            video_count=r.video_count,
            downloaded_count=r.downloaded_count,
            transcribed_count=r.transcribed_count,
            persona_id=r.persona_id,
            persona_name=r.persona_name,
            result_summary=r.result_summary,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in rows
    ]

    return TaskRecordListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{task_id}", response_model=TaskRecordDetail)
async def get_task_record(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single task record with full result summary."""
    row = (
        await db.execute(select(TaskRecord).where(TaskRecord.task_id == task_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="任务记录不存在")

    return TaskRecordDetail(
        id=str(row.id),
        task_id=row.task_id,
        trigger=row.trigger,
        url=row.url,
        anchor_name=row.anchor_name,
        anchor_avatar=row.anchor_avatar,
        follower_count=row.follower_count,
        status=row.status,
        error_message=row.error_message,
        video_count=row.video_count,
        downloaded_count=row.downloaded_count,
        transcribed_count=row.transcribed_count,
        persona_id=row.persona_id,
        persona_name=row.persona_name,
        created_at=row.created_at.isoformat() if row.created_at else "",
        result_summary=row.result_summary,
    )
