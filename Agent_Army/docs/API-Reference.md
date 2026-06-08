# 📚 Agent Army API 参考文档

## 目录

1. [核心类](#核心类)
2. [预测部API](#预测部api)
3. [策略部API](#策略部api)
4. [监控部API](#监控部api)
5. [验证部API](#验证部api)
6. [优化部API](#优化部api)
7. [配置部API](#配置部api)

---

## 核心类

### BusinessAgent

所有业务Agent的基类。

```python
class BusinessAgent(BaseAgent):
    """
    业务层Agent基类

    Attributes:
        name (str): Agent名称
        role (str): Agent角色
        corps (str): 所属军团
        analysis_type (str): 分析类型
    """

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行分析（抽象方法，子类必须实现）

        Args:
            stock_code: 股票代码（6位数字）
            **kwargs: 其他参数

        Returns:
            AnalysisResult: 分析结果

        Raises:
            ValueError: 参数无效
            NotImplementedError: 子类未实现
        """
        pass

    def validate_stock_code(self, stock_code: str) -> bool:
        """验证股票代码格式"""
        pass
```

### AnalysisResult

标准分析结果结构。

```python
@dataclass
class AnalysisResult:
    """
    分析结果

    Attributes:
        agent_name (str): 执行分析的Agent名称
        analysis_type (str): 分析类型
        conclusion (str): 核心结论（一句话总结）
        confidence (float): 置信度（0-1）
        details (Dict[str, Any]): 详细数据
        risks (List[str]): 风险提示列表
        recommendations (List[str]): 建议列表
    """
    agent_name: str
    analysis_type: str
    conclusion: str
    confidence: float
    details: Dict[str, Any]
    risks: List[str]
    recommendations: List[str]
```

---

## 预测部API

### ValuationPricingAI

估值定价AI - 目标定价 + 估值建议（2合1）

#### 初始化

```python
from src.agents.business.prediction import ValuationPricingAI

ai = ValuationPricingAI(config: Optional[Dict[str, Any]] = None)
```

#### analyze方法

```python
async def analyze(
    self,
    stock_code: str,
    current_price: float,
    prediction_period: str = "12m",
    **kwargs
) -> AnalysisResult:
    """
    估值定价分析

    Args:
        stock_code: 股票代码（如"600519"）
        current_price: 当前股价
        prediction_period: 预测周期（"3m"/"6m"/"12m"）

    Returns:
        AnalysisResult包含:
        - valuation_models: 估值模型（PE/PB/DCF/PEG）
        - target_pricing: 目标定价
        - valuation_advice: 估值建议

    Example:
        >>> result = await ai.analyze("600519", 1800.0, "12m")
        >>> print(result.details['target_pricing']['target_price'])
        1850.0
    """
```

#### 返回数据结构

```python
{
    "valuation_models": {
        "pe": {
            "method": "PE估值法",
            "target_price": 1850.0,
            "pe_ratio": 25.0,
            "eps": 74.0,
            "industry_pe": 25.0,
            "confidence": 0.80
        },
        "pb": {...},
        "dcf": {...},
        "peg": {...}
    },
    "target_pricing": {
        "target_price": 1850.0,
        "upside": 2.8,
        "confidence": 0.75,
        "price_range": {
            "lower": 1800.0,
            "upper": 1900.0,
            "width": "±5.0%"
        }
    },
    "valuation_advice": {
        "rating": "推荐",
        "action": "买入",
        "recommendations": [...]
    }
}
```

#### 便捷函数

```python
from src.agents.business.prediction import analyze_valuation_pricing

result = await analyze_valuation_pricing(
    stock_code="600519",
    current_price=1800.0,
    prediction_period="12m"
)
```

---

### ComprehensiveEvaluationAI

综合评估AI - 综合评分 + 质量评分（2合1）

#### analyze方法

```python
async def analyze(
    self,
    stock_code: str,
    research_data: Dict = None,
    analysis_data: Dict = None,
    prediction_data: Dict = None,
    **kwargs
) -> AnalysisResult:
    """
    综合评估分析

    Args:
        stock_code: 股票代码
        research_data: 研究部数据（可选）
        analysis_data: 分析部数据（可选）
        prediction_data: 预测部数据（可选）

    Returns:
        AnalysisResult包含:
        - dimension_scores: 5维度评分
        - comprehensive_score: 综合评分（0-100）
        - quality_assessment: 质量评估
        - investment_rating: 投资评级
    """
```

#### 返回数据结构

```python
{
    "dimension_scores": {
        "fundamental": {
            "score": 75.0,
            "weight": 0.30,
            "weighted_score": 22.5,
            "description": "基本面评分"
        },
        "growth": {...},
        "valuation": {...},
        "technical": {...},
        "sentiment": {...}
    },
    "comprehensive_score": 72.2,
    "quality_assessment": {
        "quality_grade": "B+",
        "quality_description": "较好",
        "strengths": [...],
        "weaknesses": [...]
    },
    "investment_rating": {
        "rating": "中性",
        "action": "持有观望",
        "risk_level": "中"
    }
}
```

---

### PriceForecastAI

预测AI - 价格预测 + 利润预测（2合1）

#### analyze方法

```python
async def analyze(
    self,
    stock_code: str,
    current_price: float,
    forecast_period: str = "12m",
    **kwargs
) -> AnalysisResult:
    """
    价格预测分析

    Args:
        stock_code: 股票代码
        current_price: 当前股价
        forecast_period: 预测周期（"3m"/"6m"/"12m"）

    Returns:
        AnalysisResult包含:
        - price_forecast: 价格预测
        - profit_forecast: 利润预测
        - trend_forecast: 趋势预测
        - scenario_analysis: 情景分析
    """
```

---

## 策略部API

### TimingJudgmentAI

时机判断AI - 买入时机 + 卖出时机（2合1）

#### analyze方法

```python
async def analyze(
    self,
    stock_code: str,
    current_price: float,
    position_cost: Optional[float] = None,
    **kwargs
) -> AnalysisResult:
    """
    时机判断分析

    Args:
        stock_code: 股票代码
        current_price: 当前股价
        position_cost: 持仓成本（可选，用于计算止盈止损）

    Returns:
        AnalysisResult包含:
        - buy_timing: 买入时机分析
        - sell_timing: 卖出时机分析
        - timing_score: 综合时机评分
        - action_suggestion: 操作建议
    """
```

#### 返回数据结构

```python
{
    "buy_timing": {
        "signal": "买入",  # 强烈买入/买入/观望/不买入
        "strength": "中",
        "confidence": 0.75,
        "technical": {
            "score": 65,
            "indicators": {...}
        },
        "entry_points": ["回调买入", "分批建仓"]
    },
    "sell_timing": {
        "signal": "持有",
        "take_profit": {
            "profit_rate": 15.0,
            "description": "盈利超过15%，考虑止盈"
        },
        "stop_loss": {
            "loss_rate": 0.0,
            "description": "无持仓，不考虑止损"
        }
    },
    "timing_score": {
        "overall_score": 75,
        "action": "买入",
        "confidence": 0.75
    },
    "action_suggestion": {
        "action": "买入",
        "timing": "良好",
        "entry_strategy": [...]
    }
}
```

---

### PositionManagementAI

仓位管理AI

#### analyze方法

```python
async def analyze(
    self,
    stock_code: str,
    current_price: float,
    total_capital: float,
    risk_tolerance: int = 3,  # 1-5
    **kwargs
) -> AnalysisResult:
    """
    仓位管理分析

    Args:
        stock_code: 股票代码
        current_price: 当前股价
        total_capital: 总资金（元）
        risk_tolerance: 风险偏好（1保守/2稳健/3平衡/4积极/5激进）

    Returns:
        AnalysisResult包含:
        - position_size: 仓位大小
        - allocation_strategy: 分配策略
        - market_assessment: 市场评估
    """
```

---

### RiskControlAI

风控AI - 风险控制 + 止损策略（2合1）

#### analyze方法

```python
async def analyze(
    self,
    stock_code: str,
    current_price: float,
    intended_buy_price: Optional[float] = None,
    **kwargs
) -> AnalysisResult:
    """
    风险控制分析

    Args:
        stock_code: 股票代码
        current_price: 当前股价
        intended_buy_price: 计划买入价（可选）

    Returns:
        AnalysisResult包含:
        - risk_assessment: 风险评估
        - stop_loss_strategy: 止损策略
        - stop_profit_strategy: 止盈策略
        - risk_control_plan: 风控方案
    """
```

---

## 监控部API

### InformationMonitoringAI

信息监控AI - 新闻监控 + 市场情绪（2合1）

#### analyze方法

```python
async def analyze(
    self,
    stock_code: str,
    days: int = 7,
    include_industry: bool = True,
    **kwargs
) -> AnalysisResult:
    """
    信息监控分析

    Args:
        stock_code: 股票代码
        days: 监控天数（默认7天）
        include_industry: 是否包含行业新闻

    Returns:
        AnalysisResult包含:
        - news_events: 新闻事件
        - sentiment_analysis: 情绪分析
        - important_info: 重要信息
    """
```

---

### CapitalMonitoringAI

资金监控AI - 资金流向 + 龙虎榜（2合1）

#### analyze方法

```python
async def analyze(
    self,
    stock_code: str,
    days: int = 5,
    include_dragon_tiger: bool = True,
    **kwargs
) -> AnalysisResult:
    """
    资金监控分析

    Args:
        stock_code: 股票代码
        days: 监控天数（默认5天）
        include_dragon_tiger: 是否包含龙虎榜

    Returns:
        AnalysisResult包含:
        - capital_flow: 资金流向
        - dragon_tiger: 龙虎榜数据
        - main_force_analysis: 主力分析
    """
```

---

## 验证部API

### ValidationBacktestAI

验证回测AI - 预测验证 + 回测分析（2合1）

#### analyze方法

```python
async def analyze(
    self,
    stock_code: str,
    predictions: List[Dict],
    actual_prices: List[Dict],
    **kwargs
) -> AnalysisResult:
    """
    验证回测分析

    Args:
        stock_code: 股票代码
        predictions: 预测数据列表
            [{"date": "2025-01-01", "predicted": 52.0}, ...]
        actual_prices: 实际价格列表
            [{"date": "2025-01-01", "actual": 51.5}, ...]

    Returns:
        AnalysisResult包含:
        - validation_metrics: 验证指标（MAE/RMSE/MAPE）
        - backtest_results: 回测结果
        - improvements: 改进建议
    """
```

---

## 优化部API

### SelfEvolutionAI

自我进化AI - 经验积累 + 参数优化 + 模式识别（3合1）

#### analyze方法

```python
async def analyze(
    self,
    stock_code: str,
    historical_data: Optional[Dict] = None,
    **kwargs
) -> AnalysisResult:
    """
    自我进化分析

    Args:
        stock_code: 股票代码
        historical_data: 历史数据（可选）

    Returns:
        AnalysisResult包含:
        - experience_learning: 经验学习
        - parameter_optimization: 参数优化
        - pattern_recognition: 模式识别
    """
```

---

## 配置部API

### AssetAllocationAI

资产配置AI

#### analyze方法

```python
async def analyze(
    self,
    stock_code: str,
    portfolio_size: float,
    risk_tolerance: str = "稳健",  # 保守/稳健/平衡/积极/激进
    investment_horizon: str = "中期",  # 短期/中期/长期
    **kwargs
) -> AnalysisResult:
    """
    资产配置分析

    Args:
        stock_code: 股票代码
        portfolio_size: 投资组合规模（元）
        risk_tolerance: 风险偏好
        investment_horizon: 投资期限

    Returns:
        AnalysisResult包含:
        - strategic_allocation: 战略配置
        - risk_parity: 风险平价配置
        - rebalancing: 再平衡建议
    """
```

---

### OpportunityScreeningAI

机会筛选AI

#### analyze方法

```python
async def analyze(
    self,
    stock_code: str,
    stock_universe: List[str],
    top_n: int = 10,
    **kwargs
) -> AnalysisResult:
    """
    机会筛选分析

    Args:
        stock_code: 基准股票代码
        stock_universe: 股票池
        top_n: 返回前N只股票

    Returns:
        AnalysisResult包含:
        - multi_factor_screening: 多因子筛选
        - industry_rotation: 行业轮动
        - market_hotspots: 市场热点
        - final_ranking: 最终排名
    """
```

---

## 错误处理

### 常见错误

```python
# 1. 无效股票代码
ValueError: 无效的股票代码: invalid

# 2. 缺少必需参数
ValueError: 缺少current_price参数

# 3. 参数类型错误
TypeError: current_price must be float

# 4. Agent未实现
NotImplementedError: 子类必须实现analyze方法
```

### 错误处理示例

```python
from src.agents.business.prediction import ValuationPricingAI

async def safe_analysis():
    ai = ValuationPricingAI()

    try:
        result = await ai.analyze("600519", 1800.0)
    except ValueError as e:
        print(f"参数错误: {e}")
    except TypeError as e:
        print(f"类型错误: {e}")
    except Exception as e:
        print(f"未知错误: {e}")
        # 记录日志
        ai.logger.error(f"分析失败: {e}")
```

---

## 版本信息

**API版本**: v1.0
**最后更新**: 2026-03-20
**兼容性**: Python 3.11+

---

## 更新日志

### v1.0 (2026-03-20)

- ✅ 初始版本发布
- ✅ 24个Agent全部实现
- ✅ 标准化API接口
- ✅ 完整的错误处理
- ✅ 异步支持

---

**更多文档**：
- [快速开始指南](Quick-Start-Guide.md)
- [架构设计](8-departments-simplified.md)
- [示例代码](../examples/)
