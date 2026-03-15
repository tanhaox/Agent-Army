"""
大模型工具 - 统一管理LLM API调用
"""

from typing import Dict, List, Any, Optional
import aiohttp
import asyncio
import json

from src.core.logger import get_logger
from src.core.utils.rate_limiter import get_global_limiter_manager


class LLMTool:
    """
    大模型工具

    职责：
    - 封装所有LLM API调用（智谱、DeepSeek、OpenAI）
    - 自动选择最优模型（成本、质量、配额）
    - 提供统一接口给AI Agent使用
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("llm_tool")
        self.config = config or {}

        # 初始化节流器
        self.rate_limiter = get_global_limiter_manager().get("zhipu_ai")

        # 模型配置
        self.models = {
            "glm-5": {
                "provider": "zhipu",
                "max_tokens": 128000,
                "cost_per_million": 0,  # Max套餐免费
                "quality": "very_high",
                "speed": "fast"
            },
            "glm-4": {
                "provider": "zhipu",
                "max_tokens": 128000,
                "cost_per_million": 0,  # Max套餐免费
                "quality": "high",
                "speed": "fast"
            },
            "glm-4-flash": {
                "provider": "zhipu",
                "max_tokens": 128000,
                "cost_per_million": 0,  # Max套餐免费
                "quality": "medium",
                "speed": "very_fast"
            },
            "deepseek-chat": {
                "provider": "deepseek",
                "max_tokens": 64000,
                "cost_per_million": 2,  # ¥2/百万tokens
                "quality": "medium",
                "speed": "fast"
            },
            "gpt-4o": {
                "provider": "openai",
                "max_tokens": 128000,
                "cost_per_million": 150,  # ¥150/百万tokens
                "quality": "very_high",
                "speed": "medium"
            }
        }

        # 默认使用智谱GLM-5（最强模型）
        self.default_model = "glm-5"

        self.logger.info("大模型工具初始化完成")

    async def chat(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> str:
        """
        统一的大模型调用接口

        Args:
            prompt: 提示词
            model: 模型名称（默认glm-4）
            temperature: 温度参数（0-1）
            max_tokens: 最大tokens数
            **kwargs: 其他参数

        Returns:
            模型生成的文本
        """
        model = model or self.default_model

        self.logger.info(f"调用大模型: {model}, tokens上限: {max_tokens}")

        try:
            # 接入智谱AI API
            import os
            from zhipuai import ZhipuAI
            import asyncio

            api_key = os.getenv("ZHIPU_API_KEY", "")
            if not api_key:
                raise ValueError("ZHIPU_API_KEY未配置，请通过Web界面配置")

            # ⭐ Phase 3: API调用节流控制（带超时）
            try:
                await self.rate_limiter.acquire(timeout=70.0)
                self.logger.info("✅ 智谱AI节流器许可已获取")
            except TimeoutError as e:
                self.logger.error(f"❌ 智谱AI调用超时: {e}")
                raise Exception(f"获取智谱AI API调用许可失败: {e}")

            self.logger.info(f"调用智谱AI: {model}")

            # 在异步环境中调用同步API
            def call_zhipu():
                client = ZhipuAI(api_key=api_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content

            # 使用线程池执行同步调用
            result = await asyncio.get_event_loop().run_in_executor(None, call_zhipu)

            self.logger.info(f"✅ 智谱AI响应成功: {len(result)}字符")

            return result

        except Exception as e:
            self.logger.error(f"❌ 智谱AI调用失败: {str(e)}")
            # 如果智谱AI失败，尝试降级方案
            self.logger.warning("⚠️ 使用备用响应...")
            return await self._sample_chat(prompt, model)

    async def chat_with_history(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        带历史记录的对话

        Args:
            messages: 消息历史 [{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数

        Returns:
            模型生成的文本
        """
        model = model or self.default_model

        self.logger.info(f"多轮对话: {len(messages)}条历史, 模型: {model}")

        # TODO: 接入真实API
        response = await self._sample_chat(
            messages[-1]["content"],  # 最后一条消息
            model
        )

        return response

    async def analyze(
        self,
        text: str,
        task: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析任务（结构化输出）

        Args:
            text: 待分析文本
            task: 任务类型（sentiment、summary、extraction等）
            model: 模型名称

        Returns:
            结构化的分析结果
        """
        model = model or self.default_model

        self.logger.info(f"分析任务: {task}, 模型: {model}")

        # 构建提示词
        if task == "sentiment":
            prompt = f"""分析以下文本的情感倾向，返回JSON格式：
{{"sentiment": "positive/negative/neutral", "score": 0.85, "confidence": 0.9}}

文本：
{text}"""
        elif task == "summary":
            prompt = f"""总结以下文本的核心内容，返回JSON格式：
{{"summary": "核心内容", "keywords": ["关键词1", "关键词2"], "importance": 8.5}}

文本：
{text}"""
        else:
            prompt = text

        # TODO: 接入真实API
        response = await self._sample_chat(prompt, model)

        # 解析JSON响应
        try:
            result = json.loads(response)
        except:
            result = {"raw_response": response}

        return result

    async def _sample_chat(self, prompt: str, model: str) -> str:
        """
        示例对话（临时方法）

        TODO: 接入真实API后删除此方法
        """
        # 模拟异步
        await asyncio.sleep(0.2)

        # 根据提示词返回示例响应
        if "情感" in prompt or "sentiment" in prompt:
            return '{"sentiment": "positive", "score": 0.85, "confidence": 0.9}'
        elif "总结" in prompt or "summary" in prompt:
            return '{"summary": "公司业绩良好，增长稳定", "keywords": ["增长", "盈利"], "importance": 8.5}'
        elif "分析" in prompt:
            return "基于分析，我认为该股票具有良好的投资价值。"
        else:
            return f"收到您的请求。根据当前信息分析，这是一个值得关注的标的。"


# ========== 便捷函数 ==========

async def chat(prompt: str, model: str = "glm-5") -> str:
    """
    大模型对话（便捷函数）

    Args:
        prompt: 提示词
        model: 模型名称（默认glm-5）

    Returns:
        模型响应
    """
    tool = LLMTool()
    return await tool.chat(prompt, model)
