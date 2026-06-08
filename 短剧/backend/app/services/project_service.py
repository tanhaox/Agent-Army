"""
项目与快照服务层 - 项目 CRUD、快照创建/恢复/对比、仪表盘、角色管理。
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character
from app.models.project import Project
from app.models.project_character import ProjectCharacter
from app.models.project_snapshot import ProjectSnapshot
from app.models.script import Script
from app.models.storyboard import Storyboard
from app.models.video_task import VideoTask

logger = logging.getLogger(__name__)


# ========== 项目 CRUD ==========

async def create_project(
    db: AsyncSession,
    name: str,
    description: str | None = None,
) -> Project:
    """创建项目。"""
    project = Project(name=name, description=description)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    logger.info("项目已创建: id=%s, name=%s", project.id, name)
    return project


async def get_project(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    """根据 ID 获取项目。"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def list_projects(db: AsyncSession) -> list[Project]:
    """获取项目列表。"""
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return list(result.scalars().all())


async def update_project(
    db: AsyncSession,
    project: Project,
    **fields: Any,
) -> Project:
    """更新项目字段。"""
    for key, value in fields.items():
        if value is not None:
            setattr(project, key, value)
    await db.commit()
    await db.refresh(project)
    logger.info("项目已更新: id=%s", project.id)
    return project


async def delete_project(db: AsyncSession, project: Project) -> None:
    """删除项目及其快照。"""
    # 先删除关联的快照
    result = await db.execute(
        select(ProjectSnapshot).where(ProjectSnapshot.project_id == str(project.id))
    )
    for snap in result.scalars().all():
        await db.delete(snap)
    await db.delete(project)
    await db.commit()
    logger.info("项目已删除: id=%s", project.id)


# ========== 快照操作 ==========

async def create_snapshot(
    db: AsyncSession,
    project: Project,
    snapshot_name: str | None = None,
    remark: str | None = None,
) -> ProjectSnapshot:
    """
    为项目创建快照。

    保存当前关联的剧本内容和所有分镜数据。

    Args:
        db: 数据库会话。
        project: 项目对象。
        snapshot_name: 快照名称（可选，默认自动生成）。
        remark: 备注（可选）。

    Returns:
        创建的快照对象。

    Raises:
        ValueError: 项目未关联剧本。
    """
    if not project.current_script_id:
        raise ValueError("项目尚未关联剧本，无法创建快照")

    # 获取剧本
    script_id = project.current_script_id
    result = await db.execute(select(Script).where(Script.id == str(script_id)))
    script = result.scalar_one_or_none()
    if script is None:
        raise ValueError(f"关联的剧本 {script_id} 不存在")

    # 获取关联的所有分镜
    sb_result = await db.execute(
        select(Storyboard)
        .where(Storyboard.script_id == str(script_id))
        .order_by(Storyboard.episode_no, Storyboard.shot_no)
    )
    storyboards = list(sb_result.scalars().all())

    # 生成快照名称
    if not snapshot_name:
        now = datetime.now(timezone.utc)
        snapshot_name = f"快照 {now.strftime('%Y-%m-%d %H:%M')}"

    # 序列化分镜数据
    storyboards_data = [
        {
            "id": str(sb.id),
            "episode_no": sb.episode_no,
            "shot_no": sb.shot_no,
            "shot_type": sb.shot_type,
            "camera_move": sb.camera_move,
            "action": sb.action,
            "dialogue": sb.dialogue,
            "emotion": sb.emotion,
            "environment": sb.environment,
            "lighting": sb.lighting,
            "prompt_text": sb.prompt_text,
        }
        for sb in storyboards
    ]

    snapshot = ProjectSnapshot(
        project_id=str(project.id),
        snapshot_name=snapshot_name,
        script_snapshot=script.content,
        storyboards_snapshot=storyboards_data,
        snapshot_meta={"remark": remark, "script_id": str(script_id), "storyboard_count": len(storyboards)},
    )
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    logger.info("快照已创建: id=%s, name=%s, 分镜数=%d", snapshot.id, snapshot_name, len(storyboards))
    return snapshot


