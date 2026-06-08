"""
图片生成服务抽象基类。

预留图片模型切换接口，未来可扩展 ComfyUI、Replicate 等实现。
通过 IMAGE_PROVIDER 环境变量切换具体实现。
"""

from abc import ABC, abstractmethod


class BaseImageGenerator(ABC):
    """
    图片生成器抽象基类。

    用法::

        generator = get_image_generator()
        url = await generator.generate("一位古装少女在月光下")
    """

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        根据提示词生成图片。

        Args:
            prompt: 图片描述提示词。
            **kwargs: 额外参数（如宽高、风格等）。

        Returns:
            生成的图片 URL 或本地路径。
        """
