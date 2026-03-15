#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股数据补充 Skill - Main Entry Point
OpenClaw 入口文件
从东方财富、同花顺获取A股核心数据，补充雅虎财经缺口
"""

# 导入 tool.py 中的功能
from tool import (
    sync_stock_money_flow,
    sync_limit_stats,
    sync_dragon_tiger_list,
    sync_sector_performance,
    sync_north_money_flow,
    sync_margin_trading,
    query_a_market,
    batch_update_all,
    init_db
)

# 暴露给 OpenClaw 的函数
__all__ = [
    'sync_stock_money_flow',      # 同步个股资金流向
    'sync_limit_stats',            # 同步涨跌停统计
    'sync_dragon_tiger_list',      # 同步龙虎榜数据
    'sync_sector_performance',     # 同步板块涨跌幅
    'sync_north_money_flow',       # 同步北向资金
    'sync_margin_trading',         # 同步融资融券
    'query_a_market',              # 查询A股数据
    'batch_update_all',            # 批量更新所有数据
    'init_db'                      # 初始化数据库
]
