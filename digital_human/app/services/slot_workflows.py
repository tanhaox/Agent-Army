"""Slot workflow implementations — one function per visual workflow type.

Each function takes (db, slot) and returns the output mp4 path.
ffmpeg helpers are co-located since they're only used here.
"""
from __future__ import annotations

import logging
import re
import shutil
import subprocess
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_config
from app.models import DirectorJob, DirectorSlot, VisualRenderJob
from app.schemas import get_video_format_spec
from app.services.asset_matcher import match_local_assets
from app.services.pexels_service import pexels_service

logger = logging.getLogger(__name__)

# HF 视觉渲染默认模板（财经杂志感竖屏）
HF_TEMPLATE_ID = "news-magazine-v1"
# 横屏模板: 由 _pick_hf_template 按 video_format 选择
HF_TEMPLATE_ID_LS = "news-magazine-v1-ls"


def _pick_hf_template(job: DirectorJob) -> str:
    """按 job.video_format 选择 HF 模板 (横屏→横屏模板, 其余→竖屏模板)。

    修复 2026-08-07 H 线 bug: 此前 execute_hf_visual_slot 硬编码竖屏模板,
    导致选择 landscape 时所有 HF 视频仍产出 1080×1920 竖屏。
    """
    spec = get_video_format_spec(job.video_format)
    if spec["width"] > spec["height"]:
        return HF_TEMPLATE_ID_LS
    return HF_TEMPLATE_ID


# ---------------------------------------------------------------------------
# ffmpeg helpers
# ---------------------------------------------------------------------------

