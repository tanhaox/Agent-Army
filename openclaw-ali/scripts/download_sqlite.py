#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下载OpenClaw记忆SQLite数据库到本地分析"""
import paramiko
import sys
import sqlite3
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_FILE = r"C:\Users\tanha\.ssh\digitalocean_openclaw"
KEY_PASSWORD = "a19571004"
SG_HOST = "157.245.195.58"
LOCAL_DIR = r"C:\AI-Agent-Local\openclaw-ali\memory_analysis"

def download_and_analyze():
    print("="*70)
    print(" 下载并分析OpenClaw记忆SQLite数据库")
    print("="*70)
    print()

    # 创建本地目录
    os.makedirs(LOCAL_DIR, exist_ok=True)

    try:
        key = paramiko.Ed25519Key.from_private_key_file(KEY_FILE, password=KEY_PASSWORD)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=SG_HOST, port=22, username='root', pkey=key, timeout=15)

        # 下载main.sqlite
        print("[1] 下载main.sqlite...")
        local_main = os.path.join(LOCAL_DIR, "main.sqlite")
        sftp = ssh.open_sftp()

        try:
            sftp.get("/root/.openclaw/memory/main.sqlite", local_main)
            print(f"  [OK] 已下载到: {local_main}")
            print(f"  文件大小: {os.path.getsize(local_main)} 字节")
        except Exception as e:
            print(f"  [ERROR] 下载失败: {e}")

        # 下载wangcai.sqlite
        print("\n[2] 下载wangcai.sqlite...")
        local_wangcai = os.path.join(LOCAL_DIR, "wangcai.sqlite")
        try:
            sftp.get("/root/.openclaw/memory/wangcai.sqlite", local_wangcai)
            print(f"  [OK] 已下载到: {local_wangcai}")
            print(f"  文件大小: {os.path.getsize(local_wangcai)} 字节")
        except Exception as e:
            print(f"  [ERROR] 下载失败: {e}")

        sftp.close()
        ssh.close()

        # 分析main.sqlite
        print("\n[3] 分析main.sqlite...")
        if os.path.exists(local_main):
            analyze_sqlite(local_main, "main agent")

        # 分析wangcai.sqlite
        print("\n[4] 分析wangcai.sqlite...")
        if os.path.exists(local_wangcai):
            analyze_sqlite(local_wangcai, "wangcai agent")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

def analyze_sqlite(db_path, agent_name):
    """分析SQLite数据库"""
    print(f"\n{'='*70}")
    print(f" {agent_name} 记忆数据库分析")
    print(f"{'='*70}\n")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print(f"[表列表] 共 {len(tables)} 个表\n")

        for table in tables:
            table_name = table[0]
            print(f"┌─ 表: {table_name}")
            print("│")

            # 获取记录数
            cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
            count = cursor.fetchone()[0]
            print(f"│  记录数: {count}")

            # 获取表结构
            cursor.execute(f"PRAGMA table_info([{table_name}]);")
            columns = cursor.fetchall()
            print(f"│  字段数: {len(columns)}")
            print("│  字段列表:")
            for col in columns:
                print(f"│    - {col[1]:<20} {col[2]:<15}")

            # 显示示例数据
            if count > 0:
                cursor.execute(f"SELECT * FROM [{table_name}] LIMIT 2")
                rows = cursor.fetchall()

                # 获取列名
                col_names = [col[1] for col in columns]

                print(f"│  示例数据 (前{len(rows)}条):")
                for i, row in enumerate(rows, 1):
                    # 格式化输出
                    row_str = " │    ".join([str(v)[:30] if v else "NULL" for v in row])
                    print(f"│    [{i}] {row_str}")

            print("└" + "─"*68)

        conn.close()

    except Exception as e:
        print(f"[ERROR] 分析失败: {e}")

if __name__ == '__main__':
    download_and_analyze()
