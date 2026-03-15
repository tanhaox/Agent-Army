# 新闻监控AI重构报告

**日期**: 2026-03-14
**任务**: Phase 2.5 - 重构新闻监控AI（使用工具库）
**状态**: ✅ 完成

---

## 一、重构目标

将新闻监控AI从"自包含"模式重构为"工具库调用"模式，实现：
- **职责分离**: 工具库负责数据/API，AI负责业务逻辑
- **代码简化**: 减少重复代码，提高可维护性
- **架构清晰**: 建立工具库 → AI的业务流程

---

## 二、重构内容

### 2.1 工具库创建（已完成）

创建了5个工具类，封装所有数据获取和计算功能：

| 工具类 | 位置 | 职责 | 状态 |
|--------|------|------|------|
| **NewsTool** | `src/core/tools/data_source/news_tool.py` | 新闻获取、情感分析 | ✅ 0-1完成 |
| **FinancialTool** | `src/core/tools/data_source/financial_tool.py` | 财务数据获取 | ✅ 0-1完成 |
| **LLMTool** | `src/core/tools/ai_service/llm_tool.py` | 大模型调用 | ✅ 0-1完成 |
| **NLPTool** | `src/core/tools/ai_service/nlp_tool.py` | NLP处理 | ✅ 0-1完成 |
| **FormulaTool** | `src/core/tools/calculation/formula_tool.py` | 公式计算 | ✅ 0-1完成 |

**工具库架构**：
```
src/core/tools/
├── __init__.py              # 统一入口
├── data_source/             # 数据源工具
│   ├── news_tool.py
│   └── financial_tool.py
├── ai_service/              # AI服务工具
│   ├── llm_tool.py
│   └── nlp_tool.py
└── calculation/             # 计算工具
    └── formula_tool.py
```

### 2.2 新闻监控AI重构

**文件对比**：

| 项目 | 重构前 | 重构后 | 改进 |
|------|--------|--------|------|
| **文件名** | `news_monitor_old.py` | `news_monitor.py` | - |
| **代码行数** | 410行 | 250行 | ⬇️ 减少40% |
| **数据获取** | `_fetch_news()` (自己实现) | `NewsTool.fetch_news()` | ✅ 委托工具库 |
| **情感分析** | `_analyze_sentiment()` (自己实现) | `NewsTool.analyze_sentiment()` | ✅ 委托工具库 |
| **事件提取** | `_extract_events()` | `_extract_events()` | ✅ 保留（业务逻辑） |
| **影响评估** | `_assess_impact()` | `_assess_impact()` | ✅ 保留（业务逻辑） |
| **摘要生成** | `_generate_summary()` | `_generate_summary()` | ✅ 保留（业务逻辑） |

**重构前后对比**：

```python
# 重构前（自包含模式）
class NewsMonitor:
    async def _fetch_news(self, stock_code: str):
        # 80行代码：构建URL、调用API、解析数据、错误处理...
        pass

    async def _analyze_sentiment(self, text: str):
        # 60行代码：调用NLP模型、解析结果...
        pass

    async def analyze(self, stock_code: str):
        news_list = await self._fetch_news(stock_code)
        for news in news_list:
            sentiment = await self._analyze_sentiment(news["content"])
            # 业务逻辑...

# 重构后（工具库模式）
class NewsMonitor:
    def __init__(self):
        self.news_tool = NewsTool()  # 初始化工具库

    async def analyze(self, stock_code: str):
        # 1. 获取新闻（工具库）
        news_list = await self.news_tool.fetch_news(stock_code, days)

        # 2. 提取事件（业务逻辑）
        events = self._extract_events(news_list)

        # 3. 情感分析（工具库）
        for event in events:
            sentiment_result = await self.news_tool.analyze_sentiment(
                event["title"] + " " + event["content"]
            )
            event["sentiment"] = sentiment_result["sentiment"]
            event["sentiment_score"] = sentiment_result["score"]

        # 4. 影响评估（业务逻辑）
        events = self._assess_impact(events)
```

---

## 三、测试结果

### 3.1 功能测试

**测试脚本**: `tests/test_news_monitor_refactored.py`

**测试内容**：
- ✅ AI初始化（NewsTool加载成功）
- ✅ 新闻获取（5条新闻）
- ✅ 事件提取（5个事件）
- ✅ 情感分析（positive/negative/neutral）
- ✅ 影响评估（0-10分）
- ✅ 摘要生成
- ✅ 警告生成

**测试输出**：
```
✅ 初始化成功
   AI名称: 新闻监控AI
   AI角色: 监控财经新闻，识别关键事件
   所属军团: hot_spot
   工具库: NewsTool 已加载

✅ 分析完成
   股票: 贵州茅台 (600519)
   监控周期: 最近7天
   新闻总数: 5条
   事件总数: 5个

事件 1:
   类型: 业绩公告
   标题: 贵州茅台发布2025年年报
   情感: positive (得分: 0.8)
   影响: 9.9/10
   来源: 东方财富
```

### 3.2 职责分离验证

| 功能模块 | 实现位置 | 职责 |
|----------|----------|------|
| **新闻获取** | NewsTool.fetch_news() | 数据获取（API调用、数据解析） |
| **情感分析** | NewsTool.analyze_sentiment() | NLP处理（情感识别、打分） |
| **事件提取** | AI._extract_events() | 业务逻辑（关键词匹配、事件分类） |
| **影响评估** | AI._assess_impact() | 业务逻辑（权重计算、排序） |
| **摘要生成** | AI._generate_summary() | 业务逻辑（内容组织） |

