# -*- coding: utf-8 -*-
"""离线蒸馏器 (2026-08-19) — 全书 → 精华 txt (规模.txt 式), 本地 Gemma 批量跑.

架构: 重计算推离线 (4090 闲时批量), 拆书产线只吃 6-15k 精华 L0 (单发上下文)。
方法论借 cangjie-skill 阶段0+1 (Adler 整书理解 + 提取), 单模型轻量版;
重点书仍可手动跑完整 cangjie (Claude), 其 DIGEST.md 可直接落书库当精华。

Gemma 生命周期礼仪 (用户决策 2026-08-19): 端口活则复用不启; 批次结束**全杀腾卡**
(llama-server.exe 全实例按 PID 精确 kill, 用户已授权含手动实例)。
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import time
from pathlib import Path

import requests

from app.config import get_config
from app.services.book_service.reader import clean_book_title, read_book

logger = logging.getLogger(__name__)

__all__ = ["GemmaClient", "ensure_gemma", "shutdown_gemma_all",
           "distill_book", "pending_distill_books", "DISTILL_SUFFIX"]

DISTILL_SUFFIX = ".蒸馏"
GEMMA_URL = "http://127.0.0.1:12348"
GEMMA_MODEL = "gemma4-31b-crack"
_LLAMA_BIN = r"E:\Llama-cpp-12\llama-server.exe"
_LLAMA_CWD = r"E:\Llama-cpp-12"  # exe 依赖同目录 cublas DLL, 必须以它为工作目录
# 参数与 Gemma--crack.bat 逐字一致 (已验证可启动), 仅 temp 降 0.2 利提取稳定性
_LLAMA_ARGS = [
    "-m", r"E:\Llama-cpp-12\models\gemma-4-31b-jang-crack-Q4_K_M.gguf",
    "--mmproj", r"E:\Llama-cpp\models\gemma4-31b-multimodal\mmproj\mmproj-Gemma-4-31B-StyleTune.gguf",
    "--alias", GEMMA_MODEL,
    "--temp", "0.2", "--top-p", "0.95", "--top-k", "20", "--min-p", "0.00",
    "--port", "12348", "--host", "127.0.0.1",
    "-ngl", "999", "-c", "131072", "-b", "2048", "-ub", "512",
    "-fa", "on", "-ctk", "f16", "-ctv", "f16", "--device", "CUDA0",
    "--parallel", "1", "--fit", "on", "--fit-target", "4096",
    "--cache-ram", "6144", "--context-shift",
    "--reasoning-budget", "2048", "--sleep-idle-seconds", "600",
    "-lv", "1",
]
# 全书(需蒸馏) vs 精华(人写/蒸馏产物) 的体量分界
_FULL_TEXT_MIN = 20000

_EXTRACT_SYS = (
    "你是书籍深度提取器(借 cangjie RIA-TV++ 阶段1)。对给定文本块做**穷尽式**提取,"
    "宁多勿漏, 不要过度概括。输出严格 JSON: "
    "{\"观点\":[str], \"概念\":[{\"name\":str,\"mech\":str}], "
    "\"案例\":[{\"desc\":str,\"point\":str}], \"数据\":[str], \"原句\":[str]}。"
    "概念必须带机制解释; 案例必须带细节与说明点; 原句必须逐字不得改写; "
    "只提取文本中存在的, 不得编造。"
)

_COMPOSE_SYS = (
    "你是书籍精华编纂器。把【提取池】(全书穷尽提取的结构化信息)编纂成一篇面向讲书创作的精华稿。"
    "格式仿《规模》式精华: 先「核心哲学」(3-6 句), 再「核心概念与机制」逐条(每条: 核心机制/精确策略/数据/案例/防御或应用, 有条写条), "
    "最后「可引用原句」全量保留。只整理编排, 严禁编造池外信息, 严禁丢弃池中信息点。直接输出稿体, 不要 JSON。"
)

_AUDIT_SYS = (
    "你是短视频平台合规审计器(抖音=关键词+语义上下文双重审核)。按【规则集】审计【提取池】,"
    "输出严格 JSON: {\"delete\":[str], \"rewrite\":[{\"orig\":str,\"dir\":str}], \"book_rules\":[str]}。"
    "delete=高风险须物理删除项(侮辱蔑称/历史悲剧阴谋论化/群体财富阴谋论/大段宗教教义/疗效描述),"
    "给池内原文片段(可子串匹配); rewrite=中风险可保含义须转述项, dir 给改写方向; "
    "book_rules=本书次要风险注意点(视角限定/禁堆砌/禁映射现实)。只输出命中项, 宁严勿漏, 不凑数。"
)


def load_book_rules() -> dict:
    p = Path(__file__).resolve().parents[3] / "config" / "compliance_rules_book.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[distill] 规则集加载失败: %s", exc)
        return {}


def audit_compliance(pool: dict, cb=None) -> dict:
    """Gate A (2026-08-19): pro 模型按 compliance_rules_book.json 审计提取池.

    返回 {delete, rewrite, book_rules}; 调用侧物理删除 delete 项。
    """
    from app.services.llm_service import LLMService
    rules = load_book_rules()
    pool_text = json.dumps(pool, ensure_ascii=False)[:90000]
    llm = LLMService(get_config().deepseek)
    try:
        out = llm.chat(_AUDIT_SYS,
                       f"【规则集】\n{json.dumps(rules, ensure_ascii=False)}\n【提取池】\n{pool_text}",
                       model="pro", temperature=0.2, timeout=600)
        audit = GemmaClient.parse_json_block(out)
    except Exception as exc:
        logger.warning("[distill] 合规审计失败 (放行+记录): %s", exc)
        audit = {}
    audit = {
        "delete": [str(x) for x in (audit.get("delete") or [])][:50],
        "rewrite": [x for x in (audit.get("rewrite") or []) if isinstance(x, dict)][:50],
        "book_rules": [str(x) for x in (audit.get("book_rules") or [])][:30],
    }
    if cb:
        cb(f"合规审计: 删除{len(audit['delete'])} 改写{len(audit['rewrite'])} 注意{len(audit['book_rules'])}")
    return audit


def _apply_delete(pool: dict, frags: list[str]) -> int:
    """物理删除: 池内任何文本字段含 frag 即移除 (高危内容不进管线)."""
    def hit(s: str) -> bool:
        return any(f and (f in s or s in f) for f in frags)
    n = 0
    for k in ("观点", "数据", "原句"):
        before = len(pool[k])
        pool[k] = [x for x in pool[k] if not hit(x)]
        n += before - len(pool[k])
    for k in ("概念", "案例"):
        before = len(pool[k])
        pool[k] = [x for x in pool[k]
                   if not hit(x.get("name", "") or x.get("desc", ""))]
        n += before - len(pool[k])
    return n


class GemmaClient:
    """llama-server OpenAI 兼容客户端 + 稳健 JSON 提取."""

    def __init__(self, url: str = GEMMA_URL, timeout: int = 560):
        self.url = url
        self.timeout = timeout

    def healthy(self) -> bool:
        try:
            return requests.get(f"{self.url}/v1/models", timeout=5).status_code == 200
        except Exception:
            return False

    def chat(self, user: str, system: str = _EXTRACT_SYS) -> str:
        r = requests.post(f"{self.url}/v1/chat/completions",
                          json={"model": GEMMA_MODEL, "temperature": 0.2,
                                "messages": [{"role": "system", "content": system},
                                             {"role": "user", "content": user}]},
                          timeout=self.timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    @staticmethod
    def parse_json_block(text: str) -> dict:
        """取首个平衡花括号块 (容忍 ```json 围栏与尾部杂质)."""
        start = text.find("{")
        if start < 0:
            return {}
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        return {}
        return {}


# ── 生命周期 ─────────────────────────────────────────────────────
def ensure_gemma(client: GemmaClient | None = None) -> tuple[GemmaClient, bool]:
    """端口活 → 复用 (started=False); 否则自启 llama-server 等健康 (最长 600s)."""
    client = client or GemmaClient()
    if client.healthy():
        return client, False
    logger.info("[distill] 自启 llama-server …")
    proc = subprocess.Popen([_LLAMA_BIN, *_LLAMA_ARGS], cwd=_LLAMA_CWD,
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    for _ in range(120):
        if client.healthy():
            return client, True
        if proc.poll() is not None:
            raise RuntimeError(f"llama-server 启动失败 exit={proc.poll()}")
        time.sleep(5)
    proc.kill()
    raise RuntimeError("llama-server 600s 未健康")


def _llama_pids() -> list[int]:
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq llama-server.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    pids = []
    for line in out.splitlines():
        parts = line.replace('"', "").split(",")
        if len(parts) >= 2 and parts[1].strip().isdigit():
            pids.append(int(parts[1]))
    return pids


def shutdown_gemma_all(own_pid: int | None = None) -> list[int]:
    """全杀腾卡 (用户授权): llama-server.exe 全实例按 PID 精确 kill."""
    pids = _llama_pids()
    if own_pid and own_pid not in pids:
        pids.append(own_pid)
    for pid in pids:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
    if pids:
        logger.info("[distill] 已释放 VRAM: kill pids %s", pids)
    return pids


# ── 蒸馏 ─────────────────────────────────────────────────────────
def _dedupe(items: list[str], seen: set[str]) -> list[str]:
    out = []
    for it in items:
        it = (it or "").strip()
        if not it or it in seen or any(it and it in s for s in seen):
            continue
        seen.add(it)
        out.append(it)
    return out


def _clean_latex(s: str) -> str:
    """模型 LaTeX 习惯清洗: $\\rightarrow$ 等 → 箭头, 去残留 $ / \\text{} (原句除外调用侧控制)."""
    s = re.sub(r"\$?\\(rightarrow|Rightarrow|longrightarrow|to|mapsto)\$?", "→", s)
    s = re.sub(r"\$?\\(leftarrow|Leftarrow)\$?", "←", s)
    s = re.sub(r"\\(text|mathrm|emph)\{([^}]*)\}", r"\2", s)
    return s.replace("$", "").replace("\\", "")


def _chunk_text(text: str, size: int = 5500) -> list[str]:
    """句界分块 (不截断): 保证全书每字都被提取."""
    chunks, cur = [], ""
    for sent in re.split(r"(?<=[。！？\n])", text):
        if len(cur) + len(sent) > size and cur:
            chunks.append(cur)
            cur = ""
        cur += sent
    if cur.strip():
        chunks.append(cur)
    return chunks


def _merge_pool(pool: dict, data: dict, seen: set) -> None:
    """v2 深提取合并: 概念{name,mech}/案例{desc,point} 结构化去重."""
    for v in data.get("观点") or []:
        v = _clean_latex((v or "").strip())
        if v and v not in seen:
            seen.add(v); pool["观点"].append(v)
    for c in data.get("概念") or []:
        if isinstance(c, dict) and (c.get("name") or "").strip():
            key = _clean_latex(c["name"].strip())
            if key not in seen:
                seen.add(key); pool["概念"].append({"name": key, "mech": _clean_latex((c.get("mech") or "").strip())})
        elif isinstance(c, str) and c.strip() and c not in seen:
            seen.add(c); pool["概念"].append({"name": c.strip(), "mech": ""})
    for c in data.get("案例") or []:
        if isinstance(c, dict) and (c.get("desc") or "").strip():
            key = c["desc"].strip()[:40]
            if key not in seen:
                seen.add(key); pool["案例"].append({"desc": _clean_latex((c.get("desc") or "").strip()), "point": _clean_latex((c.get("point") or "").strip())})
        elif isinstance(c, str) and c.strip() and c not in seen:
            seen.add(c); pool["案例"].append({"desc": c.strip(), "point": ""})
    for d in data.get("数据") or []:
        d = _clean_latex((d or "").strip())
        if d and d not in seen:
            seen.add(d); pool["数据"].append(d)
    for q in data.get("原句") or []:
        q = (q or "").strip()
        if q and q not in seen:
            seen.add(q); pool["原句"].append(q)


def distill_book(path: str | Path, client: GemmaClient,
                 progress: dict | None = None, cb=None,
                 audit: bool = True) -> str:
    """单书蒸馏 v2 (2026-08-19 质量重写): 全文分块穷尽提取 + LLM 编纂轮.

    v1 三层信息丢失修复: ①截断6000→分块全读; ②裸串→结构化深提取;
    ③编纂硬上限→LLM 编纂轮全量整理(128k 上下文), 机械编纂仅兜底。
    """
    parsed = read_book(path)
    seen: set[str] = set()
    pool: dict = {"观点": [], "概念": [], "案例": [], "数据": [], "原句": []}
    chunks: list[tuple[str, str]] = []
    for ch in parsed["chapters"]:
        if len(ch["text"]) < 500:
            continue
        for ck in _chunk_text(ch["text"]):
            chunks.append((ch["name"], ck))
    for ci, (cname, ck) in enumerate(chunks):
        if progress is not None:
            progress.update({"book": parsed["book_title"], "chapter": f"{ci + 1}/{len(chunks)}"})
        if cb:
            cb(f"块 {ci + 1}/{len(chunks)} ({cname}) 提取中…")
        data = client.parse_json_block(client.chat(f"【章节】{ck}"))
        _merge_pool(pool, data, seen)
    if cb:
        cb(f"提取完成: 观点{len(pool['观点'])} 概念{len(pool['概念'])} "
           f"案例{len(pool['案例'])} 数据{len(pool['数据'])} 原句{len(pool['原句'])}")

    # Gate A 合规审计 (成稿前): 高危物理删除, 改写方向进编纂轮.
    # audit=False = _raw 摸规则模式 (用户 2026-08-19): 保留全量信息送豆包测边界。
    audit_res = {"delete": [], "rewrite": [], "book_rules": []}
    deleted = 0
    if audit:
        # 硬黑名单 (豆包逐字清单, 确定性删除, 不依赖 LLM 命中)
        hard = load_book_rules().get("hard_blacklist_quotes") or []
        hard_n = _apply_delete(pool, hard)
        if hard_n and cb:
            cb(f"硬黑名单确定性删除 {hard_n} 条")
        audit_res = audit_compliance(pool, cb=cb)
        deleted = hard_n + _apply_delete(pool, audit_res["delete"])
        if cb:
            cb(f"高危物理删除共 {deleted} 条")

    # 编纂轮: 全池进 128k 上下文, LLM 编纂成规模式精华 (不编不丢)
    pool_text = json.dumps(pool, ensure_ascii=False)
    comp_sys = _COMPOSE_SYS
    if audit_res["rewrite"] or audit_res["book_rules"]:
        comp_sys += (
            "\n【合规改写方向(必须执行)】"
            + "; ".join(f"{(r.get('orig') or '')[:40]}→{r.get('dir') or ''}" for r in audit_res["rewrite"])
            + "\n【本书注意点】" + "; ".join(audit_res["book_rules"]))
    essence = None
    if pool_text:
        try:
            out = client.chat(f"书名: 《{parsed['book_title']}》\n【提取池】\n{pool_text[:90000]}",
                              system=comp_sys)
            if len(out) >= max(1500, len(pool_text) // 15):
                essence = _clean_latex(out)
        except Exception as exc:
            logger.warning("[distill] 编纂轮失败, 回退机械编纂: %s", exc)
    if essence and (audit_res["rewrite"] or audit_res["book_rules"] or deleted):
        essence += (
            "\n\n## 合规备注 (Gate A 审计, 成稿前必遵)\n"
            + "".join(f"- 改写: {(r.get('orig') or '')[:50]} → {r.get('dir') or ''}\n" for r in audit_res["rewrite"])
            + "".join(f"- 注意: {r}\n" for r in audit_res["book_rules"])
            + f"- 已物理删除高危 {deleted} 条, 成稿禁用其原文\n")
    return essence or _compose_essence_fallback(parsed["book_title"], pool)


def _compose_essence_fallback(title: str, p: dict) -> str:
    """机械编纂兜底 (无上限): 编纂轮失败时保信息量."""
    parts = [f"# 《{title}》蒸馏精华\n\n核心哲学\n"]
    parts += [f"{v}\n" for v in p["观点"]] or ["（无）\n"]
    parts.append("\n核心概念与机制\n")
    for i, c in enumerate(p["概念"], 1):
        parts.append(f"{i}. {c['name']}\n")
        if c["mech"]:
            parts.append(f"核心机制: {c['mech']}\n")
        rel = [x for x in p["案例"] if c["name"][:4] in x["desc"] or c["name"][:4] in x["point"]]
        for r in rel[:2]:
            parts.append(f"案例: {r['desc']}" + (f"（{r['point']}）" if r["point"] else "") + "\n")
        rel_d = [d for d in p["数据"] if c["name"][:4] in d]
        for d in rel_d[:2]:
            parts.append(f"数据: {d}\n")
        parts.append("\n")
    if p["案例"]:
        parts.append("案例库\n")
        parts += [f"- {x['desc']}" + (f"（{x['point']}）" if x["point"] else "") + "\n" for x in p["案例"]]
        parts.append("\n")
    if p["数据"]:
        parts.append("数据库\n")
        parts += [f"- {d}\n" for d in p["数据"]]
        parts.append("\n")
    parts.append("可引用原句\n")
    parts += [f"- {q}\n" for q in p["原句"]] or ["- （无）\n"]
    return "".join(parts)


def pending_distill_books(sources: list[dict]) -> list[dict]:
    """需蒸馏者: epub 全书, 或 >2万字 txt; 且同名 .蒸馏.txt 尚不存在."""
    def _base(fn: str) -> str:
        return clean_book_title(fn.rsplit(".", 1)[0].replace(DISTILL_SUFFIX, ""))
    have = {_base(s["filename"]) for s in sources if DISTILL_SUFFIX in s["filename"]}
    out = []
    for s in sources:
        if DISTILL_SUFFIX in s["filename"]:
            continue
        if s["ext"] == "epub" or (s["ext"] in ("txt", "md") and s["size"] > _FULL_TEXT_MIN * 3):
            if _base(s["filename"]) not in have:
                out.append(s)
    return out


# ── 后台批次 (线程 + 状态轮询) ───────────────────────────────────
import threading

_BATCH: dict = {"running": False, "progress": {}, "done": [], "error": None, "events": []}


def _evt(msg: str, level: str = "info", **extra) -> None:
    """关键节点事件: 环形缓冲 (轮询兜底) + SSE 总线 (channel=distill)."""
    from app.services.director_events import publish
    e = {"ts": time.strftime("%H:%M:%S"), "level": level, "msg": msg, **extra}
    _BATCH["events"].append(e)
    if len(_BATCH["events"]) > 300:
        _BATCH["events"] = _BATCH["events"][-300:]
    publish("distill", e)


def batch_status() -> dict:
    return _BATCH


def clear_state() -> dict:
    """清空蒸馏状态/事件缓冲 (2026-08-20): 前端确认完成后调用, 恢复正常页面."""
    if _BATCH["running"]:
        raise RuntimeError("蒸馏运行中, 不能清空")
    _BATCH.update(running=False, done=[], error=None, progress={}, events=[])
    return _BATCH


def start_batch(root: str) -> dict:
    if _BATCH["running"]:
        raise RuntimeError("蒸馏批次已在运行")
    _BATCH.update(running=True, done=[], error=None, progress={}, events=[])
    threading.Thread(target=_run_batch, args=(root,), daemon=True).start()
    return _BATCH


# ── 单本蒸馏 (2026-08-20): 复用批量线程/状态/SSE 模式, 与批量互斥 ──
def start_single(path: str | Path, root: str) -> dict:
    """单本书蒸馏: 拉起本地 Gemma → 蒸馏 → 写 .蒸馏.txt → 腾卡."""
    if _BATCH["running"]:
        raise RuntimeError("已有蒸馏任务在运行")
    _BATCH.update(running=True, done=[], error=None, progress={}, events=[])
    threading.Thread(target=_run_single, args=(path, root), daemon=True).start()
    return _BATCH


def _run_single(path: str | Path, root: str) -> None:
    p = Path(path)
    try:
        title = clean_book_title(p.stem)
        _evt(f"▶ 《{title}》 单本蒸馏开始", "ok")
        client, started = ensure_gemma()
        _evt("llama-server " + ("自启完成 (17G 载入)" if started else "复用已运行实例"), "ok")
        t0 = time.monotonic()
        essence = distill_book(
            p, client, _BATCH["progress"],
            cb=lambda m: _evt(f"《{title}》 {m}"))
        out = Path(root) / f"{clean_book_title(Path(p.name).stem)}{DISTILL_SUFFIX}.txt"
        out.write_text(essence, encoding="utf-8")
        _BATCH["done"].append(out.name)
        _evt(f"✓ 《{title}》 → {out.name} ({len(essence)}字, {time.monotonic()-t0:.0f}s)", "ok",
             type="distill_done")
    except Exception as exc:
        logger.exception("[distill] 单本蒸馏失败: %s", p.name)
        _BATCH["error"] = str(exc)
        _BATCH["done"].append(f"{p.name} FAILED: {exc}")
        _evt(f"✗ 《{p.stem}》 蒸馏失败: {exc}", "error", type="distill_error")
    finally:
        try:
            killed = shutdown_gemma_all()  # 与批量一致: 结束全杀腾卡
            if killed:
                _evt(f"已释放显存 (kill {killed})", "ok")
        except Exception:
            pass
        _BATCH["running"] = False


def _run_batch(root: str) -> None:
    from app.services.book_service.reader import scan_book_sources
    try:
        pend = pending_distill_books(scan_book_sources(root))
        _BATCH["progress"] = {"total": len(pend), "book": "", "chapter": ""}
        if not pend:
            _evt("无待蒸馏任务 (全书均已有精华)", "warn")
            _publish_done()
            return
        _evt(f"批量蒸馏启动: {len(pend)} 本待处理", "ok")
        client, started = ensure_gemma()
        _evt("llama-server " + ("自启完成 (17G 载入)" if started else "复用已运行实例"), "ok")
        for i, s in enumerate(pend, 1):
            title = s["book_title"]
            t0 = time.monotonic()
            _evt(f"▶ {i}/{len(pend)} 《{title}》 开始蒸馏")
            try:
                essence = distill_book(
                    s["path"], client, _BATCH["progress"],
                    cb=lambda m: _evt(f"《{title}》 {m}"))
                out = Path(root) / f"{clean_book_title(Path(s['filename']).stem)}{DISTILL_SUFFIX}.txt"
                out.write_text(essence, encoding="utf-8")
                _BATCH["done"].append(out.name)
                _evt(f"✓ {i}/{len(pend)} 《{title}》 → {out.name} ({len(essence)}字, {time.monotonic()-t0:.0f}s)", "ok")
            except Exception as exc:
                logger.exception("[distill] 失败: %s", s["filename"])
                _BATCH["done"].append(f"{s['filename']} FAILED: {exc}")
                _evt(f"✗ 《{title}》 蒸馏失败: {exc}", "error")
        killed = shutdown_gemma_all()  # 用户决策: 批次结束全杀腾卡
        _evt(f"批次结束: 成功 {len([d for d in _BATCH['done'] if 'FAILED' not in d])}/{len(pend)}; "
             f"kill pids {killed}, 显存已释放", "ok", type="distill_done")
    except Exception as exc:
        logger.exception("[distill] 批次异常")
        _BATCH["error"] = str(exc)
        _evt(f"批次异常: {exc}", "error", type="distill_error")
    finally:
        _BATCH["running"] = False


def _publish_done() -> None:
    _evt("批次结束", "info", type="distill_done")
