"""视频素材 AI 打标编排器 — 4 通道智能分析流水线 → LLM 综合打标 → 写入数据库.

流水线:
  通道1: 智能抽帧 (scdet 场景检测, 上限12帧)
  通道2: 运动分析 (scdet 低阈值频率统计, 零AI)
  通道3: OCR 预扫 (EasyOCR + 国旗色块, 可选)
  通道4: LLM 综合打标 (拿到帧 + 通道2/3结果)

后台线程执行, 进度通过 director_events 推送.
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
import threading
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..config import get_config
from ..database import get_session_maker
from ..models import VideoAsset
from .asset_tagging import infer_tags
from .director_events import publish
from .frame_extraction import smart_extract_frames
from .local_llm_client import LocalLLMClient, LocalLLMError
from .motion_analysis import analyze_motion
from .ocr_scan import ocr_scan_frames

logger = logging.getLogger(__name__)

# ── 标签维度定义 ──────────────────────────────────────────────

ALL_SCENES = ["城市", "自然", "商业", "科技", "财经", "生活", "美食", "医疗", "教育", "工业"]
ALL_SHOT_TYPES = ["航拍", "空镜", "建筑", "交通", "人像", "特写"]

TONE_VALUES = ["warm", "cool", "neutral", "bright", "dark", "monochrome"]
DENSITY_VALUES = ["sparse", "moderate", "dense"]
MOTION_VALUES = ["static", "slow", "medium", "fast"]
TIME_OF_DAY_VALUES = ["day", "night", "sunset", "indoor", "undefined"]

SYSTEM_PROMPT = f"""你是一个专业的视频素材标注员。请观察视频的多个关键帧截图，为视频生成精确的结构化标签。

## 辅助分析数据（已预计算，精度高，请优先采纳）
用户消息中会附带以下确定性算法的分析结果：
- **motion_analysis**: 运动强度 (static/slow/medium/fast) + 速度类别 (normal/timelapse/slow_motion)
  → 请将 motion_level 直接填入标签; timelapse → motion_level="fast"
- **ocr_scan**: 画面文字语言 + 国旗检测 + 国内外推断
  → OCR 检测到中文文字或中国国旗 → location="domestic"
  → OCR 检测到纯英文且无国旗 → location="foreign"
  → OCR 不确定时, 观察画面建筑/文字/车牌等线索自行判断

## 标签体系（必须从以下枚举值中选择）

**scenes（场景，可多选）**: {', '.join(ALL_SCENES)}

**shot_types（镜头类型，可多选）**: {', '.join(ALL_SHOT_TYPES)}
  - 航拍: 无人机/俯拍视角
  - 空镜: 无人无主体的空景
  - 建筑: 以建筑结构为主体的固定/推进镜头
  - 交通: 车辆/人流/道路/运输
  - 人像: 人物为主体的镜头
  - 特写: 对物体/纹理/细节的近距离拍摄

**source_type**: "footage" 或 "creative"
  - footage: 实拍视频
  - creative: 动画/MG/CGI/抽象/特效合成

**location**: "domestic" 或 "foreign"
  - domestic: 中国场景（中文招牌、中国建筑、中国车牌等）
  - foreign: 国外或无法判断

**people**: "people" 或 "none"

**tone（色调）**: {', '.join(TONE_VALUES)}

**content_density（画面信息密度）**: {', '.join(DENSITY_VALUES)}

**motion_level（动态程度）**: {', '.join(MOTION_VALUES)}

**time_of_day（时间场景）**: {', '.join(TIME_OF_DAY_VALUES)}

**description_zh**: 用一句简洁的中文描述视频画面内容（不超过30字）

**confidence**: 每个维度打一个 0.0-1.0 的置信度小数

