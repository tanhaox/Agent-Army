import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import check_ownership, get_current_user
from app.models.learning_material import LearningMaterial
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/materials", tags=["Materials"])


@router.delete("/{material_id}")
async def delete_material(
    material_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        mid = uuid.UUID(material_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    result = await db.execute(select(LearningMaterial).where(LearningMaterial.id == mid))
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    check_ownership(material, current_user)
    await db.delete(material)
    await db.commit()
    logger.info("Deleted material: %s (%s)", material.title, material_id)
    return {"id": str(material.id), "title": material.title, "status": "deleted"}
