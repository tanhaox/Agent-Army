"""
分镜 API 端点 - 分镜卡 CRUD + 提示词生成。
"""

import asyncio
import copy
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from pathlib import Path as FilePath
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.schemas.storyboard import (
    PromptGenerateRequest,
    StoryboardCreate,
    StoryboardResponse,
    StoryboardUpdate,
)
from app.services import storyboard_service
from app.services.storyboard_service import enhance_video_prompt
from app.services.video_prompt_templates import build_standard_prompt, build_negative_prompt
from app.services.storyboard_timing_service import (
    auto_assign_durations,
    analyze_episode_fitness,
    suggest_rhythm_adjustments,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/storyboards", tags=["分镜"])


@router.post(
    "",
    response_model=StoryboardResponse,
    summary="创建分镜卡",
    description="创建一个新的分镜卡。",
)
async def create_storyboard(
    req: StoryboardCreate,
    db: AsyncSession = Depends(get_db),
) -> StoryboardResponse:
    """创建分镜卡。"""
    try:
        fields = req.model_dump()
        # 将 UUID 字符串转存为兼容格式
        if fields.get("script_id"):
            fields["script_id"] = str(fields["script_id"])
        storyboard = await storyboard_service.create_storyboard(db, **fields)
        logger.info("分镜已创建: %s", storyboard.id)
        return StoryboardResponse.model_validate(storyboard)
    except Exception as e:
        logger.error("创建分镜失败: %s", e)
        raise HTTPException(status_code=500, detail=f"创建分镜失败: {e}") from e


@router.get(
    "",
    response_model=list[StoryboardResponse],
    summary="获取分镜列表",
    description="获取所有分镜，可选按 script_id 过滤。",
)
async def list_storyboards(
    script_id: str | None = Query(default=None, description="按剧本 ID 过滤"),
    project_id: str | None = Query(default=None, description="按项目 ID 过滤"),
    db: AsyncSession = Depends(get_db),
) -> list[StoryboardResponse]:
    """获取分镜列表。"""
    try:
        storyboards = await storyboard_service.list_storyboards(
            db, script_id=script_id, project_id=project_id,
        )
        return [StoryboardResponse.model_validate(s) for s in storyboards]
    except Exception as e:
        logger.error("获取分镜列表失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取分镜列表失败: {e}") from e


@router.get(
    "/{storyboard_id}",
    response_model=StoryboardResponse,
    summary="获取分镜详情",
    responses={404: {"description": "分镜不存在"}},
)
async def get_storyboard(
    storyboard_id: str,
    db: AsyncSession = Depends(get_db),
) -> StoryboardResponse:
    """根据 ID 获取分镜详情。"""
    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail=f"分镜 {storyboard_id} 不存在")
    return StoryboardResponse.model_validate(storyboard)


@router.put(
    "/{storyboard_id}",
    response_model=StoryboardResponse,
    summary="更新分镜信息",
    responses={404: {"description": "分镜不存在"}},
)
async def update_storyboard(
    storyboard_id: str,
    req: StoryboardUpdate,
    db: AsyncSession = Depends(get_db),
) -> StoryboardResponse:
    """更新分镜信息。"""
    try:
        storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
        if storyboard is None:
            raise HTTPException(status_code=404, detail=f"分镜 {storyboard_id} 不存在")

        fields = {k: v for k, v in req.model_dump().items() if v is not None}
        if fields.get("script_id"):
            fields["script_id"] = str(fields["script_id"])
        storyboard = await storyboard_service.update_storyboard(db, storyboard, **fields)
        logger.info("分镜已更新: %s", storyboard_id)
        return StoryboardResponse.model_validate(storyboard)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("更新分镜失败: %s — %s", storyboard_id, e)
        raise HTTPException(status_code=500, detail=f"更新分镜失败: {e}") from e


