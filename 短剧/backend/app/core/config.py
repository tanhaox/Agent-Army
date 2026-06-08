"""
全局配置模块 - 使用 pydantic-settings 读取环境变量。

所有配置集中在此管理，其他模块通过 get_settings() 获取。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用全局配置，自动从 .env 文件和环境变量读取。"""

    # --- 应用 ---
    APP_NAME: str = "短剧AI - 智能制片工厂"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # --- LLM Provider ---
    LLM_PROVIDER: str = "deepseek"  # 可选: deepseek

    # --- DeepSeek ---
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # --- 图片生成 Provider（预留）---
    IMAGE_PROVIDER: str = "comfyui"  # 可选: comfyui / replicate

    # --- 视频生成 Provider（预留）---
    VIDEO_PROVIDER: str = "kling"  # 可选: kling / seedance

    # --- 火山引擎 Seedream ---
    ARK_API_KEY: str = ""
    SEEDREAM_MODEL: str = "doubao-seedream-5-0-260128"
    SEEDREAM_SIZE: str = "2048x2048"

    # --- 火山引擎 Seedance 视频生成 ---
    SEEDANCE_API_KEY: str = ""
    SEEDANCE_MODEL: str = "doubao-seedance-2-0-260128"
    SEEDANCE_TIMEOUT: int = 600
    SEEDANCE_POLL_INTERVAL: float = 5.0
    SEEDANCE_MAX_CONCURRENT: int = 3  # 批量生成最大并发数

    # --- ComfyUI ---
    COMFYUI_BASE_URL: str = "http://localhost:8188"
    COMFYUI_TIMEOUT: int = 120  # 秒

    # --- Kling AI 视频生成 ---
    KLING_ACCESS_KEY: str = ""
    KLING_SECRET_KEY: str = ""
    KLING_API_BASE: str = "https://api.kling.kuaishou.com"
    KLING_TIMEOUT: int = 300  # 视频生成轮询超时（秒）
    KLING_POLL_INTERVAL: float = 3.0  # 轮询间隔（秒）

    # --- 火山引擎豆包 TTS ---
    VOLC_TTS_APP_ID: str = ""
    VOLC_TTS_TOKEN: str = ""
    VOLC_TTS_DEFAULT_VOICE: str = "zh_female_vv_uranus"
    VOLC_TTS_FORMAT: str = "mp3"
    VOLC_TTS_SAMPLE_RATE: int = 24000
    VOLC_TTS_TIMEOUT: int = 60  # 同步生成轮询超时（秒）
    VOLC_TTS_POLL_INTERVAL: float = 2.0

    # --- 数据库 ---
    DATABASE_URL: str = ""
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # --- Redis ---
    REDIS_URL: str = "redis://redis:6379/0"

    # --- 安全 ---
    CORS_ORIGINS: str = "http://localhost,http://127.0.0.1"
    ENCRYPTION_KEY: str = ""  # Fernet 密钥，留空则不加密

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """返回全局单例配置对象。"""
    return Settings()
