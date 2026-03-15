# 盈利预测AI (ProfitForecastAI) 文档

## 概述

**文件位置**: `src/agents/business/target/profit_forecast_ai.py`

**所属军团**: 目标预测军团 (Target Forecast Corps)

**核心职责**: 预测企业未来盈利能力和增长趋势

## 主要功能

### 1. 历史财务数据分析
- 获取历史收入和净利润数据
- 计算历史增长率
- 分析增长趋势稳定性

### 2. 未来盈利预测
- 预测未来3-5年收入和净利润
- 基于历史增长率和LLM分析
- 提供保守、中性、乐观三种情景

### 3. 趋势智能分析
- 使用LLM分析增长驱动因素
- 识别行业趋势和风险
- 提供增长率预测情景

### 4. 置信度评估
- 数据完整性评分
- 增长稳定性评分
- LLM分析质量评分
- 预测合理性评分

### 5. 风险识别
- 增长率波动风险
- 预测过于乐观风险
- 数据不足风险
- 行业和宏观经济风险

## 技术架构

### 工具集成

```python
# 1. YahooFinanceTool - 历史财务数据
self.yahoo_tool = YahooFinanceTool()
- 获取Yahoo Finance财务报表
- 支持A股（.SS/.SZ后缀）
- 提供收入、净利润等核心指标

# 2. LLMTool - 智能分析
self.llm_tool = LLMTool()
- 趋势分析和预测
- 增长驱动因素识别
- 风险因素评估

# 3. FinancialTool - 辅助数据
self.financial_tool = FinancialTool()
- 本地财务数据补充
- 备用数据源
```

### 数据源策略

**多数据源降级策略**:
1. **优先**: Yahoo Finance API
2. **备选**: 本地FinancialTool
3. **兜底**: 模拟数据（确保可用性）

## 数据模型

### 返回结构

```python
{
    "stock_code": "600519",              # 股票代码
    "stock_name": "贵州茅台",            # 股票名称
    "forecast_years": 3,                 # 预测年数

    # 历史数据
    "historical_revenue": [
        {
            "year": 2023,
            "revenue": 1000000000,       # 收入（元）
            "net_profit": 150000000,     # 净利润（元）
            "growth_rate": 0.10           # 增长率
        }
    ],

    # 预测数据
    "forecast": [
        {
            "year": 2025,
            "revenue": 1200000000,       # 预测收入
            "net_profit": 180000000,     # 预测净利润
            "growth_rate": 0.09,          # 预测增长率
            "confidence": 0.75            # 置信度
        }
    ],

    "avg_growth_rate": 0.097,            # 平均增长率
    "confidence": 0.75,                  # 整体置信度
    "timestamp": "2026-03-15T10:30:00",

    # 分析说明
    "analysis_notes": [
        "最新年度（2025）收入14.64亿元",
        "历史平均增长率10.0%",
        "预测未来3年年均增长率10.0%"
    ],

    # 风险因素
    "risk_factors": [
        "历史增长率波动较大",
        "预测增长率较高，实际达成存在难度"
    ]
}
```

## 使用方法

### 基本用法

```python
from src.agents.business.target.profit_forecast_ai import ProfitForecastAI

# 创建AI实例
ai = ProfitForecastAI()

# 分析盈利预测
result = await ai.analyze(
    stock_code="600519",      # 股票代码
    forecast_years=3,         # 预测年数（可选，默认3）
    use_llm=True             # 是否使用LLM（可选，默认True）
)

# 查看结果
print(f"平均增长率: {result['avg_growth_rate']*100:.1f}%")
print(f"预测置信度: {result['confidence']*100:.0f}%")
```

### 便捷函数

```python
from src.agents.business.target.profit_forecast_ai import forecast_profit

# 快速预测
result = await forecast_profit(
    stock_code="600519",
    forecast_years=3,
    use_llm=False  # 不使用LLM，速度更快
)
```

### 预测情景分析

```python
# 使用LLM获取多情景预测
result = await ai.analyze("600519", use_llm=True)

# LLM会提供三种情景：
if result.get("trend_analysis"):
    scenarios = result["trend_analysis"]["forecast_scenarios"]
    print(f"保守情景增长率: {scenarios['conservative']['growth_rate']*100:.1f}%")
    print(f"中性情景增长率: {scenarios['neutral']['growth_rate']*100:.1f}%")
    print(f"乐观情景增长率: {scenarios['optimistic']['growth_rate']*100:.1f}%")
```

