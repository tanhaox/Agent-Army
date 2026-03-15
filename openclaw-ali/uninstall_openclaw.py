#!/usr/bin/env python3
"""
完全删除OpenClaw
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

print('=' * 60)
print('  完全删除 OpenClaw')
print('=' * 60)

# 1. 停止所有进程
print('\n[1] 停止所有OpenClaw进程...')
stdin, stdout, stderr = ssh.exec_command('pkill -9 -f openclaw')
stdout.read()
time.sleep(2)
print('✓ 已停止')

# 2. 停止systemd服务
print('\n[2] 停止并禁用systemd服务...')
stdin, stdout, stderr = ssh.exec_command('systemctl stop openclaw-gateway.service 2>/dev/null || true')
stdout.read()
stdin, stdout, stderr = ssh.exec_command('systemctl disable openclaw-gateway.service 2>/dev/null || true')
stdout.read()
time.sleep(1)
print('✓ 已停止并禁用')

# 3. 卸载OpenClaw
print('\n[3] 卸载OpenClaw...')
stdin, stdout, stderr = ssh.exec_command('npm uninstall -g openclaw 2>/dev/null || true')
time.sleep(5)
result = stdout.read().decode('utf-8', errors='ignore')
print(result.strip() or '✓ 已卸载')

# 4. 删除配置文件
print('\n[4] 删除配置文件...')
stdin, stdout, stderr = ssh.exec_command('rm -rf /root/.openclaw')
stdout.read()
time.sleep(1)
stdin, stdout, stderr = ssh.exec_command('rm -rf /root/.openclaw-* 2>/dev/null || true')
stdout.read()
time.sleep(1)
print('✓ 已删除')

# 5. 删除systemd服务文件
print('\n[5] 删除systemd服务文件...')
stdin, stdout, stderr = ssh.exec_command('rm -f /etc/systemd/system/openclaw-gateway.service')
stdout.read()
stdin, stdout, stderr = ssh.exec_command('systemctl daemon-reload')
stdout.read()
time.sleep(1)
print('✓ 已删除')

# 6. 删除日志文件
print('\n[6] 删除日志文件...')
stdin, stdout, stderr = ssh.exec_command('rm -f /tmp/*openclaw* 2>/dev/null || true')
stdout.read()
print('✓ 已删除')

# 7. 删除临时文件
print('\n[7] 删除临时文件和缓存...')
stdin, stdout, stderr = ssh.exec_command('rm -rf /var/tmp/openclaw-compile-cache 2>/dev/null || true')
stdout.read()
print('✓ 已删除')

# 8. 验证删除
print('\n[8] 验证删除...')
stdin, stdout, stderr = ssh.exec_command('which openclaw')
result = stdout.read().decode('utf-8', errors='ignore').strip()
if not result or 'not found' in result:
    print('✓ openclaw 命令已删除')
else:
    print(f'⚠️  仍有残留: {result}')

stdin, stdout, stderr = ssh.exec_command('ps aux | grep [o]penclaw')
result = stdout.read().decode('utf-8', errors='ignore').strip()
if not result:
    print('✓ 没有运行中的进程')
else:
    print(f'⚠️  仍有进程: {result}')

stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore').strip()
if not result:
    print('✓ 端口18789已释放')
else:
    print(f'⚠️  端口仍在监听: {result}')

# 9. 删除nginx配置（可选）
print('\n[9] 删除nginx配置（可选）...')
stdin, stdout, stderr = ssh.exec_command('ls /etc/nginx/sites-enabled/ | grep -i openclaw')
nginx_config = stdout.read().decode('utf-8', errors='ignore').strip()
if nginx_config:
    print(f'发现nginx配置: {nginx_config}')
    print('如需删除，请手动执行:')
    print(f'  rm -f /etc/nginx/sites-enabled/{nginx_config}')
    print(f'  rm -f /etc/nginx/sites-available/{nginx_config}')
    print('  nginx -t && systemctl reload nginx')
else:
    print('✓ 没有发现nginx配置')

print('\n' + '=' * 60)
print('  OpenClaw 已完全删除')
print('=' * 60)

ssh.close()
