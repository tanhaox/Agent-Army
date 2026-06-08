"""
敏感字段加密工具 — 使用 Fernet 对称加密保护 API Key 等敏感配置。

密钥从环境变量 ENCRYPTION_KEY 读取。留空时不加密（向后兼容）。
"""

import base64
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# 敏感字段关键词（字段名包含这些词则视为敏感）
SENSITIVE_KEYWORDS = ("key", "secret", "token", "password", "credential")


def _get_fernet() -> Fernet | None:
    """获取 Fernet 实例，未配置 ENCRYPTION_KEY 时返回 None。"""
    from app.core.config import get_settings
    key = get_settings().ENCRYPTION_KEY
    if not key:
        return None
    return Fernet(key.encode() if isinstance(key, str) else key)


def is_sensitive_field(field_name: str) -> bool:
    """判断字段名是否属于敏感字段。"""
    lower = field_name.lower()
    return any(kw in lower for kw in SENSITIVE_KEYWORDS)


def encrypt_value(plaintext: str) -> str:
    """加密明文，返回 'enc:' 前缀的密文。未配置密钥时原样返回。"""
    f = _get_fernet()
    if f is None or not plaintext:
        return plaintext
    encrypted = f.encrypt(plaintext.encode())
    return f"enc:{encrypted.decode()}"


def decrypt_value(ciphertext: str) -> str:
    """解密密文。若非 'enc:' 前缀则原样返回（兼容明文数据）。"""
    if not ciphertext or not ciphertext.startswith("enc:"):
        return ciphertext
    f = _get_fernet()
    if f is None:
        logger.warning("ENCRYPTION_KEY 未配置，无法解密已加密的值")
        return ciphertext
    try:
        return f.decrypt(ciphertext[4:].encode()).decode()
    except InvalidToken:
        logger.error("解密失败：密钥不匹配或数据损坏")
        return ciphertext


def generate_key() -> str:
    """生成新的 Fernet 密钥（用于首次初始化）。"""
    return Fernet.generate_key().decode()
