"""TTS service wrapping tts_client for pipeline use."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

import soundfile as sf

# Ensure digital_human/ is on sys.path so that "from scripts import tts_client" works
# even when uvicorn loads app.main with digital_human/ as the working directory.
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts import tts_client
from ..config import DefaultsConfig
from ..models import AudioFile, AudioJob, Segment, Voice


class TTSService:
    def __init__(self, defaults: DefaultsConfig):
        self.defaults = defaults

    def generate(
        self,
        job: AudioJob,
        segments: list[Segment],
        voice: Voice | None,
        progress_callback: Callable[[int, int, str | None, AudioFile], None] | None = None,
        emotion_annotations: list[dict[str, Any]] | None = None,
        status_callback: Callable[[str, str], None] | None = None,
    ) -> dict[str, Any]:
        """Generate per-line WAV files and manifest.

        Args:
            job: AudioJob ORM instance (status updated in-place but caller commits).
            segments: List of Segment instances to synthesize.
            voice: Voice configuration.
            progress_callback: Called with (completed, total, current_text, audio_file) after each line.
            status_callback: (消息, 级别) 状态事件 (ASR 回听校验等非逐段进度)。
        """
        output_dir = Path(job.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        backend = voice.backend if voice and voice.backend else self.defaults.backend
        voice_id = voice.name if voice else self.defaults.voice_id
        ref_audio = Path(voice.reference_audio_path) if voice and voice.reference_audio_path else None
        ref_text = voice.reference_text or "" if voice else ""
        master_audio = (
            Path(voice.master_audio_path)
            if voice and voice.master_audio_path
            else (Path(voice.reference_audio_path) if voice and voice.reference_audio_path else None)
        )
        master_text = (
            voice.master_text
            or (voice.reference_text or "")
            if voice
            else ""
        )
        base_url_fish = voice.base_url_fish or self.defaults.base_url_fish if voice else self.defaults.base_url_fish
        base_url_f5 = voice.base_url_f5 or self.defaults.base_url_f5 if voice else self.defaults.base_url_f5
        base_url_indextts = (
            voice.base_url_indextts or self.defaults.base_url_indextts
            if voice
            else self.defaults.base_url_indextts
        )

        # Read saved voice params from config_json
        voice_params: dict[str, Any] | None = None
        if voice and voice.config_json and isinstance(voice.config_json, dict):
            saved = voice.config_json.get("params")
            if saved and isinstance(saved, dict):
                voice_params = saved

        # IndexTTS2.5 语速默认注入 (2026-08-25): 2.5 基线比 2 慢 ~26%, 配置层校准;
        # 音色显式配置 duration_factor 优先 (setdefault 不覆盖)。
        if voice_params is None:
            voice_params = {}
        voice_params.setdefault(
            "duration_factor", getattr(self.defaults, "indextts_duration_factor", 0.75)
        )

        # ── 段数据快照 (2026-08-25) ──
        # TTS 是长任务 (GPU 冷启动 + 逐段合成数分钟)。期间文稿保存会 _reparse_segments
        # 删旧建新行, 而 progress 回调的 db.commit() 令 ORM 对象 expire, 下次访问属性时
        # refresh 不到行 → ObjectDeletedError ("Segment has been deleted", job 卡 failed).
        # 因此: 调用方应在最后一次 db.commit() 前提取好 (id, text) 纯元组传入; 兼容直接
        # 传 ORM Segment 的老路径 (ppt 线自建自用无并发风险) — 入口一次性提取, 之后不再触碰 ORM.
        if segments and isinstance(segments[0], tuple):
            seg_pairs: list[tuple[str, str]] = [(str(sid), txt) for sid, txt in segments]
        else:
            seg_pairs = [(s.id, s.text) for s in segments]

        # Build text preserving line breaks and control chars.
        # 拼音纠音 (2026-08-25): 易错词 → <字|PINYIN> 标注, IndexTTS2/2.5 前端解析;
        # 只改 TTS 输入, 文稿/字幕不受影响。替代旧的"错别字音频替换"事后补丁。
        from .pinyin_fix import apply_pinyin_marks
        text = apply_pinyin_marks("\n".join(t for _, t in seg_pairs))

        # Collect the AudioFile rows created as synthesis progresses. Each
        # completed segment yields exactly one row (via _manifest_callback),
        # committed through progress_callback so DB and disk stay in sync even
        # if the job later fails.
        audio_files: list[AudioFile] = []

        def _manifest_callback(completed: int, total: int, text: str, manifest_seg: dict[str, Any] | None) -> None:
            if not progress_callback or not manifest_seg:
                return
            seg_id = seg_pairs[completed - 1][0]
            file_path = output_dir / manifest_seg["file"]
            audio_file = AudioFile(
                audio_job_id=job.id,
                segment_id=seg_id,
                filename=manifest_seg["file"],
                file_path=str(file_path),
                duration=manifest_seg.get("duration"),
                sample_rate=manifest_seg.get("sample_rate"),
            )
            audio_files.append(audio_file)
            progress_callback(completed, total, text, audio_file)

        # P5 情绪标注 (2026-08-13): 段落情绪 → 已解析段参数 (text/vector/alpha),
        # 传给 synthesize_lines 按段合成. 缺省 → 现状 (整篇 calm).
        emotion_segments: list[dict[str, Any]] | None = None
        # 2026-08-14: P5 产的 emotion_annotations 是 "[情绪/强度] 文本\n..." 字符串 (DB 存储),
        # TTS 需 list[dict]. 入口解析兼容 (str → list[dict]); 解析失败回退 None (整篇 calm).
        if emotion_annotations and isinstance(emotion_annotations, str):
            from .boost_service import _parse_emotion_annotations
            emotion_annotations = _parse_emotion_annotations(emotion_annotations)
        if emotion_annotations:
            from .emotion_dict import resolve_emotion

            emotion_segments = []
            for ann in emotion_annotations:
                try:
                    r = resolve_emotion(ann.get("emotion", "calm"), ann.get("strength", "中"))
                except KeyError:
                    continue
                emotion_segments.append({
                    "text": ann.get("text", ""),
                    "vector": r["vector"],
                    "alpha": r["alpha"],
                })

        manifest = tts_client.synthesize_lines(
            text=text,
            output_dir=output_dir,
            backend=backend,
            voice_id=voice_id,
            reference_audio=master_audio,
            reference_text=master_text,
            base_url_fish=base_url_fish,
            base_url_f5=base_url_f5,
            base_url_indextts=base_url_indextts,
            master_audio=master_audio,
            master_text=master_text,
            progress_callback=_manifest_callback,
            params=voice_params,
            # 批合成 (2026-08-25 回退 150): IndexTTS2 RTF~1.8, 句级批(一句一调)总时长远超
            # 批合成, 恢复 3-5 句一批。句级批是为 2.5 (RTF 0.54 + 服务端逗号切分/拼接
            # 静音问题)设计的实验配置 — 回 2.5 时改回 batch_max_chars=1。
            batch_max_chars=150,
            emotion_segments=emotion_segments,
        )

        # ── ASR 回听校验 (2026-09-03): 拼接前逐行回听, 错音自动 <字|PINYIN> 重合成 ──
        # 多音字偶发错读此前只能人工听成片发现; 现在合成后秒级发现+修复。
        # 手术式单行重合成 (_synthesize_single) 不动邻行; 失败回滚原音频宁可不修。
        # 任何异常静默降级 (whisper 缺失/显存不足) — 校验是增值不是依赖。
        verify_report = None
        if getattr(self.defaults, "tts_verify_asr", True) and manifest.get("segments"):
            try:
                from .tts_verify import verify_pronunciation

                def _resynth_line(idx: int, clean_line: str, marked_line: str) -> None:
                    from scripts.tts_lib.orchestrator import _synthesize_single
                    from scripts.tts_lib.text import _tts_text
                    import re as _re

                    wav = output_dir / f"{idx:03d}.wav"
                    # 情绪段按干净行文本匹配 (标注行与段文本对不上, 会落 calm)
                    _n = lambda s: _re.sub(r"\s+", "", s or "")
                    emo = next((s for s in (emotion_segments or [])
                                if clean_line and _n(clean_line) in _n(s.get("text", ""))), None)
                    tmp = output_dir / f"_verify_{idx:03d}.wav"
                    _synthesize_single(
                        text=_tts_text(marked_line, keep_breaks=(backend == "indextts")),
                        output_path=tmp, backend=backend, voice_id=voice_id,
                        reference_audio=ref_audio, reference_text=ref_text,
                        base_url_fish=base_url_fish, base_url_f5=base_url_f5,
                        base_url_indextts=base_url_indextts,
                        master_audio=master_audio, master_text=master_text,
                        params=voice_params,
                        emo_vector=emo.get("vector") if emo else None,
                        emo_alpha=(emo.get("alpha", 1.0) if emo else 1.0),
                    )
                    # 与产线一致: loudnorm 归一后原位覆盖
                    try:
                        from app.infrastructure.ffmpeg import normalize_audio
                        normalize_audio(tmp, wav)
                        tmp.unlink(missing_ok=True)
                    except Exception:
                        tmp.replace(wav)

                verify_report = verify_pronunciation(
                    output_dir=output_dir, manifest=manifest,
                    resynth_line=_resynth_line,
                    on_event=(lambda m, lv: status_callback(m, lv)) if status_callback else None,
                )
                # 修复行时长已变 → 同步 AudioFile 行与 manifest 段, 并重写 manifest.json
                # (2026-09-05: 只更新 DB 不回写 manifest, 导出按旧时长截段 → 吞尾字;
                #  下游 jy 轨/字幕 cum 均以 manifest 为时间轴真理源)
                _touched = False
                for fix in verify_report.get("fixed", []):
                    for af in audio_files:
                        if af.filename == fix.get("file") and fix.get("duration"):
                            af.duration = fix["duration"]
                    if fix.get("duration"):
                        for seg in manifest.get("segments", []):
                            if seg.get("file") == fix.get("file"):
                                seg["duration"] = fix["duration"]
                                _touched = True
                if _touched:
                    (output_dir / "manifest.json").write_text(
                        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as exc:
                logger.warning("[tts %s] ASR 回听校验跳过: %s", job.id[:8], exc)
                if status_callback:
                    try:
                        status_callback(f"ASR 回听校验不可用 (跳过): {exc}", "warn")
                    except Exception:
                        pass

        # ── Concatenate all segment WAVs into one paragraph-level file ──
        combined_path = output_dir / "full_paragraph.wav"
        existing_wavs = [af.file_path for af in audio_files if Path(af.file_path).exists()]
        if existing_wavs and len(existing_wavs) >= 1:
            # 段级响度归一已在 scripts/tts_lib/lines.synthesize_lines 内完成
            # (2026-08-21 loudnorm -16 LUFS), 此处直接拼接归一后段 wav.
            try:
                # 2026-08-13: 段落拼接用 fade(无静音gap), 消除段尾音+段首起音紧贴的破音("噗"),
                # 且停顿自然(用户验证 gap=0 最舒服).
                from scripts.tts_lib.audio import _concat_wavs_with_fade
                _concat_wavs_with_fade(
                    [Path(p) for p in existing_wavs], combined_path,
                    gap_sec=0.0, fade_out_sec=0.15, fade_in_sec=0.06,
                )
                try:
                    info = sf.info(str(combined_path))
                    combined_duration = info.duration
                    combined_sample_rate = info.samplerate
                except Exception:
                    combined_duration = sum(af.duration or 0 for af in audio_files)
                    combined_sample_rate = audio_files[0].sample_rate if audio_files else 24000
            except Exception:
                combined_path = None
                combined_duration = None
                combined_sample_rate = None
        else:
            combined_path = None
            combined_duration = None
            combined_sample_rate = None

        return {
            "manifest": manifest,
            "audio_files": audio_files,
            "output_dir": str(output_dir),
            "tts_verify": verify_report,
            "combined_file": {
                "file": "full_paragraph.wav",
                "file_path": str(combined_path) if combined_path else None,
                "duration": combined_duration,
                "sample_rate": combined_sample_rate,
            } if combined_path else None,
        }
