# 📚 Agent Army 最佳实践指南

## 目录

1. [设计原则](#设计原则)
2. [使用建议](#使用建议)
3. [性能优化](#性能优化)
4. [错误处理](#错误处理)
5. [数据管理](#数据管理)
6. [测试策略](#测试策略)
7. [安全考虑](#安全考虑)

---

## 设计原则

### 1. 单一职责原则

每个Agent专注一个特定领域：

```python
✅ 好的做法：
valuation_ai = ValuationPricingAI()  # 只负责估值定价
timing_ai = TimingJudgmentAI()       # 只负责时机判断

❌ 避免：
class SuperAI:
    """一个Agent做所有事情"""
    def analyze_everything(self):
        pass
```

### 2. 异步优先

使用异步编程提高并发性能：

```python
✅ 好的做法：
async def analyze_multiple():
    tasks = [
        ai.analyze(stock_code)
        for stock_code in stock_pool
    ]
    results = await asyncio.gather(*tasks)

❌ 避免：
def analyze_multiple():
    results = []
    for stock_code in stock_pool:
        result = ai.analyze(stock_code)  # 同步阻塞
        results.append(result)
```

### 3. 标准化接口

统一使用 `AnalysisResult` 返回：

```python
✅ 好的做法：
return AnalysisResult(
    agent_name="估值定价AI",
    analysis_type="valuation_pricing",
    conclusion="目标价1850元",
    confidence=0.75,
    details={...},
    risks=[...],
    recommendations=[...]
)

❌ 避免：
return {
    "price": 1850,
    "ups": 2.8,
    # 缺少标准字段
}
```

---

## 使用建议

### 1. Agent组合使用

不同Agent协同工作：

```python
async def complete_analysis(stock_code: str, current_price: float):
    """完整的投资分析流程"""

    # 步骤1: 估值定价
    valuation_ai = ValuationPricingAI()
    valuation = await valuation_ai.analyze(stock_code, current_price)

    # 步骤2: 综合评估（使用步骤1的结果）
    evaluation_ai = ComprehensiveEvaluationAI()
    evaluation = await evaluation_ai.analyze(
        stock_code,
        prediction_data={
            "target_price": valuation.details['target_pricing']['target_price']
        }
    )

    # 步骤3: 时机判断（使用步骤1-2的评分）
    timing_ai = TimingJudgmentAI()
    timing = await timing_ai.analyze(
        stock_code,
        current_price
    )

    return {
        "valuation": valuation,
        "evaluation": evaluation,
        "timing": timing
    }
```

### 2. 参数验证

始终验证输入参数：

```python
async def safe_analysis(stock_code: str, current_price: float):
    """带参数验证的分析"""

    # 验证股票代码
    if not isinstance(stock_code, str) or len(stock_code) != 6:
        raise ValueError(f"无效的股票代码: {stock_code}")

    if not stock_code.isdigit():
        raise ValueError(f"股票代码必须是数字: {stock_code}")

    # 验证价格
    if not isinstance(current_price, (int, float)) or current_price <= 0:
        raise ValueError(f"无效的价格: {current_price}")

    # 执行分析
    ai = ValuationPricingAI()
    return await ai.analyze(stock_code, current_price)
```

### 3. 置信度阈值

根据置信度调整决策：

```python
def make_decision(result: AnalysisResult) -> str:
    """基于置信度的决策"""

    confidence = result.confidence
    score = result.details.get('comprehensive_score', 0)

    if confidence >= 0.8 and score >= 80:
        return "强烈推荐"
    elif confidence >= 0.7 and score >= 70:
        return "推荐"
    elif confidence >= 0.6 and score >= 60:
        return "中性"
    else:
        return "不推荐"
```

---

## 性能优化

### 1. 并发控制

限制并发数量避免资源耗尽：

```python
import asyncio

async def analyze_with_semaphore(stock_pool: list, max_concurrent: int = 10):
    """使用信号量控制并发"""

    semaphore = asyncio.Semaphore(max_concurrent)
    ai = ValuationPricingAI()

    async def analyze_one(stock_code: str):
        async with semaphore:
            return await ai.analyze(stock_code, current_price=100.0)

    tasks = [analyze_one(code) for code in stock_pool]
    results = await asyncio.gather(*tasks)
    return results
```

### 2. 结果缓存

缓存重复分析结果：

```python
from functools import lru_cache

class CachedAnalysis:
    """带缓存的分析"""

    def __init__(self):
        self.ai = ValuationPricingAI()
        self.cache = {}

    async def analyze(self, stock_code: str, current_price: float):
        """带缓存的分析"""

        # 检查缓存
        cache_key = f"{stock_code}_{current_price}"
        if cache_key in self.cache:
            print(f"使用缓存结果: {stock_code}")
            return self.cache[cache_key]

        # 执行分析
        result = await self.ai.analyze(stock_code, current_price)

        # 存入缓存
        self.cache[cache_key] = result
        return result
```

### 3. 批量处理

批量处理减少开销：

```python
async def batch_analysis(stock_pool: list):
    """批量分析"""

    # 准备数据
    ai = ValuationPricingAI()

    # 批量执行
    results = []
    for i in range(0, len(stock_pool), 10):  # 每批10个
        batch = stock_pool[i:i+10]
        tasks = [
            ai.analyze(code, price)
            for code, price in batch
        ]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)

    return results
```

---

## 错误处理

### 1. 异常捕获

完整捕获各类异常：

```python
async def robust_analysis(stock_code: str, current_price: float):
    """健壮的分析（完整错误处理）"""

    ai = ValuationPricingAI()

    try:
        result = await ai.analyze(stock_code, current_price)
        return {"success": True, "result": result}

    except ValueError as e:
        # 参数错误
        ai.logger.error(f"参数错误: {e}")
        return {"success": False, "error": str(e), "type": "parameter"}

    except asyncio.TimeoutError:
        # 超时错误
        ai.logger.error("分析超时")
        return {"success": False, "error": "分析超时", "type": "timeout"}

    except Exception as e:
        # 未知错误
        ai.logger.exception(f"未知错误: {e}")
        return {"success": False, "error": str(e), "type": "unknown"}
```

### 2. 重试机制

自动重试失败的任务：

```python
async def analyze_with_retry(
    stock_code: str,
    current_price: float,
    max_retries: int = 3
):
    """带重试的分析"""

    ai = ValuationPricingAI()

    for attempt in range(max_retries):
        try:
            result = await ai.analyze(stock_code, current_price)
            return result

        except Exception as e:
            if attempt == max_retries - 1:
                # 最后一次尝试失败
                raise

            # 等待后重试
            await asyncio.sleep(2 ** attempt)  # 指数退避

            ai.logger.warning(
                f"分析失败，重试 {attempt + 1}/{max_retries}: {e}"
            )
```

### 3. 优雅降级

失败时提供默认结果：

```python
async def analyze_with_fallback(stock_code: str, current_price: float):
    """带降级的分析"""

    ai = ValuationPricingAI()

    try:
        result = await ai.analyze(stock_code, current_price)
        return result

    except Exception as e:
        # 返回保守的默认结果
        return AnalysisResult(
            agent_name="估值定价AI",
            analysis_type="valuation_pricing",
            conclusion="分析失败，建议谨慎投资",
            confidence=0.0,
            details={},
            risks=["分析失败，无法评估风险"],
            recommendations=["建议等待系统恢复后重新分析"]
        )
```

---

## 数据管理

### 1. 结果持久化

保存分析结果到文件：

```python
import json
from datetime import datetime

def save_analysis_result(result: AnalysisResult, filename: str):
    """保存分析结果"""

    data = {
        "timestamp": datetime.now().isoformat(),
        "agent_name": result.agent_name,
        "analysis_type": result.analysis_type,
        "conclusion": result.conclusion,
        "confidence": result.confidence,
        "details": result.details,
        "risks": result.risks,
        "recommendations": result.recommendations
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 使用
result = await ai.analyze("600519", 1800.0)
save_analysis_result(result, "analysis_600519_20260320.json")
```

### 2. 数据库存储

存储到数据库：

```python
import sqlite3

class AnalysisDatabase:
    """分析结果数据库"""

    def __init__(self, db_path: str = "analysis.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        """创建表"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                conclusion TEXT,
                confidence REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def save_result(self, result: AnalysisResult, stock_code: str):
        """保存结果"""
        self.conn.execute("""
            INSERT INTO analysis_results
            (stock_code, agent_name, analysis_type, conclusion, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, (
            stock_code,
            result.agent_name,
            result.analysis_type,
            result.conclusion,
            result.confidence
        ))
        self.conn.commit()
```

---

## 测试策略

### 1. 单元测试

为每个Agent编写单元测试：

```python
import pytest
from src.agents.business.prediction import ValuationPricingAI

@pytest.mark.asyncio
async def test_valuation_pricing():
    """测试估值定价AI"""

    ai = ValuationPricingAI()

    # 正常情况
    result = await ai.analyze("600519", 1800.0)
    assert result.agent_name == "估值定价AI"
    assert result.confidence > 0

    # 异常情况
    with pytest.raises(ValueError):
        await ai.analyze("invalid", 1800.0)
```

### 2. 集成测试

测试多个Agent协同工作：

```python
@pytest.mark.asyncio
async def test_full_workflow():
    """测试完整工作流"""

    # 步骤1: 估值
    valuation_ai = ValuationPricingAI()
    valuation = await valuation_ai.analyze("600519", 1800.0)

    # 步骤2: 评估（使用步骤1结果）
    evaluation_ai = ComprehensiveEvaluationAI()
    evaluation = await evaluation_ai.analyze(
        "600519",
        prediction_data={"target_price": valuation.details['target_pricing']['target_price']}
    )

    # 验证结果
    assert evaluation.details['comprehensive_score'] > 0
```

---

## 安全考虑

### 1. 输入验证

严格验证所有输入：

```python
def validate_stock_code(stock_code: str) -> bool:
    """验证股票代码"""

    # 长度检查
    if len(stock_code) != 6:
        return False

    # 数字检查
    if not stock_code.isdigit():
        return False

    # 范围检查（A股代码范围）
    if not (stock_code.startswith('6') or stock_code.startswith('0') or
            stock_code.startswith('3')):
        return False

    return True
```

### 2. 敏感信息保护

不要在日志中记录敏感信息：

```python
✅ 好的做法：
self.logger.info(f"分析股票: {stock_code}")

❌ 避免：
self.logger.info(f"用户{user_name}分析{stock_code}，资金{capital}")
```

### 3. 访问控制

实现权限控制：

```python
class SecureAnalysis:
    """带权限控制的分析"""

    def __init__(self):
        self.ai = ValuationPricingAI()

    async def analyze(self, stock_code: str, current_price: float, user_role: str):
        """带权限检查的分析"""

        # 检查权限
        if user_role not in ["admin", "analyst"]:
            raise PermissionError("无权限执行分析")

        # 执行分析
        return await self.ai.analyze(stock_code, current_price)
```

---

## 📚 更多资源

- 📖 [API参考文档](API-Reference.md)
- 🚀 [快速开始指南](Quick-Start-Guide.md)
- 💡 [示例代码](../examples/)

---

**最后更新**: 2026-03-20
**版本**: v1.0
