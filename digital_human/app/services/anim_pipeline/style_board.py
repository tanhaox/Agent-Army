"""风格选择板 (0922 用户令) — 书级动画风格选型: 真内容试镜 + 库轮询 + Kimi 新配方提案.

决策链: 总纲完成 → [讲书页·🎨 风格选型] → ep1 钩子段切 3 试镜镜 →
风格库全员 + Kimi 提案新配方, 样张**全走本地 K2** (选中即可产 — Kimi 只出配方文本,
防"样张≠产线能力": 云端画的风格本地 LoRA/模型链复现不出) →
选择板 (镜头×风格 网格) → 点选落绑定 (选新风格自动入库: json + 参考图)。
开工硬挡板见 anim_service.start_phase (无绑定拒跑)。

公平性: 同镜同种子 (只比风格不赌种子); 渲染串行占 GPU 锁 (与 k2/h3 批互斥)。
"""
from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from . import comfy
from .config import DEFAULT_STYLE_NAME, _safe_name, load
from .k2 import build_workflow, render_gated

logger = logging.getLogger(__name__)

_LORA_DIR = Path(r"E:/AI/ComfyUI_windows_portable/ComfyUI/models/loras/Krea2-风格")
_BOARD_SEED = 20260922  # 试镜固定种子基 (同镜同种子跨风格公平比)

_JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()

_SHOTS_SYS = (
    "你是动画试镜规划器。给定书的第一集总纲与灵魂三问, 规划 3 个试镜画面 (供动画风格选型用): "
    "①钩子镜 — 第一集最强情绪的画面化 ②人物镜 — 贯穿人物在关键处境中的一个定格 "
    "③概念镜 — 核心概念具象化成的场景。三镜画面互不重复、各代表一种镜头类型。"
    "**红线: 全链卡通大品类 — 画面主体 (含人物) 一律以卡通/动画形象呈现, 禁真人写实、禁照片感**。"
    "**丰富度规格 (0922 用户令, 全书出图以此为基准)**: 画面句必须高元素密度 — "
    "主体+配角/道具+环境细节+光线层次都要落字; 人物**必须露脸带表情** (禁无脸/背影/剪影), "
    "**服饰细节到位且能区分人物关系** (身份/阵营/地位靠服装一眼可辨, 写明具体单品)。"
    "image_prompt_zh 为 K2 文生图用中文自然语言长句: 主体+动作+场景+构图+光线, "
    "画面里**禁任何文字/字幕/招牌/品牌**。输出严格 JSON: "
    '{"shots":[{"name":"短名","image_prompt_zh":"画面长句"}]}; 恰好 3 镜。'
)

_PROPOSE_SYS = (
    "你是动画风格配方设计师。给定书题材、试镜画面、风格库现有成员与可用 LoRA 清单, "
    "提案**若干个互不相同的新风格配方** — 每个与库内现有成员及彼此明显差异化 "
    "(品类/线条/上色/质感至少三维不同)。"
    "【已排除风格】= 用户不喜欢**那个具体配方** (可能只是执行/人物形态不对), "
    "**不封杀品类方向** — 同方向换个执行再来合法 (如 2D 版被排除, 出一版 3D 锚定的同方向是最佳状态); "
    "仅同名配方不得再出。军规: "
    "①卡通大类红线 (0922 用户令): 一切画面主体 (含人物) 必须是卡通/动画形象 — "
    "禁真人写实、禁照片感、禁写实人脸、禁 3D 超写实人像, 风格词里禁出现 真人/写实/照片/realistic; "
    "②适配该书题材与受众 (老谭读书·商业拆书, 观众要看得懂画面里的商业场景); "
    "③K2 引擎可执行, 提示词遵守 K2 家规 (违反即废): "
    "style_prompt_head = **一句定调 ≤60字** (风格名+2~3个核心质感词, 以冒号结尾) — 禁长串堆砌; "
    "**head 必须锚定人物形态** (明确 2D平面动画人物/3D卡通人物/Q版三选一 — 只锚质感不锚人物形态, "
    "同风格内人物会一会2D一会3D); "
    "style_prompt_tail = **轻锚 ≤40字** (构图+16:9+至多一个质感词); "
    "**同一风格词禁在头尾出现两次** (重复稀释主体权重); "
    "质感词总量 ≤5 — 堆砌互相打架画面会脏, 画面要经得起放大看 (线条干净/上色利落); "
    "④画面禁文字元素 (防幻觉字); ⑤h3_style 为英文一句 (图生视频一致性用); "
    "⑥lora 只能从清单内选一个文件名, 或 null (纯提示词方案 — 同样合法)。"
    "输出严格 JSON: "
    '{"proposals":[{…}, …]} — 恰好按要求数量给, 逐个字段: '
    '{"name":"短英文名","desc":"中文说明: 设计理由+预期效果+与库内差异点",'
    '"style_prompt_head":"…：","style_prompt_tail":"…16:9…",'
    '"h3_style":"english one sentence","lora":"清单内文件名或null","lora_strength":0.6}'
)

