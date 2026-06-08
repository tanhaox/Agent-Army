"""
视频生成服务包。

通过 get_video_generator() 工厂方法获取具体实现。
"""

from app.services.video.base import BaseVideoGenerator

__all__ = ["BaseVideoGenerator"]
