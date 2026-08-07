"""ComfyUI HTTP client + workflow 同步接口.

约定:
- 不在 54321 Web 之外加新端口
- 不暴露 ComfyUI 内部参数(checkpoint/LoRA 路径)
- 所有 ComfyUI 调用必须走 54321 Web (本 router)

设计:
- 启动期通过 app/services/workflow_sync.py 把项目 workflows/ 同步到 ComfyUI user/default/workflows/
- 提交时按 manifest.yaml 装载 workflow JSON + 注入 inputs
- 轮询 /history/{prompt_id} 拿产物
- 产物落 E:/数字人计划/roles/<role_id>/<view>.png
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import yaml
from fastapi import APIRouter, HTTPException

from ..config import get_config
from ..database import get_session_maker
from ..models import Role, WorkflowSync
from ..schemas import (
    ComfyUISubmitRequest,
    ComfyUISubmitResponse,
    ComfyUIWorkflowInfo,
    GenerateViewsResponse,
    RoleCreate,
    WorkflowSyncOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/comfyui", tags=["comfyui"])

# ---------------------------------------------------------------------------
# Workflow SSOT (项目 → 运行时)
# ---------------------------------------------------------------------------
WORKFLOWS_DIR = Path(__file__).resolve().parents[2] / "workflows"
MANIFEST_PATH = WORKFLOWS_DIR / "manifest.yaml"


def _load_manifest() -> list[dict[str, Any]]:
    """读 manifest.yaml → workflow 列表."""
    if not MANIFEST_PATH.exists():
        logger.warning("manifest.yaml not found at %s", MANIFEST_PATH)
        return []
    raw = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8")) or {}
    wf_list = raw.get("workflows", [])
    return wf_list if isinstance(wf_list, list) else []


def _find_workflow(name: str) -> dict[str, Any] | None:
    """按 name 找 manifest 条目."""
    for wf in _load_manifest():
        if wf.get("name") == name:
            return wf
    return None


def _load_workflow_json(source: str) -> dict[str, Any]:
    """读 workflows/<source>.json."""
    src_path = WORKFLOWS_DIR / source
    if not src_path.exists():
        raise FileNotFoundError(f"Workflow JSON not found: {src_path}")
    return json.loads(src_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Prompt injection
# ---------------------------------------------------------------------------
# character_three_view.json 的 8 个 CLIPTextEncode nodes (widgets_values=空)
# 由 jasonbai 2026-07-26 验证. 描述注入策略: 同一段 description 灌入全部正向 prompt.
# 反向 prompt 节点 (negative) 跳过, 保持空.
_PROMPT_NODE_IDS: list[int] = []
_NEGATIVE_NODE_IDS: list[int] = []


def _detect_prompt_nodes(workflow: dict[str, Any]) -> tuple[list[int], list[int]]:
    """扫一遍 workflow nodes, 把 CLIPTextEncode 节点按方向分类.

    启发式:
    - class_type == "CLIPTextEncode"
    - widgets_values 非空 → 已配置 (视为正向 prompt, 跳过)
    - widgets_values 空 → 占位节点 (按后续负向 prefix 判定)

    注: 当前 character_three_view.json 的 8 个 CLIPTextEncode 全部为空;
    manifest.yaml.output_view_order 决定产物顺序.
    """
    pos: list[int] = []
    neg: list[int] = []
    for node in workflow.get("nodes", []):
        if node.get("type") != "CLIPTextEncode":
            continue
        nid = node.get("id")
        if nid is None:
            continue
        title = (node.get("title") or "").lower()
        if "negative" in title or "neg" in title:
            neg.append(int(nid))
        else:
            pos.append(int(nid))
    return pos, neg


def _inject_inputs(workflow: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    """注入 inputs 到 workflow.

    支持 keys:
    - description: str → 灌入正向 CLIPTextEncode 节点的 widgets_values[0]
    - reference_image: str → 设到 LoadImage 节点的 image 输入(第一个 LoadImage)
    - seed: int → 设到所有 KSampler 节点的 seed
    """
    wf = json.loads(json.dumps(workflow))  # deep copy
    description = inputs.get("description")
    reference_image = inputs.get("reference_image")
    seed = inputs.get("seed")

    pos_ids, neg_ids = _detect_prompt_nodes(wf)
    if description is not None:
        for node in wf.get("nodes", []):
            if node.get("id") in pos_ids:
                wv = node.get("widgets_values") or ["", ""]
                # widgets_values[0] = text, [1] = 通常是某种 flag
                if len(wv) >= 1:
                    wv[0] = str(description)
                else:
                    wv = [str(description)]
                node["widgets_values"] = wv

    if reference_image is not None:
        for node in wf.get("nodes", []):
            if node.get("type") in ("LoadImage", "ImageLoader"):
                inputs_dict = node.get("inputs") or []
                for inp in inputs_dict:
                    if inp.get("name") in ("image", "path", "file"):
                        inp["value"] = str(reference_image)
                node["inputs"] = inputs_dict

    if seed is not None:
        for node in wf.get("nodes", []):
            if node.get("type") == "KSampler":
                wv = node.get("widgets_values") or []
                # KSampler.widgets_values 顺序: seed, steps, cfg, sampler_name, scheduler, denoise
                if len(wv) >= 1:
                    wv[0] = int(seed)
                else:
                    wv.insert(0, int(seed))
                node["widgets_values"] = wv

    return wf


# ---------------------------------------------------------------------------
# HTTP submit + poll
# ---------------------------------------------------------------------------
async def submit_and_wait(
    workflow_payload: dict[str, Any],
    role_id: str | None,
    base_url: str,
    timeout_sec: int,
    output_view_order: list[str] | None = None,
    job_id: str | None = None,
) -> dict[str, Any]:
    """提交 → 轮询 /history/{prompt_id} → 落盘 views.

    返回:
        {"prompt_id": str, "status": "completed"|"failed"|"timeout",
         "views": {"front": "...", "side": "...", "full": "..."},
         "elapsed_sec": float, "error": str|None}
    """
    cfg = get_config()
    roles_root = Path(cfg.defaults.roles_output_root)
    if role_id:
        out_dir = roles_root / role_id
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = roles_root / "ad-hoc"
        out_dir.mkdir(parents=True, exist_ok=True)

    view_order = output_view_order or ["front", "side", "full"]

    t0 = time.time()
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. POST /prompt — ComfyUI 协议要求 body = {"prompt": <wf>, "client_id": <uuid>}
        client_id = str(uuid.uuid4())
        try:
            resp = await client.post(
                f"{base_url.rstrip('/')}/prompt",
                json={"prompt": workflow_payload, "client_id": client_id},
            )
        except httpx.RequestError as exc:
            return {
                "prompt_id": None,
                "status": "failed",
                "views": {},
                "elapsed_sec": 0.0,
                "error": f"ComfyUI unreachable at {base_url}: {exc}",
            }
        if resp.status_code >= 400:
            return {
                "prompt_id": None,
                "status": "failed",
                "views": {},
                "elapsed_sec": 0.0,
                "error": f"ComfyUI /prompt HTTP {resp.status_code}: {resp.text[:300]}",
            }
        try:
            prompt_id = resp.json()["prompt_id"]
        except (KeyError, ValueError) as exc:
            return {
                "prompt_id": None,
                "status": "failed",
                "views": {},
                "elapsed_sec": 0.0,
                "error": f"ComfyUI /prompt malformed response: {exc}; body={resp.text[:200]}",
            }

        logger.info(
            "[comfyui] submitted prompt_id=%s role_id=%s client_id=%s",
            prompt_id, role_id, client_id,
        )

        # 2. 轮询 /history/{prompt_id}
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            await asyncio.sleep(2.0)
            try:
                h = await client.get(f"{base_url.rstrip('/')}/history/{prompt_id}")
            except httpx.RequestError:
                continue
            if h.status_code >= 400:
                continue
            history = h.json() or {}
            entry = history.get(prompt_id)
            if not entry:
                continue
            status_dict = entry.get("status") or {}
            if status_dict.get("completed"):
                outputs = entry.get("outputs") or {}
                views = _persist_outputs(outputs, out_dir, view_order, base_url)
                elapsed = time.time() - t0
                return {
                    "prompt_id": prompt_id,
                    "status": "completed",
                    "views": views,
                    "elapsed_sec": elapsed,
                    "error": None,
                }
            if status_dict.get("errored"):
                err = (entry.get("status") or {}).get("error") or "unknown error"
                return {
                    "prompt_id": prompt_id,
                    "status": "failed",
                    "views": {},
                    "elapsed_sec": time.time() - t0,
                    "error": str(err)[:500],
                }

        return {
            "prompt_id": prompt_id,
            "status": "timeout",
            "views": {},
            "elapsed_sec": time.time() - t0,
            "error": f"timeout after {timeout_sec}s",
        }


def _persist_outputs(
    outputs: dict[str, Any],
    out_dir: Path,
    view_order: list[str],
    base_url: str,
) -> dict[str, str]:
    """把 ComfyUI /history outputs 落盘到 out_dir/<view>.png.

    outputs 结构: {node_id: {"images": [{"filename": "xxx.png", "subfolder": "...", "type": "output"}]}}
    按节点顺序 → view_order 顺序对应, 拷贝到 out_dir/<view>.png.
    返回 {view_name: 绝对路径}.
    """
    all_images: list[Path] = []
    base = base_url.rstrip("/").replace("http://", "").replace("https://", "").split(":")[0]
    comf_output_root = Path(r"E:/AI/ComfyUI_windows_portable/ComfyUI/output")

    for nid, payload in outputs.items():
        imgs = payload.get("images") or []
        for img in imgs:
            fn = img.get("filename")
            sub = img.get("subfolder", "")
            t = img.get("type", "output")
            if not fn:
                continue
            if t == "output":
                src = comf_output_root / sub / fn if sub else comf_output_root / fn
            elif t == "input":
                src = Path(r"E:/AI/ComfyUI_windows_portable/ComfyUI/input") / sub / fn
            elif t == "temp":
                src = Path(r"E:/AI/ComfyUI_windows_portable/ComfyUI/temp") / sub / fn
            else:
                src = comf_output_root / fn
            if src.exists():
                all_images.append(src)

    views: dict[str, str] = {}
    for i, src in enumerate(all_images[: len(view_order)]):
        view_name = view_order[i]
        ext = src.suffix or ".png"
        dest = out_dir / f"{view_name}{ext}"
        try:
            os.replace(str(src), str(dest))
        except OSError:
            shutil.copy2(str(src), str(dest))
            src.unlink(missing_ok=True)
        views[view_name] = str(dest)
    return views


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("/health")
def comfyui_health():
    """探测 ComfyUI 服务是否在线 (GET /) 并返回本机 ffmpeg 状态."""
    cfg = get_config()
    base = cfg.defaults.base_url_comfyui
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(base.rstrip("/") + "/")
        online = True
        status_code = r.status_code
        error = None
    except httpx.RequestError as exc:
        online = False
        status_code = None
        error = str(exc)
    return {
        "online": online,
        "base_url": base,
        "status_code": status_code,
        "error": error,
        "ffmpeg": shutil.which("ffmpeg"),
        "ffprobe": shutil.which("ffprobe"),
    }


@router.get("/workflows", response_model=list[ComfyUIWorkflowInfo])
def list_workflows():
    """列 manifest.yaml 中的 workflow."""
    return [ComfyUIWorkflowInfo(**wf) for wf in _load_manifest()]


@router.post("/submit", response_model=ComfyUISubmitResponse)
async def comfyui_submit(body: ComfyUISubmitRequest):
    """通用 workflow 提交 (测试 / 调试用).

    body.workflow_name → 找 manifest 条目 → 装入 JSON → 注入 inputs → 轮询 → 落盘.
    body.role_id 决定产物落到哪个角色目录.
    """
    cfg = get_config()
    wf_meta = _find_workflow(body.workflow_name)
    if not wf_meta:
        raise HTTPException(status_code=404, detail=f"workflow not in manifest: {body.workflow_name}")

    try:
        wf_json = _load_workflow_json(wf_meta["source"])
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    role_id = body.role_id
    if role_id:
        # 验证 role 存在
        Session = get_session_maker()
        if Session is None:
            raise HTTPException(status_code=500, detail="DB not initialized")
        with Session() as db:
            role = db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail=f"role not found: {role_id}")
            # 若 inputs 没传 description, 用角色 description
            if "description" not in body.inputs and role.description:
                body.inputs["description"] = role.description
            if "reference_image" not in body.inputs and role.reference_image:
                body.inputs["reference_image"] = role.reference_image
            if "seed" not in body.inputs and role.seed is not None:
                body.inputs["seed"] = role.seed

    payload = _inject_inputs(wf_json, body.inputs)

    result = await submit_and_wait(
        workflow_payload=payload,
        role_id=role_id,
        base_url=cfg.defaults.base_url_comfyui,
        timeout_sec=cfg.defaults.comfyui_timeout_sec,
        output_view_order=wf_meta.get("output_view_order"),
    )

    return ComfyUISubmitResponse(**result)


@router.post("/workflows/sync")
def workflows_sync():
    """手动触发同步 — 项目 → ComfyUI user/default/workflows/.

    由 app/services/workflow_sync.py 实现真正的 sha256 对比逻辑;
    本路由作为外部触发入口.
    """
    from ..services.workflow_sync import sync_workflows_on_startup

    results = sync_workflows_on_startup()
    return {"synced": results}


@router.put("/workflows/{name}/pull")
def workflow_pull(name: str):
    """运行时 → 项目回流: 复制 ComfyUI user/default/workflows/<name>.json
    到项目 workflows/<source>, 用于在 ComfyUI UI 调参后回项目.

    注: 本端点当前保留为手动入口, 自动化留给后续 backlog.
    """
    wf_meta = _find_workflow(name)
    if not wf_meta:
        raise HTTPException(status_code=404, detail=f"workflow not in manifest: {name}")
    runtime_path = Path(wf_meta["runtime_path"])
    project_path = WORKFLOWS_DIR / wf_meta["source"]
    if not runtime_path.exists():
        raise HTTPException(status_code=400, detail=f"runtime workflow missing: {runtime_path}")
    project_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(runtime_path), str(project_path))

    # 记录 workflow_syncs
    Session = get_session_maker()
    if Session is None:
        return {"status": "ok", "note": "DB unavailable, but file copied"}
    with Session() as db:
        rec = WorkflowSync(
            workflow_name=name,
            source_sha256=_sha256(project_path),
            runtime_sha256=_sha256(runtime_path),
            synced=True,
            reason="pull",
        )
        db.add(rec)
        db.commit()
    return {"status": "ok", "project_path": str(project_path)}


def _sha256(p: Path) -> str | None:
    if not p.exists():
        return None
    import hashlib
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


@router.get("/syncs", response_model=list[WorkflowSyncOut])
def list_syncs(limit: int = 50):
    """最近 N 条同步审计记录."""
    Session = get_session_maker()
    if Session is None:
        return []
    with Session() as db:
        rows = db.query(WorkflowSync).order_by(WorkflowSync.id.desc()).limit(limit).all()
        return rows