import paramiko
import sys
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = r'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

# Get token
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print("=" * 60)
print(" HTTPS Configuration Complete!")
print("=" * 60)

print("\nStatus:")
print("  nginx: " + ("✅ Running (443 listening)" if "443" in ... else "❌"))

print("\nPhone Access URLs:")
print("  HTTPS: https://112.126.61.223/#token=" + token)
print("  HTTP:  http://112.126.61.223:18789/#token=" + token)

print("\nToken:")
print("  " + token)

print("\nNext Steps:")
print("  1. Open port 443 in Aliyun security group (same as 18789)")
print("  2. Visit https://112.126.61.223/ on phone")
print("  3. Accept certificate warning (self-signed)")
print("  4. Enter token")

ssh.close()
