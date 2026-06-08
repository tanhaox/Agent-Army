"""宏观数据 API — /api/macro"""
from fastapi import APIRouter
from app.services.macro_data import get_macro_snapshot, generate_morning_brief, score_macro_impact

router = APIRouter(prefix="/macro", tags=["macro"])


@router.get("/snapshot")
async def macro_snapshot():
    data = await get_macro_snapshot()
    return {"status": "success", "data": data}


@router.get("/brief")
async def macro_brief():
    brief = await generate_morning_brief()
    return {"status": "success", **brief}
