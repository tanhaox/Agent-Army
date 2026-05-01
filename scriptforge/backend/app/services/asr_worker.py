"""Subprocess worker for ASR transcription.

Runs in isolation so ctranslate2 segfaults don't kill the main process.
Called via: python asr_worker.py <audio_path>
Outputs line-delimited JSON to stdout for progress streaming.
"""
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


def _emit(data: dict):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def main():
    if len(sys.argv) < 2:
        _emit({"error": "Usage: asr_worker.py <audio_path>"})
        sys.exit(1)

    audio_path = sys.argv[1]
    _logger.info("ASR worker started: %s", audio_path)

    try:
        _emit({"phase": "loading_model", "message": "正在加载语音识别模型..."})

        from faster_whisper import WhisperModel
        model = WhisperModel("large-v3", device="cpu", compute_type="int8")

        _emit({"phase": "model_loaded", "message": "模型加载完成，开始识别..."})

        segments_iter, info = model.transcribe(audio_path, language="zh", beam_size=5)

        total_duration = info.duration
        segments = []
        start_time = time.time()
        last_emit_time = start_time

        for seg in segments_iter:
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
            })

            now = time.time()
            elapsed = now - start_time
            progress_pct = min(round((seg.end / total_duration) * 100), 99) if total_duration > 0 else 0
            char_count = sum(len(s["text"]) for s in segments)

            # Emit progress every 2 seconds or every 5% increment
            if now - last_emit_time >= 2.0 or len(segments) % 5 == 0:
                _emit({
                    "phase": "transcribing",
                    "progress_pct": progress_pct,
                    "elapsed_seconds": round(elapsed, 1),
                    "current_time": round(seg.end, 1),
                    "total_duration": round(total_duration, 1),
                    "segment_count": len(segments),
                    "char_count": char_count,
                    "message": f"已识别 {char_count} 字（{progress_pct}%）",
                })
                last_emit_time = now

        full_text = " ".join(s["text"] for s in segments)
        total_time = time.time() - start_time
        _logger.info("ASR worker done: %.1fs, %d segments, %.1fs elapsed", info.duration, len(segments), total_time)

        _emit({
            "phase": "done",
            "text": full_text,
            "segments": segments,
            "duration": info.duration,
            "total_seconds": round(total_time, 1),
            "char_count": len(full_text),
            "segment_count": len(segments),
            "message": f"转写完成：{len(full_text)} 字，{len(segments)} 段，耗时 {total_time:.1f} 秒",
        })

    except Exception as e:
        _logger.error("ASR worker failed: %s", e)
        _emit({"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    main()
