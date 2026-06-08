# Stock Analyst Phase 执行计划 v1.0

> **用途**: 给开发窗口的 AI 使用。配合 `docs/DEVELOPER_GUIDE.md` 一起用。
> **工作流**: 每个 Phase 按顺序执行 → 读完"施工前检查"→ 改代码 → 跑自检 → 标记 ✅

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

---

## 施工规则

1. **先查 GUIDE, 再开工** — `grep "你的文件名" docs/DEVELOPER_GUIDE.md`
2. **一个 Phase 一次提交** — 不要跨 Phase 合并改动
3. **自检不通过 = 未完成** — 不要标记 ✅
4. **发现断链或新问题时** — 写在 Phase 备注栏, 不做额外修复 (留给架构师审查)
5. **主动写入执行日期** — 方便追踪进度
