"""
工具库 - 统一管理所有外部接口和工具

职责：
- 封装所有API调用（数据源、AI服务、计算）
- 提供统一接口给AI Agent使用
- AI Agent不关心工具如何实现，只关心如何使用

工具分类：
1. data_source: 数据源工具（新闻、财务、市场、政策、搜索、Tushare）
2. ai_service: AI服务工具（LLM、NLP、向量化）
3. calculation: 计算工具（公式、统计、技术指标）
4. tool_facades: 门面层（统一接口、自动降级）
"""

from src.core.tools.data_source import NewsTool, FinancialTool, PolicyTool, ZhipuSearchTool, TushareNewsAggregator
from src.core.tools.data_source.yahoo_tool import YahooFinanceTool
from src.core.tools.data_source.akshare_tool import AKShareTool
from src.core.tools.data_source.eastmoney_scraper import EastMoneyScraper
from src.core.tools.ai_service import LLMTool, NLPTool
from src.core.tools.calculation import FormulaTool

# 门面层 - 统一接口（推荐使用）
from src.core.tools.tool_facades import (
    IndustryTool,
    TechnicalTool,
    CapitalFlowTool,
    get_industry_tool,
    get_technical_tool,
    get_capital_flow_tool
)

__all__ = [
    # 底层工具
    "NewsTool",
    "FinancialTool",
    "PolicyTool",
    "ZhipuSearchTool",
    "TushareNewsAggregator",
    "YahooFinanceTool",
    "AKShareTool",
    "EastMoneyScraper",
    "LLMTool",
    "NLPTool",
    "FormulaTool",
    # 门面层（推荐使用）⭐
    "IndustryTool",
    "TechnicalTool",
    "CapitalFlowTool",
    "get_industry_tool",
    "get_technical_tool",
    "get_capital_flow_tool"
]
