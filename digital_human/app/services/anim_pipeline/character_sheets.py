"""角色设计台 (0923 用户令) — 圣经角色锁定卡 → 定妆照沉淀.

独立新功能 (不与选型/试渲合并): 每个角色一张 K2 定妆照
(书级风格配方 + look 关键词 → 单角色全身立绘, 干净背景),
产物沉淀 _资产/角色设计/{书}/{角色}.png — 全书人物锚:
人检定稿后供分镜参考 / 未来 i2i 一致性底图; look 文本回写圣经 characters。
SSE: chars_done/chars_error; GPU 锁与产线互斥; 违禁守门同产线。
"""
from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from pathlib import Path

from .config import _safe_name
from .director2 import _bible_cache_path
from .k2 import build_workflow, render_gated
from .style_board import _assets, _emit

logger = logging.getLogger(__name__)

_JOBS: dict[str, dict] = {}
_DESIGN_SEED = 20260923


def _design_dir(book_title: str) -> Path:
    return _assets() / "角色设计" / _safe_name(book_title)


def characters(book_title: str) -> list[dict]:
    try:
        raw = json.loads(_bible_cache_path(book_title).read_text(encoding="utf-8"))
        return [c for c in (raw.get("characters") or []) if isinstance(c, dict)]
    except Exception:  # noqa: BLE001
        return []


def save_characters(book_title: str, chars: list[dict]) -> dict:
    """角色卡增删改 → 回写圣经 (圣经 characters 是唯一事实源, 本页只是编辑器)."""
    p = _bible_cache_path(book_title)
    data = json.loads(p.read_text(encoding="utf-8"))
    data["characters"] = [{"name": str(c.get("name") or "").strip()[:24],
                           "role": str(c.get("role") or "")[:40],
                           "look": str(c.get("look") or "")[:160]}
                          for c in chars if (c.get("name") or "").strip()]
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"saved": len(data["characters"])}


def designs(book_title: str) -> list[dict]:
    """已沉淀定妆照 [{name, file}] (文件名=角色名)."""
    d = _design_dir(book_title)
    out = []
    if d.exists():
        for p in sorted(d.glob("*.png")):
            out.append({"name": p.stem, "file": p.name})
    return out


# 文字载体道具 (0923 用户实锤 奶球小妹围裙乱码汉字): look 里带这些词 = 给 K2 递写字许可
_TEXT_PROPS = ("标语牌", "横幅", "告示牌", "招牌", "带字", "书页字", "字牌")


def _sanitize_look(look: str) -> str:
    """确定性消毒: 剥离文字载体道具词段 (资产原文不动, 只清生成入参)."""
    out = str(look or "")
    for w in _TEXT_PROPS:
        if w in out:
            logger.warning("[char-design] look 含文字载体道具 '%s', 生成时剥离: %s", w, out[:50])
            out = out.replace(w, "")
    return out


def _scene(look: str) -> str:
    return ("角色设计定妆照，单一角色完整全身照，头顶到脚尖全部在画面内，四周留出呼吸边距，"
            "禁止裁切头部脚部或任何道具，所有标志道具完整可见不被裁切不出画，"
            "干净浅米色摄影棚背景，正面自信站姿，"
            "表情生动，完整呈现服装层次与标志道具，角色细节特征清晰。"
            "服装配饰与道具全部无文字无字母，禁标语牌横幅等一切带字物件，"
            "服装配饰禁军装警服制式元素、禁国徽军徽警徽党徽帽徽领章，"
            "徽章一律为数字或字母或几何造型：" + _sanitize_look(look))


def view(book_id: str, book_title: str, bound: str | None, recipe: dict | None) -> dict:
    j = _JOBS.get(book_id)
    return {"bound": bound, "style_recipe": recipe,
            "characters": characters(book_title),
            "designs": designs(book_title),
            "job": {k: j.get(k) for k in ("id", "kind", "status", "error", "log")}
            if j else None}


