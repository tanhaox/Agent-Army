#!/usr/bin/env python3
"""
完全删除OpenClaw（备用脚本）
"""
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print('停止所有进程...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)

print('\n停止systemd服务...')
stdin, stdout, stderr = ssh.exec_command('systemctl stop openclaw-gateway.service 2>/dev/null || true')
stdout.read()
stdin, stdout, stderr = ssh.exec_command('systemctl disable openclaw-gateway.service 2>/dev/null || true')
stdout.read()
time.sleep(1)

print('\n卸载OpenClaw...')
stdin, stdout, stderr = ssh.exec_command('npm uninstall -g openclow 2>/dev/null || npm uninstall -g openclaw 2>/dev/null || true')
time.sleep(5)

print('\n删除配置文件...')
stdin, stdout, stderr = ssh.exec_command('rm -rf /root/.openclaw /root/.openclaw-* 2>/dev/null || true')
stdout.read()
time.sleep(1)

print('\n删除systemd服务文件...')
stdin, stdout, stderr = ssh.exec_command('rm -f /etc/systemd/system/openclaw-gateway.service')
stdout.read()
stdin, stdout, stderr = ssh.exec_command('systemctl daemon-reload')
stdout.read()
time.sleep(1)

print('\n删除日志和临时文件...')
stdin, stdout, stderr = ssh.exec_command('rm -f /tmp/*openclaw* 2>/dev/null || true')
stdout.read()
stdin, stdout, stderr = ssh.exec_command('rm -rf /var/tmp/openclaw-compile-cache 2>/dev/null || true')
stdout.read()

print('\n验证删除...')
stdin, stdout, stderr = ssh.exec_command('which openclaw 2>/dev/null || echo "openclaw命令已删除"')
result = stdout.read().decode('utf-8', errors='ignore')
print(result.strip())

stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw || echo "没有运行中的进程"')
result = stdout.read().decode('utf-8', errors='ignore')
print(result.strip())

stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789 || echo "端口18789已释放"')
result = stdout.read().decode('utf-8', errors='ignore')
print(result.strip())

print('\n' + '=' * 60)
print('  OpenClaw 已完全删除')
print('=' * 60)

ssh.close()