## 输出要求
只输出以下结构的 JSON，不要含任何其他文字：
```json
{{
  "scenes": ["", ...],
  "shot_types": ["", ...],
  "source_type": "",
  "location": "",
  "people": "",
  "tone": "",
  "content_density": "",
  "motion_level": "",
  "time_of_day": "",
  "description_zh": "",
  "confidence": {{
    "scenes": 0.0,
    "shot_types": 0.0,
    "source_type": 0.0,
    "location": 0.0,
    "people": 0.0,
    "tone": 0.0,
    "content_density": 0.0,
    "motion_level": 0.0,
    "time_of_day": 0.0
  }}
}}
```"""


# ── 任务状态追踪 ──────────────────────────────────────────────

_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── 辅助 Prompt 构建 ──────────────────────────────────────────

def _build_enriched_user_prompt(
    motion_result: dict | None,
    ocr_result: dict | None,
) -> str:
    """将通道 2/3 的分析结果注入 user prompt, 供 LLM 参考."""
    parts = ["请分析这些视频关键帧，生成结构化标签 JSON。", ""]

    if motion_result and motion_result.get("confidence", 0) > 0.3:
        parts.append("## 运动分析 (预计算)")
        parts.append(f"- motion_level: **{motion_result['motion_level']}**")
        parts.append(f"- speed_category: **{motion_result['speed_category']}**")
        parts.append(f"- scene_change_rate: {motion_result.get('scene_change_rate', 0)}/s")
        parts.append(f"- 置信度: {motion_result.get('confidence', 0):.0%}")
        parts.append("")

    if ocr_result:
        if ocr_result.get("available"):
            parts.append("## OCR 扫描 (预计算)")
            parts.append(f"- 文字语言: **{ocr_result['text_language']}**")
            parts.append(f"- 检测到国旗: **{'是' if ocr_result.get('has_flag') else '否'}**")
            parts.append(f"- 文字覆盖率: {ocr_result.get('text_coverage', 0):.1%}")
            parts.append(f"- 国内外推断: {ocr_result['location_hint']}")
            parts.append("")
        elif ocr_result.get("has_flag"):
            # OCR 不可用但国旗色块检测到
            parts.append("## 国旗检测 (色块分析)")
            parts.append("- 画面中疑似检测到中国国旗色块 (红色+黄色)")
            parts.append("- 建议 location 设为 domestic")
            parts.append("")

    parts.append("请结合关键帧画面和上述预分析数据，生成标签 JSON。")

    return "\n".join(parts)


# ── 帧提取 (已废弃, 保留向后兼容) ──────────────────────────────

def _extract_frame_at(mp4_path: Path, png_path: Path, at_seconds: float, label: str) -> bool:
    """复用 ffmpeg 子进程提取单帧 (内部工具函数)."""
    import shutil

    if not shutil.which("ffmpeg"):
        logger.warning("ffmpeg not on PATH; skip frame extraction")
        return False
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", f"{at_seconds:.3f}",
        "-i", str(mp4_path),
        "-vframes", "1",
        str(png_path),
    ]
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=20, check=False,
        )
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg %s extraction timed out", label)
        return False
    ok = r.returncode == 0 and png_path.exists() and png_path.stat().st_size > 0
    if not ok:
        logger.warning("ffmpeg %s extraction failed: %s", label, r.stderr[:200])
    return ok


def extract_keyframes(video_path: str, duration: float, tmpdir: Path) -> list[Path]:
    """[已废弃] 在视频 25%/50%/75% 时间点抽取 3 帧.

    请改用 frame_extraction.smart_extract_frames() 进行智能抽帧.
    保留此函数用于向后兼容.
    """
    mp4 = Path(video_path)
    if not mp4.exists():
        logger.warning("Video file not found: %s", video_path)
        return []

    frames = []
    start_offset = min(0.5, duration * 0.05)
    positions = {
        "25%": max(start_offset, duration * 0.25),
        "50%": max(start_offset, duration * 0.50),
        "75%": max(start_offset, duration * 0.75),
    }
    for label, sec in positions.items():
        png_path = tmpdir / f"frame_{label.replace('%', 'pct')}.png"
        ok = _extract_frame_at(mp4, png_path, sec, label)
        if ok:
            frames.append(png_path)
    return frames


# ── JSON 解析与回退 ──────────────────────────────────────────

_JSON_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


def _try_parse_json(text: str) -> dict[str, Any] | None:
    """多层尝试从 LLM 输出中提取 JSON."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _JSON_PATTERN.search(text)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    return None


def _validate_tag(parsed: dict, key: str, valid_set: set[str]) -> list[str] | str | None:
    """校验并过滤单个标签维度的值."""
    val = parsed.get(key)
    if val is None:
        return None
    if isinstance(val, list):
        filtered = [v for v in val if v in valid_set]
        return filtered if filtered else None
    if isinstance(val, str) and val in valid_set:
        return val
    return None


