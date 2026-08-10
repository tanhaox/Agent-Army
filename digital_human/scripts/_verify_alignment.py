"""alignment_service 重构行为契约验证."""
import sys
from unittest.mock import patch

from app.services import alignment_service as m

results = []


def check(name, fn):
    try:
        out = fn()
        ok = bool(out) if not isinstance(out, bool) else out
    except Exception as e:
        ok = False
        results.append((name, f"EXC {type(e).__name__}: {e}"))
        return
    results.append((name, "PASS" if ok else "FAIL"))


def _cfg():
    """fake app.config 默认值对象 (whisper 覆盖默认)."""
    cfg = type("D", (), {"whisper_model_size": "large-v3", "whisper_device": "auto"})()
    return type("C", (), {"defaults": cfg})()


def api_present():
    return all(hasattr(m, n) for n in [
        "align_script_segments", "align_from_tts_durations",
        "WordSegment", "SegmentTiming",
    ])


def tts_fast_path():
    """TTS 时长快路径: 拼接时间轴 + model='tts-durations'."""
    segs = [{"id": "a", "text": "  你好 世界 ", "duration": 1.5},
            {"id": "b", "text": "第二段", "duration": 2.0}]
    r = m.align_from_tts_durations(segs)
    return (
        r["ok"] is True and r["error"] is None
        and r["model"] == "tts-durations" and r["device"] == "n/a"
        and r["total_duration_sec"] == 3.5
        and r["word_segments"] == []
        and [t["segment_id"] for t in r["segment_timings"]] == ["a", "b"]
        and r["segment_timings"][0]["text"] == "你好 世界"
        and r["segment_timings"][0]["start"] == 0.0
        and r["segment_timings"][0]["end"] == 1.5
        and r["segment_timings"][1]["start"] == 1.5
        and r["segment_timings"][1]["end"] == 3.5
    )


def tts_fast_path_cancel():
    """快路径: is_cancelled 立即抛 PlanCancelled."""
    from app.services.director_events import PlanCancelled
    try:
        m.align_from_tts_durations([{"id": "a", "text": "x", "duration": 1}],
                                   is_cancelled=lambda: True)
    except PlanCancelled:
        return True
    return False


def tts_fast_path_progress():
    """快路径: on_event 收到开头/末尾事件."""
    evts = []
    m.align_from_tts_durations(
        [{"id": "a", "text": "你好", "duration": 1}],
        on_event=evts.append,
    )
    kinds = [e["type"] for e in evts]
    return "alignment_progress" in kinds and any("使用 TTS 段落时长" in e.get("msg", "") for e in evts)


def align_missing_audio():
    """音频不存在 → 错误 dict (ok=False)."""
    r = m.align_script_segments("/nonexistent/audio.wav", [{"id": "a", "text": "x"}])
    return r["ok"] is False and "audio not found" in r["error"] and r["segment_timings"] == []


def align_error_escape():
    """whisper 异常 → {ok:False, error: f'{type}: {exc}'}, PlanCancelled 透传."""
    from app.services.alignment_service import _align
    import app.services.alignment_service._models as mod
    # 缺更快路径 + 校验通过, 触发 _ensure_model 抛 ImportError (faster_whisper 缺)
    with patch.object(_align, "_validate_audio", return_value=None), \
         patch.object(_align, "get_config") as ac, \
         patch.object(mod, "WhisperModel", None), \
         patch.object(mod, "get_config") as gc:
        cfg = type("D", (), {"whisper_model_size": "large-v3", "whisper_device": "auto"})()
        fake = type("C", (), {"defaults": cfg})()
        ac.return_value = fake
        gc.return_value = fake
        mod._MODEL_CACHE.clear()
        r = m.align_script_segments("C:/temp/x.wav", [{"id": "a", "text": "x"}])
    return r["ok"] is False and r["error"].startswith("ImportError:") and r["total_duration_sec"] is None


def align_error_transcribe_exc():
    """转录抛任意异常 → error=f'{type}: {exc}' 含在返回 dict."""
    from app.services.alignment_service import _align
    segs = [{"id": "a", "text": "x"}]
    with patch.object(_align, "_validate_audio", return_value=None), \
         patch.object(_align, "get_config", return_value=_cfg()), \
         patch.object(_align, "_ensure_model") as em, \
         patch.object(_align, "_transcribe_words", side_effect=RuntimeError("boom")) as tw:
        em.return_value = object()
        r = m.align_script_segments("C:/temp/x.wav", segs,
                                    model_size="tiny", device="cpu")
    assert tw.called
    return r["ok"] is False and r["error"] == "RuntimeError: boom"


