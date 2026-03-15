"""
Agent Army - 业务层Agent基类
所有业务Agent的基类,扩展BaseAgent添加投资分析能力
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from ...core.base_agent import BaseAgent, AgentCapability, AgentTool
from ...core.logger import get_logger


class StockInfo(BaseModel):
    """股票基本信息"""
    code: str  # 股票代码
    name: str  # 股票名称
    industry: str  # 所属行业
    market: str = "A股"  # 市场
    market_cap: Optional[float] = None  # 市值(亿元)


class AnalysisResult(BaseModel):
    """分析结果"""
    agent_name: str  # 执行分析的Agent名称
    analysis_type: str  # 分析类型
    conclusion: str  # 核心结论
    confidence: float = Field(ge=0.0, le=1.0)  # 置信度 0-1
    details: Dict[str, Any] = Field(default_factory=dict)  # 详细数据
    risks: List[str] = Field(default_factory=list)  # 风险提示
    recommendations: List[str] = Field(default_factory=list)  # 建议


class InvestmentOpportunity(BaseModel):
    """投资机会"""
    stock_info: StockInfo  # 股票信息
    analysis_results: List[AnalysisResult]  # 分析结果
    overall_score: float = Field(ge=0.0, le=100.0)  # 综合评分 0-100
    investment_rating: str  # 投资评级(强烈推荐/推荐/中性/不推荐)
    target_price: Optional[float] = None  # 目标价格
    stop_loss_price: Optional[float] = None  # 止损价格
    position_suggestion: Optional[str] = None  # 仓位建议
    key_reasons: List[str] = Field(default_factory=list)  # 核心理由
    risk_warnings: List[str] = Field(default_factory=list)  # 风险警告


class BusinessAgent(BaseAgent):
    """
    业务层Agent基类
    扩展BaseAgent,添加投资分析相关功能
    """

    def __init__(
        self,
        name: str,
        role: str,
        corps: str,  # 所属军团
        analysis_type: str,  # 分析类型
        capabilities: Optional[List[AgentCapability]] = None,
        tools: Optional[List[AgentTool]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化业务层Agent

        Args:
            name: Agent名称
            role: Agent角色
            corps: 所属军团
            analysis_type: 分析类型
            capabilities: 能力列表
            tools: 工具列表
            config: 配置
        """
        super().__init__(name, role, capabilities, tools, config)

        self.corps = corps
        self.analysis_type = analysis_type

        self.logger.info(
            f"业务层Agent初始化",
            agent=name,
            corps=corps,
            analysis_type=analysis_type
        )

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行分析(抽象方法,子类必须实现)

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数

        Returns:
            分析结果
        """
        raise NotImplementedError("子类必须实现analyze方法")

    async def execute(self, task: str, **kwargs) -> Any:
        """
        执行任务(重写BaseAgent的方法)

        Args:
            task: 任务描述
            **kwargs: 任务参数

        Returns:
            执行结果
        """
        # 默认调用analyze方法
        stock_code = kwargs.get("stock_code", "")
        if not stock_code:
            raise ValueError("缺少stock_code参数")

        return await self.analyze(stock_code, **kwargs)

    def validate_stock_code(self, stock_code: str) -> bool:
        """
        验证股票代码格式

        Args:
            stock_code: 股票代码

        Returns:
            是否有效
        """
        # A股代码格式: 6位数字
        import re
        return bool(re.match(r"^\d{6}$", stock_code))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, corps={self.corps}, type={self.analysis_type})>"
