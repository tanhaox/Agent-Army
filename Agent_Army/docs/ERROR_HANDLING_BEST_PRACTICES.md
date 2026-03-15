# Agent Army - 错误处理和告警最佳实践指南

**创建日期**: 2026-03-15
**目的**: 统一所有Agent的错误处理和日志规范

---

## 📋 已有的错误处理机制

### 1. BaseAgent 基类

**位置**: `src/core/base_agent.py`

**已实现的错误处理**:
```python
async def run(self, task: str, **kwargs) -> Any:
    """运行Agent(带状态管理)"""
    try:
        # 更新状态为忙碌
        self.state.status = "busy"

        # 执行任务
        result = await self.execute(task, **kwargs)

        # 更新状态为空闲
        self.state.status = "idle"
        self.state.completed_tasks += 1

        return result

    except Exception as e:
        # 更新状态为错误
        self.state.status = "error"
        self.state.failed_tasks += 1

        # 记录错误日志
        self.logger.error(
            f"任务执行失败",
            agent=self.name,
            task=task,
            error=str(e)
        )
        raise
```

**功能**:
- ✅ 自动捕获异常
- ✅ 更新Agent状态
- ✅ 记录结构化日志
- ✅ 统计失败次数

---

### 2. 日志系统

**位置**: `src/core/logger.py`

**已实现的功能**:
- ✅ 使用 structlog（专业日志库）
- ✅ 结构化日志（JSON格式）
- ✅ 多级别日志（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- ✅ 日志文件分离（agent-army.log, error.log）
- ✅ 控制台彩色输出
- ✅ 时间戳自动添加

---

## 🚀 错误处理最佳实践

### 1. Agent 层面的错误处理

#### ✅ 推荐做法：使用基类的 run() 方法

```python
class MyAgent(BaseAgent):
    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        try:
            # 1. 参数验证
            stock_code = kwargs.get('stock_code')
            if not stock_code:
                raise ValueError("缺少必要参数: stock_code")

            # 2. 记录开始日志
            self.logger.info(f"开始分析股票: {stock_code}")

            # 3. 执行业务逻辑
            result = await self._analyze_stock(stock_code)

            # 4. 记录成功日志
            self.logger.info(
                f"股票分析完成",
                stock_code=stock_code,
                result_summary=self._summarize_result(result)
            )

            return result

        except ValueError as e:
            # 参数错误：记录警告并返回默认值
            self.logger.warning(f"参数错误: {e}")
            return {"error": str(e)}

        except Exception as e:
            # 其他错误：记录详细信息
            self.logger.error(
                f"分析失败",
                stock_code=stock_code,
                error=str(e),
                error_type=type(e).__name__
            )
            # 重新抛出异常，让基类处理
            raise
```

#### ❌ 不推荐做法：在 execute() 中直接捕获所有异常

```python
async def execute(self, task: str, **kwargs) -> Any:
    try:
        result = await some_operation()
        return result
    except Exception as e:
        # ❌ 不要在这里直接吞掉异常
        return {"error": str(e)}  # 这样基类无法统计失败次数
```

---

### 2. 工具层面的错误处理

#### ✅ 推荐做法：返回统一格式的错误

```python
class MyTool:
    async def fetch_data(self, stock_code: str) -> Dict[str, Any]:
        """获取数据"""
        try:
            data = await api_call(stock_code)

            # 验证数据
            if not data or 'error' in data:
                raise Exception(f"API返回错误: {data}")

            return data

        except Exception as e:
            self.logger.error(f"获取数据失败: {stock_code}", error=str(e))

            # 返回统一格式的错误
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "data_source": "MyTool"
            }
```

#### ✅ Agent使用工具时应该检查错误

```python
class MyAgent(BaseAgent):
    async def execute(self, task: str, **kwargs) -> Any:
        tool = MyTool()
        result = await tool.fetch_data(stock_code)

        # 检查工具是否返回错误
        if not result.get("success", True):
            # 工具失败，降级到默认值
            self.logger.warning(f"工具调用失败，使用默认值: {result.get('error')}")
            return self._get_default_data(stock_code)

        # 处理正常数据
        return self._process_data(result)
```

---

### 3. 日志记录最佳实践

#### ✅ 推荐做法：使用结构化日志

```python
# ✅ 使用关键字参数
self.logger.info(
    "股票分析完成",
    stock_code=stock_code,
    industry=industry_name,
    score=valuation_score,
    data_source="Tushare"
)

# ❌ 不要使用字符串拼接
self.logger.info(f"股票 {stock_code} 分析完成，评分 {score}")  # 不便于解析
```

