#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deploy eastmoney-sector-crawler skill to server"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import paramiko
from pathlib import Path
import os

SERVER = "157.245.195.58"
KEY_PATH = Path.home() / '.ssh' / 'digitalocean_openclaw'

# Server paths
REMOTE_SKILLS_DIR = "/root/openclaw-ali/skills"
SKILL_NAME = "eastmoney-sector-crawler"
LOCAL_SKILL_DIR = Path(__file__).parent.parent / "skills" / SKILL_NAME

print("=" * 70)
print("  Deploy eastmoney-sector-crawler Skill")
print("=" * 70)
print()

# Check local files
print("[Step 1] Checking local files...")
required_files = [
    "_meta.json",
    ".clawhub/origin.json",
    "SKILL.md",
    "main.py",
    "tool.py"
]

missing_files = []
for file in required_files:
    file_path = LOCAL_SKILL_DIR / file
    if not file_path.exists():
        missing_files.append(file)

if missing_files:
    print(f"  ✗ Missing files: {missing_files}")
    sys.exit(1)

print(f"  ✓ All required files present")
print(f"  Local path: {LOCAL_SKILL_DIR}")
print()

# Connect to server
print("[Step 2] Connecting to server...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

key = None
for key_class in [paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey]:
    try:
        key = key_class.from_private_key_file(str(KEY_PATH))
        break
    except:
        continue

try:
    ssh.connect(hostname=SERVER, port=22, username='root', pkey=key, timeout=15)
    print(f"  ✓ Connected to {SERVER}")
except Exception as e:
    print(f"  ✗ Connection failed: {e}")
    sys.exit(1)

print()

# Create remote directory
print("[Step 3] Creating remote directory...")
sftp = ssh.open_sftp()
try:
    remote_skill_dir = f"{REMOTE_SKILLS_DIR}/{SKILL_NAME}"

    # Create skill directory
    try:
        sftp.mkdir(remote_skill_dir)
        print(f"  ✓ Created: {remote_skill_dir}")
    except IOError:
        print(f"  ✓ Directory exists: {remote_skill_dir}")

    # Create .clawhub subdirectory
    try:
        sftp.mkdir(f"{remote_skill_dir}/.clawhub")
        print(f"  ✓ Created: {remote_skill_dir}/.clawhub")
    except IOError:
        pass  # Already exists

    print()

    # Upload files
    print("[Step 4] Uploading skill files...")
    files_to_upload = [
        ("_meta.json", "_meta.json"),
        (".clawhub/origin.json", ".clawhub/origin.json"),
        ("SKILL.md", "SKILL.md"),
        ("main.py", "main.py"),
        ("tool.py", "tool.py"),
    ]

    for local_file, remote_file in files_to_upload:
        local_path = LOCAL_SKILL_DIR / local_file
        remote_path = f"{remote_skill_dir}/{remote_file}"

        try:
            sftp.put(str(local_path), remote_path)
            print(f"  ✓ Uploaded: {local_file}")
        except Exception as e:
            print(f"  ✗ Failed to upload {local_file}: {e}")

    print()

    # Verify files
    print("[Step 5] Verifying upload...")
    stdin, stdout, stderr = ssh.exec_command(f"ls -la {remote_skill_dir}")
    result = stdout.read().decode('utf-8', errors='ignore')
    print(result)

    # Check if OpenClaw recognizes the skill
    print()
    print("[Step 6] Checking skill recognition...")
    stdin, stdout, stderr = ssh.exec_command(f"cd {REMOTE_SKILLS_DIR} && find . -name '{SKILL_NAME}' -o -name '{SKILL_NAME}.py'")
    result = stdout.read().decode('utf-8', errors='ignore')
    print(result)

finally:
    sftp.close()
    ssh.close()

print()
print("=" * 70)
print("  ✓ Deployment Complete!")
print("=" * 70)
print()
print("Skill location on server:")
print(f"  {remote_skill_dir}")
print()
print("Next steps:")
print("  1. Test the skill: python3 -c \"from main import init_db; print(init_db())\"")
print("  2. Check OpenClaw UI for the new skill")
print("  3. Test data sync with WebReader")
