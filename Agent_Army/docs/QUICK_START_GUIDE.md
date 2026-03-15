# Agent Army 快速开始指南

**版本**: 1.3.0
**更新日期**: 2026-03-15
**项目状态**: 🟢 活跃开发

---

## 📋 目录

1. [环境准备](#1-环境准备)
2. [安装依赖](#2-安装依赖)
3. [配置API密钥](#3-配置api密钥)
4. [快速示例](#4-快速示例)
5. [运行测试](#5-运行测试)
6. [Web界面使用](#6-web界面使用)
7. [常见问题](#7-常见问题)

---

## 1. 环境准备

### 1.1 Python环境

**要求**: Python 3.10 或更高版本

```bash
# 检查Python版本
python --version

# 如果版本过低，请安装Python 3.10+
# 下载地址: https://www.python.org/downloads/
```

### 1.2 pip包管理器

```bash
# 检查pip版本
pip --version

# 升级pip到最新版本
pip install --upgrade pip
```

---

## 2. 安装依赖

### 2.1 克隆或下载项目

```bash
# 如果项目已存在，跳过此步骤
cd C:\AI-Agent-Local\Agent_Army
```

### 2.2 安装Python依赖

```bash
# 安装所有依赖包
pip install -r requirements.txt

# 验证关键依赖安装
python -c "import langgraph; print('LangGraph:', langgraph.__version__)"
python -c "import streamlit; print('Streamlit:', streamlit.__version__)"
python -c "import pandas; print('Pandas:', pandas.__version__)"
```

**预期输出**:
```
LangGraph: 0.2.0
Streamlit: 1.55.0
Pandas: 2.0.0
```

### 2.3 可选依赖（数据源）

```bash
# Yahoo Finance（推荐，已验证）
pip install yfinance

# AKShare（可选，国内数据源）
pip install akshare

# Tushare（可选，专业数据源）
pip install tushare
```

---

## 3. 配置API密钥

### 3.1 创建环境变量文件

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑.env文件
# Windows: notepad .env
# Mac/Linux: nano .env
```

### 3.2 配置智谱AI（主力模型）

```bash
# .env 文件内容

# ===== 智谱AI配置（主力模型） =====
ZHIPU_API_KEY=your_zhipu_api_key_here

# 获取API密钥:
# 1. 访问 https://open.bigmodel.cn/
# 2. 注册/登录账号
# 3. 进入"API密钥"页面
# 4. 创建新密钥并复制到此处
```

### 3.3 配置可选API

```bash
# ===== DeepSeek（基准测试） =====
DEEPSEEK_API_KEY=your_deepseek_api_key_here
# 获取地址: https://platform.deepseek.com/

# ===== OpenAI（高质量场景） =====
OPENAI_API_KEY=your_openai_api_key_here
# 获取地址: https://platform.openai.com/

# ===== Tushare（专业数据源） =====
TUSHARE_TOKEN=your_tushare_token_here
# 获取地址: https://tushare.pro/
```

### 3.4 验证配置

```bash
# 运行配置验证脚本
python verify_config_switch.py

# 预期输出: 所有验证通过 ✅
```

---

## 4. 快速示例

### 4.1 市场情绪分析

```python
"""
市场情绪分析示例
分析股票的市场情绪和舆论导向
"""
import asyncio
from src.agents.business.hot_spot.market_sentiment_ai import MarketSentimentAI

async def main():
    # 创建AI实例
    ai = MarketSentimentAI()

    # 分析市场情绪（默认7天）
    result = await ai.analyze(
        stock_code="600519",  # 贵州茅台
        days=7
    )

    # 查看结果
    print(f"股票代码: {result.stock_code}")
    print(f"情感指数: {result.sentiment_index:.2f}/100")
    print(f"市场情绪: {result.market_mood}")
    print(f"新闻总数: {result.news_count}")
    print(f"正面/负面/中性: {result.positive_count}/{result.negative_count}/{result.neutral_count}")
    print(f"热门关键词: {', '.join(result.top_keywords[:5])}")

# 运行示例
asyncio.run(main())
```

**预期输出**:
```
股票代码: 600519
情感指数: 65.43/100
市场情绪: bullish
新闻总数: 25
正面/负面/中性: 15/3/7
热门关键词: 茅台, 业绩, 增长, 分红, 价值投资
```

### 4.2 资金流向分析

```python
"""
资金流向分析示例
追踪主力资金流入流出情况
"""
import asyncio
from src.agents.business.hot_spot.capital_flow_ai import CapitalFlowAI

async def main():
    # 创建AI实例
    ai = CapitalFlowAI()

    # 分析资金流向
    result = await ai.analyze(
        stock_code="600519",
        market="sh",  # 上海证券交易所
        days=5
    )

    # 查看结果
    print(f"资金流向: {result.capital_trend}")
    print(f"主力净流入: {result.main_net_inflow:.2f}万元")
    print(f"散户净流入: {result.retail_net_inflow:.2f}万元")
    print(f"机构评级: {result.institution_rating}")

asyncio.run(main())
```

### 4.3 估值分析

```python
"""
估值与投资建议示例
综合评估股票的内在价值和投资建议
"""
import asyncio
from src.agents.business.target.valuation_and_recommendation_ai import ValuationAndRecommendationAI

async def main():
    # 创建AI实例
    ai = ValuationAndRecommendationAI()

    # 估值分析
    result = await ai.analyze(stock_code="600519")

    # 查看结果
    print(f"内在价值: {result.intrinsic_value:.2f}元")
    print(f"当前价格: {result.current_price:.2f}元")
    print(f"安全边际: {result.safety_margin:.2f}%")
    print(f"投资建议: {result.recommendation}")
    print(f"置信度: {result.confidence:.2f}%")

asyncio.run(main())
```

### 4.4 批量分析多只股票

```python
"""
批量分析示例
分析多只股票的市场情绪
"""
import asyncio
from src.agents.business.hot_spot.market_sentiment_ai import MarketSentimentAI

async def analyze_batch(stock_codes):
    """批量分析股票"""
    ai = MarketSentimentAI()

    results = []
    for code in stock_codes:
        try:
            result = await ai.analyze(stock_code=code, days=7)
            results.append({
                "code": code,
                "sentiment": result.sentiment_index,
                "mood": result.market_mood,
                "news_count": result.news_count
            })
        except Exception as e:
            print(f"分析{code}失败: {e}")

    return results

async def main():
    # 分析多只股票
    stocks = ["600519", "000001", "601669", "600036"]
    results = await analyze_batch(stocks)

    # 打印结果
    print("\n批量分析结果:")
    print("-" * 60)
    for r in results:
        print(f"{r['code']}: 情感指数={r['sentiment']:.2f}, 情绪={r['mood']}, 新闻={r['news_count']}条")

asyncio.run(main())
```

---

## 5. 运行测试

### 5.1 运行所有测试

```bash
# 进入项目目录
cd C:\AI-Agent-Local\Agent_Army

# 运行所有测试
pytest tests/ -v

# 运行测试并显示覆盖率
pytest tests/ --cov=. --cov-report=html
```

### 5.2 运行特定Agent测试

```bash
# 市场情绪AI测试
pytest tests/test_market_sentiment_ai.py -v

# 资金流向AI测试
pytest tests/test_capital_flow_ai.py -v

# 估值分析AI测试
pytest tests/test_valuation_model_ai.py -v
```

### 5.3 运行集成测试

```bash
# v2配置集成测试
pytest tests/test_v2_integration.py -v

# 完整工作流测试
pytest tests/test_complete_workflow.py -v
```

### 5.4 测试结果示例

```
tests/test_market_sentiment_ai.py::test_analyze PASSED [100%]
tests/test_capital_flow_ai.py::test_analyze PASSED [100%]
tests/test_valuation_model_ai.py::test_analyze PASSED [100%]

========================= 3 passed in 2.5s =========================
```

---

## 6. Web界面使用

### 6.1 启动Web界面

**方式1: 双击启动（Windows）**
```
双击桌面上的 "Agent Army Web" 图标
或双击项目目录下的 start_web.bat 文件
```

**方式2: 命令行启动**
```bash
# 进入项目目录
cd C:\AI-Agent-Local\Agent_Army

# 启动Web应用
streamlit run web_app.py

# 或指定端口
streamlit run web_app.py --server.port 8501
```

**方式3: 使用批处理脚本**
```bash
# 运行启动脚本
./start_web.bat
```

### 6.2 访问Web界面

```
浏览器访问: http://localhost:8501
```

### 6.3 Web界面功能

| 页面 | 功能 | 状态 |
|------|------|------|
| 🏠 **主页** | 项目概览、组织架构、Phase进度 | ✅ 可用 |
| 🤖 **Agent状态** | 管理层Agent状态监控、能力展示 | ✅ 可用 |
| 📋 **任务管理** | 下达任务、查看历史 | ✅ 可用 |
| 📊 **报告查看** | 投资分析报告 | ✅ 可用 |
| ⚙️ **系统配置** | 配置文件检查、环境变量 | ✅ 可用 |

### 6.4 创建分析任务

```
1. 访问 http://localhost:8501
2. 点击左侧菜单 "任务管理"
3. 选择任务类型（市场情绪分析/资金流向分析/估值分析）
4. 输入股票代码（例如：600519）
5. 选择分析周期
6. 点击 "创建任务" 按钮
7. 等待分析完成，查看结果
```

---

## 7. 常见问题

### Q1: Yahoo Finance是否支持A股？

**A**: ✅ 优秀支持

**股票代码格式**:
- 上海证券交易所: `XXXXXX.SS`（例如：`600519.SS`）
- 深圳证券交易所: `XXXXXX.SZ`（例如：`000001.SZ`）

**示例**:
```python
from src.core.tools.data_source import YahooFinanceTool

tool = YahooFinanceTool()
data = tool.get_stock_info("600519.SS")
print(data)
```

### Q2: 如何获取实时行情？

**A**: 使用YahooFinanceTool的实时行情接口

```python
from src.core.tools.data_source import YahooFinanceTool

tool = YahooFinanceTool()

# 获取实时报价
quote = tool.get_realtime_quote("600519.SS")
print(f"当前价格: {quote['price']}")
print(f"涨跌幅: {quote['change_percent']}%")
```

### Q3: 测试失败怎么办？

**A**: 检查以下几点

1. **依赖未安装**:
```bash
pip install -r requirements.txt
```

2. **API密钥未配置**:
```bash
# 检查.env文件
cat .env
```

3. **网络问题**: 使用Mock测试避免网络调用
```bash
# 使用Mock模式运行测试
pytest tests/test_market_sentiment_ai.py -v --mock-mode
```

4. **Python版本过低**: 升级到Python 3.10+

### Q4: 如何选择AI模型？

**A**: 系统自动选择最优模型

**默认策略**:
- **简单任务** → 智谱GLM-4.7（免费，速度快）
- **复杂推理** → 智谱GLM-5（高质量，仍在套餐内）
- **代码生成** → codegeex-4（专业代码模型）
- **高质量场景** → OpenAI GPT-4o（付费，质量最高）

**手动指定模型**:
```python
from src.core.config import get_model_name

# 查询Agent使用的模型
model = get_model_name("market_sentiment")
print(f"市场情绪AI使用: {model}")
```

### Q5: 如何查看日志？

**A**: 日志文件位置

```bash
# 日志目录
logs/

# 主要日志文件
logs/agent_army.log           # 主日志
logs/error.log                # 错误日志
logs/performance.log          # 性能日志

# 实时查看日志（Linux/Mac）
tail -f logs/agent_army.log

# Windows查看日志
Get-Content logs/agent_army.log -Wait
```

### Q6: 如何减少API调用成本？

**A**: 使用缓存机制

```python
from src.core.utils.cache import CacheManager

# 启用缓存（默认已启用）
cache = CacheManager()

# 缓存命中时不调用API
result = cache.get("cache_key")
if result is None:
    # 缓存未命中，调用API
    result = await ai.analyze(stock_code="600519")
    cache.set("cache_key", result, ttl=3600)  # 缓存1小时
```

**成本优化策略**:
- ✅ 分析结果缓存（TTL: 1小时）
- ✅ API调用节流（避免限流）
- ✅ 优先使用国产模型（智谱/DeepSeek）
- ✅ 批量分析（减少重复调用）

### Q7: 如何添加自定义Agent？

**A**: 继承BaseBusinessAgent

```python
from src.agents.business.base_business_agent import BaseBusinessAgent

class MyCustomAgent(BaseBusinessAgent):
    """自定义Agent"""

    def __init__(self, config=None):
        super().__init__(
            name="我的自定义AI",
            role="描述Agent职责",
            corps="自定义军团",
            analysis_type="自定义分析类型",
            config=config
        )

    async def analyze(self, stock_code: str, **kwargs):
        """实现分析逻辑"""
        # 1. 获取数据
        # 2. 分析处理
        # 3. 返回结果
        pass
```

详细教程: [Agent开发指南](AGENT_USAGE_GUIDE.md)

---

## 📚 进阶教程

- [Agent使用指南](AGENT_USAGE_GUIDE.md) - 24个Agent详细说明
- [v2配置指南](CONFIG_V2_GUIDE.md) - GLM包月版配置
- [架构设计文档](ARCHITECTURE.md) - 系统架构详解
- [API参考文档](API.md) - 完整API文档

---

## ✅ 快速启动检查清单

启动前确认:

- [ ] Python 3.10+ 已安装
- [ ] 所有依赖已安装 (`pip install -r requirements.txt`)
- [ ] API密钥已配置 (.env文件)
- [ ] 配置验证通过 (`python verify_config_switch.py`)
- [ ] 测试通过 (`pytest tests/ -v`)
- [ ] Web界面可以访问 (`http://localhost:8501`)

---

## 🎉 开始使用

**1. 验证环境**
```bash
python verify_config_switch.py
```

**2. 启动Web界面**
```bash
双击 start_web.bat
```

**3. 访问应用**
```
http://localhost:8501
```

**4. 创建第一个分析任务**
- 选择 "市场情绪分析"
- 输入股票代码: `600519`
- 点击 "创建任务"

---

**祝你使用愉快！🚀**

如有问题，请参考 [常见问题](#7-常见问题) 或查看完整文档。

---

**最后更新**: 2026-03-15
**版本**: 1.3.0
**维护**: Agent Army Team
