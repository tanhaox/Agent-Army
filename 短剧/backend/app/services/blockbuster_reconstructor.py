"""
爆款分镜重构引擎 - 基于短剧心理机制，而非量化指标。

两种模式：
- 预览模式（apply=False）：LLM 生成分镜数据，仅返回不写入数据库
- 应用模式（apply=True）：自动快照 → 删除旧分镜 → 写入新分镜 → 重新分配时长
"""

import json
import logging
import re
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.storyboard import Storyboard, SHOT_TYPES, CAMERA_MOVES, VFX_OPTIONS
from app.services.blockbuster_principles import PRINCIPLES
from app.services.storyboard_timing_service import auto_assign_durations

logger = logging.getLogger(__name__)

# ── 重构系统提示 ──────────────────────────────────────────

_RECONSTRUCT_SYSTEM_PROMPT = f"""你是一位爆款短剧分镜重构大师。你不做微调，你做的是基于爆款心理机制的彻底重建。

## 你的核心理念

你深谙短视频爆款的心理机制：
- 用户在前3秒就决定是否继续看
- 每15-20秒需要一个认知颠覆点
- 身份反差（被低估→实力暴露）是最强爽点
- 先压抑再释放，情绪落差产生放大效应
- 观众知道角色不知道的事，产生强制性关注

## 你必须遵守的规则

**最关键：你必须为剧本中的每一集都生成分镜，不能省略、合并或减少集数。原始剧本有几集，你就必须输出几集的分镜。**

1. 每集5-7个镜头，总时长60-90秒
2. 每集必须包含以下爆款结构：
   - **开场钩子**（镜头1）：特写/近景，3-4秒，制造强烈好奇心缺口
   - **身份反差**（镜头2-3）：被低估→隐藏实力暗示→即将暴露
   - **认知反转**（镜头3-4）：打破预期，制造多巴胺激增
   - **情绪爆发**（镜头5-6）：压抑积累后的释放，特写，强烈情绪
   - **悬念收尾**（最后一镜）：留下信息差，让观众必须看下一集
3. 对话要口语化、有冲击力，不要书面语
4. 动作描述要具体可执行（不要抽象描述）
5. 环境和光线要服务于情绪（暗调=压抑，暖光=温情，高对比=冲突）

## 景别/运镜/特效限制

- shot_type: {"、".join(SHOT_TYPES)}
- camera_move: {"、".join(CAMERA_MOVES)}
- vfx: {"、".join(VFX_OPTIONS)}
- emotion: 平静、紧张、愤怒、悲伤、惊喜、甜蜜、恐惧、期待、感动、困惑

## 输出格式

只输出一个JSON数组，不要输出其他文字。格式：
[
  {{
    "episode_no": 1,
    "shot_no": 1,
    "shot_type": "特写",
    "camera_move": "推",
    "action": "具体动作描述，30字内",
    "dialogue": "角色对话，可留null",
    "emotion": "紧张",
    "vfx": "无",
    "environment": "场景描述，20字内",
    "lighting": "光线描述，15字内",
    "reconstruction_note": "该镜头对应的爆款原则和设计意图"
  }}
]

记住：你不是在做量化优化，你是在用爆款心理机制重新创造分镜！"""


def _extract_json(text: str) -> str:
    """从LLM响应中提取JSON数组。"""
    t = text.strip()
    if t.startswith("["):
        return t
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", t)
    if m:
        return m.group(1).strip()
    m = re.search(r"\[[\s\S]*\]", t)
    if m:
        return m.group(0)
    return t


