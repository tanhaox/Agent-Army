#!/usr/bin/env python3
"""
批量批准所有待配对设备
使用场景：当有多个设备（电脑、手机）需要同时访问时
"""
import paramiko
import sys
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

def approve_all_devices():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

    print("=" * 60)
    print("  批量批准所有待配对设备")
    print("=" * 60)

    # 获取所有待批准的设备
    print("\n[1] 查看待批准设备...")
    stdin, stdout, stderr = ssh.exec_command('openclaw devices list', get_pty=True)
    output = stdout.read().decode('utf-8', errors='ignore')
    print(output)

    # 尝试使用 --all 参数（如果支持）
    print("\n[2] 批准所有待配对设备...")
    stdin, stdout, stderr = ssh.exec_command('openclaw devices approve --all 2>&1', get_pty=True)
    result = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')

    if '--all' not in result and 'error' in result.lower():
        print("⚠️  不支持 --all 参数，使用手动批准方式...")
        # 解析设备ID并逐个批准
        lines = output.split('\n')
        request_ids = []
        for line in lines:
            if 'pending' in line.lower() or line.strip():
                # 尝试提取UUID格式的ID
                import re
                match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', line, re.IGNORECASE)
                if match:
                    request_ids.append(match.group(1))

        if request_ids:
            print(f"找到 {len(request_ids)} 个待批准设备")
            for req_id in request_ids:
                print(f"\n批准: {req_id}")
                stdin, stdout, stderr = ssh.exec_command(f'openclaw devices approve {req_id}', get_pty=True)
                approve_result = stdout.read().decode('utf-8', errors='ignore')
                print(approve_result)
        else:
            print("✓ 没有找到待批准的设备")
    else:
        print(result)

    # 验证
    print("\n[3] 验证配对状态...")
    stdin, stdout, stderr = ssh.exec_command('openclaw devices list', get_pty=True)
    verify = stdout.read().decode('utf-8', errors='ignore')
    print(verify)

    # 获取当前 token
    stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
    config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
    token = config.get('gateway', {}).get('auth', {}).get('token', '')

    print("\n" + "=" * 60)
    print("  ✓ 批准完成！")
    print("=" * 60)
    print(f"\nToken: {token}")
    print(f"\n访问 URL:")
    print(f"  HTTPS: https://112.126.61.223/#token={token}")
    print(f"  HTTP:  http://112.126.61.223:18789/#token={token}")
    print(f"\n现在可以用电脑和手机同时访问了！")

    ssh.close()

if __name__ == '__main__':
    approve_all_devices()
