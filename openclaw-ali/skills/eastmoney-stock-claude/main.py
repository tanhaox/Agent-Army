#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个股数据补充 Skill - Main Entry Point (基于AKShare)
OpenClaw 入口文件
使用AKShare库从东方财富等数据源获取个股级别数据，补充雅虎财经个股信息缺口
"""

# 导入 tool.py 中的功能
from tool import (
    sync_stock_money_flow,
    sync_stock_shareholders,
    sync_stock_unlock,
    sync_stock_north_holdings,
    sync_stock_all,
    query_stock_detail,
    init_db
)

# 暴露给 OpenClaw 的函数
__all__ = [
    'sync_stock_money_flow',         # 同步个股资金流向
    'sync_stock_shareholders',        # 同步个股股东数据
    'sync_stock_unlock',              # 同步个股限售解禁
    'sync_stock_north_holdings',      # 同步个股北向持股
    'sync_stock_all',                 # 批量同步个股所有数据
    'query_stock_detail',             # 查询个股补充数据
    'init_db'                         # 初始化数据库
]
