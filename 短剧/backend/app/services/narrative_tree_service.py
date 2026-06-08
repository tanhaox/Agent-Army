"""
叙事树生成服务 - 调用 AI 生成分支叙事树（带评分），并支持从选中路径生成剧本。

职责：
- 结合爆款元素库构建提示词
- 调用 LLM 生成带评分的叙事树 JSON
- 解析、校验树结构（含 score/pros/cons）
- 从用户选中的节点路径构建主线描述
"""

import asyncio
import json
import logging
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.narrative_tree import NarrativeTree
from app.services.blockbuster_library import build_library_context
from app.services.llm import get_llm_client, LLMConnectionError, LLMGenerateError

logger = logging.getLogger(__name__)

# 系统提示词：整合爆款元素库，要求输出带评分的叙事树
_SYSTEM_PROMPT_TEMPLATE = """你是一位顶尖的短剧编剧和爆款策划专家。用户会给你一个短剧创意主题，请你生成一个分支叙事树（思维导图）。

你必须且只能输出一个合法的 JSON 对象，不要输出任何其他文字、解释或 markdown 代码块标记。

直接以 {{ 开头，以 }} 结尾。

JSON 结构如下（严格使用以下英文字段名）：

{{
  "root": {{
    "id": "node_1",
    "text": "核心冲突描述，20字内",
    "tags": ["核心冲突"],
    "score": null,
    "pros": null,
    "cons": null,
    "children": [
      {{
        "id": "node_2",
        "text": "分支方向描述，20字内",
        "tags": ["标签1", "标签2"],
        "score": 8,
        "pros": "这个方向的优点，15字内",
        "cons": "这个方向的缺点，15字内",
        "children": [
          {{
            "id": "node_5",
            "text": "具体发展描述，20字内",
            "tags": ["标签1"],
            "score": 7,
            "pros": "优点，15字内",
            "cons": "缺点，15字内"
          }}
        ]
      }}
    ]
  }}
}}

创作规则（必须严格遵守）：

1. 根节点(root)是核心冲突，必须吸引人，score 为 null，tags 为 ["核心冲突"]
2. 第一层分支必须 3-5 个，每个代表一种截然不同的"发展方向"。
   - 必须覆盖不同风格，例如：常规发展、狗血发展、脑洞发展、反转发展、甜蜜发展、虐心发展、爽文发展、悬疑发展。
   - 绝对不能只生成 2 个分支！至少 3 个，鼓励 4-5 个。
3. 第二层分支：每个第一层节点下必须至少 2-3 个子分支，展示该方向的不同走向。
4. 每个非根节点必须包含：
   - score：1-10 整数评分（基于爆款潜力）
   - pros：这个方向的优点，15字内
   - cons：这个方向的缺点，15字内
5. 标签要求（极其重要）：
   - 每个非根节点必须带 tags 数组（至少1个标签）。
   - 可选标签：严重、普通、脑洞、反转、狗血、甜蜜、虐心、高概念、爽文、悬疑。
   - 同一层级的兄弟节点应该使用不同标签，确保多样性。
   - 不要所有节点都用同一个标签！
6. 评分分布要求（极其重要）：
   - 评分必须有区分度！
   - 同一父节点下的子节点，必须包含至少一个高分（8-10）和至少一个低分（1-4）。
   - 避免所有分数都集中在 5-7 分之间。
   - 评分标准：8-10分=强冲突高反转出人意料，5-7分=有吸引力但套路化，1-4分=平淡可预测。
7. 每个节点的 text 要精炼，20字以内
8. 每个节点的 id 必须唯一，格式为 "node_N"

{library_context}

再次强调：
- 第一层至少3个分支，最多5个！绝不能只有2个！
- 每个节点必须带不同的标签！
- 评分必须有区分度，要有高分也有低分！
- 只输出 JSON，不要输出任何其他内容，不要用 markdown 代码块。"""


class NarrativeTreeError(Exception):
    """叙事树生成或解析失败时抛出。"""


