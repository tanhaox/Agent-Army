# 改进意见：Commander混合审核模式

**创建日期**: 2026-03-14
**优先级**: 🔴 高优先级
**类型**: 工作流程优化
**状态**: 待改进

---

## 需求描述

### 当前问题

当前工作流程是**串行一次性审核**：
1. 产业链分析AI完成
2. 基本面分析AI完成
3. 生成综合报告
4. Commander审核整个报告（一次性）

**问题**：
- ❌ 不能提前发现问题（最后才知道某个Agent质量差）
- ❌ 不能边收边审（效率低）
- ❌ 审核失败没有修复循环（直接结束）
- ❌ 浪费时间（如果产业链分析很差，基本面分析已经白做了）

### 期望效果

**方案C：混合模式**（用户已确认）

```
产业链分析AI → 提交报告 → Commander预审
                              ↓
                          合格？
                           ↓是          ↓否
                        标记"待用"    标记问题 + 需要补充的内容
                                        ↓
基本面分析AI → 提交报告              Agent补充后重新提交
                ↓
          Commander预审
                ↓
            合格？
             ↓是          ↓否
          标记"待用"    标记问题 + 需要补充的内容
                          ↓
                      所有报告收集完毕
                          ↓
                  Commander编写最终报告
                  （使用标记为"待用"的部分）
                          ↓
                      审核最终报告
                          ↓
                   通过？→ 提交给用户
                     ↓否
                指出需要补充的内容
                          ↓
                  相应Agent补充后重新提交
```

**优势**：
- ✅ **提前发现问题** - 不用等到最后才知道某个Agent质量差
- ✅ **边收边审** - 提高效率
- ✅ **明确反馈** - 每个Agent都知道自己哪里不足
- ✅ **修复循环** - 审核失败可以打回补充
- ✅ **状态标记** - 清楚知道哪些部分可用，哪些需要补充

---

## 技术方案

### 1. 新增预审机制

**位置**: `src/workflows/investment_analysis_workflow.py`

**修改内容**：

```python
async def analyze_stock(self, stock_code: str) -> InvestmentReport:
    """分析股票 - 混合审核模式"""

    # 存储预审结果
    precheck_results = {}

    # Step 1: 产业链分析
    industry_result = await self.industry_analyzer.analyze(stock_code)

    # Step 1.1: Commander预审产业链报告
    industry_precheck = await self.commander.precheck_report(
        agent_name="产业链分析AI",
        report_type="industry",
        report_data=industry_result.model_dump()
    )
    precheck_results["industry"] = industry_precheck

    if not industry_precheck["approved"]:
        # 标记问题，要求补充
        self.logger.warning(f"产业链分析预审未通过: {industry_precheck['issues']}")
        # TODO: 可以选择立即补充，或者继续等待其他报告
    else:
        self.logger.info("产业链分析预审通过，标记为'待用'")

    # Step 2: 基本面分析
    fundamental_result = await self.fundamental_analyzer.analyze(stock_code)

    # Step 2.1: Commander预审基本面报告
    fundamental_precheck = await self.commander.precheck_report(
        agent_name="基本面分析AI",
        report_type="fundamental",
        report_data=fundamental_result
    )
    precheck_results["fundamental"] = fundamental_precheck

    if not fundamental_precheck["approved"]:
        self.logger.warning(f"基本面分析预审未通过: {fundamental_precheck['issues']}")
    else:
        self.logger.info("基本面分析预审通过，标记为'待用'")

    # Step 3: 检查是否所有报告都通过预审
    all_approved = all(r["approved"] for r in precheck_results.values())

    if not all_approved:
        # 有报告未通过预审，需要补充
        self.logger.warning("部分报告预审未通过，需要补充")
        # TODO: 可以选择循环补充，或者直接终止

    # Step 4: 生成综合报告（使用预审通过的部分）
    report = self._generate_report_with_precheck(
        stock_code=stock_code,
        precheck_results=precheck_results,
        industry_result=industry_result,
        fundamental_result=fundamental_result
    )

    # Step 5: Commander最终审核
    review_result = await self.commander._check_report_quality(report.model_dump())

    if not review_result.get("approved"):
        # 最终审核未通过，打回给相应Agent
        issues = review_result.get("issues", [])
        self.logger.warning(f"最终审核未通过，需要补充: {issues}")
        # TODO: 识别是哪个Agent的问题，打回去补充

    return report
```

