"""
火山引擎豆包 TTS 服务单元测试。

Mock HTTP 调用，验证 submit/query/wait/generate 逻辑。
运行: cd backend && python -m pytest tests/unit/test_volc_tts.py -v --confcutdir=tests/unit
"""

import pytest

from app.services.volc_tts_service import VolcTTSClient, VolcTTSError


class _MockResponse:
    """模拟 httpx.Response。"""

    def __init__(self, data: dict, status_code: int = 200):
        self._data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError(
                "mock error",
                request=httpx.Request("POST", "http://test"),
                response=httpx.Response(self.status_code, json=self._data),
            )

    def json(self):
        return self._data


def _make_submit_ok(task_id: str = "task-123") -> dict:
    return {"code": 20000000, "data": {"task_id": task_id}}


def _make_query_running() -> dict:
    return {"code": 20000000, "data": {"task_status": 1, "task_id": "task-123"}}


def _make_query_success(url: str = "https://cdn.example.com/audio.mp3") -> dict:
    return {
        "code": 20000000,
        "data": {"task_status": 2, "task_id": "task-123", "audio_url": url},
    }


def _make_query_failed() -> dict:
    return {"code": 20000000, "data": {"task_status": 3, "task_id": "task-123"}}


# ── submit_task ───────────────────────────────────────────────


class TestSubmitTask:
    async def test_submit_success(self, monkeypatch):
        client = VolcTTSClient(
            app_id="test-app", access_key="test-key", default_voice="zh_female_vv_uranus"
        )

        async def mock_post(url, json, headers):
            assert "submit" in url
            assert headers["X-Api-App-Id"] == "test-app"
            assert headers["X-Api-Access-Key"] == "test-key"
            assert json["req_params"]["text"] == "你好"
            return _MockResponse(_make_submit_ok("t-001"))

        import httpx

        class MockClient:
            def __init__(self, timeout=None):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                return await mock_post(url, json, headers)

        monkeypatch.setattr(httpx, "AsyncClient", MockClient)

        task_id = await client.submit_task("你好")
        assert task_id == "t-001"

    async def test_submit_no_credentials(self):
        client = VolcTTSClient(app_id="", access_key="")
        with pytest.raises(VolcTTSError, match="未配置"):
            await client.submit_task("test")

    async def test_submit_api_error(self, monkeypatch):
        client = VolcTTSClient(app_id="a", access_key="k")

        import httpx

        class MockClient:
            def __init__(self, timeout=None):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                return _MockResponse({"code": 40000000, "message": "bad"})

        monkeypatch.setattr(httpx, "AsyncClient", MockClient)

        with pytest.raises(VolcTTSError, match="submit 失败"):
            await client.submit_task("test")

    async def test_submit_with_voice_and_speed(self, monkeypatch):
        client = VolcTTSClient(app_id="a", access_key="k")
        captured = {}

        import httpx

        class MockClient:
            def __init__(self, timeout=None):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                captured["payload"] = json
                return _MockResponse(_make_submit_ok())

        monkeypatch.setattr(httpx, "AsyncClient", MockClient)

        await client.submit_task("test", voice_type="zh_male_V_bignews", speed=1.5, volume=0.8)
        params = captured["payload"]["req_params"]
        assert params["speaker"] == "zh_male_V_bignews"
        assert params["audio_params"]["speech_rate"] == 50
        assert params["audio_params"]["loudness_rate"] == -20


# ── query_task ────────────────────────────────────────────────


class TestQueryTask:
    async def test_query_running(self, monkeypatch):
        client = VolcTTSClient(app_id="a", access_key="k")

        import httpx

        class MockClient:
            def __init__(self, timeout=None):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                return _MockResponse(_make_query_running())

        monkeypatch.setattr(httpx, "AsyncClient", MockClient)

        result = await client.query_task("task-123")
        assert result["status"] == "running"
        assert result["audio_url"] is None

    async def test_query_success(self, monkeypatch):
        client = VolcTTSClient(app_id="a", access_key="k")

        import httpx

        class MockClient:
            def __init__(self, timeout=None):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                return _MockResponse(_make_query_success())

        monkeypatch.setattr(httpx, "AsyncClient", MockClient)

        result = await client.query_task("task-123")
        assert result["status"] == "success"
        assert result["audio_url"] == "https://cdn.example.com/audio.mp3"

    async def test_query_failed(self, monkeypatch):
        client = VolcTTSClient(app_id="a", access_key="k")

        import httpx

        class MockClient:
            def __init__(self, timeout=None):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                return _MockResponse(_make_query_failed())

        monkeypatch.setattr(httpx, "AsyncClient", MockClient)

        result = await client.query_task("task-123")
        assert result["status"] == "failed"


