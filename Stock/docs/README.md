# Stock Analyst 文档索引

> **版本**: v5.1 | **日期**: 2026-06-15 | **更新**: 添加 AGENTS.md 层级索引
> **关联**: [Stock/AGENTS.md](../AGENTS.md) — 项目级 AI 理解文档

---

## 📚 文档概览

| 文档 | 行数 | 状态 | 用途 |
|------|------|------|------|
| **[architecture.md](architecture.md)** | ~1570 | ✅ 完整 | 系统架构全景图 |
| **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** | ~600 | ✅ 完整 | 开发施工手册 |
| **[P0级基建顶层设计.md](P0级基建顶层设计.md)** | ~1475 | ✅ 完整 | 基础设施顶层设计 |
| **[系统基建替换退役计划.md](系统基建替换退役计划.md)** | ~430 | ✅ 完整 | 旧系统退役计划 |
| **[news.md](news.md)** | ~580 | ✅ 完整 | 新闻事件分析系统 |
| **[tushare.md](tushare.md)** | ~420 | ✅ 准确 | Tushare API 速查 |
| **[frontend-api-db-audit.md](frontend-api-db-audit.md)** | ~156 | ✅ 准确 | API 审计报告 |
| **[PHASE_PLAN.md](PHASE_PLAN.md)** | ~157 | ✅ 准确 | Phase 执行计划 |

---

## 🗂️ AGENTS.md 层级索引 (AI 理解文档)

> 层级索引帮助 AI 快速定位代码结构，无需阅读全部代码。

| 层级 | 文件 | 内容 |
|------|------|------|
| **L0 根** | [Stock/AGENTS.md](../AGENTS.md) | 项目概览、技术栈、核心约束 |
| **L1 backend** | [backend/AGENTS.md](../backend/AGENTS.md) | 后端根目录、脚本、模型 |
| **L1 app** | [backend/app/AGENTS.md](../backend/app/AGENTS.md) | FastAPI 核心、core/utils 模块 |
| **L1 frontend** | [frontend/AGENTS.md](../frontend/AGENTS.md) | 前端根目录 |
| **L1 src** | [frontend/src/AGENTS.md](../frontend/src/AGENTS.md) | React 页面/组件、API 客户端 |
| **L2 services** | [backend/app/services/AGENTS.md](../backend/app/services/AGENTS.md) | 80+ 服务模块分类索引 |
| **L2 api** | [backend/app/api/AGENTS.md](../backend/app/api/AGENTS.md) | 17 路由模块、端点清单 |
| **L2 backend/docs** | [backend/docs/AGENTS.md](../backend/docs/AGENTS.md) | 后端补充文档 (宏观映射) |
| **L2 docs** | [docs/AGENTS.md](AGENTS.md) | 文档目录索引 |

### 快速定位指南

```
想找... → 查看...
──────────────────────────────────────────────────────
服务实现 → backend/app/services/AGENTS.md
API 端点 → backend/app/api/AGENTS.md
前端页面 → frontend/src/AGENTS.md
核心工具 → backend/app/AGENTS.md §Core Modules
数据库表 → docs/DEVELOPER_GUIDE.md §三、数据库表
开发约束 → Stock/AGENTS.md §For AI Agents
文档索引 → docs/AGENTS.md
```

---

## 🎯 快速导航

### 新开发者必读

```
1. [architecture.md] 系统全景 → 了解系统架构
2. [DEVELOPER_GUIDE.md] 开发手册 → 开始编码前必读
3. [P0级基建顶层设计.md] → 了解数据基础设施
```

### 日常开发参考

```
1. [DEVELOPER_GUIDE.md] §7 统一工具库 → 查找全局工具函数
2. [tushare.md] → Tushare API 参数速查
3. [frontend-api-db-audit.md] → API 端点验证
```

### 系统升级参考

```
1. [PHASE_PLAN.md] → 了解已完成的 Phase
2. [architecture.md] 变更日志 → 历史版本变更
3. [系统基建替换退役计划.md] → 退役计划执行状态
```

---

## 📊 系统当前状态 (v4.9)

### 核心能力

