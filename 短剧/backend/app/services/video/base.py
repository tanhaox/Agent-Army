"""
视频生成服务抽象基类。

预留视频模型切换接口，未来可扩展 Kling、Seedance 等实现。
通过 VIDEO_PROVIDER 环境变量切换具体实现。
"""

from abc import ABC, abstractmethod


class BaseVideoGenerator(ABC):
    """
    视频生成器抽象基类。

    用法::

        generator = get_video_generator()
        url = await generator.generate(image_url="...", prompt="镜头缓缓推进")
    """

    @abstractmethod
    async def generate(self, prompt: str, image_url: str | None = None, **kwargs) -> str:
        """
        根据提示词生成视频。

        Args:
            prompt: 视频描述提示词。
            image_url: 参考图片 URL（可选）。
            **kwargs: 额外参数（如时长、分辨率等）。

        Returns:
            生成的视频 URL。
        """