def _build_reconstruct_prompt(
    episodes: list[dict],
    characters: list[dict] | None = None,
    existing_summary: dict[int, list[dict]] | None = None,
) -> str:
    """构建重构请求提示词。"""
    ep_count = len(episodes)
    ep_nos = [ep.get("episode", i + 1) for i, ep in enumerate(episodes)]
    parts = [
        f"**重要：剧本共 {ep_count} 集（第{min(ep_nos)}集至第{max(ep_nos)}集），"
        f"你必须为每一集都生成分镜，共输出 {ep_count} 集的数据，绝不能省略或合并任何一集。**\n\n",
        "请根据以下剧本和角色信息，用爆款心理机制重新设计分镜。\n",
    ]

    # 剧本信息
    parts.append("## 剧本内容\n")
    for ep in episodes:
        ep_no = ep.get("episode", 1)
        parts.append(f"### 第{ep_no}集")
        scenes = ep.get("scenes", [])
        for j, scene in enumerate(scenes):
            action = scene.get("action", "")
            dialogue = scene.get("dialogue", "")
            emotion = scene.get("emotion", "平静")
            parts.append(
                f"  场景{j+1}: 动作={action}, 对话={dialogue or '无'}, 情绪={emotion}"
            )
        parts.append("")

    # 角色信息
    if characters:
        parts.append("## 角色设定\n")
        for char in characters:
            name = char.get("name", "")
            traits = char.get("traits", {})
            role = traits.get("role_type", "")
            appearance = traits.get("appearance", "")
            personality = traits.get("personality", "")
            parts.append(
                f"- {name}（{role}）：外貌={appearance}, 性格={personality}"
            )
        parts.append("")

    # 已有分镜参考（可选）
    if existing_summary:
        parts.append("## 当前分镜概要（仅供参考，你应完全重新设计）\n")
        for ep_no, shots in sorted(existing_summary.items()):
            shot_summary = ", ".join(
                f"镜头{s['shot_no']}({s['emotion']})" for s in shots[:5]
            )
            parts.append(f"第{ep_no}集（{len(shots)}镜）: {shot_summary}")
        parts.append("")

    # 爆款要求
    parts.append("## 爆款设计要求\n")
    for pid, p in PRINCIPLES.items():
        parts.append(f"### {p['name']}（权重{int(p['weight']*100)}%）")
        parts.append(f"机制：{p['mechanism']}")
        parts.append("经典示例：")
        for ex in p["examples"][:2]:
            parts.append(f"  {ex}")
        parts.append("")

    parts.append(
        f"请直接输出JSON数组，共 {ep_count} 集，每集5-7个镜头。"
        f"你必须输出第{min(ep_nos)}集到第{max(ep_nos)}集的全部分镜，不能遗漏任何一集。"
        "确保每集都满足上述5大爆款原则。"
    )

    return "\n".join(parts)


def _validate_and_fix_shots(new_shots: list[dict]) -> list[dict]:
    """校验并修复LLM生成的分镜字段。"""
    # 按 episode_no 分组，重排 shot_no
    ep_map: dict[int, list[dict]] = defaultdict(list)
    for item in new_shots:
        ep_no = item.get("episode_no", 1)
        ep_map[ep_no].append(item)

    fixed = []
    for ep_no in sorted(ep_map.keys()):
        for idx, item in enumerate(ep_map[ep_no], 1):
            item["episode_no"] = ep_no
            item["shot_no"] = idx
            if item.get("shot_type") not in SHOT_TYPES:
                item["shot_type"] = "中景"
            if item.get("camera_move") not in CAMERA_MOVES:
                item["camera_move"] = "固定"
            if not item.get("vfx") or item["vfx"] not in VFX_OPTIONS:
                item["vfx"] = "无"
            if not item.get("environment"):
                item["environment"] = ""
            if not item.get("lighting"):
                item["lighting"] = ""
            fixed.append(item)

    return fixed


def _build_preview_changes(new_shots: list[dict]) -> list[dict]:
    """构建预览用变更列表。"""
    return [
        {
            "type": "reconstructed",
            "episode_no": item["episode_no"],
            "shot_no": item["shot_no"],
            "shot_type": item.get("shot_type", "中景"),
            "camera_move": item.get("camera_move", "固定"),
            "action": item.get("action", ""),
            "dialogue": item.get("dialogue"),
            "emotion": item.get("emotion", "平静"),
            "vfx": item.get("vfx", "无"),
            "environment": item.get("environment", ""),
            "lighting": item.get("lighting", ""),
            "note": item.get("reconstruction_note", ""),
        }
        for item in new_shots
    ]


