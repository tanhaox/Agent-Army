#!/usr/bin/env python3
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

print("Fixing zai/glm-4.7 API key configuration...")

# Check current auth-profiles
print("\n[1] Current auth-profiles.json:")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/agents/main/agent/auth-profiles.json')
current = stdout.read().decode('utf-8', errors='ignore')
print(current)

# Create correct auth-profiles.json for zai
print("\n[2] Creating correct auth-profiles.json...")
auth_profiles = {
    "version": 1,
    "profiles": {
        "zai:default": {
            "type": "api_key",
            "provider": "zai",
            "key": "e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d"
        }
    },
    "lastGood": {
        "zai": "zai:default"
    }
}

auth_profiles_json = json.dumps(auth_profiles, indent=2)
stdin, stdout, stderr = ssh.exec_command('cat > /root/.openclaw/agents/main/agent/auth-profiles.json', get_pty=True)
stdin.write(auth_profiles_json.encode('utf-8'))
stdin.close()

print("✓ auth-profiles.json created")

# Verify
print("\n[3] Verifying...")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/agents/main/agent/auth-profiles.json')
verified = stdout.read().decode('utf-8', errors='ignore')
print(verified)

# Check model config
print("\n[4] Checking models.json...")
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/agents/main/agent/models.json')
models = stdout.read().decode('utf-8', errors='ignore')
print(models[:500] if len(models) > 500 else models)

# Test API
print("\n[5] Testing zai API...")
test_cmd = 'curl -s -X POST https://open.bigmodel.cn/api/coding/paas/v4/chat/completions -H "Content-Type: application/json" -d \'{"model":"glm-4.7-flash","messages":[{"role":"user","content":"test"}]}\' -H "Authorization: Bearer e1797666f1ab4ff3a44b177ec7042e8b.joophCPu5vL6oV0d" | python -m json.tool 2>/dev/null | head -20'
stdin, stdout, stderr = ssh.exec_command(test_cmd, get_pty=True)
api_result = stdout.read().decode('utf-8', errors='ignore')
print("API Test Result:")
print(api_result[:300] if len(api_result) > 300 else api_result)

print("\n" + "=" * 60)
print(" ✓ Fix Complete!")
print("=" * 60)
print("\nAgent should now work with zai/glm-4.7")
print("\nAccess URL:")
print("  https://112.126.61.223/#token=01d133a62e424e9ade0b59ac39db176fc8a2def6fd873f26")

ssh.close()