# ── wait_for_completion ───────────────────────────────────────


class TestWaitForCompletion:
    async def test_immediate_success(self, monkeypatch):
        client = VolcTTSClient(app_id="a", access_key="k")
        client._poll_interval = 0.01

        import httpx

        class MockClient:
            def __init__(self, timeout=None):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                return _MockResponse(_make_query_success())

        monkeypatch.setattr(httpx, "AsyncClient", MockClient)

        result = await client.wait_for_completion("task-123", timeout=5)
        assert result["audio_url"] == "https://cdn.example.com/audio.mp3"

    async def test_poll_then_success(self, monkeypatch):
        client = VolcTTSClient(app_id="a", access_key="k")
        client._poll_interval = 0.01
        call_count = 0

        import httpx

        class MockClient:
            def __init__(self, timeout=None):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    return _MockResponse(_make_query_running())
                return _MockResponse(_make_query_success())

        monkeypatch.setattr(httpx, "AsyncClient", MockClient)

        result = await client.wait_for_completion("task-123", timeout=5)
        assert result["status"] == "success"
        assert call_count == 3

    async def test_task_failed_raises(self, monkeypatch):
        client = VolcTTSClient(app_id="a", access_key="k")
        client._poll_interval = 0.01

        import httpx

        class MockClient:
            def __init__(self, timeout=None):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                return _MockResponse(_make_query_failed())

        monkeypatch.setattr(httpx, "AsyncClient", MockClient)

        with pytest.raises(VolcTTSError, match="合成失败"):
            await client.wait_for_completion("task-123", timeout=5)


# ── generate_speech ───────────────────────────────────────────


class TestGenerateSpeech:
    async def test_generate_success(self, monkeypatch):
        client = VolcTTSClient(app_id="a", access_key="k")
        client._poll_interval = 0.01
        call_count = 0

        import httpx

        class MockClient:
            def __init__(self, timeout=None):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def post(self, url, json=None, headers=None):
                nonlocal call_count
                call_count += 1
                if "submit" in url:
                    return _MockResponse(_make_submit_ok())
                return _MockResponse(_make_query_success("https://cdn.test/s.mp3"))

        monkeypatch.setattr(httpx, "AsyncClient", MockClient)

        url = await client.generate_speech("测试语音")
        assert url == "https://cdn.test/s.mp3"
        assert call_count == 2  # submit + query


# ── check_health ──────────────────────────────────────────────


class TestCheckHealth:
    async def test_health_ok(self):
        client = VolcTTSClient(app_id="app-12345678", access_key="key", default_voice="test")
        result = await client.check_health()
        assert result["status"] == "ok"
        assert "app-12" in result["app_id"]

    async def test_health_no_config(self):
        client = VolcTTSClient(app_id="", access_key="")
        result = await client.check_health()
        assert result["status"] == "error"
        assert "未配置" in result["error"]


# ── prompt_vocab TTS_VOICES ───────────────────────────────────


class TestTTSVocab:
    def test_list_voices(self):
        from app.services.prompt_vocab import list_tts_voices

        voices = list_tts_voices()
        assert len(voices) >= 4
        assert all("id" in v and "label" in v for v in voices)

    def test_voice_entries(self):
        from app.services.prompt_vocab import TTS_VOICES

        assert "zh_female_vv_uranus" in TTS_VOICES
        assert TTS_VOICES["zh_female_vv_uranus"]["gender"] == "female"
        assert "zh_male_V_bignews" in TTS_VOICES
