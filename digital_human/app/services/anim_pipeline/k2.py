# -*- coding: utf-8 -*-
"""K2 批生图 — 2ST 两段式高清配方 (0911 用户 A/B 裁决定稿 B 档: 纯最爱配方).

配方来源 = 用户最爱图 ComfyUI history (prompt_id 0be3129d, 唯一真相, 保存版
工作流已被后续改动污染不可复刻):
  段1 1280×720 euler/simple 7步 cfg=1 带残留噪声停 → bislerp ×1.5 (1920×1080)
  → 段2 10步表 start_at_step=4 精修 → ColorMatchV2 mkl@0.5 拉回段1 防漂色
B 档 (0911 下午 A/B 实测用户画检胜出): 纯中文场景 + 三关键词风格锚
(日系二次元动漫风格/赛璐璐平涂/清晰线稿), 默认挂白鲸记 NSW LoRA @1.0 (0911 用户令).
负面通道无效 (cfg=1 + ConditioningZeroOut), 防文字靠场景空白化设计 + 中文防字尾 + 人检.
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

from . import brand as brand_mod
from . import comfy, shots as shots_mod
from .config import resolve_style

logger = logging.getLogger(__name__)

# 防字尾 (引擎级禁忌, 不随风格变): K2 全面灭字 — 文字由 H3 视频层/text_layer 补
# 0917 政治敏感画面禁区 (用户令): 地图/旗帜/国徽/领导人画像 — 引擎级物理防尾,
# 词库闸门之外的最后一道, 不依赖 doc 状态
PROTECT_TAIL = ("。画面完全无文字、无数字、无标识，屏幕只保留纯净的空白图形区域，"
                "招牌牌匾一律空白无字。画面中没有地图、没有旗帜、没有国徽、"
                "没有军徽警徽党徽帽徽领章，没有军装警服制式服装，"
                "没有任何政治人物或国家领导人的形象。")
# 风格皮肤随书绑定 (0914 风格随书变令): LoRA/风格锚从 _资产/风格库/ 读, 单一事实源
STYLE = resolve_style  # 延迟到 build 时按书解析


# 构图升级 (0923×3: 英文 BOOST "subject small in frame" 反而缩主体 — 改中文, 对齐角色定妆照成功范式)
COMPOSITION_BOOST = (
    "。画面呈现完整的环境空间，主体人物或物体在画面中占据合适比例，"
    "背景延伸至远方展现广阔视野，前景中景远景三层纵深感清晰可见，"
    "光线从画面深处照射营造空间氛围，整体构图开阔大气"
)


import re as _re

def _clean_scene(scene: str) -> str:
    """K2 提示词清洁工 (0923 用户实锤: 产线图与选型板完全不一致):

    ① 剥英文风格前缀 — LLM 在 keyframe 加 "claymation stop-motion style," 与 K2 风格头
      双重声明, 模型被拉向英文黏土微缩解读 (选型板无此前缀, 画面正常);
    ② 删 hex 色值码 — K2 不解析 #E67E50 等技术色号, 纯噪声稀释;
    ③ 删 "1988赛璐璐" 残留 — 旧风格硬编码漏出。
    """
    s = str(scene or "")
    s = _re.sub(r'^(claymation\s+stop-motion\s+style[,，\s]*)', '', s, flags=_re.I)
    s = _re.sub(r'[（(][^)）]*#[0-9A-Fa-f]{6}[^)）]*[)）]', '', s)  # (陶土暖橘#E67E50色) → 删
    s = _re.sub(r'#[0-9A-Fa-f]{6}', '', s)  # 裸 hex
    s = s.replace('1988赛璐璐', '').replace('赛璐璐卡通', '卡通')
    # 0923 用户实锤: "指纹"致微缩感 (K2 真画出手印 = 沙盘模型), 只删词不删句
    for _fp in ('清晰的手工指纹纹理', '手工指纹纹理', '指纹纹理', '指纹痕迹',
                '手工指纹', '可见指纹', '留着清晰的指纹', '表面有指纹'):
        s = s.replace(_fp, '')
    s = s.replace('指纹', '')  # 兜底裸"指纹"
    # 0923: "手工捏制"风格头已有, 画面句不重复 (双重出现强化微缩感)
    s = s.replace('手工捏制的', '').replace('手工捏制', '')
    # 清悬空句: "…留着，" / "…表面有，" (指纹删后残留)
    for _dang in ('留着，', '表面有，', '表面留着，', '留着清晰，'):
        s = s.replace(_dang, '')
    s = _re.sub(r'[，,][\s，,]*[，,]', '，', s)  # 清理连续逗号
    s = _re.sub(r'^[，,]\s*', '', s)  # 行首逗号
    s = _re.sub(r'[。][。]+', '。', s)  # 连续句号
    return s.strip()


def build_prompt(scene_zh: str, book_title: str = "", style: dict | None = None) -> str:
    """K2 提示词 — Krea2 官方指南范式 (0914 全网学习定稿):

    [风格定调句(仅头一次)] + [画面自然语言长句] + [构图升级] + [防字句] + [轻量收尾锚]
    - 官方: natural language prompts, long detailed prompts 效果最好; 禁标签堆叠
    - 旧结构头尾双风格块把画面夹中间, 同一风格词出现两次稀释主体权重 — 已废
    - 尾部只留构图/质感轻锚, 不再重复风格描述
    - style (0922 风格选择板): 显式配方覆写, 不走书级绑定 (试镜轮询用)
    - COMPOSITION_BOOST (0923): 三层景深+环境空间感 — 治"物体特写幻灯片"
    """
    st = style or resolve_style(book_title)
    scene = _clean_scene((scene_zh or "").strip().rstrip("。"))
    return (st["style_prompt_head"] + scene + COMPOSITION_BOOST
            + PROTECT_TAIL + st["style_prompt_tail"])


def build_workflow(scene_zh: str, seed: int, prefix: str, extra_loras: list[dict[str, Any]] | None = None,
                   book_title: str = "", style: dict | None = None,
                   portrait: bool = False) -> dict[str, Any]:
    """2ST 工作流 (API 格式), 节点 ID 对齐 history 真相图. 默认链 = 书级风格配方的 LoRA.

    style (0922): 显式配方覆写 (风格选择板试镜 — 库成员/Kimi 提案逐个出样张).
    portrait (0923 用户令·定妆照): 竖版 9:16 全身像 — 横版 16:9 必裁人物道具."""
    st = style or resolve_style(book_title)
    if portrait:  # 竖版: 潜空间 720×1280 → bislerp×1.5 → 1080×1920; 配方尾 16:9 同步换竖
        st = dict(st)
        st["style_prompt_tail"] = str(st.get("style_prompt_tail") or "").replace("16:9", "9:16竖幅")
    # 无 LoRA 风格 (库 json lora 显式空): 跳过风格 LoRA 节点, 不回落默认 NSW (0922)
    loras = ([{"name": st["lora"], "strength": float(st.get("lora_strength") or 0.8)}]
             if st.get("lora") else []) + list(extra_loras or [])
    prev = ["262", 0]
    lora_nodes: dict[str, Any] = {}
    for i, lora in enumerate(loras):
        nid = "263" if i == 0 else f"263x{i}"
        lora_nodes[nid] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"lora_name": lora["name"], "strength_model": float(lora["strength"]), "model": prev},
        }
        prev = [nid, 0]

    wf: dict[str, Any] = {
        "262": {"class_type": "UNETLoader", "inputs": {"unet_name": "krea2_turbo_fp8_scaled.safetensors", "weight_dtype": "default"}},
        **lora_nodes,
        "258": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_fp8_scaled.safetensors", "type": "krea2", "device": "default"}},
        "266": {"class_type": "VAELoader", "inputs": {"vae_name": "krea2RealVae_v10.safetensors"}},
        "261": {"class_type": "EmptyLatentImage", "inputs": {
            "width": 720 if portrait else 1280, "height": 1280 if portrait else 720,
            "batch_size": 1}},
        "264": {"class_type": "CLIPTextEncode", "inputs": {"text": build_prompt(scene_zh, book_title, style=st), "clip": ["258", 0]}},
        "259": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["264", 0]}},
        # 段1: 7 步停在带残留噪声的中间态
        "202": {"class_type": "KSamplerAdvanced", "inputs": {
            "add_noise": "enable", "noise_seed": seed, "steps": 7, "cfg": 1.0,
            "sampler_name": "euler", "scheduler": "simple",
            "start_at_step": 0, "end_at_step": 7, "return_with_leftover_noise": "enable",
            "model": prev, "positive": ["264", 0], "negative": ["259", 0], "latent_image": ["261", 0]}},
        "204": {"class_type": "VAEDecode", "inputs": {"samples": ["202", 0], "vae": ["266", 0]}},
        # bislerp ×1.5 潜空间升格 → 1920×1080
        "203": {"class_type": "LatentUpscaleBy", "inputs": {"upscale_method": "bislerp", "scale_by": 1.5, "samples": ["202", 0]}},
        # 段2: 10 步表从 step4 起精修
        "211": {"class_type": "KSamplerAdvanced", "inputs": {
            "add_noise": "enable", "noise_seed": seed, "steps": 10, "cfg": 1.0,
            "sampler_name": "euler", "scheduler": "simple",
            "start_at_step": 4, "end_at_step": 999, "return_with_leftover_noise": "disable",
            "model": prev, "positive": ["264", 0], "negative": ["259", 0], "latent_image": ["203", 0]}},
        "212": {"class_type": "VAEDecode", "inputs": {"samples": ["211", 0], "vae": ["266", 0]}},
        # 段2 高清颜色向段1 锚定 50%
        "253": {"class_type": "ColorMatchV2", "inputs": {
            "method": "mkl", "strength": 0.5, "multithread": True,
            "image_target": ["212", 0], "image_ref": ["204", 0]}},
        "271": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["253", 0]}},
    }
    return wf


_CHAR_LOOKS: dict[str, list] = {}  # book_title → [(name, look, keywords)] (进程缓存)


def _char_looks(book_title: str) -> list:
    """圣经角色锁定卡 → [(name, look, 关键词组)] (0923 确定性注入用)."""
    if book_title not in _CHAR_LOOKS:
        from .director2 import _bible_cache_path
        try:
            b = json.loads(_bible_cache_path(book_title).read_text(encoding="utf-8"))
            _CHAR_LOOKS[book_title] = [
                (str(c.get("name") or ""), str(c.get("look") or ""),
                 [w.strip() for w in str(c.get("look") or "").replace("，", "+").split("+")
                  if len(w.strip()) >= 3])
                for c in (b.get("characters") or []) if c.get("name") and c.get("look")]
        except Exception:  # noqa: BLE001
            _CHAR_LOOKS[book_title] = []
    return _CHAR_LOOKS[book_title]


def _inject_char_looks(scene: str, book_title: str) -> str:
    """出场角色 look 串确定性前置 (0923 用户实锤 货不对版: 规划层 LLM 只带名字丢造型).

    命中: 角色名在画面句且 look 关键词缺失 → 前置 "角色名（look 全串），" —
    同试渲调味验证过的人物前置模式 (主体权重最高, 原句不稀释)。"""
    for name, look, kws in _char_looks(book_title):
        if name and name in (scene or "") and not any(k in (scene or "") for k in kws[:3]):
            return f"{name}（{look}），" + (scene or "")
    return scene or ""


def run_shot(shot: dict[str, Any], doc: dict[str, Any]) -> Path:
    """跑单镜 K2, 产物 move 到管线目录 img/{shot_id}.png, 状态 → img_done.

    0922 文字守门 (用户令: K2 文字生成是垃圾, 只准图形): 出图后 OCR 检字,
    命中换种子重掷 1 次, 仍脏 shot.text_suspect=True 交人检。
    0923 角色注入: 画面句含角色名但缺 look → 渲染前确定性补串 (货不对板根治)."""
    out_dir = shots_mod.ep_dir(doc["book_title"], doc["ep"]) / "img"
    dest = out_dir / f"{shot['shot_id']}.png"
    prefix = f"anim/{shots_mod._safe(doc['book_title'])}/ep{doc['ep']}/k2/{shot['shot_id']}"
    scene_eff = _inject_char_looks(str(shot.get("image_prompt_zh") or ""), doc["book_title"])
    dirty = render_gated(
        lambda sd: build_workflow(scene_eff, sd, prefix,
                                  shot.get("extra_loras"), book_title=doc["book_title"]),
        dest, int(shot.get("seed") or 0), f"k2 {shot['shot_id']}")
    if dirty:
        shot["text_suspect"] = True
    shot["image_file"] = f"img/{shot['shot_id']}.png"
    shot["attempts"]["k2"] += 1
    shots_mod.transition(shot, "img_done")
    return dest


# ── 文字守门 (0922 用户令: 所有生图必须压住文字 — K2 出字即垃圾, 只生成图形) ──

_OCR: Any = None  # 缓存引擎; False = 不可用 (跳过守门)


def _ocr_engine():
    global _OCR
    if _OCR is None:
        try:
            from app.services.material_ingest_service import _new_ocr
            _OCR = _new_ocr()
        except Exception as exc:  # noqa: BLE001
            logger.warning("[k2] OCR 守门不可用 (跳过检字): %s", exc)
            _OCR = False
    return _OCR or None


def _ocr_dirty(png: Path) -> bool:
    """图内检出可信文字 (过滤 <2% 尺寸噪点) → True."""
    ocr = _ocr_engine()
    if ocr is None:
        return False
    try:
        import numpy as np
        from PIL import Image
        im = Image.open(png).convert("RGB")
        w, h = im.size
        result, _ = ocr(np.array(im))
        for box, txt, score in (result or []):
            if float(score) < 0.55:
                continue
            ys = [p[1] for p in box]
            xs = [p[0] for p in box]
            if (max(ys) - min(ys)) >= 0.02 * h and (max(xs) - min(xs)) >= 0.02 * w:
                logger.warning("[k2] 检字命中: '%s' %.2f @%s", str(txt)[:20], score, png.name)
                return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("[k2] OCR 守门异常 (放行): %s", exc)
    return False


def _vlm_dirty(png: Path) -> str | None:
    """VLM 兜底 (0923 用户双实锤: 试渲_1 伪文字 + 试渲_3 各国国旗): 正向提示词压不住的
    都靠这道 — K2 风格化乱字 OCR 读不出 (假阴性), 国旗国徽正向禁令无效。
    glm-4v-flash 一次查: 文字/国旗/国徽/地图/政治人物。返回违禁简述或 None。"""
    try:
        import base64
        import io as _io
        from PIL import Image
        from app.services.reverse_prompt_service import _chat as _vlm_chat
        im = Image.open(png).convert("RGB")
        if im.width > 960:
            im = im.resize((960, int(im.height * 960 / im.width)))
        buf = _io.BytesIO()
        im.save(buf, "JPEG", quality=80)
        b64 = base64.b64encode(buf.getvalue()).decode()
        out = _vlm_chat(
            "data:image/jpeg;base64," + b64,
            "仔细看这张动画画面, 逐项检查: "
            "①任何可见的文字/字母/数字/汉字 (含招牌/匾额/标签/屏幕上的伪文字乱码) "
            "②任何国家的国旗 ③国徽/军徽/警徽/党徽/帽徽/领章 ④地图 ⑤军装警服制式元素 ⑥政治人物或国家领导人形象。"
            '只输出 JSON: {"violations": ["文字"/"国旗"/"国徽"/"地图"/"政治人物"], "what": "简述位置"} '
            '— 全无则 {"violations": [], "what": ""}', max_tokens=96)
        m = re.search(r'"violations"\s*:\s*\[([^\]]*)\]', out or "")
        if m and m.group(1).strip():
            return m.group(1)[:80]
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("[k2] VLM 违禁兜底不可用 (放行): %s", exc)
        return None


_HARD_VIOLATIONS = ("国旗", "国徽", "党徽", "军徽", "警徽", "军装", "警服", "领导人", "地图", "政治人物")


def render_gated(seed_to_wf, dest: Path, seed: int, label: str, *, retries: int = 1) -> bool:
    """出图 + 违禁守门双道: seed_to_wf(seed) 产工作流; 命中换 seed+1 重掷。

    第一道 OCR (真文字, 毫秒级); 第二道 VLM (伪文字/国旗/国徽/地图/政治人物, 秒级)。
    分级处置 (0923 用户实锤 国旗+国徽双中):
    - 文字类 (软, 质量问题): 重掷后仍脏 → 保留 + 返回 True 交人检;
    - 政治类 (硬, 抖音红线): **绝不落盘** — 重掷到额度用尽仍脏 → 恢复旧图或删图, True。
    判定器不可用自动放行。"""
    prev = dest.read_bytes() if dest.exists() else None
    hard = False
    for attempt in range(retries + 1):
        wf = seed_to_wf(seed + attempt)
        comfy.run_workflow(wf, dest=dest, timeout_sec=300, label=f"{label}#{attempt}")
        # 0923 修: VLM 永远跑 — OCR 先脏会短路跳过 VLM, 国徽漏检实锤 (红色制服+徽章诱导)
        vbad = _vlm_dirty(dest)
        hard = bool(vbad) and any(h in str(vbad) for h in _HARD_VIOLATIONS)
        if not (vbad or _ocr_dirty(dest)):
            return False
        logger.warning("[k2] 违禁守门重掷 (%s 第%d次, %s%s)", label, attempt + 1,
                       vbad or "OCR文字", " [硬·政治]" if hard else "")
    if hard:
        if prev is not None:  # 政治红线: 脏图绝不留 — 有旧图恢复旧图, 无旧图删脏图
            dest.write_bytes(prev)
            logger.warning("[k2] 硬违禁未通过, 已恢复上一版: %s", dest.name)
        else:
            dest.unlink(missing_ok=True)
            logger.warning("[k2] 硬违禁未通过且无旧版, 弃图: %s", dest.name)
    return True


def run_batch(doc: dict[str, Any], only: set[str] | None = None,
              on_shot_done: Any = None, stop_check: Any = None) -> dict[str, int]:
    """批跑所有 planned 镜 (串行, GPU 独占). 返回 {ok, fail}. 每镜落盘断点续跑.

    on_shot_done(shot_id, done, total): 每镜后回调 (服务层进度 SSE).
    stop_check(): 镜间返回 True 即停止 (协作取消).
    品牌卡镜零 GPU 直通: image_file=定妆 keyframe, 状态直接 img_done.
    """
    ok = fail = 0
    pending = sum(
        1 for s in doc["shots"]
        if s["status"] == "planned" and (only is None or s["shot_id"] in only)
    )
    logger.info("[k2] 待跑 %d 镜 (2ST 配方, ~15s/镜)", pending)
    done = 0
    for shot in doc["shots"]:
        if only is not None and shot["shot_id"] not in only:
            continue
        if shot["status"] != "planned":
            continue
        if stop_check and stop_check():
            logger.info("[k2] 协作取消: 已处理 %d/%d, 停止", done, pending)
            break
        try:
            if shot.get("brand_card"):
                shot["image_file"] = brand_mod.resolve(doc["book_title"], doc["ep"], "keyframe")
                shots_mod.transition(shot, "img_done")
                logger.info("[k2] %s 品牌卡直通 (零 GPU, 首帧=定妆 keyframe)", shot["shot_id"])
            else:
                p = run_shot(shot, doc)
                logger.info("[k2] %s done %s (%d ok / %d fail)", shot["shot_id"], p.name, ok, fail)
                time.sleep(1.0)
            ok += 1
        except Exception as exc:  # noqa: BLE001 — 单镜失败不断批
            fail += 1
            shot["error"] = f"k2: {exc}"[:500]
            logger.error("[k2] %s 失败: %s", shot["shot_id"], exc)
        shots_mod.save(doc)
        done += 1
        if on_shot_done:
            try:
                on_shot_done(shot["shot_id"], done, pending)
            except Exception:  # noqa: BLE001 — 回调异常不炸批
                logger.warning("[k2] 进度回调异常", exc_info=True)
    return {"ok": ok, "fail": fail}
