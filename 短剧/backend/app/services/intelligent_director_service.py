"""
智能镜头导演服务 - 基于 LLM 的全局推理与素材规划。

流程：
1. 加载项目上下文（剧本摘要、角色列表、视觉设定）
2. 加载当前分镜及前后文分镜
3. 用 LLM 深度分析，输出素材需求 + 视频生成指令
4. 调用 Seedream 生成素材图片
5. 替换占位符，返回完整可执行指令
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.script import Script
from app.services import storyboard_service
from app.services.llm import get_llm_client
from app.services.project_service import list_project_characters

logger = logging.getLogger(__name__)

_DIRECTOR_SYSTEM_PROMPT = """你是一位资深短剧导演和AI视频技术专家。你的任务是分析一个分镜镜头，规划需要预先生成的视觉素材，并输出结构化的创意数据和视频生成指令。

你必须遵循以下原则：
1. 理解剧本上下文和角色关系，确保视觉元素符合故事逻辑。
2. 对于动作描述中的模糊道具（如"一张旧照片"），你需要根据剧本和角色关系推断其具体内容（如"照片中是主角和已故父亲的合影"），并生成详细的图片描述。
3. 对于需要角色特定表情的镜头，生成表情参考图的需求。
4. 对于环境描述，如果过于简单，补充视觉细节。
5. 理解视频生成模型的能力：图生视频模式可以接受最多9张参考图片作为输入。

**素材必要性判断**：
- required（必须生成）：角色特定表情、关键道具（如含有角色的合影）、特定场景背景、特效参考图
- optional（可选生成）：通用背景（雨夜街道、办公室等）、通用道具（手机、杯子、打火机等）

**视频指令中的图片引用**：
- 为每个 required 素材分配 material_index（从1开始递增）
- 在视频 prompt 中使用"图片1"、"图片2"等占位符精确引用对应素材
- 只有 required 素材才会被视频指令引用

**creative_data 创意数据（核心输出）**：
你必须输出结构化的创意数据，包含以下字段：
- subject: 画面主体描述（可含"图片n"占位符引用素材），需具体、有视觉画面感
- action: 动作描述，描述角色的具体动作和动态变化
- environment: 环境场景描述，包含光照、氛围等视觉要素
- camera: 镜头指令对象，字段必须从预定义词汇中选择：
  - shot: 景别，可选值：极特写|特写|近景|中景|中远景|全景|远景|大远景
  - movement: 运镜，可选值：固定|推|拉|左摇|右摇|上摇|下摇|环绕|跟拍|手持|升降|甩镜
  - stability: 稳定方式，可选值：三脚架|手持|稳定器|滑轨
- style: 视觉风格，如"电影感"、"写实"、"赛博朋克"等
- lighting: 光照描述（可选），如"自然光"、"黄金时刻"、"霓虹"等
- dialogue: 对话文本（如有），用于音画同步
- duration_suggestion: 建议视频时长（秒），范围 3-15

⚠️ 严重警告：所有 prompt 字段必须使用中文！生成图片的提示词必须全部用中文描述！
如果你输出英文提示词，系统将直接报错。

输出格式必须为严格的 JSON 对象（不要包含 markdown 代码块标记），结构如下：

{
  "material_requirements": [
    {
      "id": "简短英文标识",
      "type": "prop 或 character_expression 或 background 或 vfx",
      "name": "素材名称（中文）",
      "description": "素材的详细中文描述，说明它应该长什么样",
      "reason": "为什么需要这个素材（中文，简短）",
      "necessity": "required 或 optional",
      "material_index": 1,
      "prompt": "用于 AI 生图的中文提示词，详细描述素材的外观、光照、构图，4K"
    }
  ],
  "creative_data": {
    "subject": "图片1中的泛黄旧照片被一双修长的男性手拿在手中",
    "action": "金属打火机的火焰缓缓舔舐照片边缘，照片逐渐燃烧卷曲",
    "environment": "商场奢侈品店外走廊，冷色调夜景霓虹灯光映照，背景深度虚化",
    "camera": {
      "shot": "特写",
      "movement": "固定",
      "stability": "三脚架"
    },
    "style": "电影感",
    "lighting": "霓虹冷色与火光暖色对比",
    "dialogue": "",
    "duration_suggestion": 5
  },
  "video_instruction": {
    "mode": "image_to_video",
    "images": [
      {"material_id": "prop_old_photo", "material_index": 1, "description": "泛黄的旧照片"}
    ],
    "prompt": "【系统自动从 creative_data 生成，无需手动填写】",
    "negative_prompt": "【系统自动生成】",
    "audio": {
      "voiceover": "画外音文本（如有），否则空字符串",
      "sound_effects": ["音效描述1", "音效描述2"],
      "bgm": "背景音乐描述"
    },
    "duration": 5,
    "aspect_ratio": "9:16"
  }
}

