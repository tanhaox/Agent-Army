"""
TTS 语音合成 API 端点 — 火山引擎豆包 TTS。

提供提交、查询、同步生成三种接口。
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.rate_limit import limiter

from app.services.prompt_vocab import list_tts_voices
from app.services.volc_tts_service import VolcTTSClient, VolcTTSError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["语音合成"])

_client = VolcTTSClient()


# ── Request/Response Schemas ──────────────────────────────────


class TTSSubmitRequest(BaseModel):
    """提交 TTS 异步任务。"""

    text: str = Field(..., min_length=1, max_length=100000, description="合成文本")
    voice_type: str | None = Field(default=None, description="音色 ID，不传则用默认")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="语速倍率")
    volume: float = Field(default=1.0, ge=0.5, le=2.0, description="音量倍率")
    emotion: str | None = Field(default=None, description="情感（部分音色支持）")


class TTSGenerateRequest(TTSSubmitRequest):
    """同步生成语音（提交+等待）。"""

    timeout: int | None = Field(default=None, ge=10, le=300, description="超时秒数")


class TTSTaskResponse(BaseModel):
    """TTS 任务状态。"""

    task_id: str
    status: str
    audio_url: str | None = None


class TTSVoiceItem(BaseModel):
    """音色信息。"""

    id: str
    label: str
    gender: str


# ── Endpoints ─────────────────────────────────────────────────


@router.get("/voices", response_model=list[TTSVoiceItem], summary="获取可用音色列表")
async def get_voices() -> list[TTSVoiceItem]:
    """返回内置音色列表。"""
    return [TTSVoiceItem(**v) for v in list_tts_voices()]


@router.post("/submit", response_model=TTSTaskResponse, summary="提交 TTS 异步任务")
@limiter.limit("20/minute")
async def submit_tts(request: Request, req: TTSSubmitRequest) -> TTSTaskResponse:
    """提交异步 TTS 合成任务，返回 task_id。"""
    try:
        task_id = await _client.submit_task(
            text=req.text,
            voice_type=req.voice_type,
            speed=req.speed,
            volume=req.volume,
            emotion=req.emotion,
        )
        return TTSTaskResponse(task_id=task_id, status="submitted")
    except VolcTTSError as e:
        logger.warning("TTS submit 失败: %s", e)
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.get("/query/{task_id}", response_model=TTSTaskResponse, summary="查询 TTS 任务状态")
async def query_tts(task_id: str) -> TTSTaskResponse:
    """查询已提交 TTS 任务的状态。"""
    try:
        result = await _client.query_task(task_id)
        return TTSTaskResponse(**result)
    except VolcTTSError as e:
        logger.warning("TTS query 失败: %s", e)
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.post("/generate", response_model=TTSTaskResponse, summary="同步生成语音")
@limiter.limit("20/minute")
async def generate_tts(request: Request, req: TTSGenerateRequest) -> TTSTaskResponse:
    """提交 TTS 任务并等待完成，返回 audio_url。"""
    try:
        audio_url = await _client.generate_speech(
            text=req.text,
            voice_type=req.voice_type,
            speed=req.speed,
            volume=req.volume,
        )
        return TTSTaskResponse(task_id="sync", status="success", audio_url=audio_url)
    except VolcTTSError as e:
        logger.warning("TTS generate 失败: %s", e)
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.get("/health", summary="TTS 配置健康检查")
async def tts_health() -> dict[str, Any]:
    """检查 TTS 配置是否完整。"""
    return await _client.check_health()
