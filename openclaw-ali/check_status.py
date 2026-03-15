#!/usr/bin/env python3
import paramiko
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("Checking gateway status...")
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
result = stdout.read().decode('utf-8', errors='ignore')

if '18789' in result:
    print("OK - Gateway running")
    print("\nAccess now:")
    print("  https://112.126.61.223/#token=588d77fb3dfbb08c0fa4326f3740a0e585f17eae1e1b4329")
else:
    print("NOT running - starting...")
    stdin, stdout, stderr = ssh.exec_command('nohup openclaw gateway --bind lan > /tmp/gateway.log 2>&1 &')
    stdout.read()

    import time
    time.sleep(5)

    stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep 18789')
    result = stdout.read().decode('utf-8', errors='ignore')

    if '18789' in result:
        print("Started - Access now:")
        print("  https://112.126.61.223/#token=588d77fb3dfbb08c0fa4326f3740a0e585f17eae1e1b4329")

ssh.close()