## 置信度评估体系

### 评分维度（总分100分）

1. **数据完整性**（30分）
   - 5年以上数据: 30分
   - 3-4年数据: 20分
   - 少于3年: 10分

2. **增长稳定性**（30分）
   - 标准差 < 5%: 30分
   - 标准差 5-10%: 20分
   - 标准差 > 10%: 10分

3. **LLM分析质量**（20分）
   - 基于LLM返回的confidence_level

4. **预测合理性**（20分）
   - 增长率 0-30%: 20分
   - 增长率 0-50%: 10分
   - 增长率 > 50%: 5分

### 置信度等级

- **0.8-1.0**: 高置信度（数据充分，趋势稳定）
- **0.6-0.8**: 中等置信度（数据一般，趋势基本稳定）
- **0.4-0.6**: 低置信度（数据不足或波动大）
- **0.0-0.4**: 极低置信度（不可靠）

## 风险识别

### 自动检测的风险因素

1. **增长率波动风险**
   - 标准差 > 15%时触发
   - 说明：历史增长不稳定，预测不确定性高

2. **预测过高风险**
   - 平均增长率 > 25%时触发
   - 说明：预测过于乐观，实际达成难度大

3. **远期递增风险**
   - 远期增长率 > 近期1.5倍时触发
   - 说明：后期增长假设过于乐观

4. **数据不足风险**
   - 历史数据 < 3年时触发
   - 说明：样本量小，预测可靠性有限

5. **通用风险**
   - 宏观经济波动
   - 行业竞争加剧

## 测试

运行测试：

```bash
python tests/test_profit_forecast_ai.py
```

测试覆盖：
- ✅ AI初始化
- ✅ 盈利预测分析
- ✅ 历史数据展示
- ✅ 预测数据展示
- ✅ 分析说明生成
- ✅ 风险因素识别
- ✅ 工具使用验证
- ✅ 数据结构验证
- ✅ 便捷函数测试

## 性能特点

| 指标 | 值 |
|------|-----|
| 代码行数 | ~900行 |
| 初始化时间 | < 1秒 |
| 分析耗时（不用LLM） | < 1秒 |
| 分析耗时（使用LLM） | 3-5秒 |
| 内存占用 | < 50MB |
| CPU占用 | 低 |

## 依赖项

```
src/core/base_agent.py
src/core/logger.py
src/core/tools/data_source/yahoo_tool.py
src/core/tools/ai_service/llm_tool.py
src/core/tools/data_source/financial_tool.py
pydantic
asyncio
```

## 配置要求

### 环境变量（可选）

```bash
# Yahoo Finance（自动安装，无需配置）
pip install yfinance

# 智谱AI（用于LLM分析）
ZHIPU_API_KEY=your_api_key

# Tushare（用于本地财务数据）
TUSHARE_API_KEY=your_api_key
```

### API配置

所有API均可通过Web界面配置：
- ZHIPU_API_KEY: LLM分析
- TUSHARE_API_KEY: 本地财务数据

## 注意事项

1. **数据质量**: Yahoo Finance数据可能不完整，系统会自动降级
2. **LLM调用**: 使用LLM会增加3-5秒延迟
3. **预测期限**: 建议不超过5年，远期预测可靠性低
4. **增长率范围**: 合理增长率应在0-30%之间
5. **置信度**: 低于0.6的预测建议谨慎使用

## 更新日志

### v1.0.0 (2026-03-15)
- ✅ 初始版本发布
- ✅ 支持Yahoo Finance数据
- ✅ 支持LLM趋势分析
- ✅ 实现置信度评估
- ✅ 实现风险识别
- ✅ 提供便捷函数

## 未来优化方向

1. **数据源扩展**
   - 集成更多财务数据API
   - 支持手动数据输入

2. **预测算法优化**
   - 时间序列模型（ARIMA）
   - 机器学习模型
   - 行业对比分析

3. **LLM增强**
   - 更细化的提示词
   - 多轮对话优化
   - 结果解析优化

4. **可视化**
   - 生成趋势图表
   - 导出PDF报告

## 相关文件

- **测试文件**: `tests/test_profit_forecast_ai.py`
- **基类**: `src/agents/business/base_business_agent.py`
- **工具**: `src/core/tools/`
- **配置**: `src/core/config/`

## 联系方式

如有问题或建议，请通过项目仓库提交Issue。
