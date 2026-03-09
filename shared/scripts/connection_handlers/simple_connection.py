#!/usr/bin/env python3
"""
连接管理工具
基于 mcp-builder 的连接处理简化版
"""

import asyncio
from typing import Any, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SimpleAPIConnection:
    """简化的 API 连接"""

    def __init__(
        self,
        base_url: str,
        api_key: str = None,
        headers: Dict[str, str] = None,
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = headers or {}
        self.timeout = timeout

        # 添加认证头
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

        self.session = None

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()

    def connect(self):
        """建立连接"""
        try:
            import requests
        except ImportError:
            raise ImportError("需要 requests 库: pip install requests")

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        logger.info(f"已连接到: {self.base_url}")

    def disconnect(self):
        """断开连接"""
        if self.session:
            self.session.close()
            logger.info("连接已关闭")

    def request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None,
        json_data: Dict = None
    ) -> Any:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法
            endpoint: API 端点
            params: 查询参数
            data: 表单数据
            json_data: JSON 数据

        Returns:
            响应数据
        """
        if not self.session:
            raise RuntimeError("连接未建立")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.request(
                method,
                url,
                params=params,
                data=data,
                json=json_data,
                timeout=self.timeout
            )
            response.raise_for_status()

            # 尝试解析 JSON
            try:
                return response.json()
            except ValueError:
                return response.text

        except Exception as e:
            logger.error(f"请求失败: {e}")
            raise

    def get(self, endpoint: str, params: Dict = None) -> Any:
        """GET 请求"""
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, data: Dict = None) -> Any:
        """POST 请求"""
        return self.request("POST", endpoint, json_data=data)

    def put(self, endpoint: str, data: Dict = None) -> Any:
        """PUT 请求"""
        return self.request("PUT", endpoint, json_data=data)

    def delete(self, endpoint: str) -> Any:
        """DELETE 请求"""
        return self.request("DELETE", endpoint)


# ==================== 工厂函数 ====================

def create_api_client(
    base_url: str,
    api_key: str = None,
    **kwargs
) -> SimpleAPIConnection:
    """
    创建 API 客户端

    Args:
        base_url: API 基础 URL
        api_key: API 密钥
        **kwargs: 其他参数

    Returns:
        API 连接实例
    """
    return SimpleAPIConnection(base_url, api_key, **kwargs)


# ==================== 示例使用 ====================

if __name__ == "__main__":
    # 示例：使用 API 客户端
    with create_api_client(
        base_url="https://api.example.com",
        api_key="your-api-key"
    ) as client:
        # GET 请求
        users = client.get("/users")
        print(f"用户数: {len(users)}")

        # POST 请求
        new_user = client.post("/users", data={
            "name": "Alice",
            "email": "alice@example.com"
        })
        print(f"创建用户: {new_user}")