#### ✅ 推荐做法：日志级别使用

```python
# DEBUG: 详细的调试信息（开发阶段）
self.logger.debug(f"API请求参数: {params}")

# INFO: 重要的业务流程节点
self.logger.info(f"开始分析股票: {stock_code}")

# WARNING: 警告信息（不影响功能）
self.logger.warning(f"使用默认数据源，数据可能不准确")

# ERROR: 错误信息（功能失败）
self.logger.error(f"API调用失败", error=str(e))

# CRITICAL: 严重错误（系统无法继续运行）
self.logger.critical(f"数据库连接失败，系统无法运行")
```

---

## 🔔 错误告警机制

### 1. 邮件告警（推荐）

**配置**: 在 `config/logging.yaml` 中配置邮件处理器

```python
# src/core/utils/alerts.py
import smtplib
from email.mime.text import MIMEText

class EmailAlerter:
    """邮件告警器"""

    def __init__(self, smtp_server: str, from_addr: str, to_addr: str):
        self.smtp_server = smtp_server
        self.from_addr = from_addr
        self.to_addr = to_addr

    async def send_alert(self, subject: str, message: str):
        """发送告警邮件"""
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = self.from_addr
        msg['To'] = self.to_addr

        # 发送邮件
        with smtplib.SMTP(self.smtp_server) as server:
            server.send_message(msg)
```

**使用**:
```python
# 在关键Agent中添加告警
class CriticalAgent(BaseAgent):
    async def execute(self, task: str, **kwargs) -> Any:
        try:
            result = await self._critical_operation()
            return result
        except Exception as e:
            # 发送告警
            await self.alerter.send_alert(
                subject=f"❌ Agent失败: {self.name}",
                message=f"任务: {task}\n错误: {str(e)}"
            )
            raise
```

---

### 2. 企业微信/钉钉告警（可选）

```python
# src/core/utils/webhook_alerter.py
import aiohttp

class WebhookAlerter:
    """Webhook告警器（企业微信/钉钉）"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_alert(self, message: str):
        """发送Webhook告警"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                json={"text": message}
            ) as response:
                if response.status != 200:
                    print(f"告警发送失败: {response.status}")
```

---

## 📊 错误统计和监控

### 1. 现有的统计机制

**BaseAgent 已实现的统计**:
- `completed_tasks`: 成功任务数
- `failed_tasks`: 失败任务数
- `status`: 当前状态（idle/busy/error）

**使用示例**:
```python
agent = MyAgent()
agent.state.completed_tasks  # 成功任务数
agent.state.failed_tasks     # 失败任务数
agent.state.status           # 当前状态
```

### 2. 添加错误率监控

```python
def get_error_rate(self) -> float:
    """获取错误率"""
    total = self.state.completed_tasks + self.state.failed_tasks
    if total == 0:
        return 0.0
    return self.state.failed_tasks / total * 100
```

---

## ✅ 验收清单

### Agent 层面

- [ ] 所有Agent继承自 BaseAgent
- [ ] 使用 `run()` 方法执行任务（而非直接调用 `execute()`）
- [ ] 在 `execute()` 中添加参数验证
- [ ] 区分不同类型的异常（ValueError, KeyError, APIError等）
- [ ] 使用结构化日志记录关键信息

### 工具层面

- [ ] 工具方法返回统一格式的错误（success + error + error_type）
- [ ] 所有工具方法都有完整的异常处理
- [ ] 工具失败时记录详细日志

### 日志层面

- [ ] 使用 structlog 记录结构化日志
- [ ] 正确使用日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- [ ] 日志中包含关键上下文信息（stock_code, agent_name等）
- [ ] 敏感信息过滤（API密钥、密码等）

---

## 🚀 下一步

### 立即执行

1. **检查现有Agent的错误处理**
   - 运行测试：`pytest tests/ -v`
   - 查看日志文件：`tail -f logs/error.log`

2. **添加关键Agent的告警**
   - 优先级：Commander Agent（核心）、重要业务Agent
   - 告警方式：企业微信/钉钉 Webhook

3. **完善日志格式**
   - 确保所有日志包含关键字段
   - 添加统一的日志前缀（如 `[AGENT_ERROR]`）

---

**文档完成时间**: 2026-03-15
**维护者**: Agent Army 团队
