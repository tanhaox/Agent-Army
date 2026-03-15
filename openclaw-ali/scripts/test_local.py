#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在本地测试智谱AI API Key"""
import requests
import json
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_api_key_local():
    print("="*70)
    print(" 本地测试智谱AI API Key")
    print("="*70)
    print()

    # 两个API Key
    keys = [
        ("Key 1 (AI聊天)", "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"),
        ("Key 2 (搜索专用)", "067666757b474d2d9cc9f5f59efb178d.Ezhq90VT2DtJXI4M")
    ]

    url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"

    for name, api_key in keys:
        print(f"[测试] {name}")
        print(f"  Key: {api_key[:20]}...{api_key[-10:]}")
        print()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "glm-4",
            "messages": [{"role": "user", "content": "你好，请回复测试成功"}],
            "stream": False
        }

        try:
            print("  发送请求...")
            response = requests.post(url, headers=headers, json=data, timeout=15)

            print(f"  状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                print(f"  ✅ 成功！")
                print(f"  回复: {content}")
            else:
                result = response.json()
                print(f"  ❌ 失败")
                print(f"  错误码: {result['error']['code']}")
                print(f"  错误信息: {result['error']['message']}")

        except requests.exceptions.Timeout:
            print("  ❌ 请求超时")
        except requests.exceptions.ConnectionError as e:
            print(f"  ❌ 连接错误: {e}")
        except Exception as e:
            print(f"  ❌ 其他错误: {e}")

        print()
        print("-"*70)
        print()

    # 额外测试：检查是否是IP限制
    print("[分析] IP限制检查")
    print()
    print("如果：")
    print("  - 本地成功，服务器失败 → 新加坡IP被限制")
    print("  - 本地和服务器都失败 → 账户余额问题")
    print("  - 本地和服务器都成功 → OpenClaw配置问题")
    print()

if __name__ == '__main__':
    test_api_key_local()