async def reconstruct_storyboards_preview(
    db: AsyncSession,
    project_id: str,
) -> dict:
    """
    预览模式：LLM 生成分镜但不写入数据库。

    Returns:
        {
            "preview": true,
            "changes": [...],
            "total_episodes": N,
            "total_shots": M,
            "principles_applied": [...],
            "raw_shots": [...],  # 完整分镜数据，用于后续应用
        }
    """
    from app.services.llm import get_llm_client
    from app.models.script import Script

    # 1. 读取剧本
    result = await db.execute(
        select(Script)
        .where(Script.project_id == project_id)
        .order_by(Script.created_at.desc())
    )
    script = result.scalar_one_or_none()
    if not script or not script.content:
        return {"error": "项目没有剧本，无法重构"}

    episodes = script.content.get("episodes", [])
    if not episodes:
        return {"error": "剧本内容为空"}

    # 2. 读取角色
    characters = await _read_characters(db, project_id)

    # 3. 读取已有分镜概要
    existing_summary, old_count = await _read_existing_summary(db, project_id)

    # 4. 调用LLM
    new_shots = await _call_llm(episodes, characters, existing_summary if old_count > 0 else None, project_id)
    if isinstance(new_shots, dict):  # error
        return new_shots

    # 5. 校验并构建预览
    new_shots = _validate_and_fix_shots(new_shots)

    # 集数校验：LLM 可能漏掉某些集
    original_ep_nos = {ep.get("episode", i + 1) for i, ep in enumerate(episodes)}
    generated_ep_nos = {s["episode_no"] for s in new_shots}
    missing_eps = original_ep_nos - generated_ep_nos
    if missing_eps:
        logger.warning("LLM 漏生成了第 %s 集的分镜，已记录但无法自动补全", sorted(missing_eps))
    ep_count = len(generated_ep_nos)

    changes = _build_preview_changes(new_shots)
    principles_applied = _build_principles_summary()

    return {
        "preview": True,
        "changes": changes,
        "total_episodes": ep_count,
        "total_shots": len(changes),
        "old_shot_count": old_count,
        "principles_applied": principles_applied,
        "raw_shots": new_shots,
    }


async def reconstruct_storyboards_apply(
    db: AsyncSession,
    project_id: str,
    raw_shots: list[dict],
) -> dict:
    """
    应用模式：自动快照 → 删除旧分镜 → 写入新分镜 → 重新分配时长。

    Args:
        raw_shots: 预览阶段返回的完整分镜数据

    Returns:
        {
            "preview": false,
            "snapshot_id": "...",
            "changes": [...],
            "total_episodes": N,
            "total_shots": M,
            "principles_applied": [...],
        }
    """
    from app.models.script import Script
    from app.services.storyboard_service import create_storyboard
    from app.services.video_prompt_templates import build_standard_prompt, build_negative_prompt

    # 1. 读取剧本
    result = await db.execute(
        select(Script)
        .where(Script.project_id == project_id)
        .order_by(Script.created_at.desc())
    )
    script = result.scalar_one_or_none()
    if not script:
        return {"error": "项目剧本不存在"}

    # 2. 自动快照
    snapshot_id = await _auto_snapshot(db, project_id)

    # 3. 删除旧分镜
    existing_result = await db.execute(
        select(Storyboard).where(Storyboard.project_id == project_id)
    )
    old_sbs = list(existing_result.scalars().all())
    for sb in old_sbs:
        await db.delete(sb)
    await db.flush()
    logger.info("已删除旧分镜 %d 条（快照: %s）", len(old_sbs), snapshot_id)

    # 4. 获取视觉设定
    visual_settings = await _get_visual_settings(db, script)

    # 5. 写入新分镜
    changes: list[dict] = []
    created_count = 0

    for item in raw_shots:
        try:
            standard_prompt = build_standard_prompt(item, visual_settings)
            negative = build_negative_prompt(item)

            sb = await create_storyboard(
                db,
                script_id=str(script.id),
                project_id=project_id,
                episode_no=item["episode_no"],
                shot_no=item["shot_no"],
                shot_type=item["shot_type"],
                camera_move=item["camera_move"],
                action=item["action"],
                dialogue=item.get("dialogue"),
                emotion=item["emotion"],
                vfx=item.get("vfx", "无"),
                environment=item.get("environment", ""),
                lighting=item.get("lighting", ""),
                prompt_text=standard_prompt,
                negative_prompt=negative,
            )
            created_count += 1
            changes.append({
                "type": "reconstructed",
                "episode_no": item["episode_no"],
                "shot_no": item["shot_no"],
                "detail": f"{item['shot_type']}/{item['camera_move']}, {item['action'][:30]}, 情绪={item['emotion']}",
                "note": item.get("reconstruction_note", ""),
            })
        except Exception as e:
            logger.warning("写入分镜失败 ep=%d shot=%d: %s", item.get("episode_no"), item.get("shot_no"), e)

    await db.commit()

    # 6. 重新分配时长
    if changes:
        result = await db.execute(
            select(Storyboard)
            .where(Storyboard.project_id == project_id)
            .order_by(Storyboard.episode_no, Storyboard.shot_no)
        )
        all_sbs = list(result.scalars().all())
        ep_map: dict[int, list] = defaultdict(list)
        for sb in all_sbs:
            ep_map[sb.episode_no].append(sb)

        for ep_no, ep_sbs in ep_map.items():
            items = [
                {"shot_type": s.shot_type, "camera_move": s.camera_move, "emotion": s.emotion}
                for s in ep_sbs
            ]
            auto_assign_durations(items)
            for sb, item in zip(ep_sbs, items):
                sb.duration_seconds = item["duration_seconds"]
                sb.is_key_moment = item["is_key_moment"]

        await db.commit()

    ep_count = len(set(c["episode_no"] for c in changes))
    logger.info("爆款重构应用完成: project=%s, %d集%d镜, snapshot=%s", project_id, ep_count, created_count, snapshot_id)

    return {
        "preview": False,
        "snapshot_id": snapshot_id,
        "changes": changes,
        "total_episodes": ep_count,
        "total_shots": created_count,
        "principles_applied": _build_principles_summary(),
    }


