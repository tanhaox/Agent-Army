# 🔧 Agent Army 扩展指南

**版本**: 1.0.0
**更新时间**: 2026-03-14

---

## 📋 目录

1. [API接入指南](#1-api接入指南)
2. [Skill安装指南](#2-skill安装指南)

---

## 1. API接入指南

### 1.1 架构设计

**核心理念**：Agent不关心工具如何实现，只调用统一接口

```
┌─────────────────────────────────────┐
│         Agent（业务层）              │
│  - 不关心数据从哪来                  │
│  - 只关心业务逻辑                    │
└──────────────┬──────────────────────┘
               │ 调用统一接口
               ↓
┌─────────────────────────────────────┐
│        工具库（基础设施层）           │
│  - 封装所有API调用                   │
│  - 提供标准化数据                    │
│  - 自动选择数据源                    │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│          外部API                     │
│  - Tushare、东方财富                 │
│  - 智谱AI、DeepSeek                  │
└─────────────────────────────────────┘
```

### 1.2 如何接入新API？

#### 场景1：接入财务数据API（如Tushare）

**步骤1：安装依赖**
```bash
pip install tushare
```

**步骤2：修改工具代码**

文件：`src/core/tools/data_source/financial_tool.py`

```python
# 修改前（Line 66-68）
async def fetch_financial_data(self, stock_code: str, years: int = 3):
    # TODO: 接入真实API
    # 当前返回示例数据
    data = await self._fetch_sample_financial_data(stock_code, years)
    return data

# 修改后
async def fetch_financial_data(self, stock_code: str, years: int = 3):
    """获取财务数据（已接入Tushare API）"""
    import tushare as ts

    # 从配置读取API密钥
    api_key = self.config.get("tushare_api_key")
    pro = ts.pro_api(api_key)

    # 调用真实API
    df = pro.daily_basic(ts_code=stock_code, start_date='20230101')

    # 标准化数据格式
    data = self._standardize_tushare_data(df)

    return data
```

**步骤3：配置API密钥**

文件：`config/api_keys.yaml`

```yaml
# 在文件末尾添加
tushare:
  api_key: ${TUSHARE_API_KEY}  # 从环境变量读取
  base_url: https://api.tushare.pro

  # 数据源配置
  data_sources:
    - name: tushare_pro
      priority: 1  # 最高优先级
      enabled: true
```

**步骤4：设置环境变量**

Windows（PowerShell）:
```powershell
$env:TUSHARE_API_KEY = "your_api_key_here"
```

Linux/Mac:
```bash
export TUSHARE_API_KEY="your_api_key_here"
```

**步骤5：Agent自动感知 ✅**

**重要**：Agent**不需要修改任何代码**！

原因：
- Agent调用的是统一接口：`financial_tool.fetch_financial_data()`
- 工具内部实现改变，Agent无感知
- 配置文件自动加载

**验证方式**：

```python
# 测试工具
from src.core.tools.data_source import FinancialTool

tool = FinancialTool()
data = await tool.fetch_financial_data("600519")
print(data["stock_name"])  # 应该输出: 贵州茅台
```

---

#### 场景2：接入新闻数据API

**步骤1：修改工具代码**

文件：`src/core/tools/data_source/news_tool.py`

```python
# 修改 fetch_news 方法
async def fetch_news(self, stock_code: str, days: int = 7):
    """获取新闻（已接入东方财富API）"""
    import aiohttp

    # 东方财富API
    url = f"https://newsapi.eastmoney.com/kuaixun/v1/{stock_code}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            news_data = await response.json()

    # 标准化格式
    standardized_news = self._standardize_eastmoney_news(news_data)

    return standardized_news
```

**步骤2：更新配置**

文件：`config/api_keys.yaml`

```yaml
eastmoney:
  api_key: ${EASTMONEY_API_KEY}
  enabled: true
  rate_limit: 100  # 每分钟100次
```

**步骤3：Agent自动感知 ✅**

Agent调用：`news_tool.fetch_news()`，无需修改！

---

#### 场景3：接入大模型API（如智谱AI）

**步骤1：修改工具代码**

文件：`src/core/tools/ai_service/llm_tool.py`

```python
# 修改 chat 方法
async def chat(self, prompt: str, model: str = None):
    """调用大模型（已接入智谱AI）"""
    from zhipuai import ZhipuAI

    # 从配置读取
    api_key = self.config.get("zhipu_api_key")
    client = ZhipuAI(api_key=api_key)

    # 调用真实API
    response = client.chat.completions.create(
        model=model or "glm-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

**步骤2：配置已存在**

文件：`config/api_keys.yaml`（已有配置，只需设置环境变量）

```yaml
zhipu:
  api_key: ${ZHIPU_API_KEY}  # ← 已配置
```

**步骤3：设置环境变量**
```bash
export ZHIPU_API_KEY="your_zhipu_api_key"
```

**步骤4：Agent自动感知 ✅**

---

### 1.3 API配置管理

#### 配置文件位置

```
config/
├── api_keys.yaml       ← API密钥配置
├── database.yaml       ← 数据库配置
├── agents.yaml         ← Agent配置
└── logging.yaml        ← 日志配置
```

#### 配置读取方式

```python
from src.core.config import ConfigManager

# 初始化配置管理器
config_manager = ConfigManager("./config")

# 读取API配置
api_config = config_manager.get("api_keys")

# 获取具体配置
zhipu_key = api_config["zhipu"]["api_key"]
```

#### 环境变量管理

推荐使用 `.env` 文件（不提交到Git）：

文件：`.env`（在项目根目录）
```bash
# 大模型API
ZHIPU_API_KEY=your_zhipu_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
OPENAI_API_KEY=your_openai_key_here

# 数据API
TUSHARE_API_KEY=your_tushare_key_here
EASTMONEY_API_KEY=your_eastmoney_key_here
```

加载环境变量：
```python
from dotenv import load_dotenv
load_dotenv()  # 自动加载.env文件
```

---

### 1.4 Agent如何"感知"新API？

**答案：Agent不需要感知！**

**原因**：
1. **接口统一**：工具提供标准化接口
2. **实现隔离**：Agent只调用接口，不关心实现
3. **配置驱动**：API配置在YAML文件中管理

**示例**：

```python
# Agent代码（不需要修改）
class FinancialHealthAgent:
    def __init__(self):
        self.financial_tool = FinancialTool()  # 初始化工具

    async def analyze(self, stock_code: str):
        # 调用工具接口
        data = await self.financial_tool.fetch_financial_data(stock_code)
        # Agent不关心数据从哪来，只关心业务逻辑
        score = self._calculate_score(data)
        return score

# 工具代码（修改内部实现）
class FinancialTool:
    async def fetch_financial_data(self, stock_code: str):
        # 修改前：返回假数据
        # return self._sample_data()

        # 修改后：调用真实API
        return await self._call_tushare_api(stock_code)

# 结果：Agent自动获得真实数据能力！
```

---

### 1.5 多数据源支持

**场景**：同时接入多个数据源，自动选择最优

文件：`config/api_keys.yaml`

```yaml
financial_data:
  sources:
    - name: tushare
      priority: 1  # 最高优先级
      enabled: true
      api_key: ${TUSHARE_API_KEY}

    - name: eastmoney
      priority: 2
      enabled: true
      api_key: ${EASTMONEY_API_KEY}

    - name: local_cache
      priority: 3  # 降级方案
      enabled: true

  # 自动降级策略
  fallback:
    enabled: true
    retry_times: 3
    timeout: 10  # 秒
```

工具代码：
```python
class FinancialTool:
    async def fetch_financial_data(self, stock_code: str):
        # 按优先级尝试数据源
        for source in self.config["sources"]:
            if source["enabled"]:
                try:
                    data = await self._fetch_from_source(source, stock_code)
                    return data
                except Exception as e:
                    self.logger.warning(f"{source['name']}失败: {e}")
                    continue

        raise Exception("所有数据源都失败")
```

---

## 2. Skill安装指南

### 2.1 什么是Skill？

**Skill = 可复用的Agent能力模块**

示例：
- `technical_analysis_skill` - 技术分析能力
- `sentiment_analysis_skill` - 情感分析能力
- `risk_assessment_skill` - 风险评估能力

### 2.2 Skill目录结构

**标准Skill结构**：

```
skills/
└── technical_analysis_skill/
    ├── README.md           ← Skill说明文档（必需）
    ├── skill.yaml          ← Skill配置文件（必需）
    ├── __init__.py         ← Python包初始化
    ├── agent.py            ← Agent实现
    ├── tools.py            ← 工具实现（可选）
    ├── models.py           ← 数据模型（可选）
    ├── tests/              ← 测试用例
    │   └── test_agent.py
    └── requirements.txt    ← 依赖包（可选）
```

### 2.3 如何安装GitHub上的Skill？

#### 方式1：手动安装（推荐）

**步骤1：下载Skill**
```bash
cd C:\AI-Agent-Local\Agent_Army
git clone https://github.com/xxx/technical_analysis_skill.git skills/technical_analysis_skill
```

**步骤2：安装依赖**
```bash
cd skills/technical_analysis_skill
pip install -r requirements.txt
```

**步骤3：配置Skill**

文件：`config/skills.yaml`（新建）

```yaml
enabled_skills:
  - name: technical_analysis_skill
    enabled: true
    priority: 1
    config:
      period: 60  # 技术分析周期
      indicators:
        - MA
        - MACD
        - RSI
```

**步骤4：注册Skill到系统**

文件：`src/core/skill_manager.py`（新建）

```python
class SkillManager:
    """Skill管理器"""

    def __init__(self):
        self.skills = {}
        self._load_skills()

    def _load_skills(self):
        """加载所有已启用的Skill"""
        config = self._load_config("config/skills.yaml")

        for skill_config in config["enabled_skills"]:
            if skill_config["enabled"]:
                skill_name = skill_config["name"]
                skill_module = __import__(f"skills.{skill_name}.agent", fromlist=["Agent"])
                self.skills[skill_name] = skill_module.Agent(skill_config["config"])

    def get_skill(self, skill_name: str):
        """获取Skill实例"""
        return self.skills.get(skill_name)
```

**步骤5：Agent调用Skill**

```python
# 在Agent中使用Skill
from src.core.skill_manager import SkillManager

skill_manager = SkillManager()
tech_skill = skill_manager.get_skill("technical_analysis_skill")

# 调用Skill能力
result = await tech_skill.analyze("600519")
```

---

#### 方式2：使用Skill安装器（未来功能）

```bash
# 安装Skill
python scripts/install_skill.py --github https://github.com/xxx/technical_analysis_skill.git

# 列出已安装的Skill
python scripts/install_skill.py --list

# 卸载Skill
python scripts/install_skill.py --uninstall technical_analysis_skill
```

---

### 2.4 如何创建自己的Skill？

**步骤1：创建目录结构**

```bash
cd C:\AI-Agent-Local\Agent_Army\skills
mkdir my_custom_skill
cd my_custom_skill
```

**步骤2：编写Skill配置**

文件：`skill.yaml`

```yaml
name: my_custom_skill
version: 1.0.0
description: 我的自定义Skill
author: your_name

# Skill能力
capabilities:
  - name: custom_analysis
    description: 自定义分析
    input_type: stock_code
    output_type: analysis_result

# 依赖
dependencies:
  - numpy>=1.20.0
  - pandas>=1.3.0

# 配置项
config:
  threshold: 0.7
  period: 30
```

**步骤3：编写Agent代码**

文件：`agent.py`

```python
from src.core.base_agent import BaseAgent, AgentCapability

class MyCustomAgent(BaseAgent):
    """自定义Skill Agent"""

    def __init__(self, config: dict):
        super().__init__(
            name="自定义分析Agent",
            role="执行自定义分析",
            capabilities=[
                AgentCapability(
                    name="custom_analysis",
                    description="自定义分析能力",
                    input_type="stock_code",
                    output_type="analysis_result"
                )
            ],
            config=config
        )

    async def analyze(self, stock_code: str):
        """执行分析"""
        # 实现你的分析逻辑
        result = {
            "stock_code": stock_code,
            "score": 85.0,
            "recommendation": "BUY"
        }
        return result
```

**步骤4：编写README**

文件：`README.md`

```markdown
# My Custom Skill

## 功能说明
执行自定义分析

## 安装
```bash
pip install -r requirements.txt
```

## 使用方法
```python
from skills.my_custom_skill.agent import MyCustomAgent

agent = MyCustomAgent(config={})
result = await agent.analyze("600519")
```

## 配置项
- threshold: 阈值（默认0.7）
- period: 周期（默认30）
```

**步骤5：发布到GitHub**

```bash
git init
git add .
git commit -m "feat: 创建自定义Skill"
git remote add origin https://github.com/xxx/my_custom_skill.git
git push -u origin master
```

---

### 2.5 Skill与Agent的区别

| 对比项 | Agent | Skill |
|--------|-------|-------|
| **定位** | 业务逻辑单元 | 可复用能力模块 |
| **范围** | 系统内置 | 可外部安装 |
| **配置** | agents.yaml | skills.yaml |
| **管理** | 系统核心 | Skill Manager |
| **示例** | 市场情绪AI | 技术分析Skill |

**关系**：
```
Agent（业务逻辑）
  └── 调用 Skill（能力模块）
       └── 调用 Tool（基础设施）
```

---

## 3. 总结

### API接入流程

```
1. 安装依赖包
   ↓
2. 修改工具代码（TODO → 真实API）
   ↓
3. 配置API密钥（config/api_keys.yaml）
   ↓
4. 设置环境变量（.env文件）
   ↓
5. Agent自动感知 ✅（无需修改Agent代码）
```

### Skill安装流程

```
1. 下载Skill（git clone）
   ↓
2. 安装依赖（pip install -r requirements.txt）
   ↓
3. 配置Skill（config/skills.yaml）
   ↓
4. 注册到系统（SkillManager）
   ↓
5. Agent调用Skill ✅
```

---

## 4. 常见问题

### Q1: Agent如何知道新API的能力？

**A**: Agent不需要知道！
- 工具提供统一接口
- Agent只调用接口，不关心实现
- API配置在YAML文件中管理

### Q2: 如何切换数据源？

**A**: 修改配置文件优先级
```yaml
financial_data:
  sources:
    - name: tushare
      priority: 1  # 改为2
    - name: eastmoney
      priority: 2  # 改为1
```

### Q3: Skill和Agent可以互相调用吗？

**A**: 可以！
```python
# Agent调用Skill
skill = skill_manager.get_skill("technical_analysis_skill")
result = await skill.analyze(stock_code)

# Skill调用Agent（不推荐，破坏分层）
```

---

**文档版本**: 1.0.0
**更新时间**: 2026-03-14
**维护人**: Agent Army Team
