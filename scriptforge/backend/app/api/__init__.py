from fastapi import APIRouter

from app.api.asr import router as asr_router
from app.api.persona import router as persona_router
from app.api.scripts import router as scripts_router
from app.api.room_tones import router as room_tones_router
from app.api.importer import router as importer_router
from app.api.materials import router as materials_router
from app.api.strategies import router as strategies_router
from app.api.creator import router as creator_router
from app.api.sensitive_words import router as sensitive_words_router
from app.api.logs import router as logs_router
from app.api.settings import router as settings_router

router = APIRouter()

router.include_router(asr_router)
router.include_router(persona_router)
router.include_router(scripts_router)
router.include_router(room_tones_router)
router.include_router(importer_router)
router.include_router(materials_router)
router.include_router(strategies_router)
router.include_router(creator_router)
router.include_router(sensitive_words_router)
router.include_router(logs_router)
router.include_router(settings_router)


@router.get("/health")
async def health_check():
    """Health check with dependency verification."""
    from app.core.health import get_health_status
    return await get_health_status()
