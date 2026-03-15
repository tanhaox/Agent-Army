#!/usr/bin/env python3
import paramiko
import sys
import time

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print('连接服务器...')
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=15)
print('✓ 连接成功\n')

print('停止所有进程...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)

print('停止systemd服务...')
stdin, stdout, stderr = ssh.exec_command('systemctl stop openclaw-gateway.service 2>/dev/null || true')
stdout.read()
stdin, stdout, stderr = ssh.exec_command('systemctl disable openclaw-gateway.service 2>/dev/null || true')
stdout.read()
time.sleep(1)

print('卸载OpenClaw...')
stdin, stdout, stderr = ssh.exec_command('npm uninstall -g openclaw 2>&1')
time.sleep(5)
result = stdout.read().decode('utf-8', errors='ignore')
print(result)

print('删除配置文件...')
stdin, stdout, stderr = ssh.exec_command('rm -rf /root/.openclaw /root/.openclaw-*')
stdout.read()
time.sleep(1)

print('删除systemd服务...')
stdin, stdout, stderr = ssh.exec_command('rm -f /etc/systemd/system/openclaw-gateway.service')
stdout.read()
stdin, stdout, stderr = ssh.exec_command('systemctl daemon-reload')
stdout.read()

print('清理日志...')
stdin, stdout, stderr = ssh.exec_command('rm -f /tmp/*openclaw* /var/tmp/openclaw-compile-cache 2>/dev/null || true')
stdout.read()

print('\n验证删除...')
stdin, stdout, stderr = ssh.exec_command('which openclaw 2>/dev/null || echo "✓ openclaw已删除"')
print(stdout.read().decode('utf-8', errors='ignore').strip())

stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw || echo "✓ 无运行进程"')
print(stdout.read().decode('utf-8', errors='ignore').strip())

stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789 || echo "✓ 端口已释放"')
print(stdout.read().decode('utf-8', errors='ignore').strip())

print('\n' + '=' * 50)
print('OpenClaw 已完全删除')
print('=' * 50)

ssh.close()
