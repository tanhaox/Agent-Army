import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import get_db
from app.core.security import check_ownership, get_current_user
from app.core.limiter import limiter
from app.models.script_project import ScriptProject
from app.models.user import User
from app.services.compliance import compliance_checker
from app.services.script_generator import script_generator

router = APIRouter(prefix="/scripts", tags=["Scripts"])

logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    tone_id: str
    persona_id: str
    guest_config: dict | list[dict]
    emotion_curve: str = "default"
    strategy_mix: str = "conservative"
    hot_topic: str | None = None
    multi_version: bool = False
    scene_type: str = "entertainment"
    enable_caller_enhancement: bool = False
    topic: str | None = None
    required_lines: list[str] | None = None
    director_roles: list[dict] | None = None
    director_acts: list[dict] | None = None
    custom_tone: str | None = None


class PatchScriptRequest(BaseModel):
    script_content: dict


class RegenerateRequest(BaseModel):
    regenerate_speaker: str  # "主播" or "连线观众"


@router.post("/generate")
@limiter.limit("5/minute")
async def generate_script(
    request: Request,
    req: GenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate guest_config
    if isinstance(req.guest_config, list):
        for gc in req.guest_config:
            if not gc.get("core_issue"):
                raise HTTPException(status_code=400, detail="Each guest must have core_issue")
    elif not req.guest_config.get("core_issue"):
        raise HTTPException(status_code=400, detail="guest_config.core_issue is required")

    # Normalize guest_config for downstream consumption
    raw_guest = req.guest_config if isinstance(req.guest_config, list) else req.guest_config

    try:
        result = await script_generator.generate(
            tone_id=req.tone_id,
            persona_id=req.persona_id,
            guest_config=raw_guest,
            emotion_curve=req.emotion_curve,
            strategy_mix=req.strategy_mix,
            hot_topic=req.hot_topic,
            multi_version=req.multi_version,
            scene_type=req.scene_type,
            enable_caller_enhancement=req.enable_caller_enhancement,
            topic=req.topic,
            required_lines=req.required_lines,
            db=db,
            user_id=current_user.id,
            director_roles=req.director_roles,
            director_acts=req.director_acts,
            custom_tone=req.custom_tone,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger = __import__("logging").getLogger(__name__)
        logger.exception("Script generation failed")
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    return result


@router.get("/{script_id}")
async def get_script(script_id: str, db: AsyncSession = Depends(get_db)):
    try:
        sid = uuid.UUID(script_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    script = await db.get(ScriptProject, sid)
    if not script or script.status == "archived":
        raise HTTPException(status_code=404, detail="Script not found")

    return {
        "id": str(script.id),
        "title": script.title,
        "tone_id": str(script.tone_id) if script.tone_id else None,
        "persona_id": str(script.persona_id) if script.persona_id else None,
        "script_content": script.script_content,
        "emotion_curve": script.emotion_curve,
        "strategy_mix": script.strategy_mix,
        "multi_version": script.multi_version,
        "word_count": script.word_count,
        "sensitive_hits": script.sensitive_hits,
        "status": script.status,
        "created_at": script.created_at.isoformat() if script.created_at else None,
        "updated_at": script.updated_at.isoformat() if script.updated_at else None,
    }


@router.get("/")
async def list_scripts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    keyword: str = Query(default="", description="Search title"),
    db: AsyncSession = Depends(get_db),
):
    query = select(ScriptProject)
    count_query = select(func.count()).select_from(ScriptProject)

    if status:
        query = query.where(ScriptProject.status == status)
        count_query = count_query.where(ScriptProject.status == status)
    else:
        query = query.where(ScriptProject.status != "archived")
        count_query = count_query.where(ScriptProject.status != "archived")

    if keyword:
        kw = f"%{keyword}%"
        query = query.where(ScriptProject.title.ilike(kw))
        count_query = count_query.where(ScriptProject.title.ilike(kw))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        query.order_by(ScriptProject.updated_at.desc()).offset(skip).limit(limit)
    )
    scripts = result.scalars().all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": str(s.id),
                "title": s.title,
                "emotion_curve": s.emotion_curve,
                "word_count": s.word_count,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in scripts
        ],
    }


