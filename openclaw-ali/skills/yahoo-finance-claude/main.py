#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yahoo Finance Skill - Main Entry Point
OpenClaw 入口文件
"""

# 导入 tool.py 中的功能
from tool import sync_yahoo_kline, sync_yahoo_info, query_stock_data

# 暴露给 OpenClaw 的函数
__all__ = ['sync_yahoo_kline', 'sync_yahoo_info', 'query_stock_data']