# 0923 宪法进每个入口 (用户令): 画面宪法统一注入 试镜镜/提案/重调 三个 sys —
# 改 compliance_visual.json 即全部同步 (源头规避, VLM/OCR 守门只是兜底)
try:
    from app.services.compliance import visual_constitution_prompt as _vcp
    _VISUAL_LAW = _vcp()
except Exception:  # noqa: BLE001 — 宪法加载失败不炸模块, 空块=只靠下游守门
    _VISUAL_LAW = ""
_SHOTS_SYS += _VISUAL_LAW
_PROPOSE_SYS += _VISUAL_LAW


# ── 路径 ─────────────────────────────────────────────────────

def _assets() -> Path:
    return Path(load().output_root) / "_资产"


def _board_dir(book_title: str) -> Path:
    return _assets() / "风格选型" / _safe_name(book_title)


def _binding_path(book_title: str) -> Path:
    return _assets() / f"风格绑定_{_safe_name(book_title)}.json"


def _excl_path(book_title: str) -> Path:
    return _board_dir(book_title) / "排除.json"


def exclusions(book_title: str) -> list[str]:
    try:
        return list(json.loads(_excl_path(book_title).read_text(encoding="utf-8"))["styles"])
    except Exception:  # noqa: BLE001
        return []


def set_exclusion(book_title: str, name: str, on: bool) -> list[str]:
    """排除/恢复 (0922 用户令): 排除后该书再选型不再入板, Kimi 提案补位且避开该方向."""
    cur = [s for s in exclusions(book_title) if s != name]
    if on:
        cur.append(name)
    _board_dir(book_title).mkdir(parents=True, exist_ok=True)
    _excl_path(book_title).write_text(
        json.dumps({"styles": cur}, ensure_ascii=False, indent=1), encoding="utf-8")
    return cur


def bound_style(book_title: str) -> str | None:
    p = _binding_path(book_title)
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("style")
    except Exception:  # noqa: BLE001
        return None


# ── LLM 步 ───────────────────────────────────────────────────

def _llm():
    from app.services.book_service.creation_common import _llm as _get
    return _get()


def _parse(raw: str) -> dict:
    from app.services.book_service.creation_common import _parse_json
    return _parse_json(raw)


def _plan_shots(material: dict) -> list[dict]:
    raw = _llm().chat(_SHOTS_SYS, json.dumps(material, ensure_ascii=False),
                      model="pro", temperature=0.4)
    shots = _parse(raw).get("shots") or []
    shots = [s for s in shots if isinstance(s, dict) and (s.get("image_prompt_zh") or "").strip()]
    if not 2 <= len(shots) <= 3:
        raise RuntimeError(f"试镜镜规划异常: 得 {len(shots)} 镜 (须 2-3)")
    return shots[:3]


