"""
分镜节奏自动优化服务 - 根据节奏分析结果自动修复分镜问题。

闭环流程：分析诊断 → 生成修复 → 写入数据库 → 重新分配时长。
"""

import json
import logging
import re
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.storyboard import Storyboard, SHOT_TYPES, CAMERA_MOVES, VFX_OPTIONS
from app.services.storyboard_timing_service import (
    analyze_episode_fitness,
    auto_assign_durations,
    EMOTION_INTENSITY,
    CLIMAX_EMOTIONS,
    SUSPENSE_EMOTIONS,
)

logger = logging.getLogger(__name__)

# ── LLM 系统提示 ──────────────────────────────────────────
_FIX_SYSTEM_PROMPT = f"""你是一位专业的短剧分镜师。用户会给你当前一集的分镜列表和需要修复的问题。
请你生成新增或修改的分镜参数来修复这些问题。

输出要求：
1. 输出一个合法的 JSON 数组，不要输出任何其他文字。
2. 每个元素的结构如下：
{{
  "fix_type": "add_shot" 或 "modify_last_shot" 或 "add_climax_shot",
  "episode_no": 集数,
  "shot_no": 镜头序号（新增镜头用原最大号+1），
  "shot_type": 景别（{"、".join(SHOT_TYPES)}），
  "camera_move": 运镜（{"、".join(CAMERA_MOVES)}），
  "action": "动作描述，30字内"，
  "dialogue": "对话，可留空"，
  "emotion": 情绪（从以下选取：紧张、恐惧、愤怒、悲伤、惊喜、甜蜜、喜悦、期待、感动、困惑），
  "vfx": "无"，
  "environment": "场景环境，20字内"，
  "lighting": "光线描述，15字内"
}}

规则：
- 新增镜头的 action 要与前后镜头情节连贯。
- 高潮镜头使用近景或特写，情绪选择紧张/愤怒/惊喜。
- 悬念结尾使用期待或紧张情绪，动作暗示即将发生的事情。
- 确保不与现有镜头重复。

只输出 JSON 数组，不要其他文字。"""


def _extract_json(text: str) -> str:
    """从 LLM 响应中提取 JSON。"""
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


def _build_fix_prompt(
    ep_no: int,
    existing_shots: list[dict],
    problems: list[str],
) -> str:
    """构建修复请求提示词。"""
    shots_desc = "\n".join(
        f"  镜头{s['shot_no']}: {s['shot_type']}/{s['camera_move']}, "
        f"动作={s['action']}, 情绪={s['emotion']}"
        for s in existing_shots
    )
    problems_desc = "\n".join(f"  - {p}" for p in problems)

    return (
        f"第{ep_no}集当前分镜（共{len(existing_shots)}个）：\n{shots_desc}\n\n"
        f"需要修复的问题：\n{problems_desc}\n\n"
        f"请生成修复方案（JSON 数组）。"
    )