| 能力 | 状态 | 版本 |
|------|------|------|
| TG 全市场扫描 | ✅ 运行中 | v4.9 |
| AlphaFlow 主升浪捕获 | ✅ 运行中 | v4.9 |
| DNA 个性化模型 | ✅ 运行中 | v4.5 |
| 大神仙空卖出信号 | ✅ 运行中 | v4.7 |
| 周线双周期共振 | ✅ 运行中 | v4.2 |
| 新闻分类去重 | ✅ 运行中 | v4.8 |
| 龙虎榜精细化 | ✅ 运行中 | v4.8 |

### P0 基建状态

| 模块 | 状态 | 实现 |
|------|------|------|
| M1 名称缓存 | ✅ 完成 | name_resolver.py 三级缓存 |
| M2 除权因子 | ✅ 完成 | adj_factor_chain + resync_all_kline.py |
| M3 筹码分布 | ⚠️ 进行中 | daily_chip_perf (简化版) |
| M4 资金流向 | ✅ 完成 | moneyflow_service.py |
| M5 分时数据 | ✅ 完成 | minute_on_demand.py (按需计算) |
| M6 行业标签 | ✅ 完成 | sw_sector_index + stock_sector_registry |

---

## 🔗 文档关联

```
architecture.md (系统架构)
    ├── 系统全景 (两大管线、核心能力矩阵)
    ├── 模块架构 (10 个逻辑模块)
    ├── 数据流 (TG扫描、AlphaFlow、学习闭环)
    ├── 数据库架构
    └── 变更日志

DEVELOPER_GUIDE.md (开发手册)
    ├── 核心文件连带影响表
    ├── DNA 个性化模型
    ├── 数据库表说明
    ├── 统一工具库 (§7)
    └── 常见补丁原因速查

P0级基建顶层设计.md (基建设计)
    ├── Tushare API 接口映射
    ├── 除权因子体系
    ├── 筹码分布体系
    ├── 分时体系
    ├── 名称解析体系
    └── 行业/资金标签体系

系统基建替换退役计划.md (退役计划)
    ├── 数据库总览
    ├── 退役清单
    ├── 数据回填计划
    └── 待退役调查清单

news.md (新闻系统)
    ├── 数据流
    ├── LLM 提示词
    ├── 去重引擎
    ├── 评分体系
    └── 事件衰减模型

tushare.md (API手册)
    ├── 沪深股票 API
    ├── 指数 API
    ├── 期货/期权 API
    └── 宏观经济 API

frontend-api-db-audit.md (审计报告)
    ├── 页面健康度总览
    ├── API 端点列表
    └── 数据库一致性

PHASE_PLAN.md (执行计划)
    ├── Phase 执行清单
    ├── 执行状态总览
    └── 施工规则
```

---

## 📅 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v5.4 | 2026-06-15 | ✅分钟线防伪优化：只检测高分股票(134→219)+并发降至10 |
| v5.3 | 2026-06-15 | 分钟线防伪流程改造+L3股票优先检测+潜伏猎手/形态识别待优化 |
| v5.2 | 2026-06-15 | P0-1批量查询优化+P1-4特征选择+v4.9 |
| v5.1 | 2026-06-15 | 添加 AGENTS.md 层级索引 (5 个 AI 理解文档) |
| v5.0 | 2026-06-14 | 整合所有文档，统一索引 |
| v4.8 | 2026-06-13 | DNA自动化+新闻改造+扫描重组 |
| v4.7 | 2026-06-09 | 大神仙空+AlphaFlow重构 |
| v4.6 | 2026-06-05 | 影子训练升级+宏观数据扩展 |
| v4.5 | 2026-06-07 | 系统级P0升级+DNA实验室 |
| v4.2 | 2026-06-03 | 周线共振+质量控制 |

---

## 📝 文档维护规则

1. **系统升级后必须更新**:
   - `architecture.md` 变更日志
   - `DEVELOPER_GUIDE.md` 全局约定

2. **Phase 完成后更新**:
   - `PHASE_PLAN.md` 执行状态

3. **基础设施变更后更新**:
   - `P0级基建顶层设计.md`
   - `系统基建替换退役计划.md`

4. **新闻系统变更后更新**:
   - `news.md`

---

**维护**: 每次代码提交时检查是否需要更新文档。