def render_missing(book_title: str, emit) -> tuple[int, int]:
    """补渲缺/变的定妆照 (0923 抽出: 圣经重掷自动链 + 设计台共用).

    emit(msg) 接收进度; 返回 (新渲数, 跳过数). 占 GPU 锁."""
    import hashlib
    from app.services.anim_service import _GPU_JOB_LOCK
    from .config import resolve_style
    recipe = resolve_style(book_title)
    d = _design_dir(book_title)
    d.mkdir(parents=True, exist_ok=True)

    def _meta(c):
        return d / f"{_safe_name(c['name'])}.meta.json"

    def _look_h(c):
        return hashlib.md5((c.get("look") or "").encode("utf-8")).hexdigest()[:10]

    work, skipped = [], 0
    for c in characters(book_title):
        same = False
        if (d / f"{_safe_name(c['name'])}.png").exists() and _meta(c).exists():
            try:
                same = json.loads(_meta(c).read_text(encoding="utf-8")).get("h") == _look_h(c)
            except Exception:  # noqa: BLE001
                pass
        if same:
            skipped += 1
        else:
            work.append(c)
    if work:
        with _GPU_JOB_LOCK:
            for i, c in enumerate(work, 1):
                emit(f"定妆照 {i}/{len(work)}: {c['name']} 渲染中 (含违禁守门)…")
                dirty = render_gated(
                    lambda sd, lk=c.get("look") or "": build_workflow(
                        _scene(lk), sd,
                        f"chardesign/{_safe_name(book_title)}/{_safe_name(c['name'])}",
                        style=recipe, portrait=True),
                    d / f"{_safe_name(c['name'])}.png", _DESIGN_SEED + i,
                    f"char-design {c['name']}", retries=3)
                _meta(c).write_text(json.dumps({"h": _look_h(c), "suspect": bool(dirty)},
                                               ensure_ascii=False), encoding="utf-8")
                if dirty:
                    emit(f"⚠️ 定妆照 {i}/{len(work)} {c['name']} 疑似违禁残留 (重掷后仍在), 请人检/改 look 重渲")
                else:
                    emit(f"定妆照 {i}/{len(work)} ✓: {c['name']}")
    return len(work), skipped


def start_design(book_id: str, book_title: str, names: list[str],
                 looks: dict | None = None) -> dict:
    """定妆照 job: names 空列表 = 全部角色. 单书单槽 (与圣经/试渲槽各自独立).

    looks (0923): {角色名: look} 覆写 — 页面文本框当前值随渲随存 (改完直接点 🖩 一步到位)."""
    j = _JOBS.get(book_id)
    if j and j.get("status") == "running":
        raise RuntimeError("角色设计进行中, 稍后再试")
    chars = characters(book_title)
    if looks:
        changed = False
        for c in chars:
            new_lk = str(looks.get(c["name"]) or "").strip()
            if new_lk and new_lk != (c.get("look") or ""):
                c["look"] = new_lk[:160]
                changed = True
        if changed:
            save_characters(book_title, chars)
    todo = [c for c in chars if not names or c["name"] in names]
    if not todo:
        raise RuntimeError("圣经无角色卡 (先在艺术圣经页生成/添加角色)")
    j = {"id": str(uuid.uuid4()), "kind": "chars", "status": "running",
         "error": None, "log": [], "t0": time.time()}
    _JOBS[book_id] = j

    def _run():
        from app.services.anim_service import _GPU_JOB_LOCK
        from .style_board import bound_style
        from .config import resolve_style
        import hashlib
        try:
            bound = bound_style(book_title)
            if not bound:
                raise RuntimeError("本书未绑定风格")
            recipe = resolve_style(book_title)
            d = _design_dir(book_title)
            d.mkdir(parents=True, exist_ok=True)

            def _meta(c):
                return d / f"{_safe_name(c['name'])}.meta.json"

            def _look_h(c):
                return hashlib.md5((c.get("look") or "").encode("utf-8")).hexdigest()[:10]

            if not names:  # 全部生成 = 补齐缺/变 (0923 抽出 render_missing, 与圣经自动链共用)
                n_new, n_skip = render_missing(book_title, lambda m: _emit(j, m))
                j["status"] = "done"
                if n_new == 0:
                    _emit(j, "全部已沉淀且 look 未变, 无需生成", "chars_done")
                else:
                    j["log"] = [f"新渲 {n_new} 张, 跳过 {n_skip} 张"]
                    _emit(j, f"角色设计完成 ✓ 新渲{n_new} 跳过{n_skip} → _资产/角色设计/", "chars_done")
                return
            with _GPU_JOB_LOCK:
                for i, c in enumerate(todo, 1):
                    _emit(j, f"定妆照 {i}/{len(todo)}: {c['name']} 渲染中 (含违禁守门)…")
                    dirty = render_gated(
                        lambda sd, lk=c.get("look") or "": build_workflow(
                            _scene(lk), sd,
                            f"chardesign/{_safe_name(book_title)}/{_safe_name(c['name'])}",
                            style=recipe, portrait=True),
                        d / f"{_safe_name(c['name'])}.png", _DESIGN_SEED + i,
                        f"char-design {c['name']}", retries=3)
                    if dirty:
                        _emit(j, f"⚠️ {c['name']} 疑似违禁未通过 (重掷后仍存疑), 请人检")
                    j["log"].append(f"{c['name']} ✓")
                    _emit(j, f"定妆照 {i}/{len(todo)} ✓: {c['name']}")
            j["status"] = "done"
            _emit(j, f"角色设计完成 ✓ 共{len(todo)}张 → _资产/角色设计/", "chars_done")
        except Exception as exc:  # noqa: BLE001
            j["status"] = "error"
            j["error"] = str(exc)
            _emit(j, f"角色设计失败: {exc}", "chars_error")
            logger.exception("[char-design] 失败")

    threading.Thread(target=_run, daemon=True, name="char-design").start()
    return {"status": "running", "id": j["id"], "n": len(todo)}
