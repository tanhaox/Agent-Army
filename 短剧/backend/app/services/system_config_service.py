"""
系统配置服务 - 按服务商管理配置项。

提供配置 schema 定义、CRUD 操作和敏感字段掩码处理。
"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service_config import ServiceConfig

logger = logging.getLogger(__name__)

# ── 每个 Provider 的配置项 Schema ──────────────────────────

PROVIDER_SCHEMAS: dict[str, dict[str, Any]] = {
    "deepseek": {
        "display_name": "DeepSeek",
        "description": "LLM 大语言模型服务，用于剧本生成、提示词填充等文本任务。",
        "icon": "brain",
        "tutorial": [
            {"step": 1, "title": "注册 DeepSeek 账号", "content": "访问 DeepSeek 开放平台，点击右上角「注册」。支持手机号或邮箱注册。", "link": "https://platform.deepseek.com/", "link_text": "前往 DeepSeek 开放平台"},
            {"step": 2, "title": "进入 API Keys 页面", "content": "登录后，点击左侧菜单「API Keys」或直接访问 API Keys 管理页面。", "link": "https://platform.deepseek.com/api_keys", "link_text": "直接打开 API Keys 页面"},
            {"step": 3, "title": "创建新的 API Key", "content": "点击「创建 API Key」按钮，输入名称（如「短剧AI」），确认后系统会生成一个以 sk- 开头的密钥。请立即复制保存，页面关闭后无法再次查看。"},
            {"step": 4, "title": "充值余额（如需）", "content": "新注册账号赠送少量额度。如需更多用量，可在「充值」页面购买。建议先充值 10 元体验。", "link": "https://platform.deepseek.com/usage", "link_text": "查看用量与充值"},
            {"step": 5, "title": "填入上方配置", "content": "将复制的 API Key 粘贴到上方的「API Key」输入框中，点击「保存配置」即可。"},
        ],
        "fields": [
            {"key": "api_key", "label": "API Key", "type": "password", "required": True, "sensitive": True, "description": "DeepSeek API 密钥"},
            {"key": "base_url", "label": "Base URL", "type": "text", "required": False, "sensitive": False, "default": "https://api.deepseek.com", "description": "API 基础地址"},
            {"key": "model", "label": "模型名称", "type": "text", "required": False, "sensitive": False, "default": "deepseek-chat", "description": "使用的模型 ID"},
            {"key": "timeout", "label": "超时（秒）", "type": "number", "required": False, "sensitive": False, "default": 300, "description": "API 请求超时时间"},
        ],
    },
    "volcano_ark": {
        "display_name": "火山引擎",
        "description": "字节跳动火山引擎，提供图片生成 (Seedream)、视频生成 (Seedance)、语音合成 (TTS) 等服务。",
        "icon": "fire",
        "tutorial": [
            {"step": 1, "title": "注册火山引擎账号", "content": "访问火山引擎官网，使用手机号注册并完成实名认证。", "link": "https://www.volcengine.com/", "link_text": "前往火山引擎官网"},
            {"step": 2, "title": "开通豆包大模型（ARK）", "content": "进入「豆包大模型」控制台，点击「立即体验」开通服务。开通后可获取 API Key。", "link": "https://console.volcengine.com/ark", "link_text": "进入 ARK 控制台"},
            {"step": 3, "title": "创建 API Key", "content": "在 ARK 控制台左侧菜单「API Key 管理」中，点击「创建新的 API Key」。复制生成的密钥。"},
            {"step": 4, "title": "开通 Seedream 图片生成", "content": "在 ARK 控制台「模型推理」中，找到 Seedream 模型并创建推理接入点（Endpoint）。记录模型 ID。", "link": "https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint", "link_text": "管理推理接入点"},
            {"step": 5, "title": "开通 Seedance 视频生成（可选）", "content": "同上步骤，找到 Seedance 模型创建接入点。如果视频生成与图片使用同一 API Key，则无需单独配置 Seedance API Key。"},
            {"step": 6, "title": "开通语音合成 TTS（可选）", "content": "进入「智能语音」控制台，创建应用获取 App ID 和 Token。", "link": "https://console.volcengine.com/speech/service/overview", "link_text": "进入语音服务控制台"},
            {"step": 7, "title": "填入上方配置", "content": "将获取到的 Key 和 ID 分别填入上方对应字段，点击「保存配置」。"},
        ],
        "fields": [
            {"key": "api_key", "label": "ARK API Key", "type": "password", "required": True, "sensitive": True, "description": "图片生成 API Key"},
            {"key": "seedream_model", "label": "Seedream 模型", "type": "text", "required": False, "sensitive": False, "default": "doubao-seedream-5-0-260128", "description": "图片生成模型 ID"},
            {"key": "seedance_api_key", "label": "Seedance API Key", "type": "password", "required": False, "sensitive": True, "description": "视频生成 API Key（可与 ARK Key 不同）"},
            {"key": "seedance_model", "label": "Seedance 模型", "type": "text", "required": False, "sensitive": False, "default": "doubao-seedance-2-0-260128", "description": "视频生成模型 ID"},
            {"key": "tts_app_id", "label": "TTS App ID", "type": "text", "required": False, "sensitive": False, "description": "语音合成应用 ID"},
            {"key": "tts_token", "label": "TTS Token", "type": "password", "required": False, "sensitive": True, "description": "语音合成访问令牌"},
            {"key": "timeout", "label": "超时（秒）", "type": "number", "required": False, "sensitive": False, "default": 600, "description": "API 请求超时时间"},
            {"key": "max_concurrent", "label": "最大并发数", "type": "number", "required": False, "sensitive": False, "default": 3, "description": "批量任务最大并发数"},
        ],
    },
    "kling": {
        "display_name": "Kling AI",
        "description": "快手 Kling AI 视频生成服务。",
        "icon": "video",
        "tutorial": [
            {"step": 1, "title": "注册快手开发者账号", "content": "访问 Kling AI 开放平台，注册并登录开发者账号。", "link": "https://platform.kuaishou.com/", "link_text": "前往 Kling 开放平台"},
            {"step": 2, "title": "创建应用", "content": "在控制台创建一个新应用，获取 Access Key 和 Secret Key。请妥善保管 Secret Key，创建后仅显示一次。"},
            {"step": 3, "title": "开通视频生成权限", "content": "在应用设置中开通「视频生成」API 权限。部分高级功能可能需要额外申请。"},
            {"step": 4, "title": "充值余额（如需）", "content": "在「费用中心」查看用量和余额。新用户通常有免费试用额度。", "link": "https://platform.kuaishou.com/developer/charge", "link_text": "查看费用中心"},
            {"step": 5, "title": "填入上方配置", "content": "将 Access Key 和 Secret Key 分别粘贴到上方对应字段，点击「保存配置」。"},
        ],
        "fields": [
            {"key": "access_key", "label": "Access Key", "type": "password", "required": True, "sensitive": True, "description": "Kling Access Key"},
            {"key": "secret_key", "label": "Secret Key", "type": "password", "required": True, "sensitive": True, "description": "Kling Secret Key"},
            {"key": "api_base", "label": "API 地址", "type": "text", "required": False, "sensitive": False, "default": "https://api.kling.kuaishou.com", "description": "API 基础地址"},
            {"key": "timeout", "label": "超时（秒）", "type": "number", "required": False, "sensitive": False, "default": 300, "description": "视频生成超时时间"},
            {"key": "poll_interval", "label": "轮询间隔（秒）", "type": "number", "required": False, "sensitive": False, "default": 5, "description": "状态轮询间隔"},
        ],
    },
    "comfyui": {
        "display_name": "ComfyUI",
        "description": "本地 ComfyUI 图片生成服务，用于角色参考图等本地生图任务。",
        "icon": "image",
        "tutorial": [
            {"step": 1, "title": "安装 ComfyUI", "content": "从 GitHub 下载并安装 ComfyUI。推荐使用官方安装包或便携版。需要 NVIDIA 显卡（至少 4GB 显存）。", "link": "https://github.com/comfyanonymous/ComfyUI", "link_text": "前往 ComfyUI GitHub"},
            {"step": 2, "title": "下载模型", "content": "下载 SDXL 基础模型（如 sd_xl_base_1.0.safetensors），放入 ComfyUI 的 models/checkpoints/ 目录。", "link": "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0", "link_text": "下载 SDXL 模型"},
            {"step": 3, "title": "启动 ComfyUI 服务", "content": "运行 ComfyUI，默认监听 8188 端口。确保服务启动后在浏览器能访问 http://localhost:8188 。"},
            {"step": 4, "title": "填入上方配置", "content": "确认 ComfyUI 服务地址和端口，如有不同请修改上方的「服务地址」字段。点击「保存配置」。"},
        ],
        "fields": [
            {"key": "base_url", "label": "服务地址", "type": "text", "required": True, "sensitive": False, "default": "http://localhost:8188", "description": "ComfyUI 服务地址"},
            {"key": "timeout", "label": "超时（秒）", "type": "number", "required": False, "sensitive": False, "default": 120, "description": "图片生成超时时间"},
            {"key": "poll_interval", "label": "轮询间隔（秒）", "type": "number", "required": False, "sensitive": False, "default": 2, "description": "状态轮询间隔"},
            {"key": "checkpoint", "label": "模型检查点", "type": "text", "required": False, "sensitive": False, "default": "sd_xl_base_1.0.safetensors", "description": "使用的模型检查点文件名"},
        ],
    },
}


def _mask_value(value: str) -> str:
    """对敏感值进行脱敏：仅显示末 4 位。"""
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return "****" + value[-4:]


def _is_sensitive(provider: str, key: str) -> bool:
    """判断某个配置项是否为敏感字段。"""
    schema = PROVIDER_SCHEMAS.get(provider)
    if not schema:
        return False
    for field in schema["fields"]:
        if field["key"] == key:
            return field.get("sensitive", False)
    return False


async def get_all_providers(db: AsyncSession) -> list[dict]:
    """返回所有服务商及其配置 schema。"""
    result = await db.execute(select(ServiceConfig).order_by(ServiceConfig.id))
    rows = result.scalars().all()

    providers = []
    for row in rows:
        schema = PROVIDER_SCHEMAS.get(row.provider)
        if not schema:
            continue

        masked_configs = _mask_configs(row.provider, row.configs)
        has_any_value = any(bool(v) for v in row.configs.values() if isinstance(v, str))

        providers.append({
            "provider": row.provider,
            "display_name": schema["display_name"],
            "description": schema.get("description", ""),
            "icon": schema.get("icon", ""),
            "configured": has_any_value,
            "configs": masked_configs,
            "fields": schema["fields"],
            "tutorial": schema.get("tutorial", []),
        })
    return providers


async def get_provider_config(db: AsyncSession, provider: str) -> dict | None:
    """返回指定服务商的当前配置（敏感值掩码）。"""
    result = await db.execute(
        select(ServiceConfig).where(ServiceConfig.provider == provider)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None

    schema = PROVIDER_SCHEMAS.get(provider)
    if not schema:
        return None

    return {
        "provider": row.provider,
        "display_name": schema["display_name"],
        "description": schema.get("description", ""),
        "fields": schema["fields"],
        "tutorial": schema.get("tutorial", []),
        "configs": _mask_configs(provider, row.configs),
    }


async def update_provider_config(
    db: AsyncSession, provider: str, updates: dict[str, Any],
) -> dict | None:
    """部分更新指定服务商的配置。只更新传入的字段。"""
    result = await db.execute(
        select(ServiceConfig).where(ServiceConfig.provider == provider)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None

    schema = PROVIDER_SCHEMAS.get(provider)
    if not schema:
        return None

    valid_keys = {f["key"] for f in schema["fields"]}
    merged = dict(row.configs)
    updated_keys: list[str] = []

    for key, value in updates.items():
        if key not in valid_keys:
            continue
        if value == "" and _is_sensitive(provider, key):
            merged[key] = ""
        else:
            # 敏感字段写入时加密
            if _is_sensitive(provider, key) and isinstance(value, str):
                from app.core.encryption import encrypt_value
                merged[key] = encrypt_value(value)
            else:
                merged[key] = value
        updated_keys.append(key)

    row.configs = merged  # type: ignore[assignment]
    await db.commit()
    await db.refresh(row)

    logger.info("服务商配置已更新: %s — 字段: %s", provider, ", ".join(updated_keys))

    return {
        "provider": row.provider,
        "display_name": schema["display_name"],
        "updated_keys": updated_keys,
        "configs": _mask_configs(provider, row.configs),
        "restart_required": True,
    }


def _mask_configs(provider: str, configs: dict) -> dict:
    """对配置中的敏感字段解密后脱敏。"""
    from app.core.encryption import decrypt_value
    masked = {}
    for key, value in configs.items():
        if _is_sensitive(provider, key) and isinstance(value, str):
            decrypted = decrypt_value(value)
            masked[key] = _mask_value(decrypted)
        else:
            masked[key] = value
    return masked
