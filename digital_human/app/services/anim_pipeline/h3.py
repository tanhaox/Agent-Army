# -*- coding: utf-8 -*-
"""H3 批生视频 — 节拍式提示词壳 (用户最爱视频 f8050007 配方, 2026-09-11 用户画检认证).

图 = fl2va pruned int8 + v4_step600 turbo 4步 sigma, 1024 最长边, 无音频, 热 ~102s/10s.
提示词壳 = 用户终版胜出结构 (比我 0911 单拍实证版高一档):
  首帧对齐行 + Identity lock + 屏显例外 + Physical lock 全程段
  + 多拍时间轴 (每拍 "continuing from the previous beat" 衔接, 每拍句尾无人声否定)
  + soundscape 静音底噪 (不是 N/A) + music N/A
拍结构由规划器产出 (beats), 壳由代码拼 — LLM 只填内容不发明结构.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from . import brand as brand_mod
from . import comfy
from . import shots as shots_mod
from .config import load, resolve_style

logger = logging.getLogger(__name__)

# 全程生命条款 (0915 三层模型定稿: 第2层动画层 = 已有物品尽管动, 纹理稳定防抖)
# 旧版"无风无粒子"是吉普力水彩全屏抖动的补丁, 误伤赛璐璐物品动效 — 改为动效+纹理分离
AMBIENT_LIFE = (
    "Objects already present in the frame may move naturally: cars driving, people walking, "
    "smoke rising, flags waving, water rippling, lights shifting. The flat cel-shaded colors "
    "and clean line art remain perfectly stable, no texture shimmer."
)
# 文字层承接 (0915 定稿: 中文优先 + 字体纪律): 首帧全灭字不变; 动画中文字出场 —
# 关键词用中文短词(2-4字), 数字/年份/标志保持数字与拉丁字母; 每镜一种艺术字体风格
# (书法/手写/复古装饰/描边立体), 禁平淡黑体; 落点避让主体不压字。
# 0915 s02 招牌幻觉首例已记录观察 (复发率采样中, 用户令暂不修 — docs 观察 ledger);
# 若复发率坐实再上反幻觉条款。
TEXT_POLICY = (
    "The first frame contains no text. AT MOST ONE text element may appear in the whole "
    "video, only as specified in the beats: render exactly the specified words, large and "
    "bold. Chinese text is limited to ultra-short words (2 characters); longer Chinese "
    "phrases are NEVER rendered in-video (they are added in post-production). Digits, "
    "years and brand logos stay as digits/Latin. Two text elements NEVER coexist or "
    "overlap in the same shot. "
    "Use ONE consistent artistic typography style (calligraphy, brush, retro decorative, "
    "or outlined dimensional lettering) — never plain sans-serif/heiti. "
    "Position text clear of the main subject's face and key objects. "
    "All in-video Chinese characters MUST be Simplified Chinese (简体字) exactly as "
    "specified in the beats; Traditional Chinese glyphs (繁體) are FORBIDDEN — they "
    "deform and break during animation. "
    "Anti-hallucination: surfaces that would normally carry text — signboards, door "
    "plates, billboards, screens, cards, newspapers — must remain exactly as blank as in "
    "Picture 1; never invent, add, or fill in any text, characters, numbers, or glyphs "
    "anywhere. No captions, watermarks, or UI."
)
SOUNDSCAPE = (
    "Silent video, ambient room tone only at a barely audible level. "
    "No human voice of any kind."
)


def style_h3(book_title: str = "") -> str:
    """H3 风格锚 — 从书级风格配方读 (风格随书变, 单一事实源同 K2).

    0919 隐形bug根治: "Traditional ... style" 会被模型读成 Traditional Chinese —
    中文文字出场漂成繁体, 繁体笔画动画易错 (用户实锤)。出口统一净化为 hand-drawn。
    """
    s = resolve_style(book_title).get("h3_style") or (
        "1988 hand-drawn cel animation style, clean line art, flat vivid colors, sharp cel-shading")
    return re.sub(r"(?i)\btraditional\b", "hand-drawn", s)


def _ts(t: float) -> str:
    """秒 → [00:02.5] 节拍时间戳格式."""
    return f"[00:{t:04.1f}]"


def build_prompt(anim: dict[str, Any], book_title: str = "") -> str:
    beats = anim["beats"]
    lines = [
        "integrated_multimodal_description:",
        f"[Shot 1] {style_h3(book_title)}. At 0.00 seconds the frame fully matches Picture 1: "
        f"{anim['opening_desc'].strip()}. Identity lock: keep all characters' faces, "
        "hair, and outfits consistent with Picture 1.",
        "",
        f"Physical lock for the whole video: {anim['physical_lock'].strip()} — "
        "the camera viewpoint stays locked to Picture 1; only a very slight push-in or "
        "pull-back is allowed; strictly no lateral panning or tracking; no large-area "
        "repaint of the scene (no costumes or objects morphing into different shapes).",
        "",
        AMBIENT_LIFE,
        "",
        TEXT_POLICY,
        "",
    ]
    # 0919 字级钉死 (s66 实锤: 风格净化+简体令后仍漂「誰」— 提示词层泛指令劝不住):
    # beats 将上屏的中文字符逐个圈出点名照抄 — 模型对"面前摆着的字形"服从性最高
    _cjk: list[str] = []
    for _b in beats:
        for _ch in str(_b.get("motion") or ""):
            if "一" <= _ch <= "鿿" and _ch not in _cjk:
                _cjk.append(_ch)
    if _cjk:
        lines.append(
            "Glyph lock: the ONLY Chinese glyphs permitted in this video are these exact "
            f"simplified characters, copied stroke-for-stroke: {'、'.join(_cjk[:32])}. "
            "Write 谁 with the simplified speech radical 讠 (never 誰), 买 not 買, "
            "钱 not 錢, 书 not 書, 门 not 門. A single traditional glyph ruins the frame.")
        lines.append("")
    for i, b in enumerate(beats):
        motion = b["motion"].strip()
        ending = (anim.get("ending") or "").strip()
        if i == len(beats) - 1 and ending:
            # 规划器常把结尾复述进末拍, 已含则不重复追加
            if ending[:60].lower() not in motion.lower():
                motion = f"{motion} {ending}"
        chain = "" if i == 0 else "continuing from the previous beat — "
        lines.append(
            f"From {_ts(float(b['t_start']))} to {_ts(float(b['t_end']))}, "
            f"{chain}{motion} No human voice of any kind."
        )
    lines += [
        "",
        "overall_soundscape:",
        SOUNDSCAPE,
        "",
        "non_diegetic_music:",
        "N/A",
    ]
    # 0919 出口整段净化: 旧镜 anim 字段 (opening_desc/beats) 规划时已烙
    # "traditional" 风格词 — 连根拔 (只动英文单词, 不碰中文正文)
    return re.sub(r"(?i)\btraditional\b", "hand-drawn", "\n".join(lines))


def build_workflow(image_name: str, anim: dict[str, Any], seed: int, prefix: str,
                   book_title: str = "") -> dict[str, Any]:
    """H3 I2V 工作流 (API 格式), 节点 ID 对齐最爱视频真相图 (102.4s/10s)."""
    return {
        "129": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "minimax_it2v\\minimax_h3_fl2va_pruned_int8_convrot.safetensors",
            "weight_dtype": "default"}},
        "348": {"class_type": "ModelAttentionBackend", "inputs": {
            "attention": "comfy kitchen attention", "model": ["129", 0]}},
        "244": {"class_type": "MiniMaxLowVRAMAttention", "inputs": {
            "head_chunks": 10, "model": ["348", 0]}},
        "243": {"class_type": "MiniMaxChunkFeedForward", "inputs": {
            "chunks": 2, "seq_threshold": 4096, "model": ["244", 0]}},
        "341": {"class_type": "Power Lora Loader (rgthree)", "inputs": {
            "PowerLoraLoaderHeaderWidget": {"type": "PowerLoraLoaderHeaderWidget"},
            "lora_1": {"on": False, "lora": "H3\\minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors", "strength": 1},
            "lora_2": {"on": False, "lora": "H3\\NaughtyTimes_pruned_r128_v2.safetensors", "strength": 0.8},
            "lora_3": {"on": True, "lora": "H3\\minimax_h3_turbo_v4_step600_ema_pruned_comfyui.safetensors", "strength": 1},
            "lora_4": {"on": False, "lora": "H3\\MiniMax H3  AI Girl Fictional Women Series30.safetensors", "strength": 1},
            "lora_5": {"on": False, "lora": "H3\\H3_Motion_Booster.safetensors", "strength": 0.2},
            "lora_6": {"on": False, "lora": "H3\\HMNSFW_AIO_V2.safetensors", "strength": 0.3},
            "lora_7": {"on": False, "lora": "H3\\VBVR_H3_attn_only.safetensors", "strength": 0.5},
            "➕ Add Lora": "", "model": ["243", 0]}},
        "130": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "minimax\\qwen3vl_32b_minimax_h3_int8_convrot.safetensors",
            "type": "minimax", "device": "default"}},
        "121": {"class_type": "VAELoader", "inputs": {
            "vae_name": "minimax\\minimax_h3_video_vae_fp16.safetensors"}},
        "122": {"class_type": "VAELoader", "inputs": {
            "vae_name": "minimax\\minimax_h3_audio_vae_fp32.safetensors"}},
        "114": {"class_type": "LoadImage", "inputs": {"image": image_name}},
        "136": {"class_type": "LayerUtility: ImageScaleByAspectRatio V2", "inputs": {
            "aspect_ratio": "original", "proportional_width": 1, "proportional_height": 1,
            "fit": "crop", "method": "lanczos", "round_to_multiple": "32",
            "scale_to_side": "longest", "scale_to_length": 1024,
            "background_color": "#000000", "image": ["114", 0]}},
        "187": {"class_type": "PrimitiveStringMultiline", "inputs": {"value": build_prompt(anim)}},
        "135": {"class_type": "PrimitiveFloat", "inputs": {"value": float(anim["duration_s"])}},
        "134": {"class_type": "ComfyMathExpression", "inputs": {
            "expression": "max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17",
            "values.a": ["135", 0]}},
        "133": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {
            "clip": ["130", 0], "vae": ["121", 0], "prompt": ["187", 0],
            "first_frame": ["136", 0], "width": ["136", 3], "height": ["136", 4],
            "length": ["134", 1]}},
        "128": {"class_type": "BasicGuider", "inputs": {
            "model": ["341", 0], "conditioning": ["133", 0]}},
        "131": {"class_type": "RandomNoise", "inputs": {
            "noise_seed": seed, "control_after_generate": "fixed"}},
        "221": {"class_type": "MiniMaxH3TurboSampler", "inputs": {}},
        "361": {"class_type": "ManualSigmas", "inputs": {
            "sigmas": "1.0, 0.95, 0.88, 0.75, 0.55, 0.3, 0.0"}},  # 4步档 (蒸馏实证 4≈6≈8)
        "127": {"class_type": "SamplerCustomAdvanced", "inputs": {
            "noise": ["131", 0], "guider": ["128", 0], "sampler": ["221", 0],
            "sigmas": ["361", 0], "latent_image": ["133", 1]}},
        "124": {"class_type": "VAEDecode", "inputs": {"samples": ["127", 0], "vae": ["121", 0]}},
        "138": {"class_type": "VHS_VideoCombine", "inputs": {
            "images": ["124", 0], "frame_rate": 24, "loop_count": 0,
            "filename_prefix": prefix, "format": "video/h264-mp4", "pix_fmt": "yuv420p",
            "crf": 19, "save_metadata": True, "trim_to_audio": False,
            "pingpong": False, "save_output": True}},
    }


def run_shot(shot: dict[str, Any], doc: dict[str, Any]) -> Path:
    """跑单镜 H3: 上传 K2 图 → I2V → mp4 move 到 anim/{shot_id}.mp4, 状态 → anim_done.

    0916 生成时长=语音长度铁律 (用户实锤: 旧 beats 出长片 → 装配截前段 →
    尾部文字/视觉事件陪葬 + 白烧 GPU): 开跑前强制 beats=槽 (漂移自动拉齐)."""
    base_dir = shots_mod.ep_dir(doc["book_title"], doc["ep"])
    _span = float(shot["t_end"]) - float(shot["t_start"])
    _anim = shot.get("anim") or {}
    if isinstance(_anim, dict) and _span > 0 and abs(
            float(_anim.get("duration_s") or 0) - _span) > 0.05:
        shots_mod.stretch_beats(shot, min(round(_span, 2), 10.0))
        logger.warning("[h3] %s beats 漂移已拉齐到槽 %.2fs (生成时长=语音长度)",
                       shot["shot_id"], min(round(_span, 2), 10.0))
    src_img = base_dir / shot["image_file"]
    if not src_img.exists():
        raise comfy.ComfyRunError(f"首帧图不存在: {src_img}")
    image_name = comfy.upload_image(src_img)
    dest = base_dir / "anim" / f"{shot['shot_id']}.mp4"
    prefix = f"video/anim/{shots_mod._safe(doc['book_title'])}/ep{doc['ep']}/{shot['shot_id']}"
    wf = build_workflow(image_name, shot["anim"], shot["h3_seed"], prefix,
                        book_title=doc["book_title"])
    # 10s 热机 ~102s, 冷机翻倍, 留余量; 0919 实锤: 长镜 (6.9-8.8s) 在低显存节点
    # 帧数放大超线性, 600s 定额连杀 s11/s12/s21 两轮 (ComfyUI 实际都跑完了,
    # 产物躺 output 成孤儿) — 超时按时长伸缩
    # 0920 ep5 s41 实锤: 同尺寸 latent 一次显存布局病爬到 29min (1740s) 后自愈,
    # 后续同尺寸 52s — 爬行是暂态不是固有; 90/s 系数 (1069s) 必杀暂态爬行,
    # 提到 240/s (5.2s 镜 → 1852s) 让一次性爬行能自完成, 少一轮重试孤儿
    _cfg = load()
    comfy.run_workflow(wf, dest=dest, timeout_sec=600 + int(240 * min(_span, 10.0)),
                       label=f"h3 {shot['shot_id']}",
                       soft_timeout_sec=_cfg.comfy.soft_timeout_sec,
                       interrupt_grace_sec=_cfg.comfy.interrupt_grace_sec)
    shot["video_file"] = f"anim/{shot['shot_id']}.mp4"
    # 0916 错配溯源: 生成时文案指纹 (归真/重规划改写 narration 后, 旧视频=内容错配
    # — 拆镜父镜继承实锤; 草稿装配对不上指纹即亮灯)
    import hashlib as _h
    shot["gen_narr_sha"] = _h.md5(
        shots_mod.norm_for_match(shot.get("narration") or "").encode("utf-8")).hexdigest()[:10]
    shot["attempts"]["h3"] += 1
    shot["error"] = None
    shots_mod.transition(shot, "anim_done")
    return dest


def run_batch(doc: dict[str, Any], only: set[str] | None = None, retry_failed: bool = False,
              on_shot_done: Any = None, stop_check: Any = None) -> dict[str, int]:
    """批跑 approved 镜 (--retry-failed 连 anim_fail 一起重试, 换 h3_seed).

    on_shot_done/stop_check 同 k2.run_batch (服务层进度 + 协作取消).
    品牌卡镜零 GPU 直通: video_file=定稿品牌卡 mp4, 状态直接 anim_done.
    """
    ok = fail = 0
    pending = sum(
        1 for s in doc["shots"]
        if (only is None or s["shot_id"] in only)
        and (s["status"] == "approved" or (retry_failed and s["status"] == "anim_fail"))
    )
    done = 0
    for shot in doc["shots"]:
        if only is not None and shot["shot_id"] not in only:
            continue
        runnable = shot["status"] == "approved" or (retry_failed and shot["status"] == "anim_fail")
        if not runnable:
            continue
        if stop_check and stop_check():
            logger.info("[h3] 协作取消: 已处理 %d/%d, 停止", done, pending)
            break
        if shot["status"] == "anim_fail":
            shots_mod.audit_reroll(doc, shot, "anim_fail重试")
            shots_mod.retry_anim(shot)
        try:
            if shot.get("brand_card"):
                # 0920 定稿: 品牌卡镜一律零 GPU 直通插定稿资产 (用户令修"品牌卡
                # 被对齐冲掉"死循环). 旧 0916 山脊骨架例外 (骨架注入→逐镜生成) 已废:
                # 槽长差额由草稿端仪式句锚定+首尾定格吸收, 品牌镜不再烧 GPU.
                shot["video_file"] = brand_mod.resolve(doc["book_title"], doc["ep"], "video")
                shot["error"] = None
                shots_mod.transition(shot, "anim_done")
                logger.info("[h3] %s 品牌卡直通 (零 GPU, 插定稿卡)", shot["shot_id"])
            else:
                run_shot(shot, doc)
                logger.info("[h3] %s done", shot["shot_id"])
            ok += 1
        except Exception as exc:  # noqa: BLE001 — 单镜失败不断批, 降级=静态图已在位
            fail += 1
            shot["error"] = f"h3: {exc}"[:500]
            shots_mod.transition(shot, "anim_fail")
            logger.error("[h3] %s 失败(降级用静态图): %s", shot["shot_id"], exc)
        shots_mod.save(doc)
        done += 1
        if on_shot_done:
            try:
                on_shot_done(shot["shot_id"], done, pending)
            except Exception:
                logger.warning("[h3] 进度回调异常", exc_info=True)
    return {"ok": ok, "fail": fail}
