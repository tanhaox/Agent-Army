# 市场情绪AI (MarketSentimentAI) 开发报告

## 📋 任务概述

**任务名称**: 开发市场情绪AI (MarketSentimentAI)

**文件位置**: `src/agents/business/hot_spot/market_sentiment_ai.py`

**开发日期**: 2026-03-15

**开发状态**: ✅ 完成

---

## 🎯 核心功能

### 职责
- 分析市场情绪，计算情感指数(0-100)
- 使用NewsTool获取新闻数据
- 使用NLPTool进行情感分析
- 计算整体市场情绪指数

### 输入
- 股票代码 (6位数字)
- 分析天数 (可选，默认7天)

### 输出
- 情感指数 (0-100)
- 市场情绪评级 (bullish/neutral/bearish)
- 新闻统计 (正面/负面/中性数量)
- 关键词提取
- 风险提示
- 投资建议

---

## 🏗️ 技术架构

### 继承关系
```
BaseAgent (基础Agent)
    ↓
BusinessAgent (业务Agent基类)
    ↓
MarketSentimentAI (市场情绪AI)
```

### 工具集成
- **NewsTool**: 获取股票新闻数据
- **NLPTool**: 进行情感分析和关键词提取

### 数据流
```
股票代码 → NewsTool获取新闻 → NLPTool分析情感 → 计算指数 → 生成报告
```

---

## 📦 返回值结构

### SentimentAnalysisResult (Pydantic模型)

```python
{
    "stock_code": "600519",                    # 股票代码
    "sentiment_index": 65.5,                   # 情感指数(0-100)
    "market_mood": "bullish",                  # 市场情绪(bullish/neutral/bearish)
    "news_count": 10,                          # 新闻总数
    "positive_count": 6,                       # 正面新闻数
    "negative_count": 2,                       # 负面新闻数
    "neutral_count": 2,                        # 中性新闻数
    "timestamp": "2026-03-15T10:30:00",       # 分析时间
    "analysis_period": "7天",                  # 分析周期
    "sentiment_details": {...},                # 详细情感数据
    "top_keywords": ["增长", "利好", ...]      # 热门关键词
}
```

### AnalysisResult (业务Agent标准返回值)

```python
{
    "agent_name": "市场情绪AI",
    "analysis_type": "市场情绪分析",
    "conclusion": "市场情绪乐观（指数65.0分）...",
    "confidence": 0.85,
    "details": {
        "sentiment_index": 65.0,
        "market_mood": "bullish",
        ...
    },
    "risks": ["新闻样本较少..."],
    "recommendations": ["市场情绪乐观，可适当关注"]
}
```

---

## 🔧 核心方法

### 1. analyze() - 主要分析方法

```python
async def analyze(
    self,
    stock_code: str,
    days: Optional[int] = None,
    **kwargs
) -> AnalysisResult
```

**功能**: 分析市场情绪（实现基类的抽象方法）

**流程**:
1. 验证股票代码
2. 获取新闻数据
3. 分析每条新闻的情感
4. 计算综合情感指数
5. 判断市场情绪
6. 提取关键词
7. 生成结论、风险提示和建议

**示例**:
```python
ai = MarketSentimentAI()
result = await ai.analyze("600519", days=7)
print(result.conclusion)  # "市场情绪乐观（指数65.0分）..."
```

---

### 2. get_sentiment_result() - 获取标准格式结果

```python
async def get_sentiment_result(
    self,
    stock_code: str,
    days: Optional[int] = None
) -> SentimentAnalysisResult
```

**功能**: 返回Pydantic模型的标准格式结果

**示例**:
```python
ai = MarketSentimentAI()
result = await ai.get_sentiment_result("600519", days=7)

print(result.sentiment_index)  # 65.0
print(result.market_mood)      # "bullish"
print(result.top_keywords)     # ["增长", "利好", ...]
```

---

### 3. _calculate_sentiment_index() - 计算情感指数

```python
def _calculate_sentiment_index(
    self,
    sentiment_results: Dict[str, Any]
) -> float
```

**算法**: 加权平均
- 分数越高，权重越大
- 权重 = score / 50.0
- 指数 = Σ(score × weight) / Σ(weight)

**返回**: 0-100之间的浮点数

---

### 4. _determine_market_mood() - 判断市场情绪

```python
def _determine_market_mood(self, sentiment_index: float) -> str
```

**规则**:
- `sentiment_index >= 60.0` → "bullish" (乐观)
- `sentiment_index <= 40.0` → "bearish" (悲观)
- `40.0 < index < 60.0` → "neutral" (中性)

**可配置阈值**:
```python
custom_config = {
    "sentiment_thresholds": {
        "bullish": 70.0,  # 自定义阈值
        "bearish": 30.0
    }
}
ai = MarketSentimentAI(config=custom_config)
```

---

## 📝 使用示例

### 示例1: 基本使用

```python
from src.agents.business.hot_spot.market_sentiment_ai import MarketSentimentAI

# 创建AI实例
ai = MarketSentimentAI()

# 分析市场情绪
result = await ai.analyze("600519", days=7)

# 打印结果
print(f"情感指数: {result.details['sentiment_index']}")
print(f"市场情绪: {result.details['market_mood']}")
print(f"结论: {result.conclusion}")
```

---

### 示例2: 获取标准格式结果

```python
from src.agents.business.hot_spot.market_sentiment_ai import MarketSentimentAI

ai = MarketSentimentAI()
result = await ai.get_sentiment_result("600519", days=7)

# 访问所有字段
print(result.stock_code)        # "600519"
print(result.sentiment_index)   # 65.0
print(result.market_mood)       # "bullish"
print(result.news_count)        # 5
print(result.positive_count)    # 3
print(result.top_keywords)      # ["增长", "利好", ...]
```

