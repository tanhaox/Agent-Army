#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上传OpenClaw到服务器"""
import paramiko
import sys
import os
import tarfile
import io

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'
LOCAL_SRC = "C:/AI-Agent-Local/openclaw-cn-src"
REMOTE_DIR = "/root/openclaw-cn"

def execute_cmd(ssh, cmd, description=""):
    """执行SSH命令并显示输出"""
    if description:
        print(f"\n[执行] {description}")
    print(f"命令: {cmd}")
    print("-" * 40)

    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')

    if output.strip():
        print(output)
    if error.strip() and 'warning' not in error.lower():
        print(f"错误: {error}")

    return output

print("=" * 60)
print(" 上传 OpenClaw-CN 到服务器")
print("=" * 60)

# 连接服务器
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

# SFTP上传
print("\n[步骤 1/4] 创建远程目录")
print("-" * 40)
sftp = ssh.open_sftp()
try:
    s.mkdir(REMOTE_DIR)
except:
    pass

# 步骤2: 压缩并上传
print("\n[步骤 2/4] 压缩并上传文件")
print("-" * 40)

# 创建内存中的tar.gz压缩包
print("正在压缩...")
import tempfile
with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp:
    tmp_path = tmp.name

# 压缩
with tarfile.open(tmp_path, "w:gz") as tar:
    for item in os.listdir(LOCAL_SRC):
        item_path = os.path.join(LOCAL_SRC, item)
        if os.path.isfile(item_path):
            tar.add(item_path, arcname=item)
        elif os.path.isdir(item_path):
            tar.add(item_path, arcname=item, recursive=True)

print(f"压缩完成: {tmp_path}")

# 上传
print("开始上传...")
sftp.put(tmp_path, f"/tmp/openclaw-cn.tar.gz")
print("上传完成!")

# 清理临时文件
os.unlink(tmp_path)

# 步骤3: 解压
print("\n[步骤 3/4] 解压文件")
print("-" * 40)
execute_cmd(ssh, f"cd /root && rm -rf {REMOTE_DIR} && mkdir -p {REMOTE_DIR}", "清理旧目录")
execute_cmd(ssh, "tar -xzf /tmp/openclaw-cn.tar.gz -C /root/openclaw-cn --strip-components=1", "解压到目标目录")
execute_cmd(ssh, "rm -f /tmp/openclaw-cn.tar.gz", "清理压缩包")

# 步骤4: 验证和安装
print("\n[步骤 4/4] 验证和安装")
print("-" * 40)
execute_cmd(ssh, f"ls -la {REMOTE_DIR}/ | head -20", "列出文件")
execute_cmd(ssh, f"test -f {REMOTE_DIR}/package.json && echo '✅ package.json 存在'", "验证package.json")

# 安装依赖
execute_cmd(ssh, f"cd {REMOTE_DIR} && pnpm install", "安装依赖 (可能需要几分钟)")

# 检查setup脚本
execute_cmd(ssh, f"cat {REMOTE_DIR}/package.json | grep -A 2 '\"setup\"'", "显示setup命令")

print("\n" + "=" * 60)
print(" 上传和安装完成！")
print("=" * 60)
print(f"\n项目位置: {REMOTE_DIR}")
print(f"\n下一步: cd {REMOTE_DIR} && pnpm run setup")

sftp.close()
ssh.close()
