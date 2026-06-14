# Stock Analyst Phase 执行计划 v1.1

> **用途**: 给开发窗口的 AI 使用。配合 `docs/DEVELOPER_GUIDE.md` 一起用。
> **工作流**: 每个 Phase 按顺序执行 → 读完"施工前检查"→ 改代码 → 跑自检 → 标记 ✅
> **更新**: v1.1 2026-06-14 添加 Phase 72 新闻去重修复

## 使用方式

```
步骤 0: 执行前先 grep "你要改的文件名" docs/DEVELOPER_GUIDE.md → 读连带影响
步骤 1: 选中下一个 ⏳ Phase，读完"施工前检查"
步骤 2: 改代码
步骤 3: 跑自检命令 → 通过后标记 ✅ 并写入执行日期
步骤 4: 回到步骤 1
```

---

## Phase 执行清单

### Phase 56 — signal_history enrichment 回填
- **状态**: ⚠️ 部分完成 (58/5851, 源数据不够)
- **文件**: `scripts/backfill_signal_enrichment.py`
- **施工前检查**: grep "signal_history" docs/DEVELOPER_GUIDE.md
- **自检**: `python scripts/backfill_signal_enrichment.py` → `SELECT COUNT(CASE WHEN relative_position IS NOT NULL THEN 1 END) FROM signal_history` → 预期 > 50%
- **已知限制**: 旧 analysis_scores 不含 enrichment, 回填只能覆盖 Phase 26e 之后产生的记录

### Phase 57 — T+5/T+15 验证扩展
- **状态**: ✅ 2026-06-06
- **文件**: `scripts/verify_recommendations.py`
- **执行结果**: verified_2d=318 (wr=65.7%), verified_5d=314 (wr=25.2%), verified_15d=0 (数据积累中)

### Phase 58 — 替换预测特征中的近似 sector gap 特征
- **状态**: ✅ (Phase 32a/34 已覆盖)
- **备注**: `x_real_sector_5d` 等 7 维真实板块特征已由 Phase 32a/34 实现, 无近似特征需替换

### Phase 59 — stk_mins 本地缓存 (sanxian 分时图加速)
- **状态**: ✅ 2026-06-06
- **文件**: `app/api/sanxian.py`
- **改动**: `get_intraday()` 个股优先从 `min_kline` 本地缓存读取 (≥8根bar=有足够数据), 缺才调 `stk_mins` API

### Phase 60 — 龙虎榜因子深度扩展
- **状态**: ✅ 2026-06-06
- **文件**: `app/services/predictive_features.py`
- **改动**: 69维 (63+6): `tl_inst_continuous`, `tl_seat_quality`, `tl_net_trend_10d`, `tl_consecutive_days`, `tl_avg_amount_ratio`, `tl_inst_net_streak`
- **AUC**: 0.6090 (69维, 无退化)
- **备注**: 6个新特征全未入 Top20 — 上榜样本占训练集 <5%, 任何 toplist 特征都稀疏。特征本身计算正确, 对实际命中龙虎榜的信号仍有辨识力

### Phase 61 — 三策略独立预测模型
- **状态**: ⚠️ 需要前置条件
- **备注**: 训练需要 strategy_label 字段, signal_history 当前只有 archetype。需先给 signal_history 加 tier 列或从 archetype 推导映射, 再分 tier 训练

### Phase 62 — 新闻验证结果前端展示 (Learning 页面)
- **状态**: ✅ 2026-06-06
- **文件**: `app/api/learning.py` (+`/news-verify-summary` 端点) + `frontend/src/pages/LearningPage.tsx` (新增"新闻验证"Tab)
- **执行结果**: 商品命中率表格展示, ≥5条信号的100+商品按总信号排序

### Phase 63 — 新闻验证闭环接入调度器
- **状态**: ✅ (Phase 50 已完成)
- **备注**: `task_verify_news_signals` 已在 scheduler_loop.py:23 + :50 注册

### Phase 64 — 持仓策略联动
- **状态**: ⏳
- **文件**: `app/api/holdings.py` + `frontend/src/pages/HoldingsPage.tsx`
- **依赖**: Phase 35 (三策略标签), Phase 39 (rec_index)
- **施工前检查**: grep "holdings\|HoldingsPage\|持仓" docs/DEVELOPER_GUIDE.md
- **任务**: 持仓页面展示推荐列表中对应该股的 rec_index、策略标签、新闻信号, 并生成 buy/sell/hold 建议
- **自检**: 打开 /holdings → 每只持仓可见推荐指数和策略标签

### Phase 65-67 — 前端展示补缺
- **状态**: ⏳
- **66**: `ResultPage.tsx` 展示 `predicted_return` + `rank_score`
- **67**: `HoldingsPage.tsx` 展示 `news_signal`

### Phase 68 — DNA 实验室自动化加入 (v4.8)
- **状态**: ✅ 2026-06-13
- **文件**: `app/services/stock_dna_auto_join.py`
- **机制**:
  - 机制1 (AlphaFlow): lock_state=breakout_up + TG买入 → 加入 DNA
  - 机制2 (TG扫描): 每日扫描完成后 L3 级股票 → 加入 DNA (异步, 不阻塞)
  - 机制3 (持仓): 持仓新增/清仓 → 相关股票加入 DNA

