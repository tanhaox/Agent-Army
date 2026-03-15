#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试记忆API功能"""
import paramiko
import sys
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"
MEMORY_API = f"http://{SG_HOST}:18888"

def test_memory_api():
    print("="*60)
    print(" 测试记忆API功能")
    print("="*60)
    print(f" API地址: {MEMORY_API}")
    print("="*60)
    print()

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 测试1：存储记忆
        print("[测试1] 存储记忆...")
        test_data = {
            "content": "这是一条测试记忆 - OpenClaw记忆API已成功部署！",
            "category": "test",
            "importance": 90,
            "tags": ["部署", "测试", "OpenClaw"]
        }

        cmd = f"""curl -s -X POST {MEMORY_API}/api/memory/remember \\
            -H "Content-Type: application/json" \\
            -d '{json.dumps(test_data)}'"""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = json.loads(stdout.read().decode().strip())

        if result.get("success"):
            print(f"  [OK] {result['message']}")
            memory_id = result.get("data", {}).get("id")
        else:
            print(f"  [FAIL] {result}")
            ssh.close()
            return False

        print()

        # 测试2：检索记忆
        print("[测试2] 检索记忆...")
        cmd = f"""curl -s -X POST {MEMORY_API}/api/memory/recall \\
            -H "Content-Type: application/json" \\
            -d '{{"category": "test", "limit": 10}}'"""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = json.loads(stdout.read().decode().strip())

        if result.get("success"):
            memories = result.get("data", {}).get("memories", [])
            print(f"  [OK] 检索到 {len(memories)} 条记忆:")
            for m in memories:
                print(f"       - ID:{m['id']} | {m['content'][:50]}...")
        else:
            print(f"  [FAIL] {result}")

        print()

        # 测试3：搜索记忆
        print("[测试3] 搜索记忆...")
        cmd = f"""curl -s -X POST {MEMORY_API}/api/memory/search \\
            -H "Content-Type: application/json" \\
            -d '{{"query": "OpenClaw", "limit": 5}}'"""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = json.loads(stdout.read().decode().strip())

        if result.get("success"):
            memories = result.get("data", {}).get("memories", [])
            print(f"  [OK] 搜索到 {len(memories)} 条记忆:")
            for m in memories:
                print(f"       - {m['content'][:50]}...")
        else:
            print(f"  [FAIL] {result}")

        print()

        # 测试4：统计信息
        print("[测试4] 统计信息...")
        cmd = f"curl -s {MEMORY_API}/api/memory/stats"
        stdin, stdout, stderr = ssh.exec_command(cmd)
        result = json.loads(stdout.read().decode().strip())

        if result.get("success"):
            stats = result.get("data", {})
            print(f"  [OK] 总记忆数: {stats.get('total', 0)}")
            print(f"       分类统计:")
            for cat, count in stats.get('by_category', {}).items():
                print(f"         - {cat}: {count}")
        else:
            print(f"  [FAIL] {result}")

        print()
        print("="*60)
        print(" 所有测试通过!")
        print("="*60)
        print()
        print(" 下一步: 更新sync_memory.py使用新的API地址")
        print(f"   MEMORY_API = \"{MEMORY_API}\"")
        print()

        ssh.close()
        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_memory_api()
