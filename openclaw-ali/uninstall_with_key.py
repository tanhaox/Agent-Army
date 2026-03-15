#!/usr/bin/env python3
"""
使用SSH密钥删除OpenClaw
"""
import paramiko
import sys
import time
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 使用SSH密钥
key_path = os.path.expanduser('~/.ssh/id_ed25519')
key = paramiko.Ed25519Key.from_private_key_file(key_path)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', pkey=key, timeout=10)

print('=' * 60)
print('  使用SSH密钥删除 OpenClaw')
print('=' * 60)

print('\n[1] 停止所有进程...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)
print('✓ 已停止')

print('\n[2] 停止systemd服务...')
stdin, stdout, stderr = ssh.exec_command('systemctl stop openclaw-gateway.service 2>/dev/null || true')
stdout.read()
stdin, stdout, stderr = ssh.exec_command('systemctl disable openclaw-gateway.service 2>/dev/null || true')
stdout.read()
time.sleep(1)
print('✓ 已停止')

print('\n[3] 卸载OpenClaw...')
stdin, stdout, stderr = ssh.exec_command('npm uninstall -g openclaw 2>/dev/null || true')
time.sleep(5)
result = stdout.read().decode('utf-8', errors='ignore')
print(result.strip() or '✓ 已卸载')

print('\n[4] 删除配置文件...')
stdin, stdout, stderr = ssh.exec_command('rm -rf /root/.openclaw /root/.openclaw-* 2>/dev/null || true')
stdout.read()
time.sleep(1)
print('✓ 已删除')

print('\n[5] 删除systemd服务文件...')
stdin, stdout, stderr = ssh.exec_command('rm -f /etc/systemd/system/openclaw-gateway.service')
stdout.read()
stdin, stdout, stderr = ssh.exec_command('systemctl daemon-reload')
stdout.read()
time.sleep(1)
print('✓ 已删除')

print('\n[6] 删除日志和临时文件...')
stdin, stdout, stderr = ssh.exec_command('rm -f /tmp/*openclaw* 2>/dev/null || true')
stdout.read()
stdin, stdout, stderr = ssh.exec_command('rm -rf /var/tmp/openclaw-compile-cache 2>/dev/null || true')
stdout.read()
print('✓ 已删除')

print('\n[7] 验证删除...')
stdin, stdout, stderr = ssh.exec_command('which openclaw 2>/dev/null || echo "✓ openclaw命令已删除"')
result = stdout.read().decode('utf-8', errors='ignore')
print(result.strip())

stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw || echo "✓ 没有运行中的进程"')
result = stdout.read().decode('utf-8', errors='ignore')
print(result.strip())

stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789 || echo "✓ 端口18789已释放"')
result = stdout.read().decode('utf-8', errors='ignore')
print(result.strip())

print('\n' + '=' * 60)
print('  OpenClaw 已完全删除')
print('=' * 60)

ssh.close()