---

## 四、重构成果

### 4.1 代码质量提升

| 指标 | 重构前 | 重构后 | 改进 |
|------|--------|--------|------|
| **代码行数** | 410行 | 250行 | ⬇️ 减少40% |
| **耦合度** | 高（AI包含API调用） | 低（AI只关心业务逻辑） | ✅ 职责分离 |
| **可维护性** | 低（API变更需修改AI） | 高（API变更只改工具库） | ✅ 集中管理 |
| **可复用性** | 低（代码绑定AI） | 高（工具库可被多个AI使用） | ✅ 共享资源 |

### 4.2 架构优化

**重构前**：
```
NewsMonitor AI
├── 数据获取（自己实现）
├── 情感分析（自己实现）
├── 事件提取（业务逻辑）
├── 影响评估（业务逻辑）
└── 摘要生成（业务逻辑）
```

**重构后**：
```
工具库（共享）
├── NewsTool
│   ├── fetch_news()
│   └── analyze_sentiment()
└── 其他工具...

NewsMonitor AI
├── 初始化: self.news_tool = NewsTool()
└── 业务逻辑
    ├── _extract_events()
    ├── _assess_impact()
    └── _generate_summary()
```

### 4.3 维护优势

**场景1：API变更**
- ❌ 重构前：需要修改所有使用该API的AI（3个AI = 3次修改）
- ✅ 重构后：只需修改工具库中的1个函数

**场景2：新增AI**
- ❌ 重构前：每个AI都要实现数据获取、情感分析等重复代码
- ✅ 重构后：直接调用工具库，专注于业务逻辑

**场景3：性能优化**
- ❌ 重构前：优化数据获取需要在多个AI中重复进行
- ✅ 重构后：只需优化工具库中的1个函数

---

## 五、后续工作

### 5.1 Phase 2.5 完成情况

| 任务 | 状态 | 说明 |
|------|------|------|
| 创建工具库架构 | ✅ 完成 | 5个工具类 |
| 创建NewsTool | ✅ 完成 | 新闻获取、情感分析 |
| 创建FinancialTool | ✅ 完成 | 财务数据获取 |
| 创建LLMTool | ✅ 完成 | 大模型调用 |
| 创建NLPTool | ✅ 完成 | NLP处理 |
| 创建FormulaTool | ✅ 完成 | 公式计算 |
| 重构新闻监控AI | ✅ 完成 | 代码减少40% |
| 测试验证 | ✅ 完成 | 所有功能正常 |

### 5.2 待完成任务（Phase 2）

| 任务 | 优先级 | 说明 |
|------|--------|------|
| 重构基本面分析AI | 中 | 使用FinancialTool、FormulaTool |
| 创建目标定价AI | 高 | 热点捕捉军团 2/4 |
| 创建买入时机AI | 高 | 时机把握军团 1/4 |
| 创建预测验证AI | 高 | 预测验证军团 1/4 |

### 5.3 1-100 扩展（后续）

| 任务 | 说明 | 时间点 |
|------|------|--------|
| 接入真实API | 当前使用示例数据 | 需要API密钥时 |
| 封装MCP Server | 工具库 → MCP服务 | 需要跨进程调用时 |
| 封装Skill | 工具库 → 可安装技能 | 需要分发复用时 |

---

## 六、经验总结

### 6.1 架构设计原则

✅ **职责分离**：工具库 = 数据/API，AI = 业务逻辑
✅ **0-1原则**：先建基础框架，后续扩展（不要一上来就100）
✅ **集中管理**：API、数据源、计算逻辑统一管理，避免重复

### 6.2 重构技巧

1. **识别重复代码**：多个AI都调用的功能 → 提取到工具库
2. **识别业务逻辑**：每个AI独特的判断、决策 → 保留在AI中
3. **保持接口稳定**：工具库接口不变，AI调用方式不变

### 6.3 用户需求对齐

用户提出的核心需求：
- ✅ **过程透明**：工具库让用户看到每一步用什么工具
- ✅ **结果解释**：AI专注业务逻辑，更容易理解决策过程
- ✅ **易于维护**：API变更只需修改工具库一处

---

## 七、文件清单

### 7.1 新增文件

```
src/core/tools/
├── __init__.py                          # 工具库入口
├── data_source/
│   ├── __init__.py
│   ├── news_tool.py                     # 新闻工具
│   └── financial_tool.py                # 财务工具
├── ai_service/
│   ├── __init__.py
│   ├── llm_tool.py                      # 大模型工具
│   └── nlp_tool.py                      # NLP工具
└── calculation/
    ├── __init__.py
    └── formula_tool.py                  # 公式工具

tests/
└── test_tools_library.py                # 工具库测试
```

### 7.2 修改文件

```
src/agents/business/
├── news_monitor_old.py                  # 旧版本（已备份）
└── news_monitor.py                      # 重构版本（新）

tests/
└── test_news_monitor_refactored.py      # 重构测试
```

---

## 八、结论

✅ **Phase 2.5 工具库建设完成**（0-1层）
✅ **新闻监控AI重构完成**（代码减少40%，职责清晰）
✅ **测试全部通过**（功能完整，架构合理）

**下一步**：
- 重构基本面分析AI（使用FinancialTool、FormulaTool）
- 创建剩余3个AI（目标定价、买入时机、预测验证）

---

**报告生成时间**: 2026-03-14 03:15
**测试通过率**: 100%
**重构完成度**: 100%
