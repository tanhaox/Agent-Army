#!/usr/bin/env python3
"""
查找所有配置文件并修复模型
"""
import paramiko
import sys
import json
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("=" * 60)
print("  查找并修复所有配置文件")
print("=" * 60)

# 1. 停止 Gateway
print("\n[1] 停止 Gateway...")
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)
print("✓ 已停止")

# 2. 查找所有包含 anthropic 的文件
print("\n[2] 查找包含 anthropic 的配置...")
stdin, stdout, stderr = ssh.exec_command('grep -r "anthropic" /root/.openclaw/ 2>/dev/null')
result = stdout.read().decode('utf-8', errors='ignore')

if result.strip():
    print("找到包含 anthropic 的文件:")
    print(result)

    # 尝试替换这些文件
    print("\n尝试修复...")
    stdin, stdout, stderr = ssh.exec_command('find /root/.openclaw/ -name "*.json" -type f')
    files = stdout.read().decode('utf-8', errors='ignore').strip().split('\n')

    for filepath in files:
        if filepath and 'agent.json' in filepath:
            print(f"\n检查: {filepath}")
            stdin, stdout, stderr = ssh.exec_command(f'cat {filepath}')
            content = stdout.read().decode('utf-8', errors='ignore')
            print(f"当前内容: {content[:200]}")

            # 更新为 zai/glm-4.7
            new_config = {"model": "zai/glm-4.7", "reasoning": True}
            new_json = json.dumps(new_config, indent=2)

            stdin, stdout, stderr = ssh.exec_command(f'cat > {filepath}', get_pty=True)
            stdin.write(new_json)
            stdin.channel.shutdown_write()

            print(f"✓ 已更新 {filepath}")
else:
    print("✓ 没有找到 anthropic 配置")

# 3. 强制更新 main agent 配置
print("\n[3] 强制更新 main agent.json...")
agent_config = {
    "model": "zai/glm-4.7",
    "reasoning": True
}
agent_json = json.dumps(agent_config, indent=2)

stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/agents/main/agent/agent.json', get_pty=True)
stdin.write(agent_json)
stdin.channel.shutdown_write()

# 验证
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/agents/main/agent/agent.json')
verified = stdout.read().decode('utf-8', errors='ignore')
print("配置文件内容:")
print(verified)

# 4. 检查是否有其他 agent 目录
print("\n[4] 检查是否有其他 agent...")
stdin, stdout, stderr = ssh.exec_command('ls -la /root/.openclaw/agents/')
agents_dir = stdout.read().decode('utf-8', errors='ignore')
print(agents_dir)

# 5. 启动 Gateway
print("\n[5] 启动 Gateway...")
stdin, stdout, stderr = ssh.exec_command('openclaw gateway >/dev/null 2>&1 &')
time.sleep(5)

# 6. 检查启动日志
print("\n[6] 检查启动日志...")
stdin, stdout, stderr = ssh.exec_command('tail -10 /tmp/openclaw/openclaw-*.log 2>/dev/null | grep -i model')
log_model = stdout.read().decode('utf-8', errors='ignore')
print("日志中的模型:")
print(log_model)

ssh.close()

print("\n" + "=" * 60)
print("  完成！请在浏览器中刷新并查看日志")
print("=" * 60)
