# 前端→后端→数据库 三重交叉审计报告

> **审计日期**: 2026-06-12 | **审计范围**: 15页面 + 8组件 → 91个API调用 → ~40张数据库表  
> **方法**: 逐行交叉对比 前端API调用 → 后端路由 → SQL表/列定义  
> **原则**: 只读诊断，不修改代码和数据库

---

## 总评

| 指标 | 数值 |
|------|------|
| 前端API调用总数 | 91 |
| 后端路由匹配 | 90 / 91 |
| 匹配率 | **98.9%** |
| 数据库表列匹配 | 全部通过 |

---

## 🔴 发现问题：1个

### DeepAnalysisModal.tsx → `/llm/deep-analysis` 路由不存在

| 项目 | 详情 |
|------|------|
| **前端文件** | `Stock/frontend/src/components/DeepAnalysisModal.tsx:13` |
| **调用代码** | `api.post('/llm/deep-analysis', { symbols, scores })` |
| **后端状态** | `llm_analysis.py` 中**没有** `/llm/deep-analysis` 路由 |
| **HTTP响应** | `{"detail":"Not Found"}` (404) |
| **触发场景** | ResultPage.tsx 点击"🔬 深度分析"按钮 → 打开 DeepAnalysisModal |
| **影响** | Modal弹出后API请求404，LLM深度分析功能完全不可用 |

**后端实际存在的LLM端点**（均在 `llm_analysis.py`）:

| 路由 | 方法 | 说明 |
|------|------|------|
| `/llm/candidates` | GET | 获取LLM分析候选列表 |
| `/llm/generate-prompt` | POST | 生成提示词并缓存 |
| `/llm/prompts` | GET | 读取缓存提示词 |
| `/llm/auto-analyze` | POST | **SSE流式自动分析** ← 与 deep-analysis 功能最接近 |
| `/llm/retry-one` | POST | 重试单只股票分析 |

**修复方向**:
- DeepAnalysisModal 应改为调用 `/llm/auto-analyze` (SSE流式)，或
- 在 `llm_analysis.py` 中新增 `/llm/deep-analysis` 路由

---

## 页面健康度总览

| 页面 | API数 | 状态 | 备注 |
|------|-------|------|------|
| 📰 NewsPage (首页/新闻) | 8 | ✅ | 全部通过 |
| 🔍 ScanPage (TG扫描) | 3 | ✅ | 全部通过 |
| 📊 AnalysisPage (多维度评分) | 5 | ✅ | 全部通过 |
| 🏆 ResultPage (最终推荐) | 5 | ⚠️ | 直接API均通过，但"深度分析"按钮触发DeepAnalysisModal有1个404 |
| 🏛 AlphaFlowPage | 5 | ✅ | 全部通过 |
| 💼 HoldingsPage (持仓管理) | 16 | ✅ | 全部通过 |
| 🦅 AmbushPage (潜伏猎手) | 2 | ✅ | 全部通过 |
| 🧪 LearningPage (AI自学习) | 19 | ✅ | 全部通过 |
| 🧠 DeepAnalysisPage (LLM分析) | 2 | ✅ | 全部通过 |
| 📈 MonitorPage (系统监控) | 5 | ✅ | 全部通过 |
| 🔧 SettingsPage (设置) | 3 | ✅ | 全部通过 |
| 📋 StockSelectPage | 1 | ✅ | 全部通过 |
| 📉 SanxianPage (三线对比) | 2 | ✅ | 全部通过 |
| 🕒 TailMarketPage (尾盘) | 1 | ✅ | 全部通过 |
| 🗺 BlueprintPage (架构蓝图) | 0 | ✅ | 纯静态 |
| 组件 (Feedback/Prompt/Dna等) | 14 | ✅ | 全部通过 |
| **组件 DeepAnalysisModal** | **1** | **❌** | **`/llm/deep-analysis` 404** |

---

## 数据库表→代码引用一致性

所有后端SQL查询中的表名和列名，与数据库实际schema对比结果：

- **40+ 张业务表全部存在**
- **所有SQL引用的列名均与DB实际列名匹配**
- **无类型不匹配** (之前的 `CAST(:sec AS jsonb) vs ARRAY` 等问题已修复)
- **无版本差异** (之前的 `2d vs 3d` 等问题已修复)
- **无缺列问题** (之前的 `signal_quality`, `trend_score` 等已补全)

---

## 审计结束
