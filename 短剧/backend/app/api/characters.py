"""
角色 API 端点 - 角色卡 CRUD + 图片上传 + Seedream 多角度生成。
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.character import (
    CharacterCreate,
    CharacterResponse,
    CharacterUpdate,
    GenerateAnglesRequest,
    GenerateCandidatesRequest,
    GenerateImageRequest,
    SetBaseImageRequest,
)
from app.services import character_service
from app.services.comfyui_service import (
    ComfyUIConnectionError,
    ComfyUIGenerationError,
)
from app.services.seedream_service import (
    SeedreamConnectionError,
    SeedreamGenerationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/characters", tags=["角色"])


@router.post(
    "",
    response_model=CharacterResponse,
    summary="创建角色",
    description="创建一个新的角色卡（数字演员）。",
)
async def create_character(
    req: CharacterCreate,
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """创建角色。"""
    try:
        character = await character_service.create_character(
            db=db,
            name=req.name,
            traits=req.traits,
            voice_id=req.voice_id,
            platform_bindings=req.platform_bindings,
        )
        logger.info("角色已创建: %s (%s)", character.id, character.name)
        return CharacterResponse.model_validate(character)
    except Exception as e:
        logger.error("创建角色失败: %s", e)
        raise HTTPException(status_code=500, detail=f"创建角色失败: {e}") from e


@router.get(
    "",
    response_model=list[CharacterResponse],
    summary="获取角色列表",
)
async def list_characters(
    db: AsyncSession = Depends(get_db),
) -> list[CharacterResponse]:
    """获取所有角色。"""
    try:
        characters = await character_service.list_characters(db)
        return [CharacterResponse.model_validate(c) for c in characters]
    except Exception as e:
        logger.error("获取角色列表失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取角色列表失败: {e}") from e


@router.get(
    "/{character_id}",
    response_model=CharacterResponse,
    summary="获取角色详情",
    responses={404: {"description": "角色不存在"}},
)
async def get_character(
    character_id: str,
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """根据 ID 获取角色详情。"""
    try:
        character = await character_service.get_character(db, character_id)
        if character is None:
            raise HTTPException(status_code=404, detail=f"角色 {character_id} 不存在")
        return CharacterResponse.model_validate(character)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取角色详情失败: %s — %s", character_id, e)
        raise HTTPException(status_code=500, detail=f"获取角色详情失败: {e}") from e


@router.put(
    "/{character_id}",
    response_model=CharacterResponse,
    summary="更新角色信息",
    responses={404: {"description": "角色不存在"}},
)
async def update_character(
    character_id: str,
    req: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """更新角色信息。"""
    try:
        character = await character_service.get_character(db, character_id)
        if character is None:
            raise HTTPException(status_code=404, detail=f"角色 {character_id} 不存在")

        fields = {k: v for k, v in req.model_dump().items() if v is not None}
        character = await character_service.update_character(db, character, **fields)
        logger.info("角色已更新: %s", character_id)
        return CharacterResponse.model_validate(character)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("更新角色失败: %s — %s", character_id, e)
        raise HTTPException(status_code=500, detail=f"更新角色失败: {e}") from e


@router.post(
    "/{character_id}/images",
    response_model=CharacterResponse,
    summary="上传角色参考图",
    description="上传图片并添加到角色的 reference_images 列表。支持 jpg/png/webp，最大 10MB。",
    responses={
        400: {"description": "文件类型不支持或文件过大"},
        404: {"description": "角色不存在"},
    },
)
async def upload_character_image(
    character_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """上传角色参考图。"""
    try:
        character = await character_service.get_character(db, character_id)
        if character is None:
            raise HTTPException(status_code=404, detail=f"角色 {character_id} 不存在")

        content = await file.read()
        filename = file.filename or "upload.jpg"

        try:
            _, url_path = await character_service.save_image(content, filename)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        # 添加到 reference_images 列表
        images = list(character.reference_images or [])
        images.append(url_path)
        character = await character_service.update_character(
            db, character, reference_images=images,
        )
        logger.info("角色参考图已上传: character=%s, image=%s", character_id, url_path)
        return CharacterResponse.model_validate(character)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("上传角色参考图失败: %s — %s", character_id, e)
        raise HTTPException(status_code=500, detail=f"上传角色参考图失败: {e}") from e


@router.delete(
    "/{character_id}",
    summary="删除角色",
    description="删除角色及其所有关联的参考图文件。",
    responses={404: {"description": "角色不存在"}},
)
async def delete_character(
    character_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """删除角色及关联图片。"""
    try:
        character = await character_service.get_character(db, character_id)
        if character is None:
            raise HTTPException(status_code=404, detail=f"角色 {character_id} 不存在")

        await character_service.delete_character(db, character)
        logger.info("角色已删除: %s (%s)", character_id, character.name)
        return {"detail": f"角色 {character.name} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("删除角色失败: %s — %s", character_id, e)
        raise HTTPException(status_code=500, detail=f"删除角色失败: {e}") from e


@router.post(
    "/{character_id}/generate-image",
    response_model=CharacterResponse,
    summary="AI 生成角色参考图",
    description="根据角色特征调用 ComfyUI 生成参考图。支持三种角度：front / three_quarter / side。",
    responses={
        400: {"description": "角度参数无效"},
        404: {"description": "角色不存在"},
        503: {"description": "ComfyUI 服务不可用"},
        500: {"description": "图片生成失败"},
    },
)
async def generate_character_image(
    character_id: str,
    req: GenerateImageRequest,
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """调用 ComfyUI 为角色生成参考图。"""
    from app.services.character_image_service import generate_reference_image

    try:
        await generate_reference_image(db, str(character_id), req.angle)
    except ValueError as e:
        error_msg = str(e)
        if "不存在" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg) from e
        raise HTTPException(status_code=400, detail=error_msg) from e
    except ComfyUIConnectionError as e:
        raise HTTPException(status_code=503, detail=f"ComfyUI 服务不可用: {e}") from e
    except ComfyUIGenerationError as e:
        raise HTTPException(status_code=500, detail=f"图片生成失败: {e}") from e

    # 重新查询角色以获取最新数据
    character = await character_service.get_character(db, character_id)
    return CharacterResponse.model_validate(character)


# ========== Seedream 直接生图端点 ==========


@router.post(
    "/{character_id}/generate-portrait",
    response_model=CharacterResponse,
    summary="用 image_prompt 直接生成角色肖像",
    description="读取角色 traits.image_prompt，调用 Seedream 生图，结果自动存入 reference_images。",
    responses={
        404: {"description": "角色不存在"},
        400: {"description": "角色无 image_prompt"},
        500: {"description": "生成失败"},
    },
)
async def generate_character_portrait(
    character_id: str,
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """用角色的 image_prompt 调用 Seedream 直接生成肖像。"""
    from app.services.seedream_service import SeedreamClient

    character = await character_service.get_character(db, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="角色不存在")

    traits = character.traits or {}
    image_prompt = traits.get("image_prompt", "")
    if not image_prompt:
        raise HTTPException(status_code=400, detail="角色缺少 image_prompt，请先生成角色提示词")

    try:
        client = SeedreamClient()
        image_bytes, _metadata = await client.text_to_image(image_prompt)
    except SeedreamConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Seedream 服务不可用: {e}") from e
    except SeedreamGenerationError as e:
        raise HTTPException(status_code=500, detail=f"生图失败: {e}") from e

    # 保存图片
    filename = f"{character_id[:8]}_portrait.jpg"
    _, url_path = await character_service.save_image(image_bytes, filename)

    # 添加到 reference_images
    images = list(character.reference_images or [])
    images.append({
        "id": url_path,
        "url": url_path,
        "angle": "front",
        "pose": "standing",
        "is_primary": len(images) == 0,
    })
    character = await character_service.update_character(
        db, character, reference_images=images,
    )

    logger.info("角色肖像已生成: %s -> %s", character.name, url_path)
    return CharacterResponse.model_validate(character)


@router.post(
    "/{character_id}/delete-reference-image",
    response_model=CharacterResponse,
    summary="删除角色参考图",
    description="从 reference_images 中删除指定图片记录。",
)
async def delete_reference_image(
    character_id: str,
    body: dict = {},
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """删除角色参考图。"""
    image_id = body.get("image_id", "")
    if not image_id:
        raise HTTPException(status_code=400, detail="缺少 image_id")

    character = await character_service.get_character(db, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="角色不存在")

    images = list(character.reference_images or [])
    new_images = [img for img in images if (img.get("id", "") if isinstance(img, dict) else img) != image_id]
    if len(new_images) == len(images):
        raise HTTPException(status_code=404, detail="参考图不存在")

    character = await character_service.update_character(
        db, character, reference_images=new_images,
    )
    logger.info("参考图已删除: char=%s, image_id=%s", character_id, image_id)
    return CharacterResponse.model_validate(character)


# ========== Seedream 多角度生成端点 ==========


@router.post(
    "/{character_id}/generate-candidates",
    summary="生成角色候选正面照",
    description="使用 Seedream 5.0 生成 1-8 张正面候选照供用户选择基准图。",
    responses={
        404: {"description": "角色不存在"},
        503: {"description": "Seedream 服务不可用"},
        500: {"description": "生成失败"},
    },
)
async def generate_character_candidates(
    character_id: str,
    req: GenerateCandidatesRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """生成角色正面候选照。"""
    from app.services.character_portrait_service import generate_candidates

    try:
        urls = await generate_candidates(db, character_id, req.count, req.prompt_hint)
        # 持久化候选照 URL 到 traits.candidate_images
        character = await character_service.get_character(db, character_id)
        if character:
            traits = dict(character.traits or {})
            traits["candidate_images"] = urls
            await character_service.update_character(db, character, traits=traits)
        return {"character_id": character_id, "candidates": urls, "count": len(urls)}
    except ValueError as e:
        error_msg = str(e)
        if "不存在" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg) from e
        raise HTTPException(status_code=400, detail=error_msg) from e
    except SeedreamConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Seedream 服务不可用: {e}") from e
    except SeedreamGenerationError as e:
        raise HTTPException(status_code=500, detail=f"候选照生成失败: {e}") from e


@router.post(
    "/{character_id}/set-base-image",
    response_model=CharacterResponse,
    summary="设置角色基准图",
    description="从候选照中选择一张作为基准图，用于后续图生图生成多角度。",
    responses={404: {"description": "角色不存在"}},
)
async def set_character_base_image(
    character_id: str,
    req: SetBaseImageRequest,
    db: AsyncSession = Depends(get_db),
) -> CharacterResponse:
    """设置角色基准图。"""
    from app.services.character_portrait_service import set_base_image

    try:
        character = await set_base_image(db, character_id, req.image_url)
        return CharacterResponse.model_validate(character)
    except ValueError as e:
        error_msg = str(e)
        if "不存在" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg) from e
        raise HTTPException(status_code=400, detail=error_msg) from e


@router.post(
    "/{character_id}/generate-angles",
    summary="从基准图生成多角度参考图",
    description="基于基准图使用 Seedream img2img 生成左/右/背/特写等多角度图片。",
    responses={
        400: {"description": "参数无效或未设置基准图"},
        404: {"description": "角色不存在"},
        503: {"description": "Seedream 服务不可用"},
        500: {"description": "生成失败"},
    },
)
async def generate_character_angles(
    character_id: str,
    req: GenerateAnglesRequest = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """基于基准图生成多角度参考图。"""
    from app.services.character_portrait_service import generate_angles_from_base

    if req is None:
        req = GenerateAnglesRequest()
    try:
        angle_urls = await generate_angles_from_base(db, character_id, req.angles)
        # 持久化多角度结果到 traits.angle_images
        character = await character_service.get_character(db, character_id)
        if character:
            traits = dict(character.traits or {})
            existing_angles = dict(traits.get("angle_images", {}) or {})
            existing_angles.update(angle_urls)
            traits["angle_images"] = existing_angles
            await character_service.update_character(db, character, traits=traits)
        return {"character_id": character_id, "angles": angle_urls, "count": len(angle_urls)}
    except ValueError as e:
        error_msg = str(e)
        if "不存在" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg) from e
        raise HTTPException(status_code=400, detail=error_msg) from e
    except SeedreamConnectionError as e:
        raise HTTPException(status_code=503, detail=f"Seedream 服务不可用: {e}") from e
    except SeedreamGenerationError as e:
        raise HTTPException(status_code=500, detail=f"多角度生成失败: {e}") from e