### 2. 新增Commander预审方法

**位置**: `src/agents/management/commander.py`（如果存在）或新建

**新增方法**：

```python
async def precheck_report(
    self,
    agent_name: str,
    report_type: str,
    report_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    预审单个Agent的报告

    Args:
        agent_name: Agent名称
        report_type: 报告类型（industry/fundamental/...）
        report_data: 报告数据

    Returns:
        {
            "approved": True/False,
            "quality_score": 0-100,
            "issues": ["问题1", "问题2"],
            "missing_content": ["需要补充1", "需要补充2"],
            "status": "待用"/"不合格"
        }
    """

    # 根据报告类型使用不同的预审标准
    if report_type == "industry":
        return await self._precheck_industry(report_data)
    elif report_type == "fundamental":
        return await self._precheck_fundamental(report_data)
    else:
        return {
            "approved": False,
            "quality_score": 0,
            "issues": ["未知报告类型"],
            "status": "不合格"
        }

async def _precheck_industry(self, data: Dict) -> Dict[str, Any]:
    """预审产业链分析报告"""

    issues = []
    missing_content = []

    # 检查必需字段
    if not data.get("industry_name"):
        issues.append("缺少行业名称")
        missing_content.append("需要补充行业名称")

    if not data.get("growth_driver") or len(data.get("growth_driver", [])) == 0:
        issues.append("缺少成长驱动因素")
        missing_content.append("产业链分析缺少足够的成长驱动因素")

    if not data.get("risk_factors") or len(data.get("risk_factors", [])) == 0:
        issues.append("缺少风险因素")
        missing_content.append("缺少足够的风险提示（至少需要2条）")

    # 计算质量评分
    quality_score = 100 - len(issues) * 20

    return {
        "approved": len(issues) == 0,
        "quality_score": max(0, quality_score),
        "issues": issues,
        "missing_content": missing_content,
        "status": "待用" if len(issues) == 0 else "不合格"
    }

async def _precheck_fundamental(self, data: Dict) -> Dict[str, Any]:
    """预审基本面分析报告"""

    issues = []
    missing_content = []

    # 检查必需字段
    if not data.get("stock_name"):
        issues.append("缺少股票名称")

    if data.get("composite_score", 0) == 0:
        issues.append("综合评分为0，数据可能不完整")
        missing_content.append("基本面数据不完整，需要补充财务数据")

    key_metrics = data.get("key_metrics", {})
    if key_metrics.get("roe", 0) == 0:
        issues.append("ROE为0，可能缺少关键财务数据")
        missing_content.append("缺少ROE等核心财务指标")

    # 计算质量评分
    quality_score = 100 - len(issues) * 20

    return {
        "approved": len(issues) == 0,
        "quality_score": max(0, quality_score),
        "issues": issues,
        "missing_content": missing_content,
        "status": "待用" if len(issues) == 0 else "不合格"
    }
```

### 3. Web界面展示预审状态

**位置**: `web_app.py`

**新增展示内容**：

```python
# Agent工位 #1: 产业链分析AI
with st.container():
    # ... 原有内容 ...

    # 显示预审状态
    if "industry_precheck" in st.session_state:
        precheck = st.session_state.industry_precheck

        if precheck["approved"]:
            st.success(f"✅ Commander预审通过（质量评分: {precheck['quality_score']}/100）")
            st.caption("状态: 待用")
        else:
            st.error(f"❌ Commander预审未通过（质量评分: {precheck['quality_score']}/100）")
            st.caption("状态: 不合格")

            # 显示问题
            if precheck["issues"]:
                st.markdown("**发现的问题**:")
                for i, issue in enumerate(precheck["issues"], 1):
                    st.caption(f"  {i}. {issue}")

            # 显示需要补充的内容
            if precheck["missing_content"]:
                st.markdown("**需要补充的内容**:")
                for i, item in enumerate(precheck["missing_content"], 1):
                    st.caption(f"  {i}. {item}")
```

---

## 实现步骤

### Step 1: 新增Commander预审方法
- [ ] 在 `src/agents/management/commander.py` 新增 `precheck_report()` 方法
- [ ] 实现 `_precheck_industry()` 方法
- [ ] 实现 `_precheck_fundamental()` 方法
- [ ] 返回预审结果（approved, quality_score, issues, missing_content, status）