async def optimize_storyboards_by_rhythm(
    db: AsyncSession,
    project_id: str,
) -> dict:
    """
    根据节奏分析自动优化分镜。

    流程：
    1. 读取项目所有分镜，按集分组
    2. 对每集做适配性分析
    3. 有问题的集，调用 LLM 生成修复方案
    4. 插入/修改分镜
    5. 重新分配时长
    6. 返回变更摘要

    Returns:
        {"changes": [...], "total_added": N, "total_modified": N}
    """
    from app.services.llm import get_llm_client

    # 1. 读取所有分镜
    result = await db.execute(
        select(Storyboard)
        .where(Storyboard.project_id == project_id)
        .order_by(Storyboard.episode_no, Storyboard.shot_no)
    )
    all_sbs = list(result.scalars().all())

    if not all_sbs:
        return {"changes": [], "total_added": 0, "total_modified": 0}

    # 按集分组
    episodes: dict[int, list[Storyboard]] = defaultdict(list)
    for sb in all_sbs:
        episodes[sb.episode_no].append(sb)

    changes: list[dict] = []
    client = get_llm_client()

    # 2. 逐集分析并修复
    for ep_no, ep_sbs in sorted(episodes.items()):
        items = [
            {
                "episode_no": s.episode_no,
                "shot_no": s.shot_no,
                "shot_type": s.shot_type,
                "camera_move": s.camera_move,
                "action": s.action,
                "emotion": s.emotion,
                "environment": s.environment,
                "lighting": s.lighting,
                "vfx": s.vfx or "无",
                "duration_seconds": s.duration_seconds or 5,
                "is_key_moment": s.is_key_moment or False,
            }
            for s in ep_sbs
        ]

        fitness = analyze_episode_fitness(items)

        # 跳过健康的集（评分 >= 85 且无 issue）
        if fitness["score"] >= 85 and not fitness["issues"]:
            continue

        problems = fitness["issues"] + fitness["suggestions"]
        if not problems:
            continue

        # 3. 调用 LLM 生成修复
        try:
            prompt = _build_fix_prompt(ep_no, items, problems)
            raw = await client.generate(prompt, system=_FIX_SYSTEM_PROMPT)
            json_str = _extract_json(raw)

            try:
                fixes = json.loads(json_str)
            except json.JSONDecodeError:
                logger.warning("第%d集优化方案解析失败: %s", ep_no, raw[:100])
                continue

            if not isinstance(fixes, list):
                fixes = [fixes]

        except Exception as e:
            logger.warning("第%d集 LLM 调用失败: %s", ep_no, e)
            continue

        # 4. 执行修复
        max_shot_no = max(s.shot_no for s in ep_sbs)
        for fix in fixes:
            fix_type = fix.get("fix_type", "add_shot")
            ep_fix = fix.get("episode_no", ep_no)

            if fix_type == "modify_last_shot":
                # 修改最后一个镜头的情绪/动作
                last_sb = ep_sbs[-1]
                update_fields = {}
                if fix.get("emotion"):
                    update_fields["emotion"] = fix["emotion"]
                if fix.get("action"):
                    update_fields["action"] = fix["action"]
                if fix.get("dialogue"):
                    update_fields["dialogue"] = fix["dialogue"]
                if fix.get("environment"):
                    update_fields["environment"] = fix["environment"]
                if fix.get("lighting"):
                    update_fields["lighting"] = fix["lighting"]
                if update_fields:
                    # 标记为关键镜头
                    update_fields["is_key_moment"] = True
                    for k, v in update_fields.items():
                        setattr(last_sb, k, v)
                    changes.append({
                        "type": "modified",
                        "episode_no": ep_fix,
                        "shot_no": last_sb.shot_no,
                        "detail": f"修改结尾镜头: {', '.join(update_fields.keys())}",
                    })

            else:
                # 新增镜头
                max_shot_no += 1
                new_shot = Storyboard(
                    script_id=ep_sbs[0].script_id,
                    project_id=project_id,
                    episode_no=ep_fix,
                    shot_no=max_shot_no,
                    shot_type=fix.get("shot_type", "近景"),
                    camera_move=fix.get("camera_move", "推"),
                    action=fix.get("action", ""),
                    dialogue=fix.get("dialogue"),
                    emotion=fix.get("emotion", "紧张"),
                    vfx=fix.get("vfx", "无"),
                    environment=fix.get("environment", ep_sbs[-1].environment if ep_sbs else ""),
                    lighting=fix.get("lighting", ep_sbs[-1].lighting if ep_sbs else ""),
                    is_key_moment=True,
                )
                db.add(new_shot)
                changes.append({
                    "type": "added",
                    "episode_no": ep_fix,
                    "shot_no": max_shot_no,
                    "detail": f"新增镜头: {fix.get('action', '')[:30]}, 情绪={fix.get('emotion', '')}",
                })

    # 5. 保存并重新分配时长
    await db.commit()

    if changes:
        # 刷新后重新读取
        result = await db.execute(
            select(Storyboard)
            .where(Storyboard.project_id == project_id)
            .order_by(Storyboard.episode_no, Storyboard.shot_no)
        )
        all_sbs = list(result.scalars().all())

        episodes: dict[int, list] = defaultdict(list)
        for sb in all_sbs:
            episodes[sb.episode_no].append(sb)

        for ep_no, ep_sbs in episodes.items():
            items = [
                {
                    "shot_type": s.shot_type,
                    "camera_move": s.camera_move,
                    "emotion": s.emotion,
                }
                for s in ep_sbs
            ]
            auto_assign_durations(items)
            for sb, item in zip(ep_sbs, items):
                sb.duration_seconds = item["duration_seconds"]
                sb.is_key_moment = item["is_key_moment"]

        await db.commit()

    added = sum(1 for c in changes if c["type"] == "added")
    modified = sum(1 for c in changes if c["type"] == "modified")

    logger.info("节奏优化完成: project=%s, 新增%d, 修改%d", project_id, added, modified)

    return {
        "changes": changes,
        "total_added": added,
        "total_modified": modified,
    }


