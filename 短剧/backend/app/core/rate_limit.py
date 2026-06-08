"""
请求限流配置。

使用 slowapi 实现 IP 级别的请求限流，防止 API 滥用。
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
