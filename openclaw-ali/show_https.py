import paramiko
import sys, json

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

# Check ports
stdin, stdout, stderr = ssh.exec_command('ss -tlnp | grep ":443"')
has_443 = ':443' in stdout.read().decode('utf-8', errors='ignore')

print("=" * 60)
print(" HTTPS Ready!")
print("=" * 60)
print("\nnginx port 443: " + ("OK - Listening" if has_443 else "NOT ready"))
print("\nMobile HTTPS URL:")
print("  https://112.126.61.223/#token=" + token)
print("\nToken:")
print("  " + token)
print("\nNext: Open port 443 in Aliyun security group")

ssh.close()