async def add_climax_shots(
    db: AsyncSession,
    project_id: str,
    episodes: list[int] | None = None,
) -> dict:
    """
    根据审核报告为指定集自动添加高潮镜头。

    流程：
    1. 获取指定集分镜
    2. 计算60%-80%插入位置
    3. LLM 生成高潮镜头
    4. 插入并重排 shot_no
    5. 重新分配时长
    """
    from app.services.llm import get_llm_client

    # 读取所有分镜
    result = await db.execute(
        select(Storyboard)
        .where(Storyboard.project_id == project_id)
        .order_by(Storyboard.episode_no, Storyboard.shot_no)
    )
    all_sbs = list(result.scalars().all())

    if not all_sbs:
        return {"changes": [], "total_added": 0}

    # 按集分组
    ep_map: dict[int, list[Storyboard]] = defaultdict(list)
    for sb in all_sbs:
        ep_map[sb.episode_no].append(sb)

    # 如果没指定集，自动从审核报告中提取情绪曲线低分集
    if episodes is None:
        from app.services.storyboard_review_standards import evaluate_episode
        episodes = []
        for ep_no, items_raw in ep_map.items():
            items = [
                {
                    "episode_no": s.episode_no, "shot_no": s.shot_no,
                    "shot_type": s.shot_type, "camera_move": s.camera_move,
                    "action": s.action, "emotion": s.emotion,
                    "vfx": s.vfx or "无", "duration_seconds": s.duration_seconds or 5,
                    "is_key_moment": s.is_key_moment or False,
                }
                for s in items_raw
            ]
            report = evaluate_episode(items)
            if report["dimensions"].get("emotion_curve", 100) < 70:
                episodes.append(ep_no)

    if not episodes:
        return {"changes": [], "total_added": 0}

    client = get_llm_client()
    changes: list[dict] = []

    for ep_no in episodes:
        ep_sbs = ep_map.get(ep_no, [])
        if not ep_sbs:
            continue

        # 插入位置：60%-80% 进度
        insert_idx = int(len(ep_sbs) * 0.65)
        insert_idx = max(1, min(insert_idx, len(ep_sbs) - 1))

        # 构建 LLM 提示
        shots_summary = "\n".join(
            f"  镜头{s.shot_no}: {s.shot_type}/{s.camera_move}, "
            f"动作={s.action}, 情绪={s.emotion}"
            for s in ep_sbs
        )

        system_prompt = (
            "你是一位短剧分镜师。根据现有剧情，生成一个能提升情绪高潮的镜头。\n"
            "只输出一个 JSON 对象，不要输出其他文字。"
        )
        user_prompt = (
            f"第{ep_no}集现有分镜：\n{shots_summary}\n\n"
            "请生成一个高潮镜头：\n"
            '- 景别：近景或特写\n- 运镜：推或摇\n'
            "- 情绪：紧张、愤怒、惊喜之一\n"
            "- 动作：简短有力（30字内），符合上下文\n"
            "- 特效：可选（如光效、粒子）\n\n"
            '输出 JSON：{"shot_type":"近景","camera_move":"推","action":"...","emotion":"紧张","vfx":"无","environment":"...","lighting":"..."}'
        )

        try:
            raw = await client.generate(user_prompt, system=system_prompt)
            text = raw.strip()
            if text.startswith("```"):
                m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
                if m:
                    text = m.group(1).strip()
            if not text.startswith("{"):
                m = re.search(r"\{[\s\S]*\}", text)
                if m:
                    text = m.group(0)

            shot_data = json.loads(text)
        except Exception as e:
            logger.warning("第%d集高潮镜头生成失败: %s", ep_no, e)
            continue

        # 插入位置之后的镜头 shot_no +1
        insert_shot_no = ep_sbs[insert_idx].shot_no
        for sb in ep_sbs[insert_idx:]:
            sb.shot_no += 1

        # 创建新镜头
        new_sb = Storyboard(
            script_id=ep_sbs[0].script_id,
            project_id=project_id,
            episode_no=ep_no,
            shot_no=insert_shot_no,
            shot_type=shot_data.get("shot_type", "近景"),
            camera_move=shot_data.get("camera_move", "推"),
            action=shot_data.get("action", ""),
            dialogue=shot_data.get("dialogue"),
            emotion=shot_data.get("emotion", "紧张"),
            vfx=shot_data.get("vfx", "无"),
            environment=shot_data.get("environment", ep_sbs[0].environment),
            lighting=shot_data.get("lighting", ep_sbs[0].lighting),
            is_key_moment=True,
        )
        db.add(new_sb)

        changes.append({
            "type": "added",
            "episode_no": ep_no,
            "shot_no": insert_shot_no,
            "detail": f"高潮镜头: {shot_data.get('action', '')[:30]}, 情绪={shot_data.get('emotion', '')}",
        })

    # 保存并重新分配时长
    await db.commit()

    if changes:
        result = await db.execute(
            select(Storyboard)
            .where(Storyboard.project_id == project_id)
            .order_by(Storyboard.episode_no, Storyboard.shot_no)
        )
        all_sbs = list(result.scalars().all())

        ep_map2: dict[int, list] = defaultdict(list)
        for sb in all_sbs:
            ep_map2[sb.episode_no].append(sb)

        for ep_no, ep_sbs in ep_map2.items():
            items = [{"shot_type": s.shot_type, "camera_move": s.camera_move, "emotion": s.emotion} for s in ep_sbs]
            auto_assign_durations(items)
            for sb, item in zip(ep_sbs, items):
                sb.duration_seconds = item["duration_seconds"]
                sb.is_key_moment = item["is_key_moment"]

        await db.commit()

    total_added = len(changes)
    logger.info("高潮镜头添加完成: project=%s, 新增%d", project_id, total_added)

    return {
        "changes": changes,
        "total_added": total_added,
        "total_modified": 0,
    }
