#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富板块数据网页爬虫 Skill - Main Entry Point
OpenClaw 入口文件
通过网页抓取获取板块资金流向数据
"""

# 导入 tool.py 中的功能
from tool import (
    init_db,
    sync_sector_fund_flow_from_html,
    get_sector_fund_flow,
    get_top_gainers,
    get_top_inflows,
    query_sector_data,
    batch_update_from_webreader
)

# 暴露给 OpenClaw 的函数
__all__ = [
    'init_db',                          # 初始化数据库
    'sync_sector_fund_flow_from_html',  # 从HTML同步板块资金流向
    'get_sector_fund_flow',             # 获取板块资金流向数据
    'get_top_gainers',                  # 获取涨幅榜前N名
    'get_top_inflows',                  # 获取资金流入前N名
    'query_sector_data',                # 查询指定板块数据
    'batch_update_from_webreader'       # 批量更新（使用WebReader）
]