# ── 内部辅助函数 ──────────────────────────────────────────

async def _read_characters(db: AsyncSession, project_id: str) -> list[dict]:
    """读取项目角色。"""
    characters: list[dict] = []
    try:
        from app.models.project_character import ProjectCharacter
        from app.models.character import Character

        char_result = await db.execute(
            select(ProjectCharacter).where(
                ProjectCharacter.project_id == project_id
            )
        )
        links = char_result.scalars().all()
        for link in links:
            c_result = await db.execute(
                select(Character).where(Character.id == link.character_id)
            )
            char = c_result.scalar_one_or_none()
            if char:
                characters.append({
                    "name": char.name,
                    "traits": char.traits or {},
                })
    except Exception as e:
        logger.warning("读取角色信息失败: %s", e)
    return characters


async def _read_existing_summary(
    db: AsyncSession, project_id: str,
) -> tuple[dict[int, list[dict]], int]:
    """读取已有分镜概要，返回 (summary_map, total_count)。"""
    existing_summary: dict[int, list[dict]] = defaultdict(list)
    existing_result = await db.execute(
        select(Storyboard)
        .where(Storyboard.project_id == project_id)
        .order_by(Storyboard.episode_no, Storyboard.shot_no)
    )
    old_sbs = list(existing_result.scalars().all())
    for sb in old_sbs:
        existing_summary[sb.episode_no].append({
            "shot_no": sb.shot_no,
            "emotion": sb.emotion,
            "action": sb.action[:30] if sb.action else "",
        })
    return existing_summary, len(old_sbs)


async def _call_llm(
    episodes: list[dict],
    characters: list[dict],
    existing_summary: dict[int, list[dict]] | None,
    project_id: str,
) -> list[dict] | dict:
    """调用LLM生成分镜，成功返回列表，失败返回错误dict。"""
    from app.services.llm import get_llm_client

    client = get_llm_client()
    prompt = _build_reconstruct_prompt(episodes, characters, existing_summary)

    logger.info("开始爆款重构LLM调用: project=%s", project_id)

    raw = await client.generate(prompt, system=_RECONSTRUCT_SYSTEM_PROMPT)
    json_str = _extract_json(raw)

    try:
        new_shots = json.loads(json_str)
    except json.JSONDecodeError:
        logger.error("重构JSON解析失败: %s", raw[:200])
        return {"error": "LLM返回格式错误，请重试"}

    if not isinstance(new_shots, list) or not new_shots:
        return {"error": "LLM返回空数据"}

    return new_shots


async def _auto_snapshot(db: AsyncSession, project_id: str) -> str | None:
    """应用前自动创建快照（使用嵌套事务隔离错误）。"""
    try:
        async with db.begin_nested():
            from app.services import project_service
            from app.models.project import Project

            result = await db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            if project:
                snapshot = await project_service.create_snapshot(
                    db, project,
                    snapshot_name="auto_重构前备份",
                    remark="爆款重构前自动创建的快照，可用于撤销重构",
                )
                logger.info("自动快照已创建: %s", snapshot.id)
                return str(snapshot.id)
    except Exception as e:
        logger.warning("自动快照创建失败（继续执行）: %s", e)
    return None


async def _get_visual_settings(db: AsyncSession, script) -> dict | None:
    """获取视觉设定。"""
    try:
        from app.models.visual_template import VisualTemplate
        vt_result = await db.execute(
            select(VisualTemplate).where(
                VisualTemplate.id == script.content.get("visual_template_id")
            )
        )
        vt = vt_result.scalar_one_or_none()
        if vt and vt.settings:
            return vt.settings
    except Exception:
        pass
    return None


def _build_principles_summary() -> list[dict]:
    """构建原则摘要列表。"""
    return [
        {"id": pid, "name": p["name"], "weight": p["weight"], "description": p["description"]}
        for pid, p in PRINCIPLES.items()
    ]