def frame_tagging_result(raw_text: str, fallback_tags: dict) -> dict[str, Any]:
    """解析 LLM 输出为结构化标签, 失败时回退到规则引擎."""
    parsed = _try_parse_json(raw_text)

    if parsed is None:
        logger.warning("LLM JSON parse failed, falling back to rule engine. raw=%s", raw_text[:200])
        return {
            **fallback_tags,
            "_fallback": True,
            "_ai_raw": raw_text[:500],
        }

    scenes = _validate_tag(parsed, "scenes", set(ALL_SCENES))
    shot_types = _validate_tag(parsed, "shot_types", set(ALL_SHOT_TYPES))
    source_type = _validate_tag(parsed, "source_type", {"footage", "creative"})
    location = _validate_tag(parsed, "location", {"domestic", "foreign"})
    people = _validate_tag(parsed, "people", {"people", "none"})
    tone = _validate_tag(parsed, "tone", set(TONE_VALUES))
    density = _validate_tag(parsed, "content_density", set(DENSITY_VALUES))
    motion = _validate_tag(parsed, "motion_level", set(MOTION_VALUES))
    time_of_day = _validate_tag(parsed, "time_of_day", set(TIME_OF_DAY_VALUES))
    description_zh = parsed.get("description_zh", "") or ""
    confidence = parsed.get("confidence", None)

    if scenes is None and shot_types is None and source_type is None:
        logger.warning("LLM returned no valid tags, falling back. raw=%s", raw_text[:200])
        return {
            **fallback_tags,
            "_fallback": True,
            "_ai_raw": raw_text[:500],
        }

    result: dict[str, Any] = {
        "scenes": scenes if scenes is not None else fallback_tags.get("scenes", []),
        "shot_types": shot_types if shot_types is not None else fallback_tags.get("shot_types", []),
        "source_type": source_type if source_type is not None else fallback_tags.get("source_type", "footage"),
        "location": location if location is not None else fallback_tags.get("location", "foreign"),
        "people": people if people is not None else fallback_tags.get("people", "none"),
        "description_zh": (description_zh or fallback_tags.get("description_zh", "")),
    }

    extra: dict[str, Any] = {}
    if tone:
        extra["tone"] = tone
    if density:
        extra["content_density"] = density
    if motion:
        extra["motion_level"] = motion
    if time_of_day:
        extra["time_of_day"] = time_of_day

    result["_ai_extra"] = extra if extra else None
    result["_ai_confidence"] = confidence if isinstance(confidence, dict) else None
    result["_fallback"] = False
    result["_ai_raw"] = raw_text[:500]

    return result


# ── llama-server 自动拉起 ─────────────────────────────────────

_LLAMA_SERVER_EXE = Path("E:/Llama-cpp-12/llama-server.exe")
_LLAMA_MODEL_PATH = Path("E:/Llama-cpp-12/models/Qwythos-9B-Claude-Mythos-5-1M-MTP-Q8_0.gguf")
_LLAMA_MMPROJ_PATH = Path("E:/Llama-cpp-12/models/mmproj-Qwythos-9B-Claude-Mythos-5-1M-F16.gguf")
_LLAMA_PORT = 8080
_LLAMA_HOST = "127.0.0.1"
_LLAMA_HEALTH_URL = f"http://{_LLAMA_HOST}:{_LLAMA_PORT}/health"
_LLAMA_PROC: subprocess.Popen | None = None
_LLAMA_PROC_LOCK = threading.Lock()


