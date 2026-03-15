"""
Agent Army - 投资分析数据模型
定义投资分析中使用的各种数据结构
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AnalysisType(str, Enum):
    """分析类型"""
    FUNDAMENTAL = "fundamental"  # 基本面
    TECHNICAL = "technical"  # 技术面
    VALUATION = "valuation"  # 估值
    OPPORTUNITY = "opportunity"  # 机会筛选
    INDUSTRY = "industry"  # 产业
    CHAIN = "chain"  # 产业链
    COMPETITION = "competition"  # 竞争
    POLICY = "policy"  # 政策
    VALUE = "value"  # 价值评估


class Rating(str, Enum):
    """评级"""
    STRONG_BUY = "强推"  # 强烈推荐
    BUY = "买入"  # 推荐
    HOLD = "持有"  # 持有
    SELL = "卖出"  # 卖出
    STRONG_SELL = "强卖"  # 强烈卖出
    NEUTRAL = "中性"  # 中性


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "低风险"
    MEDIUM = "中等风险"
    HIGH = "高风险"
    VERY_HIGH = "极高风险"


# ==================== 基础数据模型 ====================

class StockBasicInfo(BaseModel):
    """股票基础信息"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    industry: str = Field(..., description="所属行业")
    market: str = Field(default="A股", description="市场")
    list_date: Optional[str] = Field(None, description="上市日期")


class FinancialData(BaseModel):
    """财务数据"""
    revenue: Optional[float] = Field(None, description="营收(亿元)")
    net_profit: Optional[float] = Field(None, description="净利润(亿元)")
    gross_margin: Optional[float] = Field(None, description="毛利率(%)")
    net_margin: Optional[float] = Field(None, description="净利率(%)")
    roe: Optional[float] = Field(None, description="ROE(%)")
    debt_ratio: Optional[float] = Field(None, description="资产负债率(%)")
    current_ratio: Optional[float] = Field(None, description="流动比率")
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")


class TechnicalIndicators(BaseModel):
    """技术指标"""
    ma5: Optional[float] = Field(None, description="5日均线")
    ma10: Optional[float] = Field(None, description="10日均线")
    ma20: Optional[float] = Field(None, description="20日均线")
    ma60: Optional[float] = Field(None, description="60日均线")
    rsi: Optional[float] = Field(None, description="RSI指标")
    macd: Optional[float] = Field(None, description="MACD")
    kdj_k: Optional[float] = Field(None, description="KDJ-K值")
    kdj_d: Optional[float] = Field(None, description="KDJ-D值")
    kdj_j: Optional[float] = Field(None, description="KDJ-J值")


# ==================== 分析结果模型 ====================

