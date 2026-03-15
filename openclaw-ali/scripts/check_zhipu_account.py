#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细检查智谱AI账户状态"""
import requests
import json
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_zhipu_account():
    print("="*70)
    print(" 详细检查智谱AI账户状态")
    print("="*70)
    print()

    api_key = "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"

    # 1. 尝试不同的API端点
    endpoints = [
        ("Chat Completions", "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"),
        ("Embeddings", "https://open.bigmodel.cn/api/coding/paas/v4/embeddings"),
        ("Models List", "https://open.bigmodel.cn/api/coding/paas/v4/models"),
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for name, url in endpoints:
        print(f"[测试] {name}")
        print(f"  URL: {url}")

        try:
            if "chat" in url:
                data = {
                    "model": "glm-4",
                    "messages": [{"role": "user", "content": "测试"}]
                }
                r = requests.post(url, headers=headers, json=data, timeout=10)
            elif "embeddings" in url:
                data = {
                    "model": "embedding-2",
                    "input": "测试文本"
                }
                r = requests.post(url, headers=headers, json=data, timeout=10)
            else:
                r = requests.get(url, headers=headers, timeout=10)

            print(f"  状态码: {r.status_code}")

            if r.status_code == 200:
                print(f"  ✅ 成功！")
                result = r.json()
                print(f"  响应: {json.dumps(result, ensure_ascii=False, indent=2)[:300]}...")
            else:
                result = r.json()
                print(f"  ❌ 失败")
                print(f"  错误: {json.dumps(result, ensure_ascii=False, indent=2)}")

        except Exception as e:
            print(f"  ❌ 异常: {e}")

        print()

    # 2. 测试不同的模型
    print("[测试] 不同模型")
    models = ["glm-4", "glm-4-flash", "glm-3-turbo"]

    for model in models:
        print(f"\n  模型: {model}")
        url = "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions"
        data = {
            "model": model,
            "messages": [{"role": "user", "content": "你好"}]
        }

        try:
            r = requests.post(url, headers=headers, json=data, timeout=10)
            print(f"  状态: {r.status_code}")

            if r.status_code == 200:
                result = r.json()
                print(f"  ✅ 成功！{result['choices'][0]['message']['content'][:50]}")
                break  # 如果有一个成功，就停止测试
            else:
                result = r.json()
                print(f"  ❌ {result['error']['message'][:50]}")

        except Exception as e:
            print(f"  ❌ {e}")

    print()
    print("="*70)
    print(" 建议")
    print("="*70)
    print()
    print("如果所有测试都返回'余额不足'，请检查：")
    print("1. 登录 https://open.bigmodel.cn/user-center/finance/balance")
    print("2. 查看账户余额（可能是负数或0）")
    print("3. 检查包月套餐是否过期")
    print("4. 检查API调用统计（是否超出限制）")
    print()
    print("智谱AI客服：")
    print("- 官方群：搜索'智谱AI'加入官方用户群")
    print("- 邮箱：api@zhipuai.cn")
    print()

if __name__ == '__main__':
    check_zhipu_account()