def run_ffmpeg(cmd: list[str]) -> None:
    """Run ffmpeg and raise RuntimeError on failure."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not on PATH")
    r = subprocess.run(
        cmd, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300, check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {r.stderr[:500]}")


def extract_audio_slice(audio_path: Path, out_path: Path, start: float, end: float) -> None:
    duration = end - start
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(audio_path),
        "-ss", f"{start:.3f}", "-t", f"{duration:.3f}",
        "-c:a", "aac", "-b:a", "192k",
        str(out_path),
    ]
    run_ffmpeg(cmd)


def extract_audio_slice_wav(audio_path: Path, out_path: Path, start: float, end: float) -> None:
    """Extract slot audio segment as 16-bit PCM WAV (ComfyUI LoadAudio compatible)."""
    duration = end - start
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(audio_path),
        "-ss", f"{start:.3f}", "-t", f"{duration:.3f}",
        "-acodec", "pcm_s16le", "-ar", "48000",
        str(out_path),
    ]
    run_ffmpeg(cmd)


def replace_video_audio(video_path: Path, audio_path: Path, out_path: Path) -> None:
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video_path), "-i", str(audio_path),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        str(out_path),
    ]
    run_ffmpeg(cmd)


# ---------------------------------------------------------------------------
# Slot directory helpers
# ---------------------------------------------------------------------------

def slot_root(slot: DirectorSlot) -> Path:
    cfg = get_config().defaults
    return Path(cfg.composition_output_root) / slot.director_job_id / "slots" / str(slot.id)


def ensure_slot_dir(slot: DirectorSlot) -> Path:
    root = slot_root(slot)
    root.mkdir(parents=True, exist_ok=True)
    return root


def audio_slice_path(job: DirectorJob) -> Path | None:
    if job.audio_file is None:
        return None
    return Path(job.audio_file.file_path) if job.audio_file.file_path else None


# ---------------------------------------------------------------------------
# Workflow: host (ComfyUI LTX23)
# ---------------------------------------------------------------------------

def prepare_comfyui_storyboard(
    src: Path,
    *,
    target_w: int,
    target_h: int,
    max_source_pixels: int = 2_000_000,
    max_file_size_mb: float = 10.0,
) -> Path:
    """QA-prepare a storyboard image for ComfyUI / LTX23.

    Performs three conformance checks:
      1. Resize: if source pixel count > max_source_pixels, scale down
         preserving aspect ratio before ComfyUI sees it (saves VAE encode).
      2. Format: always convert to PNG 8-bit RGB/RGBA; strips ICC/EXIF junk.
      3. File size: if source is > max_file_size_mb, log a warning but still
         resize, so we don't feed ComfyUI a 50 MB phone photo.

    Returns the path of the prepared PNG (may equal src if already compliant).
    """
    import math
    from PIL import Image

    if not src.exists():
        raise FileNotFoundError(f"storyboard source not found: {src}")

    file_size_mb = src.stat().st_size / (1024 * 1024)
    if file_size_mb > max_file_size_mb:
        logger.warning(
            "[comfyui-qa] storyboard %s is %.1f MB (limit %.1f MB); will resize",
            src.name, file_size_mb, max_file_size_mb,
        )

    img = Image.open(src)
    # Ensure RGB/RGBA 8-bit for the VAE pipeline.
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    if img.mode == "RGBA":
        # ComfyUI LoadImage is fine with RGBA, but LTX latent expects 3 channels.
        # Flatten onto white background to avoid alpha-fringe.
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg

    w, h = img.size
    pixels = w * h
    if pixels > max_source_pixels:
        scale = math.sqrt(max_source_pixels / pixels)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        logger.info(
            "[comfyui-qa] resizing %s %dx%d -> %dx%d (%.2f Mpx -> %.2f Mpx)",
            src.name, w, h, new_w, new_h,
            pixels / 1e6, (new_w * new_h) / 1e6,
        )
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Optional: letterbox to target aspect ratio so LTX crop is predictable.
    # We do not upscale; only pad if the aspect ratio is wildly off.
    current_ratio = img.width / img.height
    target_ratio = target_w / target_h
    if abs(current_ratio - target_ratio) > 0.05:
        logger.info(
            "[comfyui-qa] aspect ratio %.3f != target %.3f; padding to target",
            current_ratio, target_ratio,
        )
        new_w = img.width
        new_h = int(new_w / target_ratio)
        if new_h < img.height:
            new_w = int(img.height * target_ratio)
            new_h = img.height
        canvas = Image.new("RGB", (new_w, new_h), (255, 255, 255))
        canvas.paste(
            img, ((new_w - img.width) // 2, (new_h - img.height) // 2)
        )
        img = canvas

    # Final format/size enforcement: write PNG to a temp path.
    tmp = src.with_suffix(".qa.png")
    img.save(tmp, format="PNG", optimize=True)

    final_size_mb = tmp.stat().st_size / (1024 * 1024)
    if final_size_mb > max_file_size_mb:
        logger.warning(
            "[comfyui-qa] prepared %s still %.1f MB; consider lowering max_source_pixels",
            tmp.name, final_size_mb,
        )

    return tmp


def execute_host_slot(db: Session, slot: DirectorSlot) -> str:
    """Generate host video via LTX23 for the slot, returning mp4 path."""
    from app.services.lit_video_builder import build_ltx23_video_workflow
    import httpx

    root = ensure_slot_dir(slot)
    cfg = get_config()
    spec = get_video_format_spec(slot.director_job.video_format)

    audio_path = audio_slice_path(slot.director_job)
    if not audio_path or not audio_path.exists():
        raise RuntimeError("whole audio missing for host slot")

    role = slot.director_job.script.host
    storyboard_image: Path | None = None

    # 获取 view_groups: Host 本身没有该字段，需通过 Persona → Role 关联链查找
    view_groups: list = []
    reference_image: str | None = None
    if role:
        reference_image = role.reference_image
        # 安全访问: 如果 role 是 Role 对象则直接取
        view_groups = getattr(role, "view_groups", None) or []
        # 如果 Host 没有 view_groups，通过 persona_key 查找 Persona → Role
        if not view_groups and hasattr(role, "persona_key") and role.persona_key:
            from app.models import Persona
            persona = (
                db.query(Persona)
                .filter(Persona.prompt_template.like(f"{role.persona_key}%"))
                .first()
            )
            if persona and persona.role:
                view_groups = persona.role.view_groups or []
                # 如果 Host 没有 reference_image，也用 Role 的
                if not reference_image and persona.role.reference_image:
                    reference_image = persona.role.reference_image

    # 优先从 view_groups 按 camera_angle + view_group_index 取图
    if view_groups:
        group_idx = slot.view_group_index or 0
        cam_key = str(slot.camera_angle or 1)
        if group_idx < len(view_groups):
            cameras = view_groups[group_idx].get("cameras") or {}
            img_path = cameras.get(cam_key)
            if img_path:
                storyboard_image = Path(img_path)

    # 回退: reference_image
    if (storyboard_image is None or not storyboard_image.exists()) and reference_image:
        storyboard_image = Path(reference_image)

    if storyboard_image is None or not storyboard_image.exists():
        raise RuntimeError("host slot requires role reference_image or view_groups camera image")

    comfy_input = Path(cfg.defaults.comfyui_input_dir)
    comfy_input.mkdir(parents=True, exist_ok=True)

    uniq = f"slot_{slot.director_job_id[:8]}_{slot.slot_index:03d}"

    slot_wav = comfy_input / f"{uniq}_audio.wav"
    extract_audio_slice_wav(audio_path, slot_wav, slot.start_sec, slot.end_sec)

    # QA preprocess the storyboard before ComfyUI sees it.
    prepared_sb = prepare_comfyui_storyboard(
        storyboard_image,
        target_w=spec["comfyui_w"],
        target_h=spec["comfyui_h"],
    )
    sb_comfy = comfy_input / f"{uniq}_sb.png"
    shutil.copy2(prepared_sb, sb_comfy)

    duration = round(slot.end_sec - slot.start_sec, 3)
    orientation = slot.director_job.video_format or "portrait"
    if orientation not in ("portrait", "landscape"):
        orientation = "portrait"  # square → portrait fallback
    workflow = build_ltx23_video_workflow(
        audio_filename=slot_wav.name,
        storyboard=[{"filename": sb_comfy.name}],
        duration_sec=duration, fps=30,
        orientation=orientation,
        filename_prefix=f"{uniq}_",
    )

    comfy_url = f"{cfg.defaults.base_url_comfyui}/prompt"
    try:
        r = httpx.post(comfy_url, json={"prompt": workflow}, timeout=10)
        r.raise_for_status()
        prompt_id = r.json().get("prompt_id")
    except Exception as exc:
        raise RuntimeError(f"ComfyUI submit failed: {exc}") from exc

    if not prompt_id:
        raise RuntimeError("ComfyUI did not return prompt_id")

    history_url = f"{cfg.defaults.base_url_comfyui}/history/{prompt_id}"
    output_path = poll_comfyui_and_collect(
        prompt_id=prompt_id, history_url=history_url,
        prefix=f"{uniq}_",
        timeout_sec=cfg.defaults.comfyui_timeout_sec,
        job_id=slot.director_job_id,
        slot_index=slot.slot_index,
    )

    # 保留 ComfyUI 原生音频 — LTX23 已根据 WAV 切片生成了口型同步的视频+音频，
    # 不再用 TTS 切片替换，避免 TTS 切片边界累积误差导致影音不同步。
    return str(output_path)


def poll_comfyui_and_collect(
    *, prompt_id: str, history_url: str, prefix: str,
    timeout_sec: int, poll_interval: float = 2.0,
    job_id: str = "",
    slot_index: int | None = None,
) -> Path:
    """Poll ComfyUI history until prompt is done, then find output video.
    Checks cancel flag each iteration; sends POST /interrupt if cancelled.
    Emits slot_progress heartbeat every ~10s so the UI does not go silent.
    """
    import httpx
    import time
    from app.services.slot_executor import _is_cancelled
    from app.services.director_events import publish as _evt

    cfg = get_config()
    deadline = time.monotonic() + timeout_sec
    last_heartbeat = 0.0
    heartbeat_interval = 10.0
    while time.monotonic() < deadline:
        now = time.monotonic()
        # 检查取消标志
        if job_id and _is_cancelled(job_id):
            # 向 ComfyUI 发送中断信号
            try:
                httpx.post(f"{cfg.defaults.base_url_comfyui}/interrupt", timeout=5)
                logger.info("[comfyui] interrupt sent for job %s", job_id)
            except Exception:
                pass
            raise RuntimeError("用户取消，ComfyUI 已发送 interrupt")

        # 每 10s 发送一次 slot 进度心跳，避免前端日志长时间静默
        if job_id and now - last_heartbeat >= heartbeat_interval:
            elapsed = int(now - (deadline - timeout_sec))
            _evt(job_id, {
                "type": "slot_progress",
                "phase": "ComfyUI (host/mixed)",
                "slot_index": slot_index,
                "workflow": "host",
                "msg": f"ComfyUI 生成中… 已 {elapsed}s",
                "elapsed_sec": elapsed,
            })
            last_heartbeat = now

        try:
            r = httpx.get(history_url, timeout=10)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            logger.warning("ComfyUI history poll error: %s", exc)
            time.sleep(poll_interval)
            continue

        outputs = data.get(prompt_id, {}).get("outputs", {})
        for node_id, node_outputs in outputs.items():
            for item in node_outputs.get("gifs", node_outputs.get("images", [])):
                filename = item.get("filename", "")
                if filename.startswith(prefix) and filename.endswith(".mp4"):
                    comfy_output = Path(cfg.defaults.comfyui_output_dir) / filename
                    if comfy_output.exists():
                        return comfy_output   # 零搬运 — 直接返回 ComfyUI output 原始路径
        time.sleep(poll_interval)

    raise RuntimeError(f"ComfyUI timeout after {timeout_sec}s for prompt {prompt_id}")


# ---------------------------------------------------------------------------
# Workflow: broll_pexels
# ---------------------------------------------------------------------------

def _collect_used_pexels_ids(db: Session, slot: DirectorSlot) -> set[int]:
    """Collect Pexels video ids already used by earlier completed broll slots.

    同片不重复素材约束 (2026-08-01): 遍历同 job 已完成且已持久化
    ``params_json["pexels_id"]`` 的 broll 类 slot, 收集已用过的 id。
    仅收集本 slot 之前 (slot_index 更小) 的 slot, 保证时间顺序、避免自引用。
    """
    job_id = slot.director_job_id
    rows = (
        db.query(DirectorSlot)
        .filter(
            DirectorSlot.director_job_id == job_id,
            DirectorSlot.slot_index < slot.slot_index,
            DirectorSlot.workflow.in_(("broll_pexels", "mixed_host_broll")),
            DirectorSlot.status == "completed",
        )
        .all()
    )
    used: set[int] = set()
    for r in rows:
        pid = (r.params_json or {}).get("pexels_id")
        if pid is not None:
            try:
                used.add(int(pid))
            except (TypeError, ValueError):
                pass
    return used

def execute_broll_pexels_slot(db: Session, slot: DirectorSlot) -> str:
    """Resolve Pexels video (降维搜索优先), trim to slot duration, return mp4 path.

    降维搜索 (2026-08-01): LLM 给出按重要性排序的关键词数组
    ``params.keywords``(≤6, 第 1 个是全局主体关键词)。API 侧每次去掉末尾
    1 个词重搜, 命中即停, 主关键词永远保留在查询里 → 保证全片地域/主题一致性。
    兼容旧 params: 无 keywords 时退化为 category/query 单次搜索。

    同片不重复素材 (2026-08-01): 一个 Pexels 视频 (pexels_id) 在同一 DirectorJob
    中只允许用一次。已用过的 id 会传给 resolve 排除, 选中后写回
    slot.params_json["pexels_id"] 持久化, 供后续 slot 排除。
    """
    root = ensure_slot_dir(slot)
    spec = get_video_format_spec(slot.director_job.video_format)
    duration = round(slot.end_sec - slot.start_sec, 3)
    min_dur = int(duration) or 5
    orientation = spec["pexels_orientation"]

    # 同一 job 内已用过的 Pexels 素材 id (从已完成 broll slot 的 params 收集)
    used_ids: set[int] = set()
    try:
        used_ids = _collect_used_pexels_ids(db, slot)
    except Exception:  # noqa: BLE001
        logger.warning("collect used pexels ids failed, fallback empty set", exc_info=True)
    if used_ids:
        logger.info("[broll_pexels] job already used %d material(s), excluding them", len(used_ids))

    params = slot.params_json or {}
    keywords = params.get("keywords")
    used_query: str | None = None
    if isinstance(keywords, list) and keywords:
        items, used_query = pexels_service.resolve_descending(
            [str(k) for k in keywords], max_results=1,
            min_duration_sec=min_dur, orientation=orientation,
            exclude_pexels_ids=used_ids,
        )
        desc = f"keywords={keywords} hit_query={used_query}"
    else:
        # 兼容旧 params: category / text_context 单次搜索
        category = params.get("category") or slot.text_context or "business"
        items = pexels_service.resolve(
            category, max_results=5, min_duration_sec=min_dur,
            orientation=orientation, exclude_pexels_ids=used_ids,
        )
        used_query = category
        desc = f"query={category}"

    usable = [i for i in items if i.local_path and Path(i.local_path).exists()]
    if not usable:
        raise RuntimeError(f"no usable Pexels material for {desc}")
    src = Path(usable[0].local_path)

    # 持久化选中的 pexels_id, 供同 job 后续 slot 排除 (唯一素材约束)
    chosen_pexels_id = usable[0].pexels_id or usable[0].id
    if chosen_pexels_id is not None:
        new_params = dict(params)
        new_params["pexels_id"] = chosen_pexels_id
        slot.params_json = new_params
        db.commit()
        logger.info("[broll_pexels] slot %d -> pexels_id=%s", slot.slot_index, chosen_pexels_id)

    out_path = root / f"broll_pexels_{slot.slot_index:03d}.mp4"
    w, h = spec["width"], spec["height"]
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(src),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-ss", "0", "-t", f"{duration:.3f}",
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        str(out_path),
    ]
    run_ffmpeg(cmd)
    return str(out_path)


# ---------------------------------------------------------------------------
# Workflow: broll_local
# ---------------------------------------------------------------------------

def execute_broll_local_slot(db: Session, slot: DirectorSlot) -> str:
    """Pick local material file, trim/pad to target aspect, return mp4 path.

    匹配策略（按优先级）:
    1. params.file 精确文件名 → 直接定位（向后兼容）
    2. params.keywords + 可选维度 → asset_matcher 语义匹配
    3. params.category 作为 keyword 兜底 → asset_matcher
    4. 全部失败 → 随机 fallback 素材（避免坠入 black_placeholder）
    """
    root = ensure_slot_dir(slot)
    cfg = get_config().defaults
    spec = get_video_format_spec(slot.director_job.video_format)
    params = slot.params_json or {}

    # 策略 1: 精确文件名
    file_name = params.get("file")
    if file_name:
        candidates = [
            Path(cfg.materials_dir) / file_name,
        ]
        src = next((p for p in candidates if p.exists()), None)
        if src is not None:
            logger.info("[broll_local] exact match: %s", file_name)
            return _render_broll_local(src, root, slot, spec)
        logger.warning("[broll_local] params.file=%s not found, falling back to keywords match", file_name)

    # 策略 2-3: 语义匹配
    keywords = params.get("keywords")
    if not keywords:
        # 从 category/text_context 构造 keywords
        category = params.get("category") or slot.text_context
        if category:
            # 简单分词：按空格/逗号/中文分词边界切
            keywords = [w.strip() for w in re.split(r"[,，\s]+", category) if w.strip()]

    if keywords:
        orientation = spec.get("pexels_orientation") if spec else None
        results = match_local_assets(
            db,
            keywords=keywords if isinstance(keywords, list) else [str(keywords)],
            scenes=params.get("scenes"),
            shot_types=params.get("shot_types"),
            tone=params.get("tone"),
            motion_level=params.get("motion_level"),
            content_density=params.get("content_density"),
            time_of_day=params.get("time_of_day"),
            orientation=orientation,
            limit=1,
        )
        if results:
            best = results[0]
            fp = best.get("file_path")
            if fp:
                src = Path(fp)
                if src.exists():
                    logger.info(
                        "[broll_local] keyword match: %s (score=%d)",
                        src.name, best.get("score", 0),
                    )
                    return _render_broll_local(src, root, slot, spec)

    # 策略 4: 随机 fallback
    logger.warning(
        "[broll_local] slot %d: no match via file/keywords, using random fallback",
        slot.slot_index,
    )
    src = _pick_fallback_material(db, slot)
    return _render_broll_local(src, root, slot, spec)


def _render_broll_local(
    src: Path, root: Path, slot: DirectorSlot, spec: dict,
) -> str:
    """ffmpeg trim + scale + pad → output mp4."""
    duration = round(slot.end_sec - slot.start_sec, 3)
    out_path = root / f"broll_local_{slot.slot_index:03d}.mp4"
    w, h = spec["width"], spec["height"]
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(src),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-ss", "0", "-t", f"{duration:.3f}",
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        str(out_path),
    ]
    run_ffmpeg(cmd)
    return str(out_path)


# ---------------------------------------------------------------------------
# Workflow: hf_chart / hf_title
# ---------------------------------------------------------------------------

def _extract_hf_content(text: str, title_max: int = 16) -> dict:
    """从口播文本提取标题卡内容 (2026-08-01, 修复黑底白字标题卡根因).

    HF 标题卡模板 (news-magazine-v1) 有大标题/副题/metrics/chart 设计,但此前
    把整句口播(含 || 停顿符)硬塞进 title,metrics/chart 用口播占位垃圾填充,
    导致渲染结果=黑底一行白字。本函数:
      - title: 只取首个分句,压到 title_max 字内(模板 108px 标题,过长会溢出);
      - subtitle: 取第 2 个分句(有内容时),替代空副题;
      - metrics: 抽取分句中的真实数字(优先),抽不到则跳过(模板 layout 会删空行);
                带 % 的数值也进 metrics(2026-08-01 问题1修复: 无图表数据时也有文字展示);
      - chart: 带 % 的数值构造图表 items,与 metrics 互补(文字+图表双轨)。

    返回 dict: {title, subtitle, metrics, chart} 全部为模板友好结构。
    """
    text = (text or "").strip()
    chunks = [c.strip() for c in re.split(r"\|\||\n", text) if c.strip()]
    if not chunks:
        return {"title": "数据展示", "subtitle": "", "metrics": [], "chart": {"type": "bar", "items": []}}

    _emotion = r"(?:情绪|serious|calm|happy|sad|angry|opening|rising|climax|falling|closing)"

    def _clean(s: str) -> str:
        s = re.sub(rf"\[{_emotion}\]", "", s)
        s = re.sub(r"\s+", "", s)
        return s

    title = _clean(chunks[0])
    # 去掉开场白/口头禅前缀(host 段文本误喂给标题卡时,不让"大家好"上屏)
    title = re.sub(r"^(?:大家好|各位朋友|各位观众|哈喽|你好|hello)[，,。\.、]?", "", title)
    title = re.sub(r"^(?:我是老陈|老陈)[，,。\.、]?", "", title)
    # 若首句只剩开场白(去前缀后为空),顺延用后续分句做标题
    if not title:
        for nxt in chunks[1:]:
            cand = _clean(nxt)
            cand = re.sub(r"^(?:大家好|各位朋友|各位观众|哈喽|你好|hello|我是老陈|老陈)[，,。\.、]?", "", cand)
            if cand:
                title = cand
                break
    # 截断: 优先停在完整分句(最后一个不超上限的标点), 避免"叫生存空"式残句
    if len(title) > title_max:
        last = 0
        for m in re.finditer(r"[，。！？,\.!?]", title):
            if m.end() <= title_max:
                last = m.end()
            else:
                break
        title = title[:last] if last else title[:title_max]

    subtitle = _clean(chunks[1])[:32] if len(chunks) > 1 else ""

    metrics: list[dict] = []
    chart_items: list[dict] = []
    seen: set[str] = set()
    for c in chunks:
        nums = re.findall(r"(-?\d+(?:\.\d+)?)\s*(%|万亿|亿|万|千|元|倍|个|点|岁)?", c)
        for val, unit in nums:
            label = c[:20]
            value_text = f"{val}{unit}".strip()
            # 带 % 的数值进 chart 条形图; 同时所有数字都进 metrics(问题1: 无图表时也有文字展示)
            if unit == "%":
                chart_items.append({"label": label, "value": float(val)})
            # metrics 去重: 同 label+value 只留一条, 且 priority 0=普通 1=含%核心
            dedup = f"{label}|{value_text}"
            if dedup not in seen:
                seen.add(dedup)
                metrics.append({"label": label, "value": value_text, "priority": 1 if unit == "%" else 0})
            if len(metrics) >= 4 and len(chart_items) >= 5:
                break
        if len(metrics) >= 4 and len(chart_items) >= 5:
            break

    # 排序: 含 % 的核心数字靠前, 保证无图表时逐条文字展示里增长率醒目
    metrics.sort(key=lambda m: -m.pop("priority", 0))
    for m in metrics:
        m.setdefault("emphasis", False)
    if metrics and metrics[0].get("value") and "%" in metrics[0]["value"]:
        metrics[0]["emphasis"] = True

    return {
        "title": title or "数据展示",
        "subtitle": subtitle,
        "metrics": metrics[:4],
        "chart": {"type": "bar", "unit": "", "items": chart_items[:5]},
    }


def _normalize_chart_input(render_config: dict, extracted: dict) -> dict:
    """归一化 LLM render_config + 口播提取结果 → 统一 chart 结构 (2026-08-01).

    兼容旧格式:
      - chart_type: "pie_chart"→pie, "bar_chart"/"line_chart"/其他→bar;
      - data: [{label,value}] 直接可用; [number] 旧格式按 label="数据N" 补全;
      - 缺 chart 字段时用 extracted.chart (口播提取的 bar items) 兜底。

    返回 {type, unit, growth, label, color_scheme, items:[{label,value}]}。
    """
    chart = dict(extracted.get("chart") or {})
    chart_type = render_config.get("chart_type") or chart.get("type") or "bar"
    if not isinstance(chart_type, str):
        chart_type = "bar"
    chart_type = chart_type.lower()
    if chart_type in ("pie", "pie_chart"):
        chart_type = "pie"
    elif chart_type in ("bar", "bar_chart", "line_chart"):
        chart_type = "bar"
    else:
        chart_type = "bar"
    chart["type"] = chart_type

    items: list[dict] = []
    data = render_config.get("data")
    if isinstance(data, list):
        for i, d in enumerate(data, start=1):
            if isinstance(d, dict) and d.get("value") is not None:
                try:
                    items.append({"label": str(d.get("label") or f"数据{i}")[:20], "value": float(d["value"])})
                except (ValueError, TypeError):
                    continue
            else:
                try:
                    items.append({"label": f"数据{i}", "value": float(d)})
                except (ValueError, TypeError):
                    continue
    # data 缺失/无效时依次兜底: render_config.chart.items → 口播提取 items
    if not items:
        rc_chart = render_config.get("chart")
        src_items = rc_chart.get("items") if isinstance(rc_chart, dict) else None
        if not src_items:
            src_items = chart.get("items") or []
        for it in src_items:
            if isinstance(it, dict) and it.get("value") is not None:
                try:
                    items.append({"label": str(it.get("label") or "数据")[:20], "value": float(it["value"])})
                except (ValueError, TypeError):
                    continue
    chart["items"] = items[:5]

    for k in ("unit", "growth", "color_scheme"):
        if render_config.get(k):
            chart[k] = str(render_config[k])
        elif not chart.get(k):
            chart[k] = ""
    if render_config.get("label"):
        chart["label"] = str(render_config["label"])
    elif not chart.get("label"):
        chart["label"] = ""

    # pie 至少保留 2 扇区: 若只有 1 项, 补 growth 对应的"其他"扇区
    if chart["type"] == "pie" and len(chart["items"]) == 1:
        growth = chart.get("growth") or ""
        m = re.search(r"(-?\d+(?:\.\d+)?)", growth)
        other = float(m.group(1)) if m else 100.0
        chart["items"].append({"label": "其他", "value": other})
    return chart


def execute_hf_visual_slot(db: Session, slot: DirectorSlot, workflow: str) -> str:
    """Render an HF visual (chart or title card) for the slot duration."""
    from app.services.visual_render_service import execute_visual_render_job

    # 按 video_format 选模板: 横屏→news-magazine-v1-ls, 竖屏/方屏→news-magazine-v1
    template_id = _pick_hf_template(slot.director_job)

    duration = round(slot.end_sec - slot.start_sec, 3)
    render_config = slot.params_json.get("render_config") or {}
    input_data = _extract_hf_content(slot.text_context or "")
    input_data["duration_sec"] = max(5, min(30, round(duration)))
    # render_config 里的真实数据(如 title/metrics/chart)优先,覆盖从口播提取的结果
    for k, v in render_config.items():
        if k == "metrics" and isinstance(v, list):
            cleaned = [{"label": str(i["label"])[:20], "value": str(i["value"])}
                       for i in v if isinstance(i, dict) and "label" in i and "value" in i]
            if cleaned:
                input_data["metrics"] = cleaned
        elif k == "title" and isinstance(v, str) and v.strip():
            input_data["title"] = v.strip()[:16]
        elif k not in ("title", "chart", "data"):
            input_data[k] = v

    # chart 数据贯通 (问题2): 归一化器统一 render_config.chart_type/data/label/unit/growth
    # 与口播提取结构为 {type, unit, growth, label, color_scheme, items}, 经 {{chart_json}} 进模板
    input_data["chart"] = _normalize_chart_input(render_config, input_data)

    # metrics 为空但 chart 有数据时, 从 chart.items 前 4 项构造 metrics (schema 恒满足)
    if not input_data.get("metrics") and input_data["chart"].get("items"):
        input_data["metrics"] = [
            {"label": it["label"], "value": str(it["value"]), "emphasis": i == 0}
            for i, it in enumerate(input_data["chart"]["items"][:4])
        ]

    # input schema 强制 metrics 非空(minItems=1);口播无数字时给空占位行,
    # 模板 layout() 会删除空 .m-row → 视觉上标题卡只有标题+副题,不出现垃圾数字
    if not input_data.get("metrics"):
        input_data["metrics"] = [{"label": "", "value": ""}]

    job = VisualRenderJob(template_id=template_id, input_json=input_data, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)

    result = execute_visual_render_job(db, job.id, template_id, input_data)
    if result.get("status") != "completed":
        raise RuntimeError(result.get("error_message") or "HF render failed")
    out_path = result.get("output_path")
    if not out_path or not Path(out_path).exists():
        raise RuntimeError("HF render output missing")
    return out_path


# ---------------------------------------------------------------------------
# Workflow: mixed_host_broll
# ---------------------------------------------------------------------------

def execute_mixed_host_broll_slot(db: Session, slot: DirectorSlot) -> str:
    """Host video foreground composited over broll background."""
    root = ensure_slot_dir(slot)
    spec = get_video_format_spec(slot.director_job.video_format)
    host_path = execute_host_slot(db, slot)
    broll_path = execute_broll_pexels_slot(db, slot)

    out_path = root / f"mixed_{slot.slot_index:03d}.mp4"
    # Host overlay: 60% width centered
    ow = int(spec["width"] * 0.6)
    oh = int(spec["height"] * 0.6)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(broll_path), "-i", str(host_path),
        "-filter_complex",
        f"[1:v]scale={ow}:{oh}[host];[0:v][host]overlay=(W-w)/2:(H-h)/2:enable='between(t,0,9999)'[v]",
        "-map", "[v]", "-map", "1:a:0",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-ar", "48000", "-b:a", "192k", "-shortest",
        str(out_path),
    ]
    run_ffmpeg(cmd)
    return str(out_path)


# ---------------------------------------------------------------------------
# Workflow: black_placeholder (ultimate fallback)
# ---------------------------------------------------------------------------

def _pick_fallback_material(db: Session, slot: DirectorSlot) -> Path:
    """Pick a generic b-roll clip from materials_dir as the universal fallback.

    We intentionally avoid pure black frames. The chosen clip is treated as
    "small error covering big error": visually harmless generic footage.
    """
    import random

    cfg = get_config().defaults
    materials_dir = Path(cfg.materials_dir)
    if not materials_dir.exists():
        raise RuntimeError(f"materials_dir not found: {materials_dir}")

    # Collect all usable video files once; deterministic but varied per slot.
    videos = sorted(p for p in materials_dir.rglob("*") if p.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm") and p.is_file())
    if not videos:
        raise RuntimeError("no fallback material videos found in materials_dir")

    # Use slot_index to pick deterministically, then shuffle slightly by job id.
    base_idx = (slot.slot_index or 0) % max(1, len(videos))
    job_hash = sum(ord(c) for c in (slot.director_job_id or ""))
    idx = (base_idx + job_hash) % len(videos)
    return videos[idx]


def execute_black_placeholder_slot(db: Session, slot: DirectorSlot) -> str:
    """Universal fallback clip (generic b-roll), not pure black.

    ID-025: the old pure-black placeholder was flagged during QC because it
    creates dead air in the final composition. We now trim/scale a generic
    material clip from materials_dir to the slot duration.
    """
    root = ensure_slot_dir(slot)
    spec = get_video_format_spec(slot.director_job.video_format)
    duration = round(slot.end_sec - slot.start_sec, 3)
    out_path = root / f"black_placeholder_{slot.slot_index:03d}.mp4"

    src = _pick_fallback_material(db, slot)
    logger.info("[black_placeholder] slot %d using fallback material %s", slot.slot_index, src.name)
    w, h = spec["width"], spec["height"]
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(src),
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-ss", "0", "-t", f"{duration:.3f}",
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black",
        "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        str(out_path),
    ]
    run_ffmpeg(cmd)
    return str(out_path)


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

WORKFLOW_HANDLERS = {
    "host": execute_host_slot,
    "broll_pexels": execute_broll_pexels_slot,
    "broll_local": execute_broll_local_slot,
    "hf_chart": execute_hf_visual_slot,
    "hf_title": execute_hf_visual_slot,
    "mixed_host_broll": execute_mixed_host_broll_slot,
    "black_placeholder": execute_black_placeholder_slot,
}