def _library_styles() -> list[dict]:
    lib = _assets() / "风格库"
    out: list[dict] = []
    for p in sorted(lib.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception as exc:  # noqa: BLE001
            logger.warning("[style-board] 库成员坏跳过 %s: %s", p.name, exc)
    return out


# 卡通红线确定性守门 (0922 用户令): 不靠 LLM 自觉 — 提示词字段含真人系词即弃
_BANNED_STYLE_WORDS = ("真人", "写实", "照片", "photoreal", "realistic", "real person", "realistic face")


def _banned(recipe_text: str) -> str | None:
    t = recipe_text.lower()
    return next((w for w in _BANNED_STYLE_WORDS if w.lower() in t), None)


def _propose_n(material: dict, shots: list[dict], styles: list[dict],
               excl: list[str], n: int) -> list[dict]:
    """Kimi 提案 ×N (0922 排除补位): 被排除风格由新提案顶替, 且提案避开排除方向."""
    loras = sorted(p.name for p in _LORA_DIR.glob("*.safetensors")) if _LORA_DIR.exists() else []
    lib_brief = "\n".join(
        f"- {s.get('name')}: {str(s.get('desc') or '')[:80]} | head={str(s.get('style_prompt_head'))[:40]}"
        for s in styles)
    user = (f"书名: 《{material.get('书名')}》\n核心主张: {material.get('核心主张')}\n"
            f"【第1集总纲】\n{json.dumps(material.get('第1集') or {}, ensure_ascii=False)}\n"
            f"【试镜画面】\n" + "\n".join(f"- {s.get('name')}: {s.get('image_prompt_zh')}" for s in shots)
            + f"\n【风格库现有成员 (提案必须与它们差异化)】\n{lib_brief or '(空)'}"
            + (f"\n【已排除风格 (用户不喜欢, 提案方向也须避开)】\n" + "\n".join(f"- {x}" for x in excl)
               if excl else "")
            + f"\n【要求数量】恰好 {n} 个互不相同的提案"
            + f"\n【可用 LoRA 清单 (Krea2-风格 目录, 只能从这里选或 null)】\n" + "\n".join(loras))
    try:
        raw = _llm().chat(_PROPOSE_SYS, user, model="pro", temperature=0.6)
        data = _parse(raw)
        items = data.get("proposals") or ([data] if data.get("name") else [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("[style-board] 新配方提案失败 (跳过, 板内仅库成员): %s", exc)
        return []
    out: list[dict] = []
    taken = {s.get("name") for s in styles} | set(excl)
    for data in items:
        if not isinstance(data, dict) or not (data.get("style_prompt_head") or "").strip():
            continue
        bad = _banned(" ".join(str(data.get(k) or "") for k in
                               ("style_prompt_head", "style_prompt_tail", "h3_style")))
        if bad:  # 卡通红线 (确定性, 不靠 LLM 自觉)
            logger.warning("[style-board] 提案踩卡通红线 (词 '%s'), 弃: %s",
                           bad, data.get("name"))
            continue
        name = str(data.get("name") or "").strip()[:24] or f"新提案{len(out) + 1}"
        if name in taken:
            name += f"_v{len(out) + 2}"
        taken.add(name)
        lora = data.get("lora")
        if lora and loras and str(lora) not in loras:  # 幻觉文件名 → 纯提示词
            logger.warning("[style-board] 提案 LoRA 不在清单, 降纯提示词: %s", lora)
            lora = None
        try:
            strength = max(0.0, min(1.0, float(data.get("lora_strength") or 0.6)))
        except (TypeError, ValueError):
            strength = 0.6
        out.append({
            "name": name, "desc": str(data.get("desc") or "")[:300],
            "style_prompt_head": (data.get("style_prompt_head")
                                  or DEFAULT_STYLE["style_prompt_head"]),
            "style_prompt_tail": (data.get("style_prompt_tail")
                                  or DEFAULT_STYLE["style_prompt_tail"]),
            "h3_style": data.get("h3_style") or DEFAULT_STYLE["h3_style"],
            "lora": f"Krea2-风格\\{lora}" if lora else "",
            "lora_strength": strength, "is_new": True,
        })
        if len(out) >= n:
            break
    return out


# ── 渲染 + job ───────────────────────────────────────────────

def _pub(job: dict, msg: str) -> None:
    job["log"].append(msg)
    job["log"] = job["log"][-80:]
    logger.info("[style-board] %s", msg)
    _emit(job, msg)


def _run_board(job: dict) -> None:
    from app.services.anim_service import _GPU_JOB_LOCK
    try:
        shots = _plan_shots(job["material"])
        job["shots"] = shots
        _pub(job, f"试镜镜规划 ✓ {len(shots)} 镜: " + " / ".join(s["name"] for s in shots))
        excl = exclusions(job["book_title"])
        lib_all = _library_styles()
        styles = [s for s in lib_all if s.get("name") not in excl]
        out = _board_dir(job["book_title"])
        out.mkdir(parents=True, exist_ok=True)
        # 0922 排除补位: 每个被排除的库成员由一个新提案顶替 (基础 1 个, 上限共 3)
        n_prop = min(3, 1 + (len(lib_all) - len(styles)))
        proposals = _propose_n(job["material"], shots, styles, excl, n_prop) if n_prop else []
        if proposals:
            styles += proposals
            # 完整配方落盘 (select 入库时吃这份, 板上只有摘要)
            (out / "提案.json").write_text(
                json.dumps({"proposals": proposals}, ensure_ascii=False, indent=1),
                encoding="utf-8")
            _pub(job, f"Kimi 新配方提案 ✓ ×{len(proposals)}: "
                      + " / ".join(f"{p['name']} ({p['lora'] or '纯提示词'})" for p in proposals))
        else:
            _pub(job, "新配方提案跳过 (板内仅库成员)")
        out = _board_dir(job["book_title"])
        rows = []
        n_total = len(styles) * len(shots)
        with _GPU_JOB_LOCK:
            for si, st in enumerate(styles):
                for ci, sh in enumerate(shots):
                    if job.get("cancel"):
                        job["status"] = "cancelled"
                        return
                    tag = _safe_name(str(st.get("name")))
                    dest = out / f"style{si}_{ci + 1}.png"
                    _pub(job, f"K2 渲染 {st.get('name')} · 镜{ci + 1} "
                              f"({job['done_n'] + 1}/{n_total})…")
                    render_gated(
                        lambda sd, s=st, c=sh, i=ci, p=f"styleboard/{_safe_name(job['book_title'])}/{tag}/m{i + 1}":
                            build_workflow(c["image_prompt_zh"], sd, p, style=s),
                        dest, _BOARD_SEED + ci,
                        f"styleboard {st.get('name')} m{ci + 1}")
                    job["done_n"] += 1
                    job.setdefault("cells", []).append(
                        {"style_idx": si, "shot_idx": ci, "file": dest.name})
        board = {
            "book_title": job["book_title"], "created_at": time.strftime("%Y-%m-%d %H:%M"),
            "shots": shots,
            "styles": [{"name": s.get("name"), "desc": s.get("desc") or "",
                        "lora": s.get("lora") or "", "is_new": bool(s.get("is_new")),
                        "idx": si}
                       for si, s in enumerate(styles)],
            "excluded": excl,
            "selected": None,
        }
        (out / "board.json").write_text(json.dumps(board, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
        job["status"] = "done"
        _pub(job, f"选择板就绪 ✓ {len(styles)} 风格 × {len(shots)} 镜")
    except Exception as exc:  # noqa: BLE001
        job["status"] = "error"
        job["error"] = str(exc)
        logger.exception("[style-board] 失败")


def start_board(book_id: str, book_title: str, material: dict) -> dict:
    with _JOBS_LOCK:
        running = next((j for j in _JOBS.values() if j["status"] == "running"), None)
        if running:
            raise RuntimeError(f"风格选型进行中 (《{running['book_title']}》), 稍后再试")
        job = {"id": str(uuid.uuid4()), "status": "running", "book_id": book_id,
               "book_title": book_title, "material": material, "shots": [],
               "done_n": 0, "cells": [], "log": [], "error": None, "cancel": False}
        _JOBS[job["id"]] = job
        if len(_JOBS) > 20:
            for old in [j for j in _JOBS.values() if j["status"] != "running"][:-10]:
                _JOBS.pop(old["id"], None)
    threading.Thread(target=_run_board, args=(job,), daemon=True,
                     name="style-board").start()
    return _view(job)


def _view(job: dict) -> dict:
    return {"id": job["id"], "status": job["status"], "done_n": job["done_n"],
            "log": job["log"][-12:], "error": job["error"],
            "shots": [{"name": s.get("name")} for s in job.get("shots") or []]}


def board_view(book_id: str, book_title: str = "") -> dict:
    with _JOBS_LOCK:
        running = next((j for j in _JOBS.values()
                        if j["status"] == "running" and j["book_id"] == book_id), None)
        any_running = next((j for j in _JOBS.values() if j["status"] == "running"), None)
    view: dict[str, Any] = {"job": _view(running) if running else None,
                            "busy_other": bool(any_running and not running)}
    rj = _RETUNE_JOBS.get(book_id)
    if rj:
        view["retune"] = {k: rj.get(k) for k in ("status", "style", "error", "result")}
    # 板子优先从盘读 (0922 修: 重启后内存 job 失忆, board.json 才是事实源)
    if not running:
        with _JOBS_LOCK:
            job = next((j for j in reversed(list(_JOBS.values()))
                        if j["book_id"] == book_id and j["status"] == "done"), None)
        b = _read_board(job["book_title"] if job else book_title)
        if b:
            view["board"] = b
    return view


def _read_board(book_title: str) -> dict | None:
    if not book_title:
        return None
    try:
        return json.loads((_board_dir(book_title) / "board.json").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def board_img(book_title: str, name: str) -> Path:
    """选择板图片 (防穿越: 纯文件名校验)."""
    if not name or "/" in name or "\\" in name or ".." in name:
        raise FileNotFoundError(name)
    p = _board_dir(book_title) / name
    if not p.exists():
        raise FileNotFoundError(name)
    return p


def _persist_proposal(book_title: str, hit: dict) -> bool:
    """新配方入库 (0922): 风格库 json + 首镜样张参考图. select/keep 共用."""
    new_json = _board_dir(book_title) / "提案.json"
    if not new_json.exists():
        return False
    try:
        payload = json.loads(new_json.read_text(encoding="utf-8"))
        proposals = payload.get("proposals") if isinstance(payload, dict) else payload
        recipe = next((p for p in (proposals or [])
                       if isinstance(p, dict) and p.get("name") == hit["name"]), None)
        if not recipe:
            return False
        lib_p = _assets() / "风格库" / f"{_safe_name(hit['name'])}.json"
        data = {k: v for k, v in recipe.items() if k != "is_new"}
        data["name"] = hit["name"]
        data["desc"] = (hit.get("desc") or "") + " (0922 风格选择板提案入库)"
        lib_p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        ref_src = _board_dir(book_title) / f"style{hit.get('idx')}_1.png"
        if ref_src.exists():
            (lib_p.parent / f"{_safe_name(hit['name'])}_参考_选择板.png").write_bytes(
                ref_src.read_bytes())
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("[style-board] 新配方入库失败: %s", exc)
        return False


_RETUNE_SYS = (
    "你是动画风格配方调优师。用户对某提案配方说'方向对, 但画面粗糙/还原不足'。"
    "给定原配方与试镜画面, 出**一版修正配方**: 风格方向与名字不变, 只准动这些旋钮 — "
    "①lora: 换清单内更贴合该方向的 LoRA, 或 null 走纯提示词; "
    "②lora_strength: ±0.1~0.2 微调; "
    "③style_prompt_head/tail: 按 K2 家规精修 (head ≤60字一句定调, tail ≤40字轻锚, "
    "禁头尾重复, 质感词总量≤5 — 画面要经得起放大看); "
    "**head 必须锚定人物形态** (2D平面动画人物/3D卡通人物/Q版 三选一 — 不锚则同风格人物 2D/3D 乱漂); "
    "④h3_style 随动。"
    "红线: 卡通大类, 禁真人/写实/照片系词。输出严格 JSON 单对象 (同提案 schema)。"
)


_RETUNE_SYS = _RETUNE_SYS + _VISUAL_LAW


def retune(book_title: str, style_name: str, note: str = "") -> dict:
    """重调 (0922 用户令·已确认): 方向对但画面糙 → Kimi 只修配方旋钮, 单列重渲 3 张.

    单列回路不动全板; kept 过的配方同步更新风格库; 板 created_at 刷新破缓存。
    """
    if not (note or "").strip():
        note = "画面粗糙, 请精修还原度"
    board_p = _board_dir(book_title) / "board.json"
    board = json.loads(board_p.read_text(encoding="utf-8"))
    hit = next((s for s in board["styles"] if s["name"] == style_name), None)
    if not hit:
        raise KeyError(f"选择板无此风格: {style_name}")
    if not hit.get("is_new"):
        raise KeyError(f"仅提案列可重调 (库成员 {style_name} 改库 json)")
    # 源配方: 提案.json 优先, kept 过的以风格库为准
    recipe = None
    try:
        payload = json.loads((_board_dir(book_title) / "提案.json").read_text(encoding="utf-8"))
        proposals = payload.get("proposals") if isinstance(payload, dict) else payload
        recipe = next((p for p in (proposals or [])
                       if isinstance(p, dict) and p.get("name") == style_name), None)
    except Exception:  # noqa: BLE001
        pass
    if recipe is None and hit.get("kept"):
        try:
            recipe = json.loads((_assets() / "风格库" / f"{_safe_name(style_name)}.json")
                                .read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    if not recipe:
        raise KeyError(f"配方源缺失: {style_name} (提案.json 无此条)")

    loras = sorted(p.name for p in _LORA_DIR.glob("*.safetensors")) if _LORA_DIR.exists() else []
    user = (f"【用户判词】{note}\n【原配方】\n{json.dumps(recipe, ensure_ascii=False)}\n"
            f"【试镜画面】\n" + "\n".join(f"- {s.get('name')}: {s.get('image_prompt_zh')}"
                                         for s in board.get("shots") or [])
            + "\n【可用 LoRA 清单 (只能从这里选或 null)】\n" + "\n".join(loras))
    raw = _llm().chat(_RETUNE_SYS, user, model="pro", temperature=0.3)
    data = _parse(raw)
    if not isinstance(data, dict) or not (data.get("style_prompt_head") or "").strip():
        raise RuntimeError("重调输出不可解析")
    if _banned(" ".join(str(data.get(k) or "") for k in
                        ("style_prompt_head", "style_prompt_tail", "h3_style"))):
        raise RuntimeError("重调配方踩卡通红线 (真人/写实系词), 已弃")
    lora = data.get("lora")
    if lora and loras and str(lora) not in loras:
        lora = None
    try:
        strength = max(0.0, min(1.0, float(data.get("lora_strength") or recipe.get("lora_strength") or 0.6)))
    except (TypeError, ValueError):
        strength = 0.6
    new_recipe = {
        "name": style_name,
        "desc": str(data.get("desc") or recipe.get("desc") or "")[:300],
        "style_prompt_head": data["style_prompt_head"],
        "style_prompt_tail": data.get("style_prompt_tail") or DEFAULT_STYLE["style_prompt_tail"],
        "h3_style": data.get("h3_style") or DEFAULT_STYLE["h3_style"],
        "lora": f"Krea2-风格\\{lora}" if lora else "",
        "lora_strength": strength, "is_new": True, "retuned": True,
    }
    # 配方回写: 提案.json 替换同名条目; kept 过的同步风格库
    prop_p = _board_dir(book_title) / "提案.json"
    try:
        payload = json.loads(prop_p.read_text(encoding="utf-8"))
        lst = payload.get("proposals") if isinstance(payload, dict) else payload
        lst = [new_recipe if (p or {}).get("name") == style_name else p for p in (lst or [])]
        if not any((p or {}).get("name") == style_name for p in lst):
            lst.append(new_recipe)
        prop_p.write_text(json.dumps({"proposals": lst}, ensure_ascii=False, indent=1),
                          encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[style-board] 重调配方回写提案.json 失败: %s", exc)
    if hit.get("kept"):
        try:
            lib_p = _assets() / "风格库" / f"{_safe_name(style_name)}.json"
            lib = {k: v for k, v in new_recipe.items() if k not in ("is_new", "retuned")}
            lib_p.write_text(json.dumps(lib, ensure_ascii=False, indent=1), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            logger.warning("[style-board] 重调同步风格库失败: %s", exc)

    # 单列重渲 3 张 (同镜同种子, 与首轮可对照) — 文字守门同产线
    from app.services.anim_service import _GPU_JOB_LOCK
    si = int(hit.get("idx") or 0)
    _board_dir(book_title).mkdir(parents=True, exist_ok=True)
    with _GPU_JOB_LOCK:
        for ci, sh in enumerate(board.get("shots") or []):
            dest = _board_dir(book_title) / f"style{si}_{ci + 1}.png"
            render_gated(
                lambda sd, c=sh, i=ci: build_workflow(
                    c["image_prompt_zh"], sd,
                    f"styleboard/{_safe_name(book_title)}/{_safe_name(style_name)}/r{i + 1}",
                    style=new_recipe),
                dest, _BOARD_SEED + ci,
                f"styleboard-retune {style_name} m{ci + 1}")
    # 板刷新: desc 标重调 + created_at 破缓存
    hit["desc"] = (new_recipe.get("desc") or hit.get("desc") or "")[:300]
    hit["retuned"] = True
    board["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    board_p.write_text(json.dumps(board, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"book_title": book_title, "style": style_name, "retuned": True,
            "recipe": {k: new_recipe[k] for k in ("style_prompt_head", "style_prompt_tail",
                                                  "lora", "lora_strength")}}


# ── 重调 job (0922): 单列回路, 页面轮询 ───────────────────────
_RETUNE_JOBS: dict[str, dict] = {}


def start_retune(book_id: str, book_title: str, style_name: str, note: str = "") -> dict:
    j = _RETUNE_JOBS.get(book_id)
    if j and j.get("status") == "running":
        raise RuntimeError(f"重调进行中 ({j.get('style')}), 稍后再试")
    j = {"id": str(uuid.uuid4()), "status": "running", "book_id": book_id,
         "style": style_name, "log": [], "error": None, "result": None}
    _RETUNE_JOBS[book_id] = j

    def _run():
        try:
            j["result"] = retune(book_title, style_name, note)
            j["status"] = "done"
        except Exception as exc:  # noqa: BLE001
            j["status"] = "error"
            j["error"] = str(exc)
            logger.exception("[style-board] 重调失败")

    threading.Thread(target=_run, daemon=True, name="style-retune").start()
    return {"id": j["id"], "status": j["status"], "style": style_name}


# ── 艺术圣经页 (0922 用户令流程: 大纲→风格选型→艺术圣经独立页) ──
_BIBLE_JOBS: dict[str, dict] = {}


def _bible_job_gate(book_id: str) -> dict | None:
    """圣经/试渲共用一槽互斥 (0923 修×2: 运行中重复触发不再 409 — 回当前 job 让页面进轮询,
    弹窗绝迹; >20min 僵尸才接管). 返回 dict=已有 job 在跑, None=可启动."""
    j = _BIBLE_JOBS.get(book_id)
    if j and j.get("status") == "running":
        if time.time() - float(j.get("t0") or 0) < 1200:
            return j
        logger.warning("[style-bible] 僵尸 job 接管 (%s, %.0f 分钟)",
                       j.get("kind"), (time.time() - float(j.get("t0") or 0)) / 60)
    return None


_BIBLE_DONE: dict[str, dict] = {}   # book_id → {"kind","t","samples"} 最近完成 (冷却用)


def _emit(job: dict, msg: str, typ: str = "info") -> None:
    """SSE 推送 (0923): 选型/圣经/试渲/重调全上实时事件流, 页面免瞎等."""
    try:
        from app.services.job_events import _publish as _jp
        _jp(str(job.get("id") or ""), {"type": typ, "message": msg})
    except Exception:  # noqa: BLE001 — SSE 挂了不影响渲染
        pass


def _bible_done_recently(book_id: str, kind: str) -> dict | None:
    """冷却 (0923 幽灵客户端实锤: Edge 卡死标签页一夜 POST 14万次, 幂等放行导致 GPU 反复点火):
    同类 job 3 分钟内完成过 → 直接回结果, 不再重启渲染。"""
    rec = _BIBLE_DONE.get(book_id)
    if rec and rec.get("kind") == kind and time.time() - rec.get("t", 0) < 180:
        return {"status": "done", "cached": True, "kind": kind, "samples": rec.get("samples")}
    return None


def render_bible_samples(book_id: str, book_title: str) -> dict:
    """圣经试渲 (0922 用户令: 纯文字难转图形效果): 色板/质感/角色策略烘进画面渲 2 张.

    用选定配方 (head/tail/LoRA) + 圣经字段组景; 产 圣经试渲_1/2.png 于板目录
    (经既有 style-board img 端点供页). 占 GPU 锁, 后台 job."""
    running = _bible_job_gate(book_id)
    if running:
        return {"status": "already-running", "kind": running.get("kind")}
    cached = _bible_done_recently(book_id, "samples")
    if cached:
        return cached
    j = {"id": str(uuid.uuid4()), "kind": "samples", "status": "running", "error": None,
         "samples": [], "t0": time.time()}
    _BIBLE_JOBS[book_id] = j

    def _run():
        from app.services.anim_service import _GPU_JOB_LOCK
        _emit(j, "试渲启动: 原镜+角色卡+主色, 3 张 + 文字守门")
        try:
            view = bible_view(book_id, book_title)
            recipe = view.get("style_recipe")
            bible = view.get("bible") or {}
            if not recipe:
                raise RuntimeError("无风格绑定")
            # 试渲画面 = 原试镜镜 (LLM 画面长句) + 圣经调味 — 同镜同种子,
            # 与板原图并排 A/B, 差异纯 = 圣经贡献 (0922 用户实锤: 首版两句占位文画面过瘦)
            try:
                board = json.loads((_board_dir(book_title) / "board.json").read_text(encoding="utf-8"))
                shots = board.get("shots") or []
            except Exception:  # noqa: BLE001
                shots = []
            if not shots:
                raise RuntimeError("板上无试镜镜 (先跑风格选型)")
            # 0922 调味改确定性追加: LLM 调味器两版都偷偷缩句掉细节 (密度比 0.5x 实锤),
            # 正则抽圣经主色 + 角色锁定卡轮穿上镜 + 纯字符串拼接, 零改写风险
            import re as _re
            pal = str(bible.get("color_palette") or "")
            m = _re.search(r"主色[:：]?\s*([^;；,，。(（]{2,20})", pal)
            hue = (m.group(1).strip() if m else "")[:12]
            chars = [c for c in (bible.get("characters") or [])
                     if isinstance(c, dict) and c.get("look")]
            scenes = []
            for i, s in enumerate(shots):
                base = str(s.get("image_prompt_zh") or "")
                # 人物前置 (0923 修: 角色卡放画面句开头 — 主体权重最高; 原镜句随其后不被稀释)
                if chars:
                    c = chars[i % len(chars)]
                    base = f"前景人物为{c['name']}（{c['look']}）," + base
                if hue:
                    base += f"，主角服装与核心道具以{hue}为主色调"
                scenes.append(base)
            d = _board_dir(book_title)
            d.mkdir(parents=True, exist_ok=True)
            (d / "调味句.json").write_text(
                json.dumps({"hue": hue, "scenes": scenes}, ensure_ascii=False, indent=1),
                encoding="utf-8")
            with _GPU_JOB_LOCK:
                for ci, scene in enumerate(scenes, 1):
                    render_gated(
                        lambda sd, sc=scene, i=ci: build_workflow(
                            sc, sd, f"styleboard/{_safe_name(book_title)}/bible/s{i}",
                            style=recipe),
                        d / f"圣经试渲_{ci}.png", _BOARD_SEED + ci,
                        f"bible-sample s{ci}")
                    j["samples"].append(f"圣经试渲_{ci}.png")
                    _emit(j, f"试渲 {ci}/{len(scenes)} ✓ (已过文字守门)")
            j["status"] = "done"
            _BIBLE_DONE[book_id] = {"kind": "samples", "t": time.time(),
                                    "samples": list(j["samples"])}
            _emit(j, "试渲完成 ✓", "samples_done")
        except Exception as exc:  # noqa: BLE001
            j["status"] = "error"
            j["error"] = str(exc)
            _emit(j, f"试渲失败: {exc}", "samples_error")
            j["error"] = str(exc)
            logger.exception("[style-bible] 试渲失败")

    threading.Thread(target=_run, daemon=True, name="bible-sample").start()
    return {"status": "running", "id": j["id"]}


def bible_view(book_id: str, book_title: str) -> dict:
    """圣经现值 + 书级绑定摘要 (无绑定=流程未到, 页面挡)."""
    from .director2 import _bible_cache_path
    bible = None
    try:
        bible = json.loads(_bible_cache_path(book_title).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        pass
    bound = bound_style(book_title)
    recipe = None
    if bound:
        try:
            recipe = json.loads((_assets() / "风格库" / f"{_safe_name(bound)}.json")
                                .read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    j = _BIBLE_JOBS.get(book_id)
    # 样张 (0922): 选定风格的板样张 (style{idx}_1..3) + 圣经试渲 (如有)
    samples: list[str] = []
    try:
        board = json.loads((_board_dir(book_title) / "board.json").read_text(encoding="utf-8"))
        hit = next((s for s in board.get("styles", []) if s.get("name") == bound), None)
        if hit and hit.get("idx") is not None:
            samples += [f"style{hit['idx']}_{ci}.png" for ci in (1, 2, 3)]
    except Exception:  # noqa: BLE001
        pass
    samples += sorted(p.name for p in _board_dir(book_title).glob("圣经试渲_*.png"))
    return {"bound": bound, "style_recipe": recipe, "bible": bible,
            "samples": samples,
            "job": {k: j.get(k) for k in ("id", "kind", "status", "error", "bible", "samples")} if j else None}


def start_bible(book_id: str, book_title: str, force: bool = False) -> dict:
    running = _bible_job_gate(book_id)
    if running:
        return {"status": "already-running", "kind": running.get("kind")}
    j = {"id": str(uuid.uuid4()), "kind": "bible", "status": "running", "error": None,
         "bible": None, "t0": time.time()}
    _BIBLE_JOBS[book_id] = j

    def _run():
        import hashlib as _hl
        _emit(j, "圣经生成中 (灵魂三问+受众+总纲贯穿人物+樊登稿+选定配方)…")
        chars_before = _hl.md5(json.dumps(
            [{"n": c.get("name"), "l": c.get("look")}
             for c in bible_view(book_id, book_title).get("bible", {}).get("characters") or []],
            ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        try:
            from .director2 import load_or_derive_bible
            j["bible"] = load_or_derive_bible(book_id, book_title, force=force)
            if not j["bible"].get("style_prefix"):
                j["status"] = "error"
                j["error"] = "生成结果缺 style_prefix (走空)"
                _emit(j, "生成失败: 缺 style_prefix", "bible_error")
                return
            # 0923 status 时序修: 定妆照链跑完才置 done (提前置 done 页面以为完事, 链还在渲)
            # 0923 撕裂修复 (用户令): 角色卡变了 → 定妆照自动重渲, 同一条流滚完, 不用跨页追
            chars_after = _hl.md5(json.dumps(
                [{"n": c.get("name"), "l": c.get("look")} for c in j["bible"].get("characters") or []],
                ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            if force or chars_after != chars_before:
                _emit(j, "圣经生成 ✓ 角色卡已变更 → 定妆照自动重渲…")
                try:
                    from .character_sheets import render_missing
                    n_new, _ = render_missing(book_title, lambda m: _emit(j, m))
                    _emit(j, f"定妆照沉淀 ✓ 新渲{n_new}张 (角色设计台可看)", "bible_done")
                except Exception as exc:  # noqa: BLE001
                    _emit(j, f"定妆照自动重渲失败 (可去角色设计台手动): {exc}", "bible_done")
                j["status"] = "done"
            else:
                _emit(j, "圣经生成 ✓ (角色卡未变, 定妆照不动)", "bible_done")
                j["status"] = "done"
        except Exception as exc:  # noqa: BLE001
            j["status"] = "error"
            j["error"] = str(exc)
            _emit(j, f"生成失败: {exc}", "bible_error")
            logger.exception("[style-bible] 生成失败")

    threading.Thread(target=_run, daemon=True, name="style-bible").start()
    return {"status": "running", "id": j["id"]}


def save_bible(book_title: str, bible: dict) -> dict:
    """手工修经落盘 (= 写缓存, plan 全系列复用; 手调优先于重掷)."""
    if not (bible or {}).get("style_prefix"):
        raise ValueError("style_prefix 不可为空")
    from .director2 import _bible_cache_path
    p = _bible_cache_path(book_title)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(bible, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"saved": True}


def keep(book_title: str, style_name: str) -> dict:
    """留存 (0922 用户令): 这本书不用它, 但风格好 — 配方入库备用, 不绑本书不落选定."""
    p = _board_dir(book_title) / "board.json"
    board = json.loads(p.read_text(encoding="utf-8"))
    hit = next((s for s in board["styles"] if s["name"] == style_name), None)
    if not hit:
        raise KeyError(f"选择板无此风格: {style_name}")
    if not hit.get("is_new"):
        return {"book_title": book_title, "style": style_name, "kept": False,
                "note": "库成员本就在库, 无需留存"}
    ok = _persist_proposal(book_title, hit)
    if ok:
        hit["kept"] = True
        p.write_text(json.dumps(board, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"book_title": book_title, "style": style_name, "kept": ok}


def select(book_title: str, style_name: str) -> dict:
    """点选落绑定; 选中新提案配方 → 自动入库 (json + 首镜样张作参考图)."""
    p = _board_dir(book_title) / "board.json"
    board = json.loads(p.read_text(encoding="utf-8"))
    hit = next((s for s in board["styles"] if s["name"] == style_name), None)
    if not hit:
        raise KeyError(f"选择板无此风格: {style_name}")
    # 新配方入库: 完整配方来自板上 提案.json
    if hit.get("is_new"):
        _persist_proposal(book_title, hit)
    _binding_path(book_title).write_text(
        json.dumps({"style": style_name, "note": "0922 风格选择板选定"}, ensure_ascii=False),
        encoding="utf-8")
    board["selected"] = style_name
    p.write_text(json.dumps(board, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"book_title": book_title, "style": style_name}
