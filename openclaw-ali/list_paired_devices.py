#!/usr/bin/env python3
"""
查看已配对的设备列表
"""
import paramiko
import sys
import json
from datetime import datetime

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PASSWORD = 'Dandanyi2024!&Root'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname='112.126.61.223', port=22, username='root', password=PASSWORD, timeout=10)

print("=" * 60)
print("  已配对设备列表")
print("=" * 60)

# 检查 paired.json 文件
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/devices/paired.json 2>/dev/null')
paired_data = stdout.read().decode('utf-8', errors='ignore')

if paired_data.strip():
    try:
        paired = json.loads(paired_data)
        devices = paired.get('devices', {})

        if devices:
            print(f"\n✓ 已配对设备数量: {len(devices)}\n")
            print(f"{'设备ID':<36} {'配对时间':<20} {'设备名称'}")
            print("-" * 80)

            for device_id, device_info in devices.items():
                device_name = device_info.get('name', 'Unknown')
                paired_at = device_info.get('pairedAt', '')

                # 转换时间戳
                if paired_at:
                    try:
                        dt = datetime.fromtimestamp(paired_at)
                        time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        time_str = paired_at
                else:
                    time_str = 'Unknown'

                # 显示设备ID（前8位）
                short_id = device_id[:8] + '...' if len(device_id) > 8 else device_id
                print(f"{short_id:<36} {time_str:<20} {device_name}")
        else:
            print("\n⚠️  配对文件存在，但没有已配对的设备")
    except json.JSONDecodeError as e:
        print(f"\n❌ 配对文件格式错误: {e}")
        print(f"原始数据:\n{paired_data[:200]}")
else:
    print("\n⚠️  没有找到已配对的设备")
    print("提示：这是正常的，当设备首次访问并批准后，这里会显示设备列表")

# 获取当前 token
stdin, stdout, stderr = ssh.exec_command('cat /root/.openclaw/openclaw.json')
config = json.loads(stdout.read().decode('utf-8', errors='ignore'))
token = config.get('gateway', {}).get('auth', {}).get('token', '')

print("\n" + "=" * 60)
print(f"\n当前访问 URL:")
print(f"  HTTPS: https://112.126.61.223/#token={token}")
print(f"  HTTP:  http://112.126.61.223:18789/#token={token}")

ssh.close()
