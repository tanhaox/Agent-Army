#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenClaw Server File Reader - Simplified
Reads configuration and source files from the OpenClaw server
"""

import paramiko
import sys

# Server connection details
HOST = '157.245.195.58'
PORT = 2323
USERNAME = 'root'
KEY_FILE = r'C:/Users/tanha/.ssh/digitalocean_openclaw'
KEY_PASSWORD = 'a19571004'

# Files to read
FILES_TO_READ = [
    '/root/.openclaw/workspace/agent_army/coordinator_agent.py',
    '/root/.openclaw/workspace/scripts/monitor.py',
    '/root/.openclaw/workspace/scripts/scanner.py',
    '/root/.openclaw/workspace/config/weights.json',
    '/root/.openclaw/workspace/config/scanner_config.json',
    '/root/.openclaw/workspace/config/market_sentiment_config.json',
    '/root/.openclaw/workspace/config/capital_flow_config.json'
]

def connect_ssh():
    """Connect to the OpenClaw server via SSH"""
    try:
        # Load the private key
        key = paramiko.Ed25519Key.from_private_key_file(
            KEY_FILE,
            password=KEY_PASSWORD
        )

        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect
        print(f"Connecting to {HOST}:{PORT}...")
        ssh.connect(
            hostname=HOST,
            port=PORT,
            username=USERNAME,
            pkey=key,
            timeout=15
        )

        print("OK Connected\n")
        return ssh

    except Exception as e:
        print(f"X Connection failed: {e}")
        sys.exit(1)

def read_file_via_sftp(ssh, file_path):
    """Read a file via SFTP"""
    try:
        sftp = ssh.open_sftp()
        with sftp.file(file_path, 'r') as f:
            content = f.read().decode('utf-8')
        sftp.close()
        return content
    except Exception as e:
        return f"Error reading file: {e}"

def main():
    print("="*80)
    print("OpenClaw Server File Reader")
    print("="*80)
    print(f"Server: {HOST}:{PORT}")
    print(f"Files to read: {len(FILES_TO_READ)}")
    print()

    # Connect to server
    ssh = connect_ssh()

    # Open output file
    with open('openclaw_files_output.txt', 'w', encoding='utf-8') as outfile:
        # Write header
        outfile.write("="*80 + "\n")
        outfile.write("OpenClaw Server Files\n")
        outfile.write("="*80 + "\n\n")

        # Read each file
        for file_path in FILES_TO_READ:
            print(f"Reading: {file_path}")

            # Write separator
            outfile.write("#"*80 + "\n")
            outfile.write(f"# FILE: {file_path}\n")
            outfile.write("#"*80 + "\n\n")

            # Read file content
            content = read_file_via_sftp(ssh, file_path)

            if content.startswith("Error"):
                outfile.write(f"ERROR: {content}\n\n")
            else:
                outfile.write(content)
                outfile.write("\n\n")

            print(f"  OK\n")

        # Write footer
        outfile.write("="*80 + "\n")
        outfile.write("END OF OUTPUT\n")
        outfile.write("="*80 + "\n")

    # Close connection
    ssh.close()

    print("="*80)
    print("OK All files saved to: openclaw_files_output.txt")
    print("="*80)

if __name__ == '__main__':
    main()
