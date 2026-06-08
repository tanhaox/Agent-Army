"""
FFmpeg 服务单元测试。

覆盖：concat_videos、embed_subtitle、convert_format、merge_audio_video。
全部 mock subprocess 调用，不依赖真实 FFmpeg。
"""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ffmpeg_service import (
    FFmpegError,
    check_ffmpeg_available,
    concat_videos,
    convert_format,
    embed_subtitle,
    merge_audio_video,
)


def _create_fake_file(path: str, content: bytes = b"fake") -> str:
    """创建假文件并返回路径。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
    return path


class TestConcatVideos:
    """视频拼接测试。"""

    @pytest.mark.asyncio
    async def test_concat_videos_success(self) -> None:
        """正常拼接两个视频。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            v1 = _create_fake_file(os.path.join(tmpdir, "v1.mp4"))
            v2 = _create_fake_file(os.path.join(tmpdir, "v2.mp4"))
            output = os.path.join(tmpdir, "output.mp4")

            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))

            with patch("app.services.ffmpeg_service.asyncio.create_subprocess_exec", return_value=mock_proc):
                result = await concat_videos([v1, v2], output)
                assert result == output

    @pytest.mark.asyncio
    async def test_concat_videos_empty_list(self) -> None:
        """空列表抛出 FFmpegError。"""
        with pytest.raises(FFmpegError, match="不能为空"):
            await concat_videos([], "/tmp/out.mp4")

    @pytest.mark.asyncio
    async def test_concat_videos_missing_file(self) -> None:
        """输入文件不存在时抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            await concat_videos(["/nonexistent/v1.mp4"], "/tmp/out.mp4")

    @pytest.mark.asyncio
    async def test_concat_videos_ffmpeg_error(self) -> None:
        """FFmpeg 返回非零退出码时抛出 FFmpegError。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            v1 = _create_fake_file(os.path.join(tmpdir, "v1.mp4"))
            output = os.path.join(tmpdir, "output.mp4")

            mock_proc = MagicMock()
            mock_proc.returncode = 1
            mock_proc.communicate = AsyncMock(return_value=(b"", b"Error details"))

            with patch("app.services.ffmpeg_service.asyncio.create_subprocess_exec", return_value=mock_proc):
                with pytest.raises(FFmpegError, match="退出码 1"):
                    await concat_videos([v1], output)


class TestEmbedSubtitle:
    """字幕嵌入测试。"""

    @pytest.mark.asyncio
    async def test_embed_subtitle_success(self) -> None:
        """正常嵌入字幕。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            video = _create_fake_file(os.path.join(tmpdir, "video.mp4"))
            srt = _create_fake_file(os.path.join(tmpdir, "sub.srt"), b"1\n00:00:00,000 --> 00:00:03,000\nTest")
            output = os.path.join(tmpdir, "output.mp4")

            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))

            with patch("app.services.ffmpeg_service.asyncio.create_subprocess_exec", return_value=mock_proc):
                result = await embed_subtitle(video, srt, output)
                assert result == output

    @pytest.mark.asyncio
    async def test_embed_subtitle_missing_video(self) -> None:
        """视频不存在时抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError, match="视频"):
            await embed_subtitle("/nonexistent.mp4", "/tmp/sub.srt", "/tmp/out.mp4")


class TestConvertFormat:
    """格式转换测试。"""

    @pytest.mark.asyncio
    async def test_convert_format_success(self) -> None:
        """正常转码。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            video = _create_fake_file(os.path.join(tmpdir, "input.mp4"))
            output = os.path.join(tmpdir, "output.mp4")

            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))

            with patch("app.services.ffmpeg_service.asyncio.create_subprocess_exec", return_value=mock_proc):
                result = await convert_format(video, output, (1080, 1920), "2M")
                assert result == output


class TestMergeAudioVideo:
    """音视频合并测试。"""

    @pytest.mark.asyncio
    async def test_merge_success(self) -> None:
        """正常合并。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            video = _create_fake_file(os.path.join(tmpdir, "video.mp4"))
            audio = _create_fake_file(os.path.join(tmpdir, "audio.mp3"))
            output = os.path.join(tmpdir, "output.mp4")

            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = AsyncMock(return_value=(b"", b""))

            with patch("app.services.ffmpeg_service.asyncio.create_subprocess_exec", return_value=mock_proc):
                result = await merge_audio_video(video, audio, output)
                assert result == output

    @pytest.mark.asyncio
    async def test_merge_missing_audio(self) -> None:
        """音频不存在时抛出 FileNotFoundError。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            video = _create_fake_file(os.path.join(tmpdir, "video.mp4"))
            with pytest.raises(FileNotFoundError, match="音频"):
                await merge_audio_video(video, "/nonexistent.mp3", "/tmp/out.mp4")


class TestCheckFFmpeg:
    """健康检查测试。"""

    def test_ffmpeg_available(self) -> None:
        """FFmpeg 在 PATH 中时返回 ok。"""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            result = check_ffmpeg_available()
            assert result["status"] == "ok"

    def test_ffmpeg_not_available(self) -> None:
        """FFmpeg 不在 PATH 中时返回 error。"""
        with patch("shutil.which", return_value=None):
            result = check_ffmpeg_available()
            assert result["status"] == "error"
