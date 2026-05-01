import logging

from app.services.deepseek_client import deepseek

logger = logging.getLogger(__name__)


class SearchEnhancer:
    async def enhance(self, anchor_name: str, follower_count: int) -> dict:
        """用 DeepSeek 补充大V的公开背景信息。失败时抛异常，由调用方降级处理。"""
        prompt = f"""你是直播行业分析师。请根据以下主播信息，补充其公开背景资料。

主播昵称：{anchor_name}
粉丝数：{follower_count}

请输出严格 JSON：
{{
  "real_name": "真实姓名（如公开可知，否则填 null）",
  "background": "个人背景简介（50字内）",
  "content_style": "内容风格特征（30字内）",
  "controversies": "已知争议事件（如有，否则 null）",
  "career_highlights": ["里程碑事件1", "里程碑事件2"],
  "audience_profile": "核心受众画像（20字内）",
  "brand_collaborations": "已知品牌合作（如无填 null）",
  "source_note": "以上信息来自 AI 推理，可能不完全准确"
}}"""

        result = await deepseek.chat(
            [
                {"role": "system", "content": "你是直播行业数据分析师，只输出纯 JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1024,
            timeout=30.0,
            response_format={"type": "json_object"},
        )

        result["anchor_name"] = anchor_name
        logger.info("Search enhancement complete for %s", anchor_name)
        return result


search_enhancer = SearchEnhancer()
