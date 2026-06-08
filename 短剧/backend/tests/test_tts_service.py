"""
TTS 服务单元测试。

覆盖：generate_speech（mock edge-tts）、缓存机制。
"""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.tts_service import (
    DEFAULT_VOICE,
    _cache_key,
    _get_cached,
    _save_cache,
    generate_speech,
    generate_speech_to_file,
)


class TestGenerateSpeech:
    """语音生成测试。"""

    @pytest.mark.asyncio
    async def test_generate_speech_success(self) -> None:
        """正常生成语音，返回音频字节。"""
        fake_audio = b"\xff\xfb\x90\x00" * 100  # 伪 MP3 数据

        mock_chunk_audio = {"type": "audio", "data": fake_audio}

        # edge-tts 的 stream() 返回异步迭代器
        async def mock_stream():
            yield mock_chunk_audio

        with patch("app.services.tts_service.edge_tts.Communicate") as MockComm:
            mock_instance = MockComm.return_value
            mock_instance.stream = MagicMock(return_value=mock_stream())

            with patch("app.services.tts_service._get_cached", return_value=None):
                with patch("app.services.tts_service._save_cache"):
                    result = await generate_speech("测试文本")
                    assert result == fake_audio

    @pytest.mark.asyncio
    async def test_generate_speech_empty_text(self) -> None:
        """空文本抛出 ValueError。"""
        with pytest.raises(ValueError, match="不能为空"):
            await generate_speech("")

    @pytest.mark.asyncio
    async def test_generate_speech_cache_hit(self) -> None:
        """缓存命中时直接返回，不调用 edge-tts。"""
        cached_audio = b"cached_audio_data"

        with patch("app.services.tts_service._get_cached", return_value=cached_audio):
            result = await generate_speech("缓存文本")
            assert result == cached_audio


class TestCacheMechanism:
    """缓存机制测试。"""

    def test_cache_key_deterministic(self) -> None:
        """相同文本和音色生成相同缓存 key。"""
        key1 = _cache_key("你好", DEFAULT_VOICE)
        key2 = _cache_key("你好", DEFAULT_VOICE)
        assert key1 == key2

    def test_cache_key_differs_by_text(self) -> None:
        """不同文本生成不同缓存 key。"""
        key1 = _cache_key("你好", DEFAULT_VOICE)
        key2 = _cache_key("再见", DEFAULT_VOICE)
        assert key1 != key2

    def test_cache_key_differs_by_voice(self) -> None:
        """不同音色生成不同缓存 key。"""
        key1 = _cache_key("你好", "zh-CN-XiaoxiaoNeural")
        key2 = _cache_key("你好", "zh-CN-YunxiNeural")
        assert key1 != key2

    def test_save_and_get_cache(self) -> None:
        """保存缓存后可以读取。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.services.tts_service._get_cache_dir", return_value=__import__("pathlib").Path(tmpdir)):
                audio_data = b"test_audio_bytes"
                _save_cache("测试文本", DEFAULT_VOICE, audio_data)
                cached = _get_cached("测试文本", DEFAULT_VOICE)
                assert cached == audio_data

    def test_get_cache_miss(self) -> None:
        """缓存未命中返回 None。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("app.services.tts_service._get_cache_dir", return_value=__import__("pathlib").Path(tmpdir)):
                cached = _get_cached("不存在的文本", DEFAULT_VOICE)
                assert cached is None


class TestGenerateSpeechToFile:
    """保存为文件测试。"""

    @pytest.mark.asyncio
    async def test_save_to_file(self) -> None:
        """生成语音并保存到文件。"""
        fake_audio = b"audio_data"

        with patch("app.services.tts_service.generate_speech", return_value=fake_audio):
            with tempfile.TemporaryDirectory() as tmpdir:
                output = os.path.join(tmpdir, "test.mp3")
                result = await generate_speech_to_file("测试", output)
                assert result == output
                assert os.path.isfile(output)
                with open(output, "rb") as f:
                    assert f.read() == fake_audio
