"""
工具库统一面板 - ToolsLibraryPanel
解决接口分散、格式不统一的问题，提供统一的工具调用接口
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import asyncio

from src.core.logger import get_logger
from src.core.tools.data_source.news_tool import NewsTool
from src.core.tools.data_source.financial_tool import FinancialTool
from src.core.tools.data_source.policy_tool import PolicyTool
from src.core.tools.data_source.zhipu_search_tool import ZhipuSearchTool
from src.core.tools.data_source.tushare_news_aggregator import TushareNewsAggregator
from src.core.tools.calculation.formula_tool import FormulaTool


class ToolsLibraryPanel:
    """
    工具库统一面板

    职责：
    - 统一所有工具的调用接口
    - 标准化返回格式
    - 自动降级和错误处理
    - 提供工具发现和使用统计

    支持的功能分类：
    1. 新闻资讯（NewsTool, TushareNewsAggregator）
    2. 政策文件（PolicyTool）
    3. 财经搜索（ZhipuSearchTool）
    4. 财务数据（FinancialTool）
    5. 技术指标（FormulaTool）
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("tools_library_panel")
        self.config = config or {}

        # 初始化所有工具
        self.tools = {
            'news': NewsTool(),
            'financial': FinancialTool(),
            'policy': PolicyTool(),
            'search': ZhipuSearchTool(),
            'tushare_news': TushareNewsAggregator(),
            'formula': FormulaTool()
        }

        # 工具注册表
        self.tool_registry = self._build_tool_registry()

        self.logger.info("工具库统一面板初始化完成")

    def _build_tool_registry(self) -> Dict[str, Any]:
        """构建工具注册表"""
        return {
            'news': {
                'name': '新闻资讯',
                'description': '获取股票相关新闻和市场快讯',
                'methods': {
                    'fetch_news': {
                        'description': '获取新闻',
                        'params': {'stock_code': '股票代码', 'days': '天数(默认7)'},
                        'returns': '新闻列表（标题、内容、来源、时间）'
                    },
                    'analyze_sentiment': {
                        'description': '情感分析',
                        'params': {'text': '待分析文本'},
                        'returns': '情感结果（正/负/中性、分数、关键词）'
                    }
                }
            },
            'policy': {
                'name': '政策文件',
                'description': '搜索政府政策和新闻',
                'methods': {
                    'search_policies': {
                        'description': '搜索政策',
                        'params': {'keyword': '关键词', 'limit': '数量限制'},
                        'returns': '政策列表（标题、来源、日期、链接）'
                    },
                    'get_latest_policies': {
                        'description': '获取最新政策',
                        'params': {'limit': '数量限制'},
                        'returns': '最新政策列表'
                    },
                    'get_stats': {
                        'description': '获取统计信息',
                        'params': {},
                        'returns': '数据库统计（总数、按来源、按分类）'
                    }
                }
            },
            'search': {
                'name': '财经搜索',
                'description': '使用智谱AI进行网络搜索',
                'methods': {
                    'search_web': {
                        'description': '网页搜索',
                        'params': {'query': '搜索关键词', 'importance': '重要性', 'top_k': '结果数量'},
                        'returns': '搜索结果（标题、链接、摘要、来源）'
                    },
                    'get_balance_stats': {
                        'description': '获取搜索余额',
                        'params': {},
                        'returns': '余额统计（总余额、各引擎余额、到期时间）'
                    }
                }
            },
            'tushare_news': {
                'name': 'Tushare新闻',
                'description': '聚合10个新闻源',
                'methods': {
                    'fetch_news': {
                        'description': '获取新闻',
                        'params': {'source': '新闻源代码', 'category': '子分类', 'limit': '数量限制'},
                        'returns': '新闻列表（10个源+26个分类）'
                    },
                    'search_news': {
                        'description': '搜索新闻',
                        'params': {'keyword': '关键词', 'source': '过滤源', 'limit': '数量限制'},
                        'returns': '搜索结果'
                    },
                    'get_available_sources': {
                        'description': '获取可用源列表',
                        'params': {},
                        'returns': '10个新闻源+26个子分类的详细信息'
                    }
                }
            },
            'financial': {
                'name': '财务数据',
                'description': '获取财务数据和技术指标',
                'methods': {
                    'fetch_financial_data': {
                        'description': '获取财务数据',
                        'params': {'stock_code': '股票代码'},
                        'returns': 'ROE、EPS等财务指标'
                    },
                    'get_top_list': {
                        'description': '获取涨跌榜',
                        'params': {},
                        'returns': '涨跌榜数据'
                    }
                }
            },
            'formula': {
                'name': '技术指标',
                'description': '计算技术指标',
                'methods': {
                    'calculate': {
                        'description': '计算指标',
                        'params': {'indicator_name': '指标名称', 'data': '数据'},
                        'returns': '计算结果'
                    }
                }
            }
        }

    def call_tool(
        self,
        category: str,
        method: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        统一工具调用接口

        Args:
            category: 工具分类（news/policy/search/tushare_news/financial/formula）
            method: 方法名
            **kwargs: 方法参数

        Returns:
            标准化返回格式:
            {
                "success": True/False,
                "data": {...},
                "error": "错误信息（如果失败）",
                "tool": "使用的工具",
                "method": "调用的方法",
                "timestamp": "时间戳"
            }
        """
        self.logger.info(f"调用工具: {category}.{method}")

        # 验证工具和方法
        if category not in self.tools:
            return self._error_response(f"未知的工具分类: {category}")

        if category not in self.tool_registry:
            return self._error_response(f"工具未注册: {category}")

        if method not in self.tool_registry[category]['methods']:
            return self._error_response(f"未知的工具方法: {category}.{method}")

        try:
            # 获取工具实例
            tool = self.tools[category]

            # 调用方法
            method_func = getattr(tool, method)
            result = method_func(**kwargs)

            # 标准化返回格式
            return self._success_response(result, category, method)

        except Exception as e:
            self.logger.error(f"工具调用失败: {str(e)}")
            return self._error_response(str(e), category, method)

    def _success_response(
        self,
        data: Any,
        tool: str,
        method: str
    ) -> Dict[str, Any]:
        """成功响应"""
        return {
            'success': True,
            'data': data,
            'tool': tool,
            'method': method,
            'timestamp': datetime.now().isoformat()
        }

    def _error_response(
        self,
        error: str,
        tool: Optional[str] = None,
        method: Optional[str] = None
    ) -> Dict[str, Any]:
        """错误响应"""
        return {
            'success': False,
            'error': error,
            'tool': tool or 'unknown',
            'method': method or 'unknown',
            'timestamp': datetime.now().isoformat()
        }

    def get_tool_list(self) -> Dict[str, Any]:
        """
        获取所有可用工具列表

        Returns:
            {
                "tools": {
                    "category": {
                        "name": "工具名称",
                        "description": "描述",
                        "methods": ["方法1", "方法2"]
                    }
                },
                "total": 6,
                "timestamp": "..."
            }
        """
        tools_info = {}

        for category, info in self.tool_registry.items():
            tools_info[category] = {
                'name': info['name'],
                'description': info['description'],
                'methods': list(info['methods'].keys())
            }

        return {
            'tools': tools_info,
            'total': len(tools_info),
            'timestamp': datetime.now().isoformat()
        }

    def get_method_info(self, category: str, method: str) -> Dict[str, Any]:
        """
        获取方法详细信息

        Returns:
            {
                "category": "分类",
                "method": "方法名",
                "description": "描述",
                "params": {"param": "描述"},
                "returns": "返回值说明"
            }
        """
        if category not in self.tool_registry:
            return self._error_response(f"未知的工具分类: {category}")

        if method not in self.tool_registry[category]['methods']:
            return self._error_response(f"未知的工具方法: {category}.{method}")

        method_info = self.tool_registry[category]['methods'][method]

        return {
            'category': category,
            'method': method,
            'description': method_info['description'],
            'params': method_info.get('params', {}),
            'returns': method_info.get('returns', ''),
            'timestamp': datetime.now().isoformat()
        }

    def search_all(self, keyword: str, limit: int = 20) -> Dict[str, Any]:
        """
        跨工具搜索

        在所有支持搜索的工具中搜索关键词

        Args:
            keyword: 搜索关键词
            limit: 每个工具的结果限制

        Returns:
            {
                "success": True,
                "results": {
                    "policy": [...],
                    "tushare_news": [...]
                },
                "total": 100,
                "timestamp": "..."
            }
        """
        self.logger.info(f"跨工具搜索: {keyword}")

        all_results = {}

        # 搜索政策
        policy_result = self.call_tool('policy', 'search_policies', keyword=keyword, limit=limit)
        if policy_result['success']:
            all_results['policy'] = policy_result['data']

        # 搜索Tushare新闻
        news_result = self.call_tool('tushare_news', 'search_news', keyword=keyword, limit=limit)
        if news_result['success']:
            all_results['tushare_news'] = news_result['data']

        total = sum(len(results) for results in all_results.values())

        return {
            'success': True,
            'results': all_results,
            'total': total,
            'keyword': keyword,
            'timestamp': datetime.now().isoformat()
        }

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        获取工具库仪表板统计

        Returns:
            {
                "tools": {
                    "news": {"total_methods": 2, "status": "available"},
                    ...
                },
                "summary": {
                    "total_tools": 6,
                    "total_methods": 15,
                    "available_tools": 6
                },
                "timestamp": "..."
            }
        """
        tools_stats = {}
        total_methods = 0

        for category, info in self.tool_registry.items():
            method_count = len(info['methods'])
            total_methods += method_count

            tools_stats[category] = {
                'name': info['name'],
                'total_methods': method_count,
                'status': 'available'
            }

        return {
            'tools': tools_stats,
            'summary': {
                'total_tools': len(tools_stats),
                'total_methods': total_methods,
                'available_tools': len(tools_stats)
            },
            'timestamp': datetime.now().isoformat()
        }


# ========== 便捷函数 ==========

def call_tool(category: str, method: str, **kwargs) -> Dict[str, Any]:
    """
    调用工具（便捷函数）

    Args:
        category: 工具分类
        method: 方法名
        **kwargs: 参数

    Returns:
        标准化返回结果
    """
    panel = ToolsLibraryPanel()
    return panel.call_tool(category, method, **kwargs)


def search_all_tools(keyword: str, limit: int = 20) -> Dict[str, Any]:
    """
    跨工具搜索（便捷函数）

    Args:
        keyword: 搜索关键词
        limit: 结果限制

    Returns:
        搜索结果汇总
    """
    panel = ToolsLibraryPanel()
    return panel.search_all(keyword, limit)


def get_tool_info() -> Dict[str, Any]:
    """
    获取工具信息（便捷函数）

    Returns:
        所有工具的列表和说明
    """
    panel = ToolsLibraryPanel()
    return panel.get_tool_list()
