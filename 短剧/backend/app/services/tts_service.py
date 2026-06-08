"""
TTS 语音合成服务 - 使用 Edge TTS（免费，无需 API Key）。

支持多音色、文件缓存，相同文本+音色不会重复生成。
"""

import hashlib
import logging
import os
from pathlib import Path

import edge_tts

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 默认音色（中文女声）
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"

# 音色预设（角色 → 音色映射，预留扩展）
VOICE_PRESETS: dict[str, str] = {
    "女声-温柔": "zh-CN-XiaoxiaoNeural",
    "女声-成熟": "zh-CN-XiaoyiNeural",
    "男声-沉稳": "zh-CN-YunjianNeural",
    "男声-年轻": "zh-CN-YunxiNeural",
}


def _get_cache_dir() -> Path:
    """获取 TTS 缓存目录。"""
    settings = get_settings()
    cache_dir = Path("static/tts_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _cache_key(text: str, voice: str) -> str:
    """根据文本和音色生成缓存文件名。"""
    raw = f"{voice}:{text}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"tts_{h}.mp3"


def _get_cached(text: str, voice: str) -> bytes | None:
    """
    尝试从缓存获取音频。

    Returns:
        音频字节数据，未命中返回 None。
    """
    cache_dir = _get_cache_dir()
    key = _cache_key(text, voice)
    path = cache_dir / key
    if path.is_file():
        logger.debug("TTS 缓存命中: %s", key)
        return path.read_bytes()
    return None


def _save_cache(text: str, voice: str, data: bytes) -> str:
    """
    保存音频到缓存。

    Returns:
        缓存文件路径。
    """
    cache_dir = _get_cache_dir()
    key = _cache_key(text, voice)
    path = cache_dir / key
    path.write_bytes(data)
    logger.debug("TTS 缓存已保存: %s (%d bytes)", key, len(data))
    return str(path)


async def generate_speech(
    text: str,
    voice: str = DEFAULT_VOICE,
) -> bytes:
    """
    使用 Edge TTS 生成语音。

    自动缓存：相同 text + voice 组合只生成一次。

    Args:
        text: 要朗读的文本。
        voice: 音色名称（默认 zh-CN-XiaoxiaoNeural）。

    Returns:
        MP3 音频字节数据。
    """
    if not text.strip():
        raise ValueError("文本不能为空")

    # 检查缓存
    cached = _get_cached(text, voice)
    if cached is not None:
        return cached

    logger.info("TTS 生成中: voice=%s, text前30字=%s", voice, text[:30])

    communicate = edge_tts.Communicate(text, voice)
    chunks: list[bytes] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])

    if not chunks:
        raise RuntimeError(f"Edge TTS 未返回音频数据: text={text[:50]}")

    audio_data = b"".join(chunks)

    # 保存缓存
    _save_cache(text, voice, audio_data)
    logger.info("TTS 生成完成: %d bytes", len(audio_data))
    return audio_data


async def generate_speech_to_file(
    text: str,
    output_path: str,
    voice: str = DEFAULT_VOICE,
) -> str:
    """
    生成语音并保存为文件。

    Args:
        text: 朗读文本。
        output_path: 输出文件路径（MP3）。
        voice: 音色。

    Returns:
        输出文件路径。
    """
    audio_data = await generate_speech(text, voice)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(audio_data)
    logger.info("TTS 音频已保存: %s (%d bytes)", output_path, len(audio_data))
    return output_path
