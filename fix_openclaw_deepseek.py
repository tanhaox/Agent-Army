#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复OpenClaw DeepSeek配置"""
import paramiko
import sys
import time
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
HOST = "157.245.195.58"
PORT = 2323

# 正确的配置格式（根据官方文档）
CORRECT_CONFIG = {
    "gateway": {
        "mode": "local"
    },
    "agents": {
        "defaults": {
            "model": {
                "primary": "deepseek/deepseek-reasoner"
            }
        }
    },
    "models": {
        "mode": "merge",
        "providers": {
            "deepseek": {
                "baseUrl": "https://api.deepseek.com",
                "apiKey": "sk-ade7bc9668ee4d148fc3362165c1960a",
                "api": "openai-completions",
                "models": [
                    {"id": "deepseek-chat", "name": "DeepSeek 快速模式"},
                    {"id": "deepseek-reasoner", "name": "DeepSeek 推理模式"}
                ]
            }
        }
    },
    "commands": {
        "restart": True
    }
}

def fix_deepseek_config():
    print("="*70)
    print(" 修复OpenClaw DeepSeek配置")
    print("="*70)
    print()

    try:
        # 1. 连接服务器
        print("[1] 连接服务器...")
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=HOST, port=PORT, username='root', pkey=key, timeout=15)
        print(f"   已连接: {HOST}:{PORT}")
        print()

        # 2. 停止OpenClaw
        print("[2] 停止OpenClaw...")
        stdin, stdout, stderr = ssh.exec_command("pkill -f 'openclaw'; pkill -f 'claw'")
        stdout.read()
        time.sleep(2)
        print("   已停止")
        print()

        # 3. 备份当前配置
        print("[3] 备份当前配置...")
        stdin, stdout, stderr = ssh.exec_command("cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d-%H%M%S)")
        stdout.read()
        print("   已备份")
        print()

        # 4. 写入正确配置
        print("[4] 写入正确配置...")
        config_json = json.dumps(CORRECT_CONFIG, ensure_ascii=False, indent=2)

        # 使用 heredoc 方式写入配置文件
        cmd = f'''cat > ~/.openclaw/openclaw.json << 'EOFCONFIG'
{config_json}
EOFCONFIG'''

        stdin, stdout, stderr = ssh.exec_command(cmd)
        error = stderr.read().decode().strip()
        if error:
            print(f"   警告: {error}")
        else:
            print("   配置已写入")
        print()

        # 5. 验证配置文件
        print("[5] 验证配置文件...")
        stdin, stdout, stderr = ssh.exec_command("cat ~/.openclaw/openclaw.json")
        config_content = stdout.read().decode().strip()
        try:
            parsed = json.loads(config_content)
            print(f"   模型: {parsed['agents']['defaults']['model']['primary']}")
            print(f"   Providers: {list(parsed['models']['providers'].keys())}")
            print("   配置格式正确")
        except json.JSONDecodeError as e:
            print(f"   ❌ 配置文件格式错误: {e}")
            return
        print()

        # 6. 启动OpenClaw
        print("[6] 启动OpenClaw...")
        stdin, stdout, stderr = ssh.exec_command(
            "cd ~/.openclaw && nohup openclaw gateway > /tmp/openclaw.log 2>&1 &"
        )
        stdout.read()
        time.sleep(5)
        print("   已启动")
        print()

        # 7. 检查进程状态
        print("[7] 检查进程状态...")
        stdin, stdout, stderr = ssh.exec_command("ps aux | grep openclaw | grep -v grep")
        processes = stdout.read().decode().strip()
        if processes:
            for line in processes.split('\n'):
                print(f"   {line}")
        else:
            print("   ❌ 未找到运行中的进程")
        print()

        # 8. 查看日志
        print("[8] 查看启动日志...")
        stdin, stdout, stderr = ssh.exec_command("tail -30 /tmp/openclaw.log 2>/dev/null || tail -30 ~/.openclaw/logs/gateway.log 2>/dev/null || echo '日志文件未找到'")
        log = stdout.read().decode().strip()
        print(log)
        print()

        ssh.close()

        print("="*70)
        print(" 修复完成")
        print("="*70)
        print()
        print("提示: 如果OpenClaw正常运行，可以通过以下方式测试:")
        print("  curl http://localhost:18789/v1/chat/completions \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{\"model\":\"deepseek/deepseek-chat\",\"messages\":[{\"role\":\"user\",\"content\":\"你好\"}]}'")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_deepseek_config()
