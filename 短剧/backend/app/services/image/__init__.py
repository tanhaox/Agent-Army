"""
图片生成服务包。

通过 get_image_generator() 工厂方法获取具体实现。
"""

from app.services.image.base import BaseImageGenerator

__all__ = ["BaseImageGenerator"]
