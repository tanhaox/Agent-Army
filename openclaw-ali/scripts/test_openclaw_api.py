#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""直接测试OpenClaw API"""
import requests
import json
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_openclaw_api():
    print("="*70)
    print(" 直接测试OpenClaw API")
    print("="*70)
    print()

    # OpenClaw Gateway地址
    base_url = "http://157.245.195.58:18789"

    # 1. 测试健康检查
    print("[1] 测试健康检查...")
    try:
        r = requests.get(f"{base_url}/health", timeout=5)
        print(f"  状态码: {r.status_code}")
        print(f"  响应: {r.text[:200]}")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
    print()

    # 2. 测试聊天API
    print("[2] 测试聊天API...")
    headers = {"Content-Type": "application/json"}
    data = {
        "message": "你好",
        "userId": "test-user"
    }

    try:
        r = requests.post(
            f"{base_url}/api/chat",
            headers=headers,
            json=data,
            timeout=30
        )
        print(f"  状态码: {r.status_code}")
        print(f"  响应头: {dict(r.headers)}")
        print(f"  响应体: {r.text[:500]}")

        if r.status_code == 200:
            result = r.json()
            print(f"\n  ✅ 成功")
            print(f"  回复: {json.dumps(result, ensure_ascii=False, indent=2)[:300]}")
        else:
            print(f"\n  ❌ 失败")
            print(f"  错误: {r.text}")

    except requests.exceptions.Timeout:
        print("  ❌ 请求超时")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
    print()

    # 3. 测试Agent端点
    print("[3] 测试Agent端点...")
    try:
        r = requests.get(f"{base_url}/api/agents", timeout=5)
        print(f"  状态码: {r.status_code}")
        if r.status_code == 200:
            agents = r.json()
            print(f"  Agents: {json.dumps(agents, ensure_ascii=False, indent=2)[:300]}")
        else:
            print(f"  响应: {r.text[:200]}")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
    print()

if __name__ == '__main__':
    test_openclaw_api()