async def list_snapshots(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> list[ProjectSnapshot]:
    """获取项目的快照列表。"""
    result = await db.execute(
        select(ProjectSnapshot)
        .where(ProjectSnapshot.project_id == str(project_id))
        .order_by(ProjectSnapshot.created_at.desc())
    )
    return list(result.scalars().all())


async def get_snapshot(db: AsyncSession, snapshot_id: uuid.UUID) -> ProjectSnapshot | None:
    """获取快照详情。"""
    result = await db.execute(
        select(ProjectSnapshot).where(ProjectSnapshot.id == snapshot_id)
    )
    return result.scalar_one_or_none()


async def restore_snapshot(
    db: AsyncSession,
    project: Project,
    snapshot: ProjectSnapshot,
) -> Project:
    """
    从快照恢复项目数据。

    1. 根据快照的 script_snapshot 创建新的剧本记录
    2. 根据快照的 storyboards_snapshot 重建分镜记录
    3. 更新项目的 current_script_id

    Args:
        db: 数据库会话。
        project: 项目对象。
        snapshot: 要恢复的快照。

    Returns:
        更新后的项目对象。
    """
    # 1. 创建新剧本
    old_content = snapshot.script_snapshot or {}
    new_script = Script(
        project_name=project.name,
        theme=old_content.get("metadata", {}).get("theme", "从快照恢复"),
        content=old_content,
        project_id=str(project.id),
    )
    db.add(new_script)
    await db.flush()  # 获取 new_script.id

    # 2. 重建分镜
    storyboards_data = snapshot.storyboards_snapshot or []
    for sb_data in storyboards_data:
        new_sb = Storyboard(
            script_id=str(new_script.id),
            project_id=str(project.id),
            episode_no=sb_data["episode_no"],
            shot_no=sb_data["shot_no"],
            shot_type=sb_data["shot_type"],
            camera_move=sb_data["camera_move"],
            action=sb_data["action"],
            dialogue=sb_data.get("dialogue"),
            emotion=sb_data["emotion"],
            environment=sb_data["environment"],
            lighting=sb_data["lighting"],
            prompt_text=sb_data.get("prompt_text"),
        )
        db.add(new_sb)

    # 3. 更新项目关联
    project.current_script_id = str(new_script.id)
    await db.commit()
    await db.refresh(project)
    logger.info(
        "快照已恢复: project=%s, snapshot=%s, 新剧本=%s, 分镜数=%d",
        project.id, snapshot.id, new_script.id, len(storyboards_data),
    )
    return project


async def compare_snapshots(
    db: AsyncSession,
    snapshot_id_1: str,
    snapshot_id_2: str,
) -> dict[str, Any]:
    """
    对比两个快照的差异。

    Args:
        db: 数据库会话。
        snapshot_id_1: 快照 1 ID（较早）。
        snapshot_id_2: 快照 2 ID（较新）。

    Returns:
        差异字典。
    """
    snap1 = await get_snapshot(db, uuid.UUID(snapshot_id_1))
    snap2 = await get_snapshot(db, uuid.UUID(snapshot_id_2))

    if snap1 is None or snap2 is None:
        raise ValueError("快照不存在")

    # 剧本差异
    script_diff = _compare_scripts(
        snap1.script_snapshot or {},
        snap2.script_snapshot or {},
    )

    # 分镜差异
    storyboards_diff = _compare_storyboards(
        snap1.storyboards_snapshot or [],
        snap2.storyboards_snapshot or [],
    )

    return {
        "snapshot_1_name": snap1.snapshot_name,
        "snapshot_2_name": snap2.snapshot_name,
        "script_diff": script_diff,
        "storyboards_diff": storyboards_diff,
    }


def _compare_scripts(script1: dict, script2: dict) -> dict[str, Any]:
    """对比两个剧本快照的结构化差异。"""
    diff: dict[str, Any] = {}

    # 标题
    t1 = script1.get("title", "")
    t2 = script2.get("title", "")
    diff["title_changed"] = t1 != t2
    diff["title_1"] = t1
    diff["title_2"] = t2

    # 总集数
    ep1 = len(script1.get("episodes", []))
    ep2 = len(script2.get("episodes", []))
    diff["episodes_changed"] = ep1 != ep2
    diff["episodes_count_1"] = ep1
    diff["episodes_count_2"] = ep2

    # 每集变化
    episodes_detail = []
    eps1 = {e.get("episode", i): e for i, e in enumerate(script1.get("episodes", []))}
    eps2 = {e.get("episode", i): e for i, e in enumerate(script2.get("episodes", []))}

    all_ep_nums = sorted(set(eps1.keys()) | set(eps2.keys()))
    for ep_num in all_ep_nums:
        e1 = eps1.get(ep_num)
        e2 = eps2.get(ep_num)
        if e1 is None:
            episodes_detail.append({"episode": ep_num, "change": "added", "hook": e2.get("hook", "") if e2 else ""})
        elif e2 is None:
            episodes_detail.append({"episode": ep_num, "change": "removed", "hook": e1.get("hook", "")})
        else:
            hook_changed = e1.get("hook", "") != e2.get("hook", "")
            cliff_changed = e1.get("cliffhanger", "") != e2.get("cliffhanger", "")
            if hook_changed or cliff_changed:
                episodes_detail.append({
                    "episode": ep_num,
                    "change": "modified",
                    "hook_1": e1.get("hook", ""),
                    "hook_2": e2.get("hook", ""),
                    "cliffhanger_1": e1.get("cliffhanger", ""),
                    "cliffhanger_2": e2.get("cliffhanger", ""),
                })

    diff["episodes_detail"] = episodes_detail
    return diff


def _compare_storyboards(sbs1: list[dict], sbs2: list[dict]) -> dict[str, Any]:
    """对比两个分镜快照的差异。"""
    diff: dict[str, Any] = {}

    diff["count_1"] = len(sbs1)
    diff["count_2"] = len(sbs2)
    diff["count_changed"] = len(sbs1) != len(sbs2)

    # 按集数+镜头序号建立索引
    def make_key(sb: dict) -> str:
        return f"{sb.get('episode_no', 0)}-{sb.get('shot_no', 0)}"

    map1 = {make_key(sb): sb for sb in sbs1}
    map2 = {make_key(sb): sb for sb in sbs2}

    keys1 = set(map1.keys())
    keys2 = set(map2.keys())

    added = sorted(keys2 - keys1)
    removed = sorted(keys1 - keys2)
    common = keys1 & keys2

    modified = []
    for key in sorted(common):
        if map1[key] != map2[key]:
            modified.append({
                "key": key,
                "action_1": map1[key].get("action", ""),
                "action_2": map2[key].get("action", ""),
            })

    diff["added"] = added
    diff["removed"] = removed
    diff["modified"] = modified

    return diff


# ========== 仪表盘 ==========

async def get_project_dashboard(db: AsyncSession, project_id: str) -> dict[str, Any]:
    """
    获取项目仪表盘统计数据。

    Args:
        db: 数据库会话。
        project_id: 项目 ID。

    Returns:
        包含统计信息和最近活动的字典。
    """
    project = await get_project(db, project_id)
    if project is None:
        return None

    # 统计数量
    script_count = await db.scalar(
        select(func.count()).where(Script.project_id == project_id)
    ) or 0

    storyboard_count = await db.scalar(
        select(func.count()).where(Storyboard.project_id == project_id)
    ) or 0

    character_count = await db.scalar(
        select(func.count()).where(ProjectCharacter.project_id == project_id)
    ) or 0

    video_task_count = await db.scalar(
        select(func.count()).where(VideoTask.project_id == project_id)
    ) or 0

    # 最近剧本
    recent_scripts_result = await db.execute(
        select(Script)
        .where(Script.project_id == project_id)
        .order_by(Script.created_at.desc())
        .limit(3)
    )
    recent_scripts = [
        {"id": str(s.id), "project_name": s.project_name, "created_at": s.created_at.isoformat()}
        for s in recent_scripts_result.scalars().all()
    ]

    # 最近视频任务
    recent_tasks_result = await db.execute(
        select(VideoTask)
        .where(VideoTask.project_id == project_id)
        .order_by(VideoTask.created_at.desc())
        .limit(5)
    )
    recent_video_tasks = [
        {"id": str(t.id), "status": t.status, "created_at": t.created_at.isoformat()}
        for t in recent_tasks_result.scalars().all()
    ]

    return {
        "project": project,
        "script_count": script_count,
        "storyboard_count": storyboard_count,
        "character_count": character_count,
        "video_task_count": video_task_count,
        "recent_scripts": recent_scripts,
        "recent_video_tasks": recent_video_tasks,
    }


# ========== 项目角色管理 ==========

async def list_project_characters(db: AsyncSession, project_id: str) -> list[dict[str, Any]]:
    """
    获取项目关联的角色列表。

    Returns:
        包含角色信息和剧中角色名的字典列表。
    """
    result = await db.execute(
        select(ProjectCharacter, Character)
        .join(Character, ProjectCharacter.character_id == Character.id)
        .where(ProjectCharacter.project_id == project_id)
        .order_by(ProjectCharacter.created_at)
    )
    rows = result.all()
    return [
        {
            "character_id": str(pc.character_id),
            "character_name": c.name,
            "role_name": pc.role_name,
            "traits": c.traits or {},
            "reference_images": c.reference_images or [],
            "created_at": pc.created_at,
        }
        for pc, c in rows
    ]


async def add_project_character(
    db: AsyncSession,
    project_id: str,
    character_id: str,
    role_name: str | None = None,
) -> ProjectCharacter:
    """
    添加角色到项目。

    Raises:
        ValueError: 角色不存在或已添加。
    """
    # 检查角色是否存在
    char_result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    if char_result.scalar_one_or_none() is None:
        raise ValueError(f"角色 {character_id} 不存在")

    # 检查是否已添加
    existing = await db.execute(
        select(ProjectCharacter).where(
            ProjectCharacter.project_id == project_id,
            ProjectCharacter.character_id == character_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError("该角色已在项目中")

    pc = ProjectCharacter(
        project_id=project_id,
        character_id=character_id,
        role_name=role_name,
    )
    db.add(pc)
    await db.commit()
    await db.refresh(pc)
    logger.info("角色已添加到项目: character=%s, project=%s", character_id, project_id)
    return pc


async def remove_project_character(
    db: AsyncSession,
    project_id: str,
    character_id: str,
) -> None:
    """从项目移除角色。"""
    await db.execute(
        delete(ProjectCharacter).where(
            ProjectCharacter.project_id == project_id,
            ProjectCharacter.character_id == character_id,
        )
    )
    await db.commit()
    logger.info("角色已从项目移除: character=%s, project=%s", character_id, project_id)