### Step 2: 修改工作流主流程
- [ ] 在 `src/workflows/investment_analysis_workflow.py` 新增预审调用
- [ ] 存储预审结果到 `precheck_results`
- [ ] 检查是否所有报告都通过预审
- [ ] 使用预审通过的部分生成最终报告

### Step 3: Web界面展示预审状态
- [ ] 在 `web_app.py` 的Agent工位中显示预审状态
- [ ] 显示"待用"或"不合格"状态标签
- [ ] 显示预审发现的问题
- [ ] 显示需要补充的内容

### Step 4: 实现补充循环（可选，Phase 2）
- [ ] 如果预审未通过，允许Agent重新提交
- [ ] 最多重试3次
- [ ] 3次后仍然不合格，触发HR Agent介入

---

## 预期结果

### 用户体验提升

**优化前**：
```
产业链分析AI → 完成
基本面分析AI → 完成
生成报告 → 完成
Commander审核 → ❌ 未通过（最后才发现问题）
→ 流程结束，无法修复
```

**优化后**：
```
产业链分析AI → 完成
Commander预审 → ✅ 通过（标记"待用"）

基本面分析AI → 完成
Commander预审 → ❌ 未通过
  ↓
  发现问题：缺少ROE数据
  ↓
  标记：需要补充"核心财务指标"
  ↓
基本面分析AI → 补充数据
Commander预审 → ✅ 通过（标记"待用"）

所有报告收集完毕
  ↓
Commander编写最终报告（使用两个"待用"部分）
  ↓
Commander最终审核 → ✅ 通过
  ↓
提交给用户
```

### 关键指标

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| **问题发现时间** | 最后才发现 | 提交即发现 |
| **修复循环** | ❌ 无 | ✅ 有（最多3次） |
| **状态透明度** | 不知道质量如何 | 实时显示"待用/不合格" |
| **反馈明确性** | 只知道未通过 | 明确指出需要补充什么 |
| **整体效率** | 低（最后才发现问题） | 高（边收边审） |

---

## 影响范围

### 修改的文件

1. **src/agents/management/commander.py** - 新增预审方法（+150行）
2. **src/workflows/investment_analysis_workflow.py** - 修改主流程（+80行）
3. **web_app.py** - 新增预审状态展示（+60行）

### 不影响的文件

- ✅ `src/agents/business/industry_analyzers.py` - 无需修改
- ✅ `src/agents/business/fundamental_analyzer.py` - 无需修改
- ✅ `src/core/tools/` - 无需修改

---

## 测试计划

### 单元测试

- [ ] 测试 `precheck_report()` 方法
- [ ] 测试 `_precheck_industry()` 方法
- [ ] 测试 `_precheck_fundamental()` 方法
- [ ] 测试预审结果格式

### 集成测试

- [ ] 测试完整工作流（预审通过）
- [ ] 测试完整工作流（预审未通过 → 补充 → 通过）
- [ ] 测试Web界面预审状态显示

### 手动测试

1. 访问 http://localhost:8501
2. 输入股票代码：600519
3. 观察产业链分析AI的预审状态
4. 观察基本面分析AI的预审状态
5. 查看最终报告是否使用了"待用"部分

---

## 后续优化（Phase 2）

- [ ] **自动补充循环** - 预审未通过时，自动触发Agent补充
- [ ] **重试次数限制** - 最多3次，超过触发HR Agent
- [ ] **部分可用机制** - 某个Agent不合格时，其他Agent可以先标记"待用"
- [ ] **预审标准配置** - 允许配置不同严格程度的预审标准
- [ ] **预审历史记录** - 记录每次预审的结果，用于分析Agent质量趋势

---

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 预审标准过严 | 所有报告都被打回 | 提供配置选项，调整严格程度 |
| 预审标准过松 | 质量差的报告也能通过 | 基于测试数据调优标准 |
| 补充循环死循环 | 一直重试，永不通过 | 限制重试次数（最多3次） |
| Web界面卡顿 | 实时预审导致界面变慢 | 使用异步预审，不阻塞UI |

---

## 完成标准

- [ ] 所有代码实现完成
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] Web界面测试通过
- [ ] 文档更新完成
- [ ] 版本号更新（v2.7.0 → v2.8.0）

---

**创建人**: Claude
**审核人**: 待定
**预计完成时间**: 2026-03-14
