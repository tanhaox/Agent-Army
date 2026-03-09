#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print('=== PM2重启记录（为什么重启了93次？）===')
stdin, stdout, stderr = ssh.exec_command('pm2 describe miaoying | grep -A 5 "restart time"')
print(stdout.read().decode('utf-8', errors='ignore'))

print('\n=== PM2内存使用情况 ===')
stdin, stdout, stderr = ssh.exec_command('pm2 jlist')
import json
try:
    jlist = json.loads(stdout.read().decode('utf-8', errors='ignore'))
    for proc in jlist:
        if proc['name'] == 'miaoying':
            print(f"进程内存: {proc['monit']['memory']} bytes ({proc['monit']['memory'] / 1024 / 1024:.1f} MB)")
            print(f"CPU使用: {proc['monit']['cpu']}%")
            print(f"重启次数: {proc['pm2_env'].get('restart_time', 0)}")
            print(f"异常退出: {proc['pm2_env'].get('unstable_restarts', 0)}")
except Exception as e:
    print(f"解析失败: {e}")

print('\n=== 最近的错误/崩溃日志 ===')
stdin, stdout, stderr = ssh.exec_command('tail -100 /var/www/miaoying/logs/pm2-error-0.log | grep -E "崩溃|crash|Error|FATAL|memory|OOM" | tail -20')
output = stdout.read().decode('utf-8', errors='ignore')
if output.strip():
    print(output)
else:
    print("（未找到崩溃关键字）")

print('\n=== SSE连接错误 ===')
stdin, stdout, stderr = ssh.exec_command('tail -100 /var/www/miaoying/logs/pm2-error-0.log | grep -i "stream\|sse\|controller\|closed" | tail -20')
output = stdout.read().decode('utf-8', errors='ignore')
if output.strip():
    print(output)
else:
    print("（未找到SSE错误）")

print('\n=== 临时文件占用情况 ===')
stdin, stdout, stderr = ssh.exec_command('du -sh /tmp/orders/temp-images 2>/dev/null && ls /tmp/orders/temp-images/ | wc -l')
output = stdout.read().decode('utf-8', errors='ignore')
print(f"临时文件大小和数量: {output}")

print('\n=== 数据库连接数 ===')
stdin, stdout, stderr = ssh.exec_command('ps aux | grep postgres | wc -l')
output = stdout.read().decode('utf-8', errors='ignore')
print(f"PostgreSQL进程数: {output.strip()}")

ssh.close()