class NarrativeTreeService:
    """
    叙事树生成服务。

    流程：
    1. 结合爆款元素库构建提示词
    2. 调用 LLM 生成带评分的叙事树
    3. 解析、校验并保存
    """

    def __init__(self) -> None:
        self._client = get_llm_client()
        self._system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            library_context=build_library_context(),
        )

    def _extract_json(self, text: str) -> str:
        """从 AI 响应中提取 JSON 字符串。"""
        text_stripped = text.strip()

        if text_stripped.startswith("{"):
            return text_stripped

        # 提取代码块
        code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text_stripped)
        if code_block_match:
            return code_block_match.group(1).strip()

        # 查找最外层 { }
        brace_match = re.search(r"\{[\s\S]*\}", text_stripped)
        if brace_match:
            return brace_match.group(0)

        raise NarrativeTreeError(
            f"无法从 AI 响应中提取 JSON。原始响应前200字：{text_stripped[:200]}"
        )

    def _validate_tree_structure(self, data: dict[str, Any]) -> None:
        """
        校验叙事树结构。

        要求：
        - 必须有 root 节点
        - root 必须有 id、text、children
        - 每个子节点必须有 id、text、tags、score、pros、cons
        """
        if "root" not in data:
            raise NarrativeTreeError("叙事树缺少 root 节点")

        root = data["root"]
        if not root.get("id") or not root.get("text"):
            raise NarrativeTreeError("根节点缺少 id 或 text")

        children = root.get("children", [])
        if not children:
            raise NarrativeTreeError("根节点至少需要 3 个分支方向")
        if len(children) < 3:
            logger.warning("根节点分支不足3个: 只有%d个", len(children))

        # 收集所有节点 ID，检查唯一性和评分
        all_ids: set[str] = set()

        def check_node(node: dict, depth: int) -> None:
            node_id = node.get("id")
            if not node_id:
                raise NarrativeTreeError(f"深度 {depth} 的节点缺少 id")
            if node_id in all_ids:
                raise NarrativeTreeError(f"节点 ID 重复: {node_id}")
            all_ids.add(node_id)

            if not node.get("text"):
                raise NarrativeTreeError(f"节点 {node_id} 缺少 text")

            # 非根节点检查评分
            if depth > 0:
                score = node.get("score")
                if score is not None:
                    if not isinstance(score, (int, float)) or score < 1 or score > 10:
                        logger.warning("节点 %s 评分异常: %s，已修正", node_id, score)
                        node["score"] = 5

                # 补全缺失的 pros/cons
                if not node.get("pros"):
                    node["pros"] = ""
                if not node.get("cons"):
                    node["cons"] = ""

            for child in node.get("children", []):
                check_node(child, depth + 1)

        check_node(root, 0)

    def _parse_response(self, raw_text: str) -> dict[str, Any]:
        """解析 AI 响应为叙事树字典。"""
        json_str = self._extract_json(raw_text)

        # 清理非法控制字符
        json_str = re.sub(r"[\x00-\x1f]", " ", json_str)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise NarrativeTreeError(
                f"JSON 解析失败: {e}. 原始内容前200字：{json_str[:200]}"
            ) from e

        if not isinstance(data, dict):
            raise NarrativeTreeError(
                f"JSON 根元素不是对象，而是 {type(data).__name__}"
            )

        self._validate_tree_structure(data)
        return data

    def _build_prompt(self, theme: str, max_breadth: int, max_depth: int) -> str:
        """构建用户提示词，含爆款元素参考。"""
        return (
            f"请根据以下创意主题生成分支叙事树：\n\n"
            f"主题：{theme}\n\n"
            f"强制要求：\n"
            f"1. 第一层必须生成 {max(min(max_breadth, 5), 3)} 个分支（每个分支代表不同发展方向）\n"
            f"2. 第二层每个节点下至少 2 个子分支\n"
            f"3. 每个分支必须附带不同标签（从：严重、普通、脑洞、反转、狗血、甜蜜、虐心、高概念、爽文、悬疑 中选）\n"
            f"4. 评分必须有区分度：同一父节点的子节点中，至少1个8分以上，至少1个4分以下\n"
            f"5. 高分分支应当是冲突强、反转多、出人意料的方向\n\n"
            f"请直接输出 JSON，不要包含任何其他文字。"
        )

    async def generate_tree(
        self,
        db: AsyncSession,
        project_id: str,
        theme: str,
        max_breadth: int = 3,
        max_depth: int = 2,
    ) -> NarrativeTree:
        """
        生成叙事树并保存到数据库。

        Args:
            db: 数据库会话。
            project_id: 项目 ID。
            theme: 创意主题。
            max_breadth: 每层最大分支数。
            max_depth: 最大深度。

        Returns:
            保存后的 NarrativeTree 对象。
        """
        prompt = self._build_prompt(theme, max_breadth, max_depth)

        logger.info("开始生成叙事树: project=%s, theme=%s", project_id, theme[:30])

        # 第一次调用
        raw_response = await self._client.generate(prompt, system=self._system_prompt)

        try:
            tree_data = self._parse_response(raw_response)
            logger.info("叙事树解析成功: root=%s", tree_data.get("root", {}).get("text"))
        except NarrativeTreeError as e:
            logger.warning("首次解析失败: %s，尝试修复...", e)

            # 第二次调用
            fix_prompt = (
                "上一次你输出的内容不是合法的 JSON。请修正并重新输出。\n\n"
                "要求：只输出一个 JSON 对象，不要有任何其他文字。\n"
                "非根节点必须包含 score、pros、cons 字段。\n\n"
                f"主题：{theme}"
            )
            raw_response = await self._client.generate(fix_prompt, system=self._system_prompt)

            try:
                tree_data = self._parse_response(raw_response)
                logger.info("修复后解析成功")
            except NarrativeTreeError as e2:
                logger.error("修复后仍解析失败: %s", e2)
                raise NarrativeTreeError(
                    f"两次尝试均无法解析叙事树 JSON。最后错误：{e2}"
                ) from e2

        # 保存到数据库
        tree = NarrativeTree(
            project_id=project_id,
            user_theme=theme,
            tree_data=tree_data,
            status="draft",
        )
        db.add(tree)
        await db.commit()
        await db.refresh(tree)

        logger.info("叙事树已保存: id=%s, project=%s", tree.id, project_id)
        return tree

    async def generate_outlines(
        self,
        db: "AsyncSession",
        tree_id: str,
        tree_data: dict[str, Any],
        selected_ids: list[str],
        user_theme: str,
        styles: list[str] | None = None,
    ) -> tuple[list[dict[str, str]], str]:
        """
        根据叙事树选中路径生成并保存多版本剧情概要。

        Args:
            db: 数据库会话。
            tree_id: 叙事树 ID。
            tree_data: 叙事树数据。
            selected_ids: 用户选中的节点 ID 列表。
            user_theme: 用户原始主题。
            styles: 风格列表，默认虐心催泪/甜宠搞笑/强反转爽文。

        Returns:
            (outlines, storyline) — 概要列表（含 ID）和主线描述。
        """
        from app.models.narrative_outline import NarrativeOutline

        if styles is None:
            styles = ["虐心催泪", "甜宠搞笑", "强反转爽文"]

        storyline = self.collect_node_texts(tree_data, selected_ids)
        logger.info("生成概要主线: %s", storyline[:100])

        library_ctx = build_library_context()

        version_letters = "ABCDEFGHIJ"

        async def _gen_one(idx: int, style: str) -> dict[str, str]:
            sys_prompt = (
                f"你是一位顶尖短剧编剧，擅长{style}风格。\n"
                f"{library_ctx}\n\n"
                f"请根据以下故事主线，写一段 200-300 字的剧情概要，"
                f"突出{style}风格的特点。\n\n"
            )
            style_hints = {
                "虐心催泪": "强调牺牲、误会、悲伤氛围，结尾留有希望。多使用情感撕裂和极致羞辱等钩子。",
                "甜宠搞笑": "强调甜蜜互动、幽默对白、轻松反转。多使用意外重逢和甜蜜陷阱等钩子。",
                "强反转爽文": "强调身份揭露、打脸、逆袭、爽点密集。多使用身份反转和权力碾压等钩子。",
            }
            hint = style_hints.get(style, "突出该风格的典型元素和节奏。")
            user_prompt = (
                f"原始主题：{user_theme}\n"
                f"故事主线：{storyline}\n\n"
                f"风格要求：{style}。{hint}\n\n"
                f"请直接输出剧情概要文本（200-300字），不要加标题、不要用 markdown。"
            )
            raw = await self._client.generate(user_prompt, system=sys_prompt)
            return {
                "style": style,
                "text": raw.strip(),
                "version": version_letters[idx % len(version_letters)],
            }

        # 串行生成三种风格
        outlines: list[dict[str, str]] = []
        for i, s in enumerate(styles):
            logger.info("正在生成概要 %d/%d: %s", i + 1, len(styles), s)
            outline = await _gen_one(i, s)

            # 保存到数据库
            record = NarrativeOutline(
                narrative_tree_id=tree_id,
                style=outline["style"],
                outline_text=outline["text"],
                version_label=outline["version"],
                storyline=storyline,
            )
            db.add(record)
            await db.flush()

            outline["id"] = record.id
            outlines.append(outline)

        await db.commit()
        logger.info("概要生成并保存完成: %d 个版本", len(outlines))
        return outlines, storyline

    @staticmethod
    def collect_node_texts(
        tree_data: dict[str, Any],
        selected_ids: list[str],
    ) -> str:
        """
        从叙事树中收集选中节点的文本，构建主线描述。

        Args:
            tree_data: 叙事树数据。
            selected_ids: 用户选中的节点 ID 列表。

        Returns:
            串联的主线描述文本（200-300字）。
        """
        selected_set = set(selected_ids)
        texts: list[str] = []

        def traverse(node: dict) -> None:
            if node.get("id") in selected_set:
                texts.append(node.get("text", ""))
            for child in node.get("children", []):
                traverse(child)

        root = tree_data.get("root", {})
        if root.get("id") in selected_set:
            texts.insert(0, root.get("text", ""))
        for child in root.get("children", []):
            traverse(child)

        return " → ".join(texts)

    @staticmethod
    def validate_path(
        tree_data: dict[str, Any],
        selected_ids: list[str],
    ) -> bool:
        """
        校验选中的节点是否构成一条从根到叶子的连续路径。

        路径必须包含根节点，且每个选中的节点必须是上一个选中节点的后代。
        """
        if not selected_ids:
            return False

        selected_set = set(selected_ids)

        # 构建父子关系映射
        parent_map: dict[str, str | None] = {}

        def build_parent_map(node: dict, parent_id: str | None = None) -> None:
            node_id = node.get("id")
            if node_id:
                parent_map[node_id] = parent_id
            for child in node.get("children", []):
                build_parent_map(child, node_id)

        root = tree_data.get("root", {})
        build_parent_map(root)

        # 必须包含根节点
        root_id = root.get("id")
        if root_id not in selected_set:
            return False

        # 检查每个选中节点都存在于树中
        for sid in selected_ids:
            if sid not in parent_map:
                return False

        # 检查路径连续性：每个节点的父节点（或祖先）必须也在选中列表中
        for sid in selected_ids:
            if sid == root_id:
                continue
            pid = parent_map.get(sid)
            found_ancestor = False
            current = pid
            while current is not None:
                if current in selected_set:
                    found_ancestor = True
                    break
                current = parent_map.get(current)
            if not found_ancestor:
                return False

        return True

    async def expand_node(
        self,
        db: AsyncSession,
        tree_id: str,
        node_id: str,
        count: int = 3,
    ) -> NarrativeTree:
        """
        针对指定节点生成额外的子分支，合并到原有叙事树中。

        Args:
            db: 数据库会话。
            tree_id: 叙事树 ID。
            node_id: 要扩展的节点 ID。
            count: 要生成的新分支数量，默认 3。

        Returns:
            更新后的 NarrativeTree 对象。
        """
        result = await db.execute(
            select(NarrativeTree).where(NarrativeTree.id == tree_id)
        )
        tree = result.scalar_one_or_none()
        if tree is None:
            raise NarrativeTreeError(f"叙事树 {tree_id} 不存在")

        tree_data = tree.tree_data

        # 查找目标节点及其已有子节点文本（用于避免重复）
        target_node = self._find_node_in_tree(tree_data["root"], node_id)
        if target_node is None:
            raise NarrativeTreeError(f"节点 {node_id} 不存在于叙事树中")

        existing_texts = [c.get("text", "") for c in target_node.get("children", [])]
        existing_desc = "、".join(existing_texts) if existing_texts else "无"

        # 收集从根到目标节点的路径文本，提供上下文
        path_texts = self._collect_path_to_node(tree_data["root"], node_id)
        context = " → ".join(path_texts)

        # 构建 prompt 让 AI 生成新分支
        expand_prompt = (
            f"当前叙事树路径：{context}\n"
            f"当前节点「{target_node.get('text', '')}」已有分支：{existing_desc}\n\n"
            f"请为这个节点生成 {count} 个全新的、不同于已有分支的子分支。\n"
            f"要求：\n"
            f"1. 每个分支必须风格不同（参考标签：脑洞、反转、狗血、甜蜜、虐心、爽文、悬疑等）\n"
            f"2. 评分 1-10 分，必须有区分度（至少1个高分8+，至少1个低分4-以下）\n"
            f"3. 每个分支必须有 tags、score、pros、cons\n"
            f"4. 直接输出 JSON 数组，格式如下：\n"
            f'[{{"id": "node_N", "text": "...", "tags": ["..."], "score": N, "pros": "...", "cons": "..."}}]\n'
            f"5. 不要输出任何其他文字"
        )

        logger.info("扩展节点: tree=%s, node=%s, count=%d", tree_id, node_id, count)

        raw = await self._client.generate(expand_prompt, system=self._system_prompt)

        # 解析新分支
        json_str = self._extract_json(raw)
        json_str = re.sub(r"[\x00-\x1f]", " ", json_str)
        try:
            new_children = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise NarrativeTreeError(
                f"扩展节点 JSON 解析失败: {e}"
            ) from e

        if not isinstance(new_children, list):
            raise NarrativeTreeError("扩展节点返回的不是数组")

        # 分配唯一 ID
        max_id = self._get_max_node_id(tree_data["root"])
        for child in new_children:
            max_id += 1
            child["id"] = f"node_{max_id}"
            # 确保必要字段
            if "tags" not in child:
                child["tags"] = ["普通"]
            if "score" not in child or child["score"] is None:
                child["score"] = 5
            if "pros" not in child:
                child["pros"] = ""
            if "cons" not in child:
                child["cons"] = ""
            if "children" not in child:
                child["children"] = []

        # 合并到目标节点
        if "children" not in target_node:
            target_node["children"] = []
        target_node["children"].extend(new_children)

        # 更新数据库
        tree.tree_data = tree_data
        await db.commit()
        await db.refresh(tree)

        logger.info(
            "节点扩展完成: tree=%s, node=%s, 新增%d个分支",
            tree_id, node_id, len(new_children),
        )
        return tree

    @staticmethod
    def _find_node_in_tree(node: dict, node_id: str) -> dict | None:
        """在树中查找指定 ID 的节点。"""
        if node.get("id") == node_id:
            return node
        for child in node.get("children", []):
            found = NarrativeTreeService._find_node_in_tree(child, node_id)
            if found is not None:
                return found
        return None

    @staticmethod
    def _collect_path_to_node(node: dict, target_id: str, path: list[str] | None = None) -> list[str]:
        """收集从当前节点到目标节点的路径文本。"""
        if path is None:
            path = []
        path.append(node.get("text", ""))
        if node.get("id") == target_id:
            return list(path)
        for child in node.get("children", []):
            result = NarrativeTreeService._collect_path_to_node(child, target_id, path)
            if result is not None:
                return result
        path.pop()
        return []  # type: ignore[return-value]

    @staticmethod
    def _get_max_node_id(node: dict) -> int:
        """获取树中最大的 node_N 编号。"""
        max_id = 0
        node_id = node.get("id", "")
        if isinstance(node_id, str) and node_id.startswith("node_"):
            try:
                max_id = max(max_id, int(node_id.split("_")[1]))
            except (ValueError, IndexError):
                pass
        for child in node.get("children", []):
            max_id = max(max_id, NarrativeTreeService._get_max_node_id(child))
        return max_id