def align_plan_cancelled_escape():
    """转录抛 PlanCancelled → 原样上抛, 不吞."""
    from app.services.alignment_service import _align
    from app.services.director_events import PlanCancelled
    with patch.object(_align, "_validate_audio", return_value=None), \
         patch.object(_align, "get_config", return_value=_cfg()), \
         patch.object(_align, "_ensure_model") as em, \
         patch.object(_align, "_transcribe_words", side_effect=PlanCancelled) as tw:
        em.return_value = object()
        try:
            m.align_script_segments("C:/temp/x.wav", [{"id": "a", "text": "x"}],
                                    model_size="tiny", device="cpu")
        except PlanCancelled:
            assert tw.called
            return True
    return False


def align_success_shape():
    """成功路径: 形状/键序一致."""
    from app.services.alignment_service import _align
    from app.services.alignment_service._timings import SegmentTiming
    from app.services.alignment_service._transcribe import WordSegment
    segs = [{"id": "a", "text": "你好"}]
    with patch.object(_align, "_validate_audio", return_value=None), \
         patch.object(_align, "get_config", return_value=_cfg()), \
         patch.object(_align, "_ensure_model") as em, \
         patch.object(_align, "_transcribe_words") as tw, \
         patch.object(_align, "_match_segments") as ms:
        em.return_value = object()
        tw.return_value = [WordSegment("你好", 0.0, 1.0, 1.0)]
        ms.return_value = [SegmentTiming("a", "你好", 0.0, 1.0, 1.0, [])]
        r = m.align_script_segments("C:/temp/x.wav", segs,
                                    model_size="tiny", device="cpu")
    return (
        list(r.keys()) == ["ok", "error", "word_segments", "segment_timings",
                           "total_duration_sec", "model", "device"]
        and r["ok"] is True and r["model"] == "tiny" and r["device"] == "cpu"
        and r["total_duration_sec"] == 1.0
        and list(r["segment_timings"][0].keys()) == ["segment_id", "text", "start", "end", "duration"]
        and list(r["word_segments"][0].keys()) == ["text", "start", "end", "probability"]
    )


def model_heartbeat_events():
    """_ensure_model 加载时发送 model_load_start/done 事件."""
    import app.services.alignment_service._models as mod
    class FakeModel:
        def __init__(self, *a, **k):
            pass

    evts = []
    with patch.object(mod, "WhisperModel", FakeModel), \
         patch.object(mod, "get_config") as gc:
        cfg = type("D", (), {"whisper_model_size": "large-v3", "whisper_device": "auto"})()
        gc.return_value = type("C", (), {"defaults": cfg})()
        mod._MODEL_CACHE.clear()
        m._models._ensure_model(on_event=evts.append)
    kinds = [e["type"] for e in evts]
    return "model_load_start" in kinds and "model_load_done" in kinds


def transcribe_progress_throttle():
    """转录每 10 段回传进度; PlanCancelled 在段迭代时抛出."""
    from app.services.alignment_service import _transcribe
    from app.services.alignment_service._models import _MODEL_CACHE
    seg = type("S", (), {"text": "x", "start": 0.0, "end": 1.0})
    fake_model = type("M", (), {"transcribe": lambda self, *a, **k: (iter([seg] * 25), None)})
    with patch.object(_transcribe, "_ensure_model", return_value=fake_model()):
        evts = []
        words = _transcribe._transcribe_words("C:/x.wav", on_event=evts.append)
    progress = [e for e in evts if e["type"] == "alignment_progress"]
    return len(words) == 25 and any("转录中" in e["msg"] for e in progress)


check("公共 API + dataclass", api_present)
check("TTS 快路径时间轴", tts_fast_path)
check("TTS 快路径取消透传", tts_fast_path_cancel)
check("TTS 快路径进度事件", tts_fast_path_progress)
check("音频缺失错误 dict", align_missing_audio)
check("whisper ImportError 逃逸", align_error_escape)
check("转录异常 → error dict", align_error_transcribe_exc)
check("PlanCancelled 原样上抛", align_plan_cancelled_escape)
check("成功路径形状/键序", align_success_shape)
check("模型加载事件", model_heartbeat_events)
check("转录进度节流", transcribe_progress_throttle)

failed = 0
for name, status in results:
    print(f"  {'✓' if status == 'PASS' else '✗'} {name}: {status}")
    if status != "PASS":
        failed += 1
print(f"\n通过 {len(results) - failed}/{len(results)}")
sys.exit(1 if failed else 0)
