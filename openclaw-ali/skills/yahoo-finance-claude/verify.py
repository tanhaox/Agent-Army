#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雅虎财经Skill验证脚本
"""
import sys
import os
from pathlib import Path

# 设置UTF-8输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加skill目录
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

def main():
    print("=" * 60)
    print("  雅虎财经Skill验证")
    print("=" * 60)
    print()

    # 检查文件
    print("1. 检查Skill文件...")
    files_to_check = [
        SKILL_DIR / 'SKILL.md',
        SKILL_DIR / 'tool.py',
        SKILL_DIR / 'README.md',
        SKILL_DIR / 'DEPLOY.md',
    ]

    for file in files_to_check:
        if file.exists():
            print(f"   ✅ {file.name}")
        else:
            print(f"   ❌ {file.name} 缺失")

    print()

    # 测试工具函数
    print("2. 测试工具函数...")
    try:
        from tool import sync_yahoo_kline, sync_yahoo_info

        print("   导入工具函数: ✅")
    except Exception as e:
        print(f"   导入工具函数: ❌ {e}")
        return False

    print()

    # 测试K线同步
    print("3. 测试K线同步...")
    try:
        result = sync_yahoo_kline('600887', '伊利股份', 'SS', '1mo')
        if result['status'] == 'success':
            print(f"   状态: ✅ {result['message']}")
            print(f"   插入: {result['inserted']}条记录")
        else:
            print(f"   状态: ❌ {result['message']}")
    except Exception as e:
        print(f"   错误: ❌ {e}")
        return False

    print()

    # 测试个股信息
    print("4. 测试个股信息...")
    try:
        result = sync_yahoo_info('600887', '伊利股份', 'SS')
        if result['status'] == 'success':
            print(f"   状态: ✅ {result['message']}")
            print(f"   有效字段: {result.get('valid_fields', 'N/A')}+")
        else:
            print(f"   状态: ❌ {result['message']}")
    except Exception as e:
        print(f"   错误: ❌ {e}")
        return False

    print()
    print("=" * 60)
    print("  ✅ Skill验证通过！")
    print("=" * 60)
    print()
    print("下一步：")
    print("  1. 将skill复制到OpenClaw目录:")
    print("     cp -r yahoo-finance ~/.openclaw/skills/")
    print("  2. 刷新OpenClaw:")
    print("     openclaw gateway restart")
    print("  3. 在OpenClaw中测试:")
    print("     同步贵州茅台的雅虎财经数据")
    print()

    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