@router.patch("/{script_id}")
async def update_script(
    script_id: str,
    req: PatchScriptRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        sid = uuid.UUID(script_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    script = await db.get(ScriptProject, sid)
    if not script or script.status == "archived":
        raise HTTPException(status_code=404, detail="Script not found")

    check_ownership(script, current_user)

    script.script_content = req.script_content

    # 重新统计字数
    dialogues = req.script_content.get("dialogues", [])
    full_text = " ".join(d.get("text", "") for d in dialogues)
    script.word_count = len(full_text)

    # 重新合规检测
    await compliance_checker._ensure_loaded()
    compliance_result = compliance_checker.check(full_text)
    script.sensitive_hits = compliance_result.get("hits", [])

    await db.commit()
    await db.refresh(script)

    return {
        "id": str(script.id),
        "title": script.title,
        "word_count": script.word_count,
        "compliance": compliance_result,
        "status": script.status,
    }


@router.delete("/{script_id}")
async def archive_script(
    script_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        sid = uuid.UUID(script_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    script = await db.get(ScriptProject, sid)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    check_ownership(script, current_user)
    script.status = "archived"
    await db.commit()

    return {"id": str(script.id), "status": "archived"}


@router.post("/{script_id}/regenerate")
async def regenerate_script(
    script_id: str,
    req: RegenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.regenerate_speaker not in ("主播", "连线观众"):
        raise HTTPException(
            status_code=400, detail="regenerate_speaker must be '主播' or '连线观众'"
        )

    try:
        sid = uuid.UUID(script_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    script = await db.get(ScriptProject, sid)
    if not script or script.status == "archived":
        raise HTTPException(status_code=404, detail="Script not found")

    check_ownership(script, current_user)

    content = script.script_content
    dialogues = content.get("dialogues", [])

    # 收集需要重新生成的台词
    target_lines = [d for d in dialogues if d.get("speaker") == req.regenerate_speaker]
    if not target_lines:
        raise HTTPException(
            status_code=400,
            detail=f"No dialogues found for speaker: {req.regenerate_speaker}",
        )

    # 构建上下文供 DeepSeek 重新生成
    context_lines = []
    for d in dialogues:
        context_lines.append(f"[{d.get('speaker', '?')}]: {d.get('text', '')}")

    context_text = "\n".join(context_lines)
    speaker_label = req.regenerate_speaker

    # Find the other speaker label from dialogues
    other_speaker = None
    for d in dialogues:
        s = d.get("speaker", "")
        if s != speaker_label:
            other_speaker = s
            break

    prompt = f"""以下是当前的直播对话脚本：
{context_text}

请重新生成 [{speaker_label}] 的所有台词（保持 [{other_speaker}] 的台词完全不变）。
要求：每句台词都必须重新创作，内容要有明显变化，不要照搬原话。
只输出 JSON 格式：
{{
  "regenerated": [
    {{"turn": 轮次编号(整数), "text": "全新的台词内容", "emotion": "情绪", "is_highlight": false, "highlight_title": ""}}
  ]
}}"""

    try:
        from app.services.deepseek_client import deepseek as ds_client

        result = await ds_client.chat(
            [
                {
                    "role": "system",
                    "content": "你是直播脚本编剧，只输出纯JSON，不要markdown标记。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=2048,
            timeout=60.0,
            response_format={"type": "json_object"},
        )
        regenerated = result.get("regenerated", [])

        # Normalize turn values to int for reliable matching
        regen_map = {}
        for r in regenerated:
            try:
                turn_key = int(r["turn"])
                regen_map[turn_key] = r
            except (ValueError, KeyError, TypeError):
                continue

        replaced_count = 0
        for d in dialogues:
            if d.get("speaker") == speaker_label:
                turn_val = d.get("turn")
                try:
                    turn_key = int(turn_val)
                except (ValueError, TypeError):
                    continue
                if turn_key in regen_map:
                    new_line = regen_map[turn_key]
                    d["text"] = new_line.get("text", d["text"])
                    d["emotion"] = new_line.get("emotion", d.get("emotion", ""))
                    d["is_highlight"] = new_line.get("is_highlight", False)
                    d["highlight_title"] = new_line.get("highlight_title", "")
                    replaced_count += 1

        logger.info("Regenerate: speaker=%s, ai_returned=%d, actually_replaced=%d",
                     speaker_label, len(regenerated), replaced_count)

        # 重新检测合规
        full_text = " ".join(d.get("text", "") for d in dialogues)
        await compliance_checker._ensure_loaded()
        compliance_result = compliance_checker.check(full_text)

        script.script_content = content
        flag_modified(script, "script_content")
        script.word_count = len(full_text)
        script.sensitive_hits = compliance_result.get("hits", [])
        await db.commit()
        await db.refresh(script)

        return {
            "script_id": str(script.id),
            "regenerated_speaker": speaker_label,
            "regenerated_count": replaced_count,
            "compliance": compliance_result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {e}")