### Phase 69 — 新闻特征系统改造 (v4.8)
- **状态**: ✅ 2026-06-13
- **旧问题**: `stock_events`/`news_aggregated`/`news_verify` 表数据稀疏
- **新方案**: 使用 `compute_sector_macro_score()` + Tushare 宏观数据
- **改造位置**:
  - `deep_scorer.py`: `score_event_impact()` → `compute_sector_macro_score()`
  - `holdings.py`: `news_signal` 用 `sector_macro_cache` 预计算
  - `LearningPage.tsx`: 新闻验证标签 → 宏观快照展示

### Phase 70 — 新闻分类去重 + 龙虎榜精细化 (v4.8)
- **状态**: ✅ 2026-06-13
- **新闻分类** (`news_classifier.py`): SimHash 指纹 + 三级分类 (company/sector/macro/garbage)
- **个股摘要保留**: `get_stock_news_summary()` 从 `news_raw` + `stock_events` 合并
- **龙虎榜精细化** (`toplist_analyzer.py`):
  - 机构: 公募/北向/社保/QFII/私募
  - 游资: 顶级/一线/二线/三线
  - 共振: 5 级强度 + 标签
  - 净买持续性: 1/3/5 日
  - 智能缓存: 历史永久 / 当日交易 5min / 休市 1h
- **SSE 刷新接口**: `POST /api/scan/toplist-refresh`
- **新闻 SSE 接口**: `POST /api/scan/crawl-news` (浏览器加超时)
- **聚合接口**: `GET /api/scan/news-dashboard` (6 请求 → 1)
- **新鲜度 API**: `GET /api/scan/news-freshness` (skip/crawl/analyze/full 4 建议)
- **融资融券重写**: `get_margin_sentiment()` 改用 rzye (融资余额) 1.6/1.2 万亿阈值

### Phase 71 — TG 扫描阶段重组 v4.8.2 (本次修复 15 项)
- **状态**: ✅ 2026-06-13
- **修复**:
  - P0-1: `setCurrentPhase` 类型扩展为 10 个 `ScanPhase`
  - P0-2: DNA auto-join 异步化 (`asyncio.create_task`)
  - P1-1: `toplist_sync` 合并到 `toplist` (去除重复)
  - P1-2: phaseMessages slice(-8) → slice(-20), maxHeight 120 → 280
  - P1-3: `market_filter` 后端真过滤 (用 `classify_board`)
  - P1-4: `skip_download` 同时控制龙虎榜 + DNA
  - P1-5: scan phase 5% 步长推送 (5000只 → 100 事件)
  - P1-6: `accuracy_feedback(isolated_meta=True)` 写独立列
  - P2-1: 14 维文案修正
  - P2-2: phase 异常信息统一 "异常: {e}"
  - P2-3: 覆盖率 < 95% 时回退 365 天
  - P2-4: ambush_scan 用 `scan_results` 最新日期
  - P2-5: ST 过滤正则修正 (支持中文 "ST")
  - P2-6: phaseLabel 新增 🧬DNA训练
- **数据库变更**: `param_library` 新增 `accuracy_feedback_factor`, `accuracy_feedback_at` 列
- **关联文档**: `docs/architecture.md` 变更日志, `docs/DEVELOPER_GUIDE.md` §7

---

## 执行状态

| Phase | 状态 | 执行日期 | 备注 |
|-------|:--:|---------|------|
| 56 | ⚠️ | 06-06 | 1%覆盖, 源数据不足, 随扫描积累 |
| 57 | ✅ | 06-06 | T+5 verified=314 wr=25%, T+15待积累 |
| 58 | ✅ | 06-06 | Phase 32a/34 已覆盖, 7维真实板块特征替代近似 |
| 59 | ✅ | 06-06 | sanxian 优先读本地 min_kline, 缺才调 API |
| 60 | ✅ | 06-06 | 69维含17维龙虎榜, AUC 0.609 无退化 |
| 61 | ⚠️ | 06-06 | 需 signal_history 加 strategy_label 列 |
| 62 | ✅ | 06-06 | /learning/news-verify-summary + 前端Tab |
| 63 | ✅ | 06-06 | Phase 50 已完成调度器注册 |
| 64 | ✅ | 06-06 | 持仓页加入 rec_index + news_signal + recent_wins |
| 65-67 | ✅ | 06-06 | ResultPage 加入 predicted_return + rank_score 列 |
| 68 | ✅ | 06-13 | DNA 实验室 3 机制自动化加入 |
| 69 | ✅ | 06-13 | 新闻特征系统改造 (→ Tushare 宏观数据) |
| 70 | ✅ | 06-13 | 新闻分类去重 + 龙虎榜精细化 v2.0 + 融资融券重写 |
| 71 | ✅ | 06-13 | TG 扫描阶段重组 v4.8.2 (15 项 P0/P1/P2 修复) |
| 72 | ✅ | 06-14 | 新闻页面重复标题修复 (SimHash 去重) |

---

## 施工规则

1. **先查 GUIDE, 再开工** — `grep "你的文件名" docs/DEVELOPER_GUIDE.md`
2. **一个 Phase 一次提交** — 不要跨 Phase 合并改动
3. **自检不通过 = 未完成** — 不要标记 ✅
4. **发现断链或新问题时** — 写在 Phase 备注栏, 不做额外修复 (留给架构师审查)
5. **主动写入执行日期** — 方便追踪进度
