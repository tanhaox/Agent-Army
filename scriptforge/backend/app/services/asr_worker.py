"""Subprocess worker for ASR transcription.

Runs in isolation so ctranslate2 segfaults don't kill the main process.
Called via: python asr_worker.py <audio_path> [--model-size SIZE] [--no-vad]
Outputs line-delimited JSON to stdout for progress streaming.
"""
import argparse
import gc
import json
import logging
import os
import sys
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    # Ensure ctranslate2 can find cuDNN 8 DLLs
    _site = Path(__file__).resolve().parent.parent.parent / ".venv-py312" / "Lib" / "site-packages"
    for _dll_dir in [
        _site / "ctranslate2",
        _site / "nvidia" / "cudnn" / "bin",
        _site / "nvidia" / "cublas" / "bin",
    ]:
        if _dll_dir.exists():
            os.add_dll_directory(str(_dll_dir))
            os.environ["PATH"] = str(_dll_dir) + os.pathsep + os.environ.get("PATH", "")

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("asr_worker")
_logger.setLevel(logging.DEBUG)
_handler = TimedRotatingFileHandler(
    _LOG_DIR / "scriptforge.log",
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8",
)
_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"))
_logger.addHandler(_handler)


# ---------------------------------------------------------------------------
# Auto-detect device – CUDA if available, else CPU
# ---------------------------------------------------------------------------
import torch as _torch
if _torch.cuda.is_available():
    _device = "cuda"
    _compute_type = "float16"
    _default_model = "large-v3"
else:
    _device = "cpu"
    _compute_type = "int8"
    _default_model = "medium"
# ---------------------------------------------------------------------------


def _emit(data: dict):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description="ASR worker subprocess")
    parser.add_argument("audio_path", help="Path to audio file")
    parser.add_argument("--model-size", default=_default_model,
                        help=f"Whisper model size (default: {_default_model})")
    parser.add_argument("--no-vad", action="store_true", help="Disable VAD filter")
    args = parser.parse_args()

    audio_path = args.audio_path
    model_size = args.model_size
    _logger.info("ASR worker started: %s (device=%s, model=%s, vad=%s)",
                 audio_path, _device, model_size, not args.no_vad)

    try:
        _emit({
            "phase": "loading_model",
            "message": f"正在加载语音识别模型...（{_device.upper()} / {model_size}）",
            "device": _device,
            "model_size": model_size,
        })

        from faster_whisper import WhisperModel
        model = WhisperModel(model_size, device=_device, compute_type=_compute_type)

        _emit({
            "phase": "model_loaded",
            "message": f"模型加载完成，开始识别（{_device.upper()} / {model_size}）...",
            "device": _device,
            "model_size": model_size,
        })

        # VAD filter — enabled by default, disabled via --no-vad or DLL failure
        vad_filter = not args.no_vad
        if vad_filter:
            try:
                from faster_whisper.vad import get_vad_model
                get_vad_model()
            except Exception:
                vad_filter = False
                _logger.warning("VAD disabled — onnxruntime DLL failed to load")

        transcribe_kwargs = dict(language="zh", beam_size=5)
        if vad_filter:
            transcribe_kwargs["vad_filter"] = True
            transcribe_kwargs["vad_parameters"] = dict(min_silence_duration_ms=500, threshold=0.5)

        segments_iter, info = model.transcribe(audio_path, **transcribe_kwargs)

        total_duration = info.duration
        segments = []
        start_time = time.monotonic()
        last_emit_time = start_time
        last_heartbeat = start_time

        for seg in segments_iter:
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            })

            now = time.monotonic()
            elapsed = now - start_time
            progress_pct = min(round((seg.end / total_duration) * 100), 99) if total_duration > 0 else 0
            char_count = sum(len(s["text"]) for s in segments)

            # Emit progress every 1.5 seconds or every 3% increment
            prev_pct = getattr(main, "_last_pct", 0)
            if now - last_emit_time >= 1.5 or (progress_pct - prev_pct) >= 3:
                # Estimate remaining time
                eta = (elapsed / progress_pct * (100 - progress_pct)) if progress_pct > 0 else 0
                _emit({
                    "phase": "transcribing",
                    "progress_pct": progress_pct,
                    "elapsed_seconds": round(elapsed, 1),
                    "eta_seconds": round(eta, 1),
                    "current_time": round(seg.end, 1),
                    "total_duration": round(total_duration, 1),
                    "segment_count": len(segments),
                    "char_count": char_count,
                    "message": f"已识别 {char_count} 字（{progress_pct}%，预计剩余 {eta:.0f}秒）",
                })
                last_emit_time = now
                main._last_pct = progress_pct  # type: ignore[attr-defined]

            # Heartbeat every 30 seconds
            if now - last_heartbeat >= 30:
                _emit({"phase": "heartbeat", "elapsed_seconds": round(elapsed, 1),
                       "progress_pct": progress_pct, "segment_count": len(segments)})
                last_heartbeat = now

        # Convert Traditional Chinese → Simplified Chinese
        from zhconv import convert as zhconv_convert
        for s in segments:
            s["text"] = zhconv_convert(s["text"], "zh-cn")
        full_text = " ".join(s["text"] for s in segments)
        total_time = time.monotonic() - start_time
        speedup = total_duration / total_time if total_time > 0 else 0
        _logger.info("[ASR_WORKER] Done: file=%s, %.1fs audio, %d segments, %d chars, %.1fs elapsed (%.1fx speedup)",
                     audio_path, info.duration, len(segments), len(full_text), total_time, speedup)

        if len(full_text) == 0:
            _logger.warning("[ASR_WORKER] Empty result! audio=%.1fs, segments=%d, file=%s",
                            info.duration, len(segments), audio_path)

        _emit({
            "phase": "done",
            "text": full_text,
            "segments": segments,
            "duration": info.duration,
            "total_seconds": round(total_time, 1),
            "char_count": len(full_text),
            "segment_count": len(segments),
            "speedup": round(speedup, 1),
            "message": f"转写完成：{len(full_text)} 字，{len(segments)} 段，耗时 {total_time:.1f} 秒（{speedup:.1f}x 加速）",
        })

    except Exception as e:
        import traceback
        _logger.error("[ASR_WORKER] Failed: %s\n%s", e, traceback.format_exc())
        _emit({"error": str(e), "traceback": traceback.format_exc()})
        sys.exit(1)
    finally:
        # Cleanup GPU memory
        del model
        gc.collect()
        if _device == "cuda":
            _torch.cuda.empty_cache()
            _torch.cuda.synchronize()


if __name__ == "__main__":
    main()
