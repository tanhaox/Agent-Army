#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenClaw Server File Reader
Reads files from the Malaysia server and saves them locally
"""

import paramiko
import os

# Server connection info
HOST = '157.245.195.58'
PORT = 2323
USERNAME = 'root'
KEY_FILE = r'C:/Users/tanha/.ssh/digitalocean_openclaw'
KEY_PASSWORD = 'a19571004'

# Files to read
FILES_TO_READ = [
    {
        'remote': '/root/.openclaw/workspace/agent_army/coordinator_agent.py',
        'local': r'C:\AI-Agent-Local\coordinator_agent.py'
    },
    {
        'remote': '/root/.openclaw/workspace/config/weights.json',
        'local': r'C:\AI-Agent-Local\weights.json'
    }
]

def read_remote_file(ssh, remote_path):
    """Read a remote file and return its content"""
    stdin, stdout, stderr = ssh.exec_command(f'cat {remote_path}')
    content = stdout.read().decode('utf-8')
    error = stderr.read().decode('utf-8')

    if error and not content:
        raise Exception(f"Error reading {remote_path}: {error}")

    return content

def save_local_file(content, local_path):
    """Save content to a local file"""
    with open(local_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[+] Saved: {local_path}")

def main():
    print("=" * 60)
    print("  OpenClaw Server File Reader")
    print("=" * 60)

    # Load SSH key
    print(f"\n[*] Loading SSH key...")
    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        print("[+] SSH key loaded successfully")
    except Exception as e:
        print(f"[-] Failed to load SSH key: {e}")
        return

    # Connect to server
    print(f"\n[*] Connecting to {HOST}:{PORT}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(hostname=HOST, port=PORT, username=USERNAME, pkey=key, timeout=15)
        print("[+] Connected successfully")
    except Exception as e:
        print(f"[-] Connection failed: {e}")
        return

    # Read each file
    print("\n[*] Reading files...")
    for file_info in FILES_TO_READ:
        remote_path = file_info['remote']
        local_path = file_info['local']

        print(f"\n[*] Reading: {remote_path}")
        try:
            content = read_remote_file(ssh, remote_path)
            save_local_file(content, local_path)
            print(f"    Size: {len(content)} bytes")
        except Exception as e:
            print(f"[-] Failed to read {remote_path}: {e}")
            continue

    # Close connection
    ssh.close()
    print("\n[+] Done!")

if __name__ == '__main__':
    main()
