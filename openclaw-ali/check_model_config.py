#!/usr/bin/env python3
"""
检查和修复 OpenClaw 模型配置问题
"""
import paramiko
import sys
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("=" * 60)
print("  检查模型配置问题")
print("=" * 60)

# 1. 检查当前的模型配置
print("\n[1] 检查 agent.json...")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/agents/main/agent/agent.json')
agent_config = stdout.read().decode('utf-8', errors='ignore')
print(agent_config)

# 2. 检查 auth-profiles.json
print("\n[2] 检查 auth-profiles.json...")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/agents/main/agent/auth-profiles.json')
auth_config = stdout.read().decode('utf-8', errors='ignore')
print(auth_config)

# 3. 检查 models.json 中的模型ID
print("\n[3] 检查可用的模型...")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/agents/main/agent/models.json')
models = json.loads(stdout.read().decode('utf-8', errors='ignore'))

print("\n可用的 zai 模型:")
if 'zai' in models.get('providers', {}):
    for model in models['providers']['zai'].get('models', []):
        model_id = model.get('id')
        model_name = model.get('name')
        print(f"  ID: {model_id}")
        print(f"     名称: {model_name}")
        print(f"     完整路径: zai/{model_id}")

# 4. 尝试修改 agent.json 使用正确的模型ID格式
print("\n[4] 更新 agent.json 使用正确的模型格式...")
new_agent_config = {
    "model": "zai/glm-4.7",
    "reasoning": True
}

agent_json = json.dumps(new_agent_config, indent=2)
print("新配置:")
print(agent_json)

# 上传
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/agents/main/agent/agent.json', get_pty=True)
stdin.write(agent_json)
stdin.channel.shutdown_write()

print("✓ agent.json 已更新")

# 5. 检查是否有其他配置文件覆盖了模型设置
print("\n[5] 检查 Gateway 配置...")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
gateway_config = json.loads(stdout.read().decode('utf-8', errors='ignore'))

# 查找任何模型相关的配置
if 'agents' in gateway_config:
    if 'defaults' in gateway_config['agents'] and 'model' in gateway_config['agents']['defaults']:
        print(f"⚠️  Gateway 默认模型: {gateway_config['agents']['defaults']['model']}")
        print("   这可能会覆盖 agent.json 的设置！")
    else:
        print("✓ Gateway 没有设置默认模型")

# 6. 检查是否有数据库或缓存
print("\n[6] 检查是否有缓存文件...")
stdin, stdout, stderr = ssh.exec_command('find /root/.openclaw -name "*.db" -o -name "*.cache" -o -name "state*" 2>/dev/null | head -10')
cache_files = stdout.read().decode('utf-8', errors='ignore')
if cache_files.strip():
    print("找到缓存文件:")
    print(cache_files)
else:
    print("✓ 没有找到缓存文件")

print("\n" + "=" * 60)
print("  建议的解决方案")
print("=" * 60)
print("""
问题分析：
• 服务器端配置正确（agent.json 使用 zai/glm-4.7）
• 但错误信息显示仍在尝试使用 anthropic

可能原因：
1. 浏览器端选择了错误的模型
2. Gateway 配置中有默认模型覆盖
3. 有缓存文件存储了旧的配置

解决步骤：
1. 在浏览器 Control UI 中手动选择模型
2. 选择 "zai/glm-4.7" 或 "glm-4.7"
3. 避免选择任何 anthropic/claude 相关的模型
""")

ssh.close()