注意事项：
- material_requirements 至少包含1个背景图需求
- necessity 为 required 的素材必须有 material_index，optional 的素材 material_index 为 null
- video_instruction.images 数组的顺序必须与 creative_data.subject 中"图片1""图片2"的引用顺序一致
- creative_data 的 subject 要包含"图片n"占位符来引用 required 素材
- duration 根据动作复杂度建议 3-10 秒
- video_instruction.prompt 和 negative_prompt 将由系统根据 creative_data 自动生成"""


def _extract_json_object(text: str) -> str:
    """从 LLM 响应中提取 JSON 对象。"""
    text = text.strip()
    if text.startswith("{"):
        return text
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        return m.group(0)
    raise ValueError(f"无法提取 JSON。响应前200字：{text[:200]}")


async def _load_project_context(db: AsyncSession, project_id: str) -> dict[str, Any]:
    """加载项目上下文：剧本摘要、角色列表。"""
    from app.services.project_service import get_project

    project = await get_project(db, project_id)
    if not project:
        return {"title": "未知项目", "script_summary": "", "characters": [], "visual_settings": {}}

    # 加载剧本
    script_summary = ""
    if project.current_script_id:
        result = await db.execute(select(Script).where(Script.id == project.current_script_id))
        script = result.scalar_one_or_none()
        if script and script.content:
            content = script.content
            title = content.get("title", "")
            episodes = content.get("episodes", [])
            parts = [f"《{title}》"]
            for ep in episodes[:3]:
                ep_no = ep.get("episode", 1)
                scenes = ep.get("scenes", [])
                actions = [s.get("action", "") for s in scenes[:3] if s.get("action")]
                if actions:
                    parts.append(f"第{ep_no}集：{'；'.join(actions)}")
            script_summary = "\n".join(parts)

    # 加载角色
    char_list = await list_project_characters(db, project_id)
    characters = []
    for c in char_list:
        traits = c.get("traits", {})
        characters.append({
            "name": c.get("character_name", ""),
            "role_type": traits.get("role_type", ""),
            "appearance": traits.get("appearance", ""),
            "personality": traits.get("personality", ""),
        })

    return {
        "title": project.name,
        "script_summary": script_summary[:2000],
        "characters": characters,
        "visual_settings": {},
    }


async def analyze_and_plan(
    db: AsyncSession,
    storyboard_id: str,
    regenerate: bool = False,
) -> dict[str, Any]:
    """
    智能导演：分析分镜并规划素材 + 视频指令。

    Returns:
        包含 material_requirements（含生成的图片URL）和 video_instruction 的字典。
    """
    # 1. 加载当前分镜
    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise ValueError(f"分镜 {storyboard_id} 不存在")

    # 如果已有分析且不强制重新生成，返回（补全新字段后）
    if not regenerate and storyboard.director_analysis:
        logger.info("使用缓存的导演分析: storyboard=%s", storyboard_id[:8])
        return migrate_director_analysis(storyboard.director_analysis)

    # 2. 加载项目上下文
    project_id = storyboard.project_id
    context = await _load_project_context(db, project_id) if project_id else {
        "title": "", "script_summary": "", "characters": [], "visual_settings": {},
    }

    # 3. 加载前后文分镜
    all_sbs = await storyboard_service.list_storyboards(db, project_id=project_id)
    neighbors = []
    for i, sb in enumerate(all_sbs):
        if sb.id == storyboard.id:
            for j in range(max(0, i - 2), min(len(all_sbs), i + 3)):
                if j != i:
                    neighbors.append({
                        "episode": all_sbs[j].episode_no,
                        "shot_no": all_sbs[j].shot_no,
                        "action": all_sbs[j].action[:100],
                        "emotion": all_sbs[j].emotion,
                    })
            break

    # 4. 构建 LLM 用户提示词
    current_sb = {
        "episode": storyboard.episode_no,
        "shot_no": storyboard.shot_no,
        "shot_type": storyboard.shot_type,
        "camera_move": storyboard.camera_move,
        "action": storyboard.action,
        "emotion": storyboard.emotion,
        "environment": storyboard.environment,
        "lighting": storyboard.lighting,
        "vfx": storyboard.vfx or "无",
        "dialogue": storyboard.dialogue or "",
        "duration": storyboard.duration_seconds,
    }

    user_data = {
        "project": {
            "title": context["title"],
            "script_summary": context["script_summary"],
            "characters": context["characters"],
        },
        "current_storyboard": current_sb,
        "neighbor_storyboards": neighbors,
    }

    user_prompt = (
        f"项目信息：\n{json.dumps(user_data, ensure_ascii=False, indent=2)}\n\n"
        f"请分析这个分镜，输出素材需求和视频生成指令。"
    )

    # 5. 调用 LLM
    client = get_llm_client()
    logger.info("智能导演分析开始: storyboard=%s", storyboard_id[:8])
    raw = await client.generate(user_prompt, system=_DIRECTOR_SYSTEM_PROMPT)

    json_str = _extract_json_object(raw)
    json_str = re.sub(r"[\x00-\x1f]", " ", json_str)

    try:
        analysis = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error("导演分析 JSON 解析失败: %s", e)
        raise ValueError(f"导演分析结果解析失败: {e}") from e

    # 6. 标记素材状态 + 补全新字段 + 构建引用
    requirements = analysis.get("material_requirements", [])
    required_count = 0
    for req in requirements:
        req["status"] = "pending"
        req["generated_url"] = None
        # 补全 necessity（兼容 LLM 偶尔遗漏）
        if "necessity" not in req:
            rtype = req.get("type", "")
            req["necessity"] = "required" if rtype in ("character_expression", "prop") else "optional"
        # 分配 material_index
        if req.get("necessity") == "required":
            required_count += 1
            req.setdefault("material_index", required_count)
        else:
            req.setdefault("material_index", None)

    # 补全 video_instruction.images
    vi = analysis.get("video_instruction", {})
    if not vi.get("images"):
        images_arr = []
        for req in requirements:
            if req.get("necessity") == "required":
                images_arr.append({
                    "material_id": req.get("id"),
                    "material_index": req.get("material_index"),
                    "description": req.get("name"),
                })
        vi["images"] = images_arr
        analysis["video_instruction"] = vi

    # 7. 从 creative_data 生成符合 Seedance 规范的 prompt
    creative_data = analysis.get("creative_data")
    if creative_data:
        from app.services.prompt_engineering_service import PromptAssembler

        assembler = PromptAssembler()
        assembled = assembler.assemble_from_creative_data(creative_data)
        vi["prompt"] = assembled["prompt"]
        vi["negative_prompt"] = assembled["negative_prompt"]
        analysis["video_instruction"] = vi
        # duration 优先用 creative_data 的建议
        dur = creative_data.get("duration_suggestion")
        if dur:
            vi.setdefault("duration", dur)
        logger.info(
            "PromptAssembler 已生成: prompt_len=%d, neg_len=%d",
            len(assembled["prompt"]), len(assembled["negative_prompt"]),
        )

    # 8. 保存到数据库
    await storyboard_service.update_storyboard(
        db, storyboard,
        director_analysis=analysis,
        pregen_materials=dict(storyboard.pregen_materials or {}),
    )

    logger.info("智能导演分析完成: storyboard=%s, %d个素材(%d个必需)", storyboard_id[:8], len(requirements), required_count)
    return analysis


def migrate_director_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    """为旧格式 director_analysis 补全新字段（necessity / material_index / images / creative_data）。"""
    if not analysis:
        return analysis
    requirements = analysis.get("material_requirements", [])
    if not requirements:
        return analysis

    required_count = 0
    for req in requirements:
        if "necessity" not in req:
            rtype = req.get("type", "")
            req["necessity"] = "required" if rtype in ("character_expression", "prop") else "optional"
        if req.get("necessity") == "required":
            required_count += 1
            req.setdefault("material_index", required_count)
        else:
            req.setdefault("material_index", None)

    vi = analysis.get("video_instruction", {})
    if not vi.get("images"):
        vi["images"] = [
            {"material_id": r.get("id"), "material_index": r.get("material_index"), "description": r.get("name")}
            for r in requirements if r.get("necessity") == "required"
        ]
        analysis["video_instruction"] = vi

    # 为旧格式补全 creative_data（启发式从 prompt 提取）
    if not analysis.get("creative_data"):
        analysis["creative_data"] = _extract_creative_data_from_prompt(vi.get("prompt", ""))

    return analysis


def _extract_creative_data_from_prompt(prompt: str) -> dict[str, Any]:
    """启发式从旧格式 prompt 中提取 creative_data 字段。"""
    return {
        "subject": prompt[:100] if prompt else "",
        "action": "",
        "environment": "",
        "camera": {"shot": "中景", "movement": "固定", "stability": "三脚架"},
        "style": "电影感",
        "lighting": "",
        "dialogue": "",
        "duration_suggestion": 5,
        "_migrated": True,
    }