---

### 示例3: 使用便捷函数

```python
from src.agents.business.hot_spot.market_sentiment_ai import analyze_market_sentiment

# 直接调用，无需创建实例
result = await analyze_market_sentiment("600519", days=7)

print(f"情感指数: {result.sentiment_index}")
print(f"市场情绪: {result.market_mood}")
```

---

### 示例4: 批量分析

```python
from src.agents.business.hot_spot.market_sentiment_ai import MarketSentimentAI

stocks = ["600519", "000858", "000333"]
ai = MarketSentimentAI()

results = []
for stock_code in stocks:
    result = await ai.get_sentiment_result(stock_code, days=7)
    results.append(result)

# 排序
results.sort(key=lambda r: r.sentiment_index, reverse=True)

for i, result in enumerate(results, 1):
    print(f"{i}. {result.stock_code}: {result.sentiment_index:.1f}分 ({result.market_mood})")
```

---

### 示例5: 自定义配置

```python
from src.agents.business.hot_spot.market_sentiment_ai import MarketSentimentAI

custom_config = {
    "default_days": 14,
    "sentiment_thresholds": {
        "bullish": 70.0,  # 更严格
        "bearish": 30.0
    }
}

ai = MarketSentimentAI(config=custom_config)
result = await ai.get_sentiment_result("600519", days=14)
```

---

## ✅ 验收标准

### 代码质量
- ✅ 继承BaseBusinessAgent
- ✅ 使用工具库（不直接调用API）
- ✅ 包含完整文档和日志
- ✅ 异常处理完善

### 功能完整性
- ✅ 分析市场情绪
- ✅ 计算情感指数(0-100)
- ✅ 判断市场情绪(bullish/neutral/bearish)
- ✅ 提取关键词
- ✅ 生成风险提示和建议
- ✅ 返回标准格式

### 测试覆盖
- ✅ 12个测试用例全部通过
- ✅ 覆盖核心功能和边界情况
- ✅ 工具集成测试通过

---

## 🧪 测试结果

### 测试文件
`tests/test_market_sentiment_ai.py`

### 测试覆盖
1. ✅ 初始化测试
2. ✅ 基本分析功能测试
3. ✅ 标准格式结果测试
4. ✅ 市场情绪判定测试
5. ✅ 关键词提取测试
6. ✅ 风险提示和建议测试
7. ✅ 置信度计算测试
8. ✅ 无效股票代码测试
9. ✅ 便捷函数测试
10. ✅ 工具集成测试
11. ✅ 继承测试
12. ✅ 自定义配置测试

### 测试命令
```bash
python tests/test_market_sentiment_ai.py
```

---

## 📊 示例输出

```
📊 市场情绪分析结果:
   Agent名称: 市场情绪AI
   分析类型: 市场情绪分析
   情感指数: 65.0分
   市场情绪: bullish
   新闻数量: 5
   正面新闻: 3
   负面新闻: 0
   中性新闻: 2

   分析结论: 市场情绪乐观（指数65.0分），正面新闻3条，负面新闻0条。投资者信心较强，市场氛围积极。
   置信度: 25.00%
```

---

## 🚀 演示脚本

**位置**: `examples/market_sentiment_demo.py`

**运行**:
```bash
python examples/market_sentiment_demo.py
```

**内容**:
- 示例1: 基本使用
- 示例2: 获取标准格式结果
- 示例3: 使用便捷函数
- 示例4: 批量分析多只股票
- 示例5: 使用自定义配置
- 示例6: 风险分析

---

## 📚 相关文档

### 基类文档
- `src/agents/business/base_business_agent.py` - BusinessAgent基类

### 工具文档
- `src/core/tools/data_source/news_tool.py` - NewsTool
- `src/core/tools/ai_service/nlp_tool.py` - NLPTool

### 参考Agent
- `src/agents/business/hot_spot/dragon_tiger_ai.py` - 龙虎榜AI

---

## 🔍 与旧版本对比

### 旧版本 (已废弃)
- ❌ 继承BaseAgent（而非BaseBusinessAgent）
- ❌ 直接调用API（而非使用工具库）
- ❌ 返回Dict（而非Pydantic模型）
- ❌ 缺少标准analyze()方法

### 新版本 (当前)
- ✅ 继承BaseBusinessAgent
- ✅ 使用NewsTool和NLPTool
- ✅ 返回SentimentAnalysisResult (Pydantic)
- ✅ 实现标准analyze()方法
- ✅ 符合业务Agent规范

---

## 🎉 总结

### 完成情况
- ✅ 代码完成，符合规范
- ✅ 使用工具库（不直接调用API）
- ✅ 包含完整文档和日志
- ✅ 可运行且输出正确格式
- ✅ 12个测试用例全部通过
- ✅ 6个使用示例演示

### 核心特性
- 🎯 继承BaseBusinessAgent，符合业务Agent规范
- 🔧 集成NewsTool和NLPTool，使用工具库
- 📊 返回标准Pydantic模型，类型安全
- 🚀 提供便捷函数，开箱即用
- ⚙️ 支持自定义配置，灵活可扩展
- 📝 完整的文档和测试，易于维护

### 下一步
- 接入真实新闻API（当前使用模拟数据）
- 接入真实NLP服务（当前使用关键词匹配）
- 添加更多情绪指标（如社交媒体、论坛等）
- 优化情感分析算法（提高准确性）

---

**开发完成时间**: 2026-03-15 06:40

**测试状态**: ✅ 所有测试通过

**文档状态**: ✅ 完整