class AnalysisResult(BaseModel):
    """分析结果基类"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    analysis_type: AnalysisType = Field(..., description="分析类型")
    timestamp: datetime = Field(default_factory=datetime.now, description="分析时间")
    score: float = Field(0.0, description="评分(0-100)")
    confidence: float = Field(0.0, description="置信度(0-1)")
    summary: str = Field("", description="分析摘要")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细数据")
    warnings: List[str] = Field(default_factory=list, description="风险提示")


class FundamentalAnalysisResult(AnalysisResult):
    """基本面分析结果"""
    analysis_type: AnalysisType = AnalysisType.FUNDAMENTAL

    # 财务质量
    financial_score: float = Field(0.0, description="财务质量评分")
    profitability: float = Field(0.0, description="盈利能力评分")
    growth_ability: float = Field(0.0, description="成长能力评分")
    solvency: float = Field(0.0, description="偿债能力评分")

    # 核心指标
    roe_trend: str = Field("", description="ROE趋势")
    revenue_growth: float = Field(0.0, description="营收增长率")
    profit_growth: float = Field(0.0, description="利润增长率")

    # 结论
    rating: Rating = Field(Rating.NEUTRAL, description="投资评级")
    investment_value: str = Field("", description="投资价值评价")


class TechnicalAnalysisResult(AnalysisResult):
    """技术面分析结果"""
    analysis_type: AnalysisType = AnalysisType.TECHNICAL

    # 趋势判断
    trend: str = Field("", description="趋势(上涨/下跌/震荡)")
    trend_strength: float = Field(0.0, description="趋势强度")
    support_level: float = Field(0.0, description="支撑位")
    resistance_level: float = Field(0.0, description="阻力位")

    # 买卖信号
    buy_signal: bool = Field(False, description="买入信号")
    sell_signal: bool = Field(False, description="卖出信号")
    signal_strength: float = Field(0.0, description="信号强度")

    # 技术形态
    pattern: str = Field("", description="技术形态")
    pattern_reliability: float = Field(0.0, description="形态可靠性")


class ValuationResult(AnalysisResult):
    """估值分析结果"""
    analysis_type: AnalysisType = AnalysisType.VALUATION

    # 估值方法
    pe_valuation: float = Field(0.0, description="PE估值")
    pb_valuation: float = Field(0.0, description="PB估值")
    dcf_valuation: float = Field(0.0, description="DCF估值")

    # 综合估值
    intrinsic_value: float = Field(0.0, description="内在价值")
    current_price: float = Field(0.0, description="当前价格")
    safety_margin: float = Field(0.0, description="安全边际(%)")

    # 估值结论
    valuation_level: str = Field("", description="估值水平(低估/合理/高估)")
    target_price: float = Field(0.0, description="目标价格")
    upside_potential: float = Field(0.0, description="上涨空间(%)")


class IndustryAnalysisResult(AnalysisResult):
    """产业分析结果"""
    analysis_type: AnalysisType = AnalysisType.INDUSTRY

    # 行业概况
    industry_name: str = Field("", description="行业名称")
    industry_size: float = Field(0.0, description="行业规模(亿元)")
    industry_growth: float = Field(0.0, description="行业增长率(%)")

    # 行业地位
    market_share: float = Field(0.0, description="市场份额(%)")
    industry_rank: int = Field(0, description="行业排名")

    # 行业前景
    industry_cycle: str = Field("", description="行业周期")
    growth_driver: List[str] = Field(default_factory=list, description="增长驱动因素")
    risk_factors: List[str] = Field(default_factory=list, description="风险因素")


# ==================== 综合分析报告 ====================

class InvestmentReport(BaseModel):
    """投资分析报告(综合)"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    report_date: datetime = Field(default_factory=datetime.now, description="报告日期")

    # 分析结果
    fundamental: Optional[FundamentalAnalysisResult] = Field(None, description="基本面分析")
    technical: Optional[TechnicalAnalysisResult] = Field(None, description="技术面分析")
    valuation: Optional[ValuationResult] = Field(None, description="估值分析")
    industry: Optional[IndustryAnalysisResult] = Field(None, description="产业分析")

    # 综合评价
    overall_score: float = Field(0.0, description="综合评分(0-100)")
    overall_rating: Rating = Field(Rating.NEUTRAL, description="综合评级")
    risk_level: RiskLevel = Field(RiskLevel.MEDIUM, description="风险等级")

    # 投资建议
    investment_advice: str = Field("", description="投资建议")
    target_price: float = Field(0.0, description="目标价格")
    stop_loss_price: float = Field(0.0, description="止损价格")
    position_suggestion: str = Field("", description="仓位建议")

    # 风险提示
    key_risks: List[str] = Field(default_factory=list, description="关键风险")
    investment_horizon: str = Field("", description="投资期限")

    # 预审结果（方案C v2）
    precheck_results: Optional[Dict[str, Any]] = Field(None, description="各Agent预审结果")
    warnings: List[str] = Field(default_factory=list, description="警告信息")

    # Commander审核
    commander_review: Optional[Dict[str, Any]] = Field(None, description="Commander审核结果")

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
        }