@router.delete(
    "/{storyboard_id}",
    summary="删除分镜",
    responses={404: {"description": "分镜不存在"}},
)
async def delete_storyboard(
    storyboard_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """删除分镜。"""
    try:
        storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
        if storyboard is None:
            raise HTTPException(status_code=404, detail=f"分镜 {storyboard_id} 不存在")

        await storyboard_service.delete_storyboard(db, storyboard)
        logger.info("分镜已删除: %s (第%d集 第%d镜)", storyboard_id, storyboard.episode_no, storyboard.shot_no)
        return {"detail": f"分镜 (第{storyboard.episode_no}集 第{storyboard.shot_no}镜) 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("删除分镜失败: %s — %s", storyboard_id, e)
        raise HTTPException(status_code=500, detail=f"删除分镜失败: {e}") from e


@router.post(
    "/generate-prompt",
    summary="生成视频提示词",
    description="根据分镜参数生成英文视频提示词（不保存到数据库）。",
)
async def generate_prompt(
    req: PromptGenerateRequest,
) -> dict:
    """根据参数生成英文视频提示词。"""
    try:
        prompt_text = storyboard_service.generate_prompt_text(req.model_dump())
        logger.info("提示词已生成: %s", prompt_text[:80])
        return {"prompt_text": prompt_text}
    except Exception as e:
        logger.error("生成提示词失败: %s", e)
        raise HTTPException(status_code=500, detail=f"生成提示词失败: {e}") from e


@router.post(
    "/{storyboard_id}/regenerate-prompt",
    summary="重新生成并保存视频提示词",
    description="使用模板重新生成指定分镜的英文视频提示词并保存到数据库。",
)
async def regenerate_prompt(
    storyboard_id: str,
    db: AsyncSession = Depends(get_db),
) -> StoryboardResponse:
    """重新生成分镜的提示词并保存（模板版）。"""
    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail=f"分镜 {storyboard_id} 不存在")

    item = {
        "shot_type": storyboard.shot_type,
        "camera_move": storyboard.camera_move,
        "action": storyboard.action,
        "emotion": storyboard.emotion,
        "environment": storyboard.environment,
        "lighting": storyboard.lighting,
        "vfx": storyboard.vfx or "无",
    }
    prompt_text = storyboard_service.generate_prompt_text(item)
    negative = build_negative_prompt(item)

    storyboard = await storyboard_service.update_storyboard(
        db, storyboard, prompt_text=prompt_text, negative_prompt=negative,
    )
    logger.info("提示词已重新生成并保存: %s", storyboard_id)
    return StoryboardResponse.model_validate(storyboard)


@router.post(
    "/{storyboard_id}/enhance-prompt",
    summary="DeepSeek 增强提示词",
    description="调用 DeepSeek 生成增强版视频提示词（含标准版/增强版/负面提示）。",
)
async def enhance_prompt(
    storyboard_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """调用 DeepSeek 增强分镜提示词。"""
    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail=f"分镜 {storyboard_id} 不存在")

    item = {
        "shot_type": storyboard.shot_type,
        "camera_move": storyboard.camera_move,
        "action": storyboard.action,
        "emotion": storyboard.emotion,
        "environment": storyboard.environment,
        "lighting": storyboard.lighting,
        "vfx": storyboard.vfx or "无",
    }

    result = await enhance_video_prompt(item)

    # 保存增强版到数据库
    update_fields = {"prompt_text": result["enhanced"]}
    if result.get("negative_prompt"):
        update_fields["negative_prompt"] = result["negative_prompt"]

    await storyboard_service.update_storyboard(db, storyboard, **update_fields)
    logger.info("DeepSeek 增强提示词已保存: %s", storyboard_id)

    return result


@router.post(
    "/auto-assign-durations",
    summary="自动分配时长",
    description="为指定项目的所有分镜自动分配时长，按集分组计算。",
)
async def auto_assign_durations_api(
    project_id: str = Query(..., description="项目 ID"),
    target_duration: int = Query(default=75, ge=30, le=300, description="每集目标时长(秒)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """自动分配时长。"""
    from collections import defaultdict

    storyboards = await storyboard_service.list_storyboards(db, project_id=project_id)
    if not storyboards:
        raise HTTPException(status_code=404, detail="该项目暂无分镜")

    # 按集分组
    episodes: dict[int, list] = defaultdict(list)
    for sb in storyboards:
        episodes[sb.episode_no].append(sb)

    updated_count = 0
    for ep_no, ep_sbs in episodes.items():
        items = [
            {
                "shot_type": s.shot_type,
                "camera_move": s.camera_move,
                "emotion": s.emotion,
                "action": s.action,
            }
            for s in ep_sbs
        ]
        auto_assign_durations(items, total_episode_duration=target_duration)

        for sb, item in zip(ep_sbs, items):
            await storyboard_service.update_storyboard(
                db, sb,
                duration_seconds=item["duration_seconds"],
                is_key_moment=item["is_key_moment"],
            )
            updated_count += 1

    logger.info("自动分配时长完成: project=%s, %d条更新", project_id, updated_count)
    return {"detail": f"已为 {updated_count} 个分镜分配时长", "updated_count": updated_count}


@router.get(
    "/rhythm-analysis/{project_id}",
    summary="节奏分析",
    description="分析项目所有分镜的节奏，返回适配性报告和爆款建议。",
)
async def rhythm_analysis(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """节奏分析。"""
    from collections import defaultdict

    storyboards = await storyboard_service.list_storyboards(db, project_id=project_id)
    if not storyboards:
        raise HTTPException(status_code=404, detail="该项目暂无分镜")

    episodes: dict[int, list[dict]] = defaultdict(list)
    for sb in storyboards:
        episodes[sb.episode_no].append({
            "episode_no": sb.episode_no,
            "shot_no": sb.shot_no,
            "shot_type": sb.shot_type,
            "camera_move": sb.camera_move,
            "emotion": sb.emotion,
            "action": sb.action,
            "duration_seconds": sb.duration_seconds or 5,
            "is_key_moment": sb.is_key_moment or False,
        })

    result = suggest_rhythm_adjustments(episodes, total_episodes=len(episodes))
    return result


# ========== 镜头制作（素材预审 + 视频生成）端点 ==========


@router.post(
    "/{storyboard_id}/materials/{req_id}/generate",
    response_model=StoryboardResponse,
    summary="生成单个素材图片",
    description="按需生成指定素材的图片，使用 Seedream 文生图。",
    responses={404: {"description": "分镜或素材不存在"}, 500: {"description": "图片生成失败"}},
)
async def generate_material_image(
    storyboard_id: str,
    req_id: str,
    body: dict = {},
    db: AsyncSession = Depends(get_db),
) -> StoryboardResponse:
    from app.services.seedream_service import SeedreamClient, SeedreamConnectionError, SeedreamGenerationError

    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="分镜不存在")

    analysis = copy.deepcopy(storyboard.director_analysis)
    if not analysis or "material_requirements" not in analysis:
        raise HTTPException(status_code=400, detail="请先运行智能导演分析")

    # 找到匹配的素材需求
    requirements = analysis["material_requirements"]
    target_idx = None
    for i, req in enumerate(requirements):
        if req.get("id") == req_id:
            target_idx = i
            break
    if target_idx is None:
        raise HTTPException(status_code=404, detail=f"素材 {req_id} 不存在")

    req = requirements[target_idx]
    prompt = body.get("prompt") or req.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="缺少生图提示词")

    rtype = req.get("type", "prop")
    name = req.get("name", req_id)

    try:
        seedream = SeedreamClient()

        # 注入项目视觉风格
        style = None
        if storyboard.project_id:
            from app.services.visual_style_service import (
                get_or_create_style, apply_style_to_prompt, has_style_config,
            )
            style = await get_or_create_style(db, storyboard.project_id)
            if style and has_style_config(style):
                prompt = apply_style_to_prompt(prompt, style)

        # 检测多类型引用，自动切换图生图
        from app.services.material_reference_parser import (
            parse_references, resolve_references, stitch_images,
            build_reference_description,
        )
        clean_prompt, refs = parse_references(prompt)

        # 如果有风格参考图且无其他引用，用图生图模式注入风格
        style_ref_bytes = None
        if style and style.style_reference_image and not refs:
            try:
                import httpx
                style_url = style.style_reference_image
                if not style_url.startswith("http"):
                    style_url = f"http://localhost:8000{style_url}"
                style_resp = httpx.get(style_url, timeout=15)
                style_resp.raise_for_status()
                style_ref_bytes = style_resp.content
            except Exception as e:
                logger.warning("风格参考图下载失败: %s", e)

        if style_ref_bytes:
            final_prompt = clean_prompt + ", style consistent with the reference image"
            image_bytes, _ = await seedream.image_to_image(final_prompt, style_ref_bytes)
            logger.info("风格参考图注入(图生图): material=%s", req_id)
        elif refs and storyboard.project_id:
            resolved = await resolve_references(db, storyboard.project_id, refs)
            if resolved:
                ref_images = [r.image_bytes for r in resolved if r.image_bytes]
                if ref_images:
                    # 附加参考图布局说明到提示词
                    ref_desc = build_reference_description(resolved)
                    final_prompt = clean_prompt + ref_desc if ref_desc else clean_prompt
                    # 多图拼接为一张传入图生图
                    stitched = stitch_images(ref_images)
                    if stitched:
                        image_bytes, _ = await seedream.image_to_image(final_prompt, stitched)
                        ref_names = ", ".join(r.name for r in resolved)
                        logger.info(
                            "图生图模式: %d个引用[%s], prompt=%s",
                            len(resolved), ref_names, final_prompt[:100],
                        )
                    else:
                        image_bytes, _ = await seedream.text_to_image(clean_prompt)
                else:
                    image_bytes, _ = await seedream.text_to_image(prompt)
            else:
                image_bytes, _ = await seedream.text_to_image(prompt)
        else:
            image_bytes, _ = await seedream.text_to_image(prompt)
    except (SeedreamConnectionError, SeedreamGenerationError) as e:
        raise HTTPException(status_code=500, detail=f"图片生成失败: {e}") from e

    # 保存图片文件
    import re as _re
    import time
    save_dir = FilePath("static/storyboards") / storyboard_id[:8]
    save_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _re.sub(r"[^\w]", "_", name)[:20]
    ts = int(time.time())
    filename = f"{rtype}_{safe_name}_{ts}.jpg"
    (save_dir / filename).write_bytes(image_bytes)
    url = f"/static/storyboards/{storyboard_id[:8]}/{filename}"

    # 更新 pregen_materials
    materials = dict(storyboard.pregen_materials or {})
    if rtype == "background":
        materials["background"] = url
    elif rtype == "vfx":
        materials["vfx_ref"] = url
    elif rtype == "prop":
        props = dict(materials.get("props", {}) or {})
        props[name] = url
        materials["props"] = props
    else:
        materials[req_id] = url

    # 更新 director_analysis 中对应项
    req["generated_url"] = url
    req["status"] = "success"
    req["prompt"] = prompt
    analysis["material_requirements"][target_idx] = req

    storyboard = await storyboard_service.update_storyboard(
        db, storyboard,
        director_analysis=analysis,
        pregen_materials=materials,
    )
    logger.info("素材图片已生成: storyboard=%s, material=%s", storyboard_id[:8], req_id)
    return StoryboardResponse.model_validate(storyboard)


@router.put(
    "/{storyboard_id}/materials/{req_id}/prompt",
    response_model=StoryboardResponse,
    summary="更新素材提示词",
    description="修改指定素材的生图提示词。",
)
async def update_material_prompt(
    storyboard_id: str,
    req_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
) -> StoryboardResponse:
    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="分镜不存在")

    prompt = body.get("prompt")
    if prompt is None:
        raise HTTPException(status_code=400, detail="缺少 prompt 字段")

    analysis = copy.deepcopy(storyboard.director_analysis)
    if not analysis or "material_requirements" not in analysis:
        raise HTTPException(status_code=400, detail="请先运行智能导演分析")

    requirements = analysis["material_requirements"]
    found = False
    for i, req in enumerate(requirements):
        if req.get("id") == req_id:
            requirements[i]["prompt"] = prompt
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail=f"素材 {req_id} 不存在")

    storyboard = await storyboard_service.update_storyboard(
        db, storyboard, director_analysis=analysis,
    )
    return StoryboardResponse.model_validate(storyboard)


@router.post(
    "/{storyboard_id}/pregen-materials",
    response_model=StoryboardResponse,
    summary="素材预生成（批量）",
    description="分析镜头需求，调用 Seedream 生成背景/道具/特效参考图。",
    responses={404: {"description": "分镜不存在"}, 500: {"description": "素材生成失败"}},
)
async def pregen_materials(
    storyboard_id: str,
    db: AsyncSession = Depends(get_db),
) -> StoryboardResponse:
    from app.services.material_pregen_service import pregen_materials_for_shot
    from app.services.seedream_service import SeedreamConnectionError, SeedreamGenerationError

    try:
        await pregen_materials_for_shot(db, storyboard_id)
        storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
        return StoryboardResponse.model_validate(storyboard)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except (SeedreamConnectionError, SeedreamGenerationError) as e:
        raise HTTPException(status_code=500, detail=f"素材生成失败: {e}") from e


@router.post(
    "/{storyboard_id}/upload-material",
    response_model=StoryboardResponse,
    summary="上传素材图片",
    description="手动上传素材图片，可关联到智能导演分析的指定素材。",
)
async def upload_material(
    storyboard_id: str,
    file: UploadFile = File(...),
    material_type: str = "background",
    material_id: str | None = Query(default=None, description="关联的素材需求 ID"),
    db: AsyncSession = Depends(get_db),
) -> StoryboardResponse:
    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="分镜不存在")

    content = await file.read()
    save_dir = FilePath("static/storyboards") / storyboard_id[:8]
    save_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{material_type}_{storyboard.shot_no}_{file.filename}"
    (save_dir / filename).write_bytes(content)
    url_path = f"/static/storyboards/{storyboard_id[:8]}/{filename}"

    materials = dict(storyboard.pregen_materials or {})
    if material_type in ("background", "vfx_ref"):
        materials[material_type] = url_path
    else:
        props = dict(materials.get("props", {}) or {})
        props[material_type] = url_path
        materials["props"] = props

    # 如果指定了 material_id，同步更新 director_analysis
    update_fields: dict = {"pregen_materials": materials}
    if material_id and storyboard.director_analysis:
        analysis = copy.deepcopy(storyboard.director_analysis)
        requirements = analysis.get("material_requirements", [])
        for i, req in enumerate(requirements):
            if req.get("id") == material_id:
                requirements[i]["generated_url"] = url_path
                requirements[i]["status"] = "uploaded"
                break
        update_fields["director_analysis"] = analysis

    storyboard = await storyboard_service.update_storyboard(
        db, storyboard, **update_fields,
    )
    logger.info("素材已上传: storyboard=%s, type=%s, material_id=%s", storyboard_id[:8], material_type, material_id)
    return StoryboardResponse.model_validate(storyboard)


@router.post(
    "/{storyboard_id}/generate-video",
    summary="生成镜头视频",
    description="根据提示词和素材调用视频模型生成视频。支持智能导演分析的素材作为多模态输入。",
    responses={400: {"description": "缺少提示词"}, 404: {"description": "分镜不存在"}},
)
@limiter.limit("10/minute")
async def generate_shot_video(
    request: Request,
    storyboard_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    import json

    from app.services.video_task_service import create_video_task, submit_video_task

    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="分镜不存在")

    # 优先使用导演分析的视频指令
    prompt = storyboard.prompt_text
    negative_prompt = storyboard.negative_prompt or ""
    image_urls: list[str] = []
    duration = storyboard.duration_seconds or 5
    aspect_ratio = "9:16"

    director = storyboard.director_analysis
    if director and isinstance(director, dict):
        vi = director.get("video_instruction", {})
        if isinstance(vi, dict):
            if vi.get("prompt"):
                prompt = vi["prompt"]
            if vi.get("negative_prompt"):
                negative_prompt = vi["negative_prompt"]
            if vi.get("duration"):
                duration = vi["duration"]
            if vi.get("aspect_ratio"):
                aspect_ratio = vi["aspect_ratio"]
            # 按引用顺序收集已生成的素材图片
            if vi.get("images"):
                image_urls = _collect_image_urls_by_instruction(
                    vi["images"],
                    director.get("material_requirements", []),
                )

    # 兼容旧格式：无 images 引用时回退到全量收集
    if not image_urls:
        image_urls = _collect_image_urls_legacy(storyboard.pregen_materials)

    # 注入项目视觉风格
    if storyboard.project_id:
        from app.services.visual_style_service import (
            get_or_create_style, apply_style_to_prompt, has_style_config,
        )
        style = await get_or_create_style(db, storyboard.project_id)
        if style and has_style_config(style):
            prompt = apply_style_to_prompt(prompt, style, is_video=True)
            if style.style_reference_image:
                ref_url = style.style_reference_image
                if not ref_url.startswith("http"):
                    ref_url = f"http://localhost:8000{ref_url}"
                image_urls.insert(0, ref_url)
                logger.info("风格参考图注入视频: project=%s", storyboard.project_id[:8])

    # 过滤掉外部不可访问的本地 URL（Seedance 服务器无法下载 localhost）
    image_urls = [u for u in image_urls if not _is_local_url(u)]
    if not image_urls:
        logger.info("无公开可访问的参考图片，使用纯文本生视频")

    if not prompt:
        raise HTTPException(status_code=400, detail="缺少视频提示词，请先生成提示词")

    task = await create_video_task(
        db,
        storyboard_id=storyboard_id,
        prompt=prompt,
        negative_prompt=negative_prompt,
        duration=str(duration),
        aspect_ratio=aspect_ratio,
        project_id=storyboard.project_id,
        image_urls=image_urls[:9],
    )
    await submit_video_task(db, task)

    await storyboard_service.update_storyboard(
        db, storyboard,
        video_status="generating",
        video_task_id=str(task.id),
    )

    logger.info("视频生成任务已提交: storyboard=%s, task=%s, images=%d", storyboard_id[:8], task.id, len(image_urls))
    return {"task_id": str(task.id), "storyboard_id": storyboard_id, "status": "generating"}


# ── 批量视频生成 ──────────────────────────────────────────

# 模块级信号量，按需初始化
_batch_semaphore: asyncio.Semaphore | None = None


def _get_batch_semaphore() -> asyncio.Semaphore:
    """获取或创建批量生成并发控制信号量。"""
    global _batch_semaphore
    if _batch_semaphore is None:
        from app.core.config import get_settings
        max_c = getattr(get_settings(), "SEEDANCE_MAX_CONCURRENT", 3)
        _batch_semaphore = asyncio.Semaphore(max_c)
    return _batch_semaphore


async def _generate_one_video(
    storyboard_id: str,
    sem: asyncio.Semaphore,
) -> dict:
    """带并发控制的单镜头视频生成。"""
    async with sem:
        from app.core.database import get_session_maker
        session_maker = get_session_maker()
        async with session_maker() as db:
            try:
                storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
                if storyboard is None:
                    return {"storyboard_id": storyboard_id, "status": "error", "detail": "分镜不存在"}
                if not storyboard.prompt_text:
                    return {"storyboard_id": storyboard_id, "status": "error", "detail": "缺少提示词"}

                prompt = storyboard.prompt_text
                negative_prompt = storyboard.negative_prompt or ""
                image_urls: list[str] = []
                duration = storyboard.duration_seconds or 5
                aspect_ratio = "9:16"

                director = storyboard.director_analysis
                if director and isinstance(director, dict):
                    vi = director.get("video_instruction", {})
                    if isinstance(vi, dict):
                        if vi.get("prompt"):
                            prompt = vi["prompt"]
                        if vi.get("negative_prompt"):
                            negative_prompt = vi["negative_prompt"]
                        if vi.get("duration"):
                            duration = vi["duration"]
                        if vi.get("aspect_ratio"):
                            aspect_ratio = vi["aspect_ratio"]
                        if vi.get("images"):
                            image_urls = _collect_image_urls_by_instruction(
                                vi["images"], director.get("material_requirements", []),
                            )

                if not image_urls:
                    image_urls = _collect_image_urls_legacy(storyboard.pregen_materials)

                if storyboard.project_id:
                    from app.services.visual_style_service import (
                        get_or_create_style, apply_style_to_prompt, has_style_config,
                    )
                    style = await get_or_create_style(db, storyboard.project_id)
                    if style and has_style_config(style):
                        prompt = apply_style_to_prompt(prompt, style, is_video=True)
                        if style.style_reference_image:
                            ref_url = style.style_reference_image
                            if not ref_url.startswith("http"):
                                ref_url = f"http://localhost:8000{ref_url}"
                            image_urls.insert(0, ref_url)

                image_urls = [u for u in image_urls if not _is_local_url(u)]

                from app.services.video_task_service import create_video_task, submit_video_task
                task = await create_video_task(
                    db, storyboard_id=storyboard_id, prompt=prompt,
                    negative_prompt=negative_prompt, duration=str(duration),
                    aspect_ratio=aspect_ratio, project_id=storyboard.project_id,
                    image_urls=image_urls[:9],
                )
                await submit_video_task(db, task)

                await storyboard_service.update_storyboard(
                    db, storyboard, video_status="generating", video_task_id=str(task.id),
                )

                logger.info("批量-视频任务已提交: storyboard=%s, task=%s", storyboard_id[:8], task.id)
                return {"storyboard_id": storyboard_id, "task_id": str(task.id), "status": "generating"}

            except Exception as e:
                logger.error("批量-视频生成失败: storyboard=%s, %s", storyboard_id[:8], e)
                return {"storyboard_id": storyboard_id, "status": "error", "detail": str(e)}


@router.post(
    "/batch-generate-videos",
    summary="批量生成视频",
    description="一次性提交多个镜头的视频生成任务，支持并发控制。",
)
@limiter.limit("5/minute")
async def batch_generate_videos(
    request: Request,
    body: dict,
) -> list[dict]:
    """
    批量生成视频。

    body: { "storyboard_ids": ["id1","id2"], "concurrency": 3 }
    返回每个镜头的 task_id 和初始状态。
    """
    storyboard_ids = body.get("storyboard_ids", [])
    concurrency = body.get("concurrency", 3)

    if not storyboard_ids:
        raise HTTPException(status_code=400, detail="storyboard_ids 不能为空")
    if len(storyboard_ids) > 20:
        raise HTTPException(status_code=400, detail="单次最多提交 20 个镜头")

    sem = asyncio.Semaphore(concurrency)
    logger.info("批量视频生成: %d个镜头, 并发=%d", len(storyboard_ids), concurrency)

    tasks = [_generate_one_video(sid, sem) for sid in storyboard_ids]
    results = await asyncio.gather(*tasks)
    return results


@router.get(
    "/batch-status",
    summary="批量查询视频生成状态",
    description="根据 storyboard_ids 查询参数返回所有镜头的视频生成状态。",
)
async def batch_video_status(
    storyboard_ids: str = Query(..., description="逗号分隔的镜头 ID 列表"),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """批量查询视频状态。"""
    from app.services.video_task_service import get_video_task

    ids = [s.strip() for s in storyboard_ids.split(",") if s.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="storyboard_ids 不能为空")
    if len(ids) > 20:
        raise HTTPException(status_code=400, detail="单次最多查询 20 个镜头")

    results: list[dict] = []
    for sid in ids:
        storyboard = await storyboard_service.get_storyboard(db, sid)
        if storyboard is None:
            results.append({"storyboard_id": sid, "status": "error", "detail": "分镜不存在"})
            continue

        entry: dict = {
            "storyboard_id": sid,
            "episode_no": storyboard.episode_no,
            "shot_no": storyboard.shot_no,
            "video_status": storyboard.video_status,
            "video_url": storyboard.video_url,
            "video_task_id": storyboard.video_task_id,
        }

        if storyboard.video_task_id:
            task = await get_video_task(db, storyboard.video_task_id)
            if task:
                entry["task_status"] = task.status
                entry["video_url"] = task.video_url or task.output_url or storyboard.video_url

        results.append(entry)

    return results


@router.get(
    "/{storyboard_id}/video-status",
    summary="查询视频生成状态",
)
async def get_video_status(
    storyboard_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.services.video_task_service import get_video_task
    from app.models.video_task import TASK_STATUS_FAILED, TASK_STATUS_PENDING, TASK_STATUS_PROCESSING, TASK_STATUS_SUCCESS

    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="分镜不存在")

    task_id = storyboard.video_task_id
    if not task_id:
        return {"status": storyboard.video_status, "video_url": storyboard.video_url}

    task = await get_video_task(db, task_id)
    if task is None:
        return {"status": "unknown", "video_url": None}

    # 如果任务成功且 storyboard 尚未更新，同步状态
    if task.status == TASK_STATUS_SUCCESS and storyboard.video_status != "success":
        video_url = task.video_url or task.output_url
        await storyboard_service.update_storyboard(
            db, storyboard,
            video_status="success",
            video_url=video_url,
        )
    elif task.status == TASK_STATUS_FAILED and storyboard.video_status != "failed":
        await storyboard_service.update_storyboard(
            db, storyboard, video_status="failed",
        )


    # 将中间任务状态归一化为 generating，前端模板只处理 generating/success/failed
    if task.status in (TASK_STATUS_PENDING, TASK_STATUS_PROCESSING):
        display_status = "generating"
    else:
        display_status = task.status

    resolved_url = (task.video_url or task.output_url) if task.status == TASK_STATUS_SUCCESS else None
    return {
        "status": display_status,
        "video_url": resolved_url,
        "task_id": str(task.id),
    }


@router.get(
    "/{storyboard_id}/video-candidates",
    summary="获取候选视频列表",
    description="返回该分镜所有成功生成的视频列表，用于多版本对比选择。",
)
async def get_video_candidates(
    storyboard_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """获取分镜所有成功视频候选。"""
    from app.models.video_task import VideoTask, TASK_STATUS_SUCCESS

    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail=f"分镜 {storyboard_id} 不存在")

    result = await db.execute(
        select(VideoTask)
        .where(
            VideoTask.storyboard_id == storyboard_id,
            VideoTask.status == TASK_STATUS_SUCCESS,
        )
        .order_by(VideoTask.created_at.desc())
    )
    tasks = result.scalars().all()

    return [
        {
            "task_id": str(t.id),
            "video_url": t.output_url or t.video_url,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "duration": t.duration,
            "mode": t.mode,
            "aspect_ratio": t.aspect_ratio,
        }
        for t in tasks
    ]


@router.get(
    "/{storyboard_id}/video-candidates/{task_id}/download",
    summary="下载候选视频",
    description="代理下载指定候选视频，文件名自动包含第N集第N镜编号。",
    responses={404: {"description": "分镜或任务不存在"}, 400: {"description": "视频URL为空"}},
)
async def download_video_candidate(
    storyboard_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """代理下载视频，Content-Disposition 自动包含分镜编号。"""
    import httpx
    from urllib.parse import quote
    from fastapi.responses import StreamingResponse

    from app.models.video_task import VideoTask

    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail=f"分镜 {storyboard_id} 不存在")

    result = await db.execute(
        select(VideoTask).where(VideoTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail=f"视频任务 {task_id} 不存在")

    video_url = task.output_url or task.video_url
    if not video_url:
        raise HTTPException(status_code=400, detail="该任务的视频 URL 为空")

    filename = f"第{storyboard.episode_no}集第{storyboard.shot_no}镜.mp4"
    encoded_filename = quote(filename)

    # 优先使用本地文件
    if task.output_url and not task.output_url.startswith("http"):
        from fastapi.responses import FileResponse
        from pathlib import Path
        file_path = Path(task.output_url.lstrip("/"))
        if file_path.exists():
            return FileResponse(file_path, media_type="video/mp4", filename=filename)

    async def stream_video():
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("GET", video_url, follow_redirects=True) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk

    return StreamingResponse(
        stream_video(),
        media_type="video/mp4",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )


@router.get(
    "/{storyboard_id}/video-candidates/{task_id}/stream",
    summary="代理播放候选视频",
    description="代理流式播放视频，签名 URL 过期时自动刷新。",
)
async def stream_video_candidate(
    storyboard_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """代理流式播放视频，用于前端 video 标签。"""
    import httpx
    from fastapi.responses import StreamingResponse

    from app.models.video_task import VideoTask

    result = await db.execute(
        select(VideoTask).where(VideoTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail=f"视频任务 {task_id} 不存在")

    video_url = task.output_url or task.video_url
    if not video_url:
        raise HTTPException(status_code=400, detail="该任务的视频 URL 为空")

    # 如果有本地文件，直接返回 FileResponse（无需代理）
    if task.output_url and not task.output_url.startswith("http"):
        from fastapi.responses import FileResponse
        from pathlib import Path
        file_path = Path(task.output_url.lstrip("/"))
        if file_path.exists():
            return FileResponse(file_path, media_type="video/mp4")

    # 外部 URL：检查是否过期，过期则尝试刷新
    url_ok = False
    async with httpx.AsyncClient(timeout=15) as client:
        head_resp = await client.head(video_url, follow_redirects=True)
        if head_resp.status_code == 200:
            url_ok = True
        elif head_resp.status_code in (403, 410) and task.provider_task_id:
            new_url = await _refresh_video_url(db, task)
            if new_url and new_url != video_url:
                check_resp = await client.head(new_url, follow_redirects=True)
                if check_resp.status_code == 200:
                    video_url = new_url
                    url_ok = True
            # 即使 API 返回同 URL，也尝试直接 GET（部分 CDN HEAD 不可用但 GET 可用）
            if not url_ok:
                try:
                    test_resp = await client.get(video_url, follow_redirects=True)
                    if test_resp.status_code == 200 and len(test_resp.content) > 1024:
                        url_ok = True
                except Exception:
                    pass

    if not url_ok:
        raise HTTPException(status_code=410, detail="视频链接已过期，请重新生成视频")

    async def stream_all():
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("GET", video_url, follow_redirects=True) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    yield chunk

    return StreamingResponse(
        stream_all(),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
        },
    )


async def _refresh_video_url(db, task) -> str | None:
    """通过 provider_task_id 重新获取视频 URL。"""
    from app.services.seedance_video_service import SeedanceClient
    from app.core.config import get_settings

    settings = get_settings()
    try:
        client = SeedanceClient(
            api_key=settings.SEEDANCE_API_KEY or settings.ARK_API_KEY,
            model=settings.SEEDANCE_MODEL,
        )
        result = await client.get_task_status(task.provider_task_id)
        new_url = result.get("video_url")
        if new_url:
            task.video_url = new_url
            await db.commit()
            logger.info("视频 URL 已刷新: task=%s", task.id)
            return new_url
    except Exception as e:
        logger.warning("刷新视频 URL 失败: %s", e)
    return None


@router.put(
    "/{storyboard_id}/audio-config",
    response_model=StoryboardResponse,
    summary="更新音频配置",
)
async def update_audio_config(
    storyboard_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
) -> StoryboardResponse:
    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="分镜不存在")

    audio_config = body.get("audio_config")
    if audio_config is None:
        raise HTTPException(status_code=400, detail="缺少 audio_config")

    storyboard = await storyboard_service.update_storyboard(
        db, storyboard, audio_config=audio_config,
    )
    return StoryboardResponse.model_validate(storyboard)


@router.post(
    "/{storyboard_id}/director-plan",
    summary="智能导演规划",
    description="基于 LLM 分析分镜上下文，自动规划素材需求和视频生成指令，并调用 Seedream 生成素材图片。",
    responses={404: {"description": "分镜不存在"}, 500: {"description": "分析失败"}},
)
@limiter.limit("5/minute")
async def director_plan(
    request: Request,
    storyboard_id: str,
    body: dict = {},
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.services.intelligent_director_service import analyze_and_plan

    regenerate = body.get("regenerate", False)
    try:
        result = await analyze_and_plan(db, storyboard_id, regenerate=regenerate)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("智能导演分析失败: %s — %s", storyboard_id, e)
        raise HTTPException(status_code=500, detail=f"智能导演分析失败: {e}") from e


@router.put(
    "/{storyboard_id}/director-analysis",
    response_model=StoryboardResponse,
    summary="更新导演分析结果",
    description="更新 director_analysis 字段（如删除素材引用后保存）。",
)
async def update_director_analysis(
    storyboard_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
) -> StoryboardResponse:
    if "director_analysis" not in body:
        raise HTTPException(status_code=400, detail="缺少 director_analysis 字段")
    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise HTTPException(status_code=404, detail="分镜不存在")
    storyboard = await storyboard_service.update_storyboard(
        db, storyboard,
        director_analysis=body["director_analysis"],
    )
    return StoryboardResponse.model_validate(storyboard)


# ── 视频生成辅助函数 ──────────────────────────────────────


def _is_local_url(url: str) -> bool:
    """判断 URL 是否为外部不可访问的本地地址。"""
    lowered = url.lower()
    return any(
        host in lowered
        for host in ("localhost", "127.0.0.1", "0.0.0.0", "host.docker.internal")
    )


def _collect_image_urls_by_instruction(
    images_instruction: list[dict],
    material_requirements: list[dict],
) -> list[str]:
    """按 video_instruction.images 的引用顺序收集已生成素材的 URL。"""
    base = "http://localhost:8000"
    req_map = {r.get("id"): r for r in material_requirements}
    urls: list[str] = []
    for img_ref in sorted(images_instruction, key=lambda x: x.get("material_index", 0)):
        req = req_map.get(img_ref.get("material_id"))
        if not req:
            logger.warning("视频引用素材 %s 未找到", img_ref.get("material_id"))
            continue
        if req.get("status") not in ("success", "uploaded") or not req.get("generated_url"):
            logger.warning("视频引用素材 %s 未就绪(status=%s), 跳过", img_ref.get("material_id"), req.get("status"))
            continue
        url = req["generated_url"]
        if not url.startswith("http"):
            url = f"{base}{url}"
        urls.append(url)
    return urls


def _collect_image_urls_legacy(pregen_materials: dict | None) -> list[str]:
    """兼容旧格式：从 pregen_materials 收集所有图片 URL。"""
    if not pregen_materials or not isinstance(pregen_materials, dict):
        return []
    base = "http://localhost:8000"
    urls: list[str] = []
    for key, value in pregen_materials.items():
        if key == "props" and isinstance(value, dict):
            for _, v in value.items():
                if isinstance(v, str) and v:
                    urls.append(v if v.startswith("http") else f"{base}{v}")
        elif isinstance(value, str) and value:
            urls.append(value if value.startswith("http") else f"{base}{value}")
    return urls