def _is_llama_running() -> bool:
    """快速健康检查: llama-server 是否已就绪."""
    try:
        req = urllib.request.Request(_LLAMA_HEALTH_URL, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def _ensure_llama_server() -> bool:
    """确保 llama-server 正在运行；未运行则自动拉起."""
    global _LLAMA_PROC

    if _is_llama_running():
        return True

    with _LLAMA_PROC_LOCK:
        if _is_llama_running():
            return True

        if not _LLAMA_SERVER_EXE.is_file():
            logger.error("llama-server.exe 不存在: %s", _LLAMA_SERVER_EXE)
            return False
        if not _LLAMA_MODEL_PATH.is_file():
            logger.error("模型文件不存在: %s", _LLAMA_MODEL_PATH)
            return False

        _kill_port_owner(_LLAMA_PORT)

        cmd = [
            str(_LLAMA_SERVER_EXE),
            "-m", str(_LLAMA_MODEL_PATH),
            "--mmproj", str(_LLAMA_MMPROJ_PATH),
            "--alias", "qwythos-9b",
            "--temp", "0.3", "--top-p", "0.95", "--top-k", "20", "--min-p", "0.00",
            "--port", str(_LLAMA_PORT), "--host", _LLAMA_HOST,
            "-ngl", "999", "-c", "32768", "-b", "2048", "-ub", "512",
            "-fa", "on", "-ctk", "f16", "-ctv", "f16", "--device", "CUDA0",
            "--parallel", "1",
            "--sleep-idle-seconds", "600",
            "-lv", "1",
        ]

        logger.info("[llama] 正在启动 llama-server: %s", cmd[:4])

        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        try:
            _LLAMA_PROC = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
        except Exception as exc:
            logger.error("[llama] 启动失败: %s", exc)
            return False

    for i in range(120):
        time.sleep(1)
        if _is_llama_running():
            logger.info("[llama] llama-server 就绪 (耗时 ~%ds)", i + 1)
            return True

    logger.error("[llama] llama-server 启动超时 (120s)")
    _LLAMA_PROC = None
    return False


def _kill_port_owner(port: int) -> None:
    """Windows: 杀掉占用指定端口的进程."""
    if os.name != "nt":
        return
    try:
        result = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = parts[-1]
                subprocess.run(
                    ["taskkill", "/PID", pid, "/F"],
                    capture_output=True, timeout=10,
                )
                logger.info("[llama] 已清理端口 %d 占用 (PID %s)", port, pid)
                time.sleep(1)
                break
    except Exception:
        pass


# ── 4 通道流水线 (单素材) ─────────────────────────────────────

def _run_pipeline_for_asset(
    video_path: str,
    duration: float,
    tmpdir: Path,
    client: LocalLLMClient,
    fallback: dict,
    asset_no: str,
) -> dict[str, Any]:
    """对单个素材执行完整 4 通道流水线.

    通道1: 智能抽帧 (scdet 场景检测)
    通道2: 运动分析 (并行, 不依赖帧)
    通道3: OCR 预扫 (依赖帧输出, 可选)
    通道4: LLM 综合打标

    Returns:
        结构化标签字典.
    """
    # ── 通道1: 智能抽帧 ──
    frames = smart_extract_frames(video_path, duration, tmpdir)
    logger.debug("[pipeline:%s] 通道1: %d 帧", asset_no, len(frames))

    if not frames:
        logger.warning("No frames extracted for %s, using rule fallback", asset_no)
        return {**fallback, "_fallback": True, "_ai_raw": "no frames extracted"}

    # ── 通道2: 运动分析 ──
    motion_result = None
    try:
        motion_result = analyze_motion(video_path, duration)
        logger.debug("[pipeline:%s] 通道2: motion=%s speed=%s",
                     asset_no, motion_result.get("motion_level"), motion_result.get("speed_category"))
    except Exception as exc:
        logger.warning("[pipeline:%s] 通道2 失败: %s", asset_no, exc)

    # ── 通道3: OCR 预扫 ──
    ocr_result = None
    try:
        ocr_result = ocr_scan_frames(frames)
        logger.debug("[pipeline:%s] 通道3: lang=%s flag=%s hint=%s",
                     asset_no, ocr_result.get("text_language"),
                     ocr_result.get("has_flag"), ocr_result.get("location_hint"))
    except Exception as exc:
        logger.warning("[pipeline:%s] 通道3 失败: %s", asset_no, exc)

    # ── 通道4: LLM 综合打标 ──
    enriched_prompt = _build_enriched_user_prompt(motion_result, ocr_result)

    try:
        raw = client.chat_with_images(
            image_paths=frames,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=enriched_prompt,
        )
        logger.debug("LLM raw response for %s: %s", asset_no, raw[:300])
        tags = frame_tagging_result(raw, fallback)
    except LocalLLMError as exc:
        logger.error("LLM call failed for %s: %s", asset_no, exc)
        tags = {**fallback, "_fallback": True, "_ai_raw": f"LocalLLMError: {exc}"}

    # 把通道2/3结果注入 ai_tags_extra 供后续查询
    extra = tags.get("_ai_extra") or {}
    if isinstance(extra, dict):
        if motion_result:
            extra["_motion_analysis"] = motion_result
        if ocr_result:
            extra["_ocr_scan"] = ocr_result
        tags["_ai_extra"] = extra if extra else None

    return tags


# ── 核心编排 ─────────────────────────────────────────────────

def _write_asset_tags(asset_id: str, tags: dict, model_name: str) -> bool:
    """将标签写入数据库 (独立 session)."""
    session: Session = get_session_maker()()
    try:
        asset = session.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
        if asset is None:
            logger.error("Asset not found: %s", asset_id)
            return False

        asset.scenes = tags.get("scenes", [])
        asset.shot_types = tags.get("shot_types", [])
        asset.source_type = tags.get("source_type", "footage")
        asset.location = tags.get("location", "foreign")
        asset.people = tags.get("people", "none")
        asset.description_zh = tags.get("description_zh", None)

        asset.ai_tagged_at = datetime.now(timezone.utc)
        asset.ai_tag_model = model_name
        asset.ai_confidence = tags.get("_ai_confidence")
        asset.ai_tags_extra = tags.get("_ai_extra")

        session.commit()
        return True
    except Exception:
        logger.exception("Failed to write tags for asset %s", asset_id)
        session.rollback()
        return False
    finally:
        session.close()


def _run_tagging_job_thread(job_id: str, asset_ids: list[str], model_name: str) -> None:
    """后台线程: 4 通道流水线顺序处理素材打标."""
    with _jobs_lock:
        _jobs[job_id]["status"] = "running"
        _jobs[job_id]["started_at"] = _now_iso()

    cfg = get_config()

    total = len(asset_ids)

    # 自动拉起 llama-server
    if not _ensure_llama_server():
        logger.error("[tagging-job] llama-server 无法启动, 任务中止")
        with _jobs_lock:
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["failed"] = total
            _jobs[job_id]["finished_at"] = _now_iso()
        publish(job_id, {"type": "complete", "done": 0, "failed": total, "total": total,
                         "error": "llama-server 无法启动"})
        return

    client = LocalLLMClient(cfg.local_llm)
    done = 0
    failed = 0

    publish(job_id, {"type": "start", "total": total, "msg": f"开始 AI 打标 (4通道流水线), 共 {total} 个素材"})

    with tempfile.TemporaryDirectory(prefix="tagging_frames_") as tmpdir_str:
        tmpdir = Path(tmpdir_str)

        for aid in asset_ids:
            # 检查取消
            with _jobs_lock:
                if _jobs[job_id].get("cancelled"):
                    _jobs[job_id]["status"] = "cancelled"
                    _jobs[job_id]["finished_at"] = _now_iso()
                    publish(job_id, {"type": "cancelled", "done": done, "failed": failed})
                    return
                job = _jobs[job_id]

            # 加载素材信息
            session: Session = get_session_maker()()
            try:
                asset = session.query(VideoAsset).filter(VideoAsset.id == aid).first()
                if asset is None:
                    failed += 1
                    done += 1
                    with _jobs_lock:
                        _jobs[job_id].update({"done": done, "failed": failed})
                    publish(job_id, {
                        "type": "progress", "done": done, "failed": failed, "total": total,
                        "current_asset_no": f"unknown({aid[:8]})",
                        "msg": f"素材不存在: {aid}",
                    })
                    continue

                asset_no = asset.asset_no
                video_path = asset.file_path
                duration = asset.duration_sec or 10.0
                fallback = infer_tags(
                    asset.raw_query or "",
                    asset.width or 1920,
                    asset.height or 1080,
                )
            finally:
                session.close()

            # 更新当前进度
            with _jobs_lock:
                _jobs[job_id]["current_asset_no"] = asset_no
            publish(job_id, {
                "type": "progress", "done": done, "failed": failed, "total": total,
                "current_asset_no": asset_no,
                "msg": f"正在处理 {asset_no} ({done + 1}/{total}) — 4通道流水线",
            })

            # ── 执行 4 通道流水线 ──
            tags = _run_pipeline_for_asset(
                video_path=video_path,
                duration=duration,
                tmpdir=tmpdir,
                client=client,
                fallback=fallback,
                asset_no=asset_no,
            )

            # ── 写回数据库 ──
            ok = _write_asset_tags(aid, tags, model_name)
            done += 1
            if not ok:
                failed += 1
            elif tags.get("_fallback"):
                failed += 1

            with _jobs_lock:
                _jobs[job_id].update({"done": done, "failed": failed})

            # 清理临时帧文件 (为下一个素材腾空间)
            for f in tmpdir.glob("frame_*.png"):
                try:
                    f.unlink(missing_ok=True)
                except OSError:
                    pass

            publish(job_id, {
                "type": "item_done", "done": done, "failed": failed, "total": total,
                "current_asset_no": asset_no,
                "msg": f"完成 {asset_no} {'✓' if not tags.get('_fallback') else '⚠ 回退规则'}",
            })

    # 完成
    all_failed = failed >= total
    with _jobs_lock:
        _jobs[job_id]["status"] = "failed" if all_failed else "completed"
        _jobs[job_id]["finished_at"] = _now_iso()
        _jobs[job_id].update({"done": done, "failed": failed})

    publish(job_id, {
        "type": "complete",
        "done": done,
        "failed": failed,
        "total": total,
        "msg": f"AI 打标完成: {done} 处理, {failed} 失败/回退",
    })


# ── 公共 API ─────────────────────────────────────────────────

def start_tagging_job(asset_ids: list[str] | None = None) -> str:
    """启动批量 AI 打标后台任务 (4 通道流水线).

    Args:
        asset_ids: 指定素材 ID 列表；为 None 时全量打标.

    Returns:
        job_id, 用于查询进度/取消.
    """
    job_id = uuid.uuid4().hex[:12]

    if asset_ids is None:
        session: Session = get_session_maker()()
        try:
            rows = session.query(VideoAsset.id).all()
            asset_ids = [r[0] for r in rows]
        finally:
            session.close()

    if not asset_ids:
        raise ValueError("没有可打标的素材")

    cfg = get_config()
    model_name = cfg.local_llm.model

    with _jobs_lock:
        _jobs[job_id] = {
            "status": "pending",
            "total": len(asset_ids),
            "done": 0,
            "failed": 0,
            "current_asset_no": None,
            "started_at": None,
            "finished_at": None,
            "cancelled": False,
        }

    t = threading.Thread(
        target=_run_tagging_job_thread,
        args=(job_id, asset_ids, model_name),
        name=f"tagging-{job_id}",
        daemon=True,
    )
    t.start()

    return job_id


def tag_single_asset(asset_id: str) -> dict[str, Any]:
    """同步打标单个素材 (4 通道流水线), 返回完整标签字典.

    Returns:
        tags dict, 含 _success, _fallback, _error 等元信息.
    """
    if not _ensure_llama_server():
        return {"_success": False, "_error": "llama-server 无法启动"}

    cfg = get_config()
    client = LocalLLMClient(cfg.local_llm)
    model_name = cfg.local_llm.model

    session: Session = get_session_maker()()
    try:
        asset = session.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
        if asset is None:
            return {"_success": False, "_error": f"Asset not found: {asset_id}"}
        video_path = asset.file_path
        duration = asset.duration_sec or 10.0
        asset_no = asset.asset_no
        fallback = infer_tags(
            asset.raw_query or "",
            asset.width or 1920,
            asset.height or 1080,
        )
    finally:
        session.close()

    with tempfile.TemporaryDirectory(prefix="tagging_single_") as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        tags = _run_pipeline_for_asset(
            video_path=video_path,
            duration=duration,
            tmpdir=tmpdir,
            client=client,
            fallback=fallback,
            asset_no=asset_no,
        )

    ok = _write_asset_tags(asset_id, tags, model_name)
    tags["_success"] = ok
    tags["_asset_no"] = asset_no
    return tags


def get_job_status(job_id: str) -> dict[str, Any] | None:
    """查询任务状态."""
    with _jobs_lock:
        return _jobs.get(job_id, None).copy() if job_id in _jobs else None


def cancel_job(job_id: str) -> bool:
    """请求取消任务."""
    with _jobs_lock:
        if job_id not in _jobs or _jobs[job_id]["status"] in ("completed", "failed", "cancelled"):
            return False
        _jobs[job_id]["cancelled"] = True
        return True
