#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雅虎财经Skill快速测试
"""
import sys
from pathlib import Path

# 添加skill目录
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

def test_tool():
    """测试工具函数"""
    print("测试工具函数...")

    try:
        from tool import sync_yahoo_kline, query_stock_data

        # 测试1: 同步K线
        print("\n1. 测试K线同步...")
        result = sync_yahoo_kline('600887', '伊利股份', 'SS', '1mo')
        print(f"   状态: {result['status']}")
        print(f"   消息: {result['message']}")

        # 测试2: 查询数据
        print("\n2. 测试数据查询...")
        result = query_stock_data("SELECT COUNT(*) as cnt FROM stock_kline_unified")
        print(f"   状态: {result['status']}")
        if result['status'] == 'success':
            print(f"   总记录数: {result['rows'][0]['cnt']}")

        print("\n✅ 测试通过！")
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_tool()
    sys.exit(0 if success else 1)
