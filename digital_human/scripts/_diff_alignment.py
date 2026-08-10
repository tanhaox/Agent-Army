"""alignment_service 重构逐字 diff — 旧单文件 vs 新包."""
import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import patch

ROOT = Path("app/services")


def load_old() -> types.ModuleType:
    """加载旧 alignment_service.py, __package__ 指向 app.services 使相对导入正确."""
    name = "app.services.alignment_service"
    spec = importlib.util.spec_from_file_location(name, ROOT / "alignment_service.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclass _process_class 需完整模块
    spec.loader.exec_module(mod)
    return mod


def cfg():
    return type("C", (), {"defaults": type("D", (), {
        "whisper_model_size": "large-v3", "whisper_device": "auto",
    })()})()


def flat(timings):
    """SegmentTiming dataclass → 纯 dict 列表 (跨模块 dataclass __eq__ 有 is 检查)."""
    return [
        {"segment_id": t.segment_id, "text": t.text, "start": t.start,
         "end": t.end, "duration": t.duration, "words": list(t.words)}
        for t in timings
    ]


def run(name, fn):
    try:
        ok = fn()
    except Exception as e:
        print(f"  ✗ {name}: EXC {type(e).__name__}: {e}")
        return False
    print(f"  {'✓' if ok else '✗'} {name}")
    return ok


def main():
    old = load_old()
    # 注销旧模块, 让 `from app.services import alignment_service` 解析到真包
    # (sys.modules 中的旧模块会遮蔽 app/services/alignment_service/ 包目录)
    del sys.modules["app.services.alignment_service"]
    from app.services import alignment_service as new  # 新包
    from app.services.alignment_service import _timings as n_timings
    from app.services.alignment_service import _transcribe as n_transcribe
    from app.services.alignment_service import _models as n_models

    results = []

    def compare(fn, *args, **kwargs):
        """同输入跑新旧, 比较完整返回 dict."""
        with patch("app.config.get_config", return_value=cfg()):
            ro = fn(old, *args, **kwargs)
        with patch("app.config.get_config", return_value=cfg()):
            rn = fn(new, *args, **kwargs)
        return ro == rn

    def tts_fast():
        segs = [{"id": "a", "text": "  你好 世界 ", "duration": 1.5},
                {"id": "b", "text": "第二段", "duration": 2.0},
                {"id": "c", "text": "第三", "duration": 0.0}]
        return compare(lambda m: m.align_from_tts_durations(segs))

    def tts_fast_events():
        segs = [{"id": f"s{i}", "text": f"文本{i}", "duration": 0.5} for i in range(50)]
        ev_o, ev_n = [], []
        old.align_from_tts_durations(segs, on_event=ev_o.append)
        new.align_from_tts_durations(segs, on_event=ev_n.append)
        return ev_o == ev_n

    def missing_audio():
        return compare(
            lambda m: m.align_script_segments("C:/nonexistent/x.wav", [{"id": "a", "text": "x"}]),
        )

    def error_shape():
        return compare(
            lambda m: m.align_script_segments("C:/x.wav", [{"id": "a", "text": "x"}],
                                              model_size="tiny", device="cpu"),
        )

    def match():
        segs = [{"id": "a", "text": "你好世界"},
                {"id": "b", "text": "第二段文本内容"},
                {"id": "c", "text": "三"}]
        W = old.WordSegment
        words = [W("你好世界", 0.0, 1.0, 1.0), W("第二段文本内容", 1.0, 2.0, 1.0),
                 W("三", 2.0, 3.0, 1.0)]
        ev_o, ev_n = [], []
        ro = old._match_segments(words, segs, on_event=ev_o.append)
        rn = n_timings._match_segments(words, segs, on_event=ev_n.append)
        return flat(ro) == flat(rn) and ev_o == ev_n

    def match_empty():
        segs = [{"id": "a", "text": "  x  "}, {"id": "b", "text": ""}]
        ro = old._match_segments([], segs)
        rn = n_timings._match_segments([], segs)
        return flat(ro) == flat(rn)

    def match_zero_char():
        segs = [{"id": "a", "text": ""}, {"id": "b", "text": ""}, {"id": "c", "text": "x"}]
        W = old.WordSegment
        words = [W("x", 0.0, 1.0, 1.0)]
        ro = old._match_segments(words, segs)
        rn = n_timings._match_segments(words, segs)
        return flat(ro) == flat(rn)

    def normalize():
        return old._normalize("  a   b  ") == n_transcribe._normalize("  a   b  ")

    def normalize_both():
        for s in ["", "   ", "a", " a  b ", "你好 世界"]:
            if old._normalize(s) != n_transcribe._normalize(s):
                return False
        return True

    def match_throttle():
        """每 20 段进度: 事件序列相同."""
        segs = [{"id": f"s{i}", "text": f"文本{i}", } for i in range(45)]
        W = old.WordSegment
        words = [W(f"文本{i}", float(i), float(i) + 1.0, 1.0) for i in range(45)]
        ev_o, ev_n = [], []
        old._match_segments(words, segs, on_event=ev_o.append)
        n_timings._match_segments(words, segs, on_event=ev_n.append)
        return ev_o == ev_n

    def plan_cancel():
        """PlanCancelled 原样透传 + 同一异常对象."""
        from app.services.director_events import PlanCancelled
        segs = [{"id": "a", "text": "x"}]
        W = old.WordSegment
        words = [W("x", 0.0, 1.0, 1.0)]
        for m in (old, n_timings):
            try:
                m._match_segments(words, segs, is_cancelled=lambda: True)
                return False
            except PlanCancelled:
                pass
        return True

    def align_success():
        """成功返回 dict 逐字相等 + 事件序列相等."""
        segs = [{"id": "a", "text": "你好"}, {"id": "b", "text": "世界"}]
        W = old.WordSegment
        ST = old.SegmentTiming
        words = [W("你好", 0.0, 1.0, 1.0), W("世界", 1.0, 2.5, 1.0)]
        timings = [ST("a", "你好", 0.0, 1.0, 1.0, []), ST("b", "世界", 1.0, 2.5, 1.5, [])]
        # 旧版无 _validate_audio 辅助函数, 音频不存在会短路 → 用临时文件
        audio = Path("scripts/_tmp_align_audio.wav")
        audio.touch()
        try:
            with patch.object(old, "get_config", return_value=cfg()):
                with patch.object(old, "_ensure_model", return_value=object()):
                    with patch.object(old, "_transcribe_words", return_value=words):
                        with patch.object(old, "_match_segments", return_value=timings):
                            ev_o = []
                            ro = old.align_script_segments(audio, segs, model_size="tiny", device="cpu",
                                                           on_event=ev_o.append)
            from app.services.alignment_service import _align as n_align
            with patch.object(n_align, "_validate_audio", return_value=None):
                with patch.object(n_align, "get_config", return_value=cfg()):
                    with patch.object(n_align, "_ensure_model", return_value=object()):
                        with patch.object(n_align, "_transcribe_words", return_value=words):
                            with patch.object(n_align, "_match_segments", return_value=timings):
                                ev_n = []
                                rn = new.align_script_segments(audio, segs, model_size="tiny", device="cpu",
                                                               on_event=ev_n.append)
        finally:
            audio.unlink(missing_ok=True)
        return ro == rn and ev_o == ev_n

    print("alignment_service 逐字 diff:")
    results.append(("TTS 快路径返回 dict", run("TTS 快路径返回 dict", tts_fast)))
    results.append(("TTS 快路径事件序列", run("TTS 快路径事件序列", tts_fast_events)))
    results.append(("音频缺失错误 dict", run("音频缺失错误 dict", missing_audio)))
    results.append(("whisper 失败错误 dict", run("whisper 失败错误 dict", error_shape)))
    results.append(("_match_segments 分布+事件", run("_match_segments 分布+事件", match)))
    results.append(("_match_segments 空输入", run("_match_segments 空输入", match_empty)))
    results.append(("_match_segments 零字符", run("_match_segments 零字符", match_zero_char)))
    results.append(("_normalize 一致性", run("_normalize 一致性", normalize_both)))
    results.append(("_match_segments 进度节流", run("_match_segments 进度节流", match_throttle)))
    results.append(("PlanCancelled 透传", run("PlanCancelled 透传", plan_cancel)))
    results.append(("align_script_segments 成功", run("align_script_segments 成功", align_success)))

    failed = [n for n, ok in results if not ok]
    print(f"\n通过 {len(results) - len(failed)}/{len(results)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
