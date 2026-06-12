# Stock Analyst 开发施工手册 v2.1

> **用途**: 给开发窗口的 AI 使用。每次修改代码前，先查找你要改的文件/表，
> 然后看"连带影响"表格 + 全局约定。新增/修改任何模块前，先查阅第七章"统一工具库"。
> **最近更新**: 2026-06-09 — 大神仙空 v2.0 + AlphaFlow 信号规则 + 事件过滤

---

## 零、新增模块时必读 ⭐ v2.0 新增

**不要在模块内打补丁。** 以下全局能力已统一提供，新增模块时直接导入：

| 需求 | 导入 | 说明 |
|------|------|------|
| 数值安全 | `from app.utils.numpy_utils import safe_float, sanitize_array, sanitize_for_json` | 不要再写 `np.nan_to_num` 或 `if np.isnan(x)` |
| 超额收益 | `from app.core.market_data import compute_excess_return, get_benchmark_closes` | 不要再写自己的 700001.TI SQL |
| 进度回调 | `from app.core.progress import ProgressCallback, make_progress_adapter` | 统一 4 参数 `cb(phase, current, total, message)` |
| 代码规范 | `from app.utils.stock_code import normalize_ts_code, strip_suffix` | 不要再写 `startswith('6') → .SH` |
| 名称查询 | `from app.core.name_resolver import get_stock_name, batch_get_stock_names` | 不要再直接查 scan_results |
| 前复权K线 | `from app.services.kline_utils import get_adjusted_kline, get_ex_rights_dates` | K线已全局前复权, 除权日可精确识别 |

---

## 如何使用

```
步骤 0: 先查"统一工具库" → 需要的功能是否已有全局实现
步骤 1: 确定你要改的文件 → 在下方目录中找到它
步骤 2: 读该文件的"连带影响"表格 → 列出所有必须同步修改的文件
步骤 3: 做修改 → 自检 → 提交
```

**搜索方式**: grep 你要改的文件名或表名，只读命中的段落。

---

## 一、核心 Python 文件

### `app/services/deep_scorer.py`

**职责**: 深度评分主引擎。`deep_analyze()` 是 5 管线段的编排者 (v4.4: JSON 序列化已加边界守卫 sanitize_for_json)。

**连带影响** (改这个文件必须检查):

| 如果你改了 | 必须同步检查 |
|-----------|------------|
| `deep_analyze()` 函数签名 | `app/api/analysis.py:15,128` — trigger_analysis 调用 signature |
| | `app/api/scan.py:206,208` — trigger_scan SSE 调用 |
| `_deep_enrich_phase()` 新增字段 | `app/api/result.py:163-167` — result/final 透出字段 |
| | `frontend/src/pages/ResultPage.tsx` — 前端渲染该字段 |
| `_deep_persist_phase()` INSERT 列 | `app/models/data_models.py` — ORM 模型列对齐 |
| | 数据库 ALTER TABLE — 新列必须在 DB 中存在 |
| `DEFAULT_WEIGHTS` | `app/services/shadow_trainer.py:75` — import 此常量 |
| `_deep_preload_phase()` 预加载调用 | `app/services/predictive_features.py` — 训练特征预加载 |

**进度回调**: ⭐ v4.5 已统一为 4 参数 `progress_cb(phase, current, total, message)`。不要再传 3 参数。

---

### `app/services/predictive_features.py`

**职责**: 特征工程。`build_features()` 构建单股特征, `build_training_data()` 构建训练集。

**连带影响**:

| 如果你改了 | 必须同步检查 |
|-----------|------------|
| `FEAT_NAMES` 列表增删特征 | `app/services/predictive_scorer.py:71` — `batch_predict` 用 FEAT_NAMES 顺序组装向量 |
| | `scripts/train_predictive_model.py` — 训练脚本读取 FEAT_NAMES |
| `build_training_data()` 返回值 | `scripts/train_predictive_model.py:23` — 解包 (X,y,weights,sources,groups) |
| 大盘基准 | `app/core/market_data.py` — ⭐ v4.5 统一使用 `compute_excess_return()` |

**关键约定**:
- 训练标签 = 超额收益 vs 700001.TI (⭐ v4.5 统一公式: 交易日计数, 非日历日)
- 特征缺失时填 0, 不要填 None 或 NaN (⭐ `app/utils/numpy_utils.safe_float` 统一处理)
- `FEAT_NAMES` 顺序 = `build_features` 返回 dict 的顺序 = `batch_predict` 读的顺序

---

### `app/services/shadow_trainer.py`

**职责**: 影子训练引擎 (Bayesian Optimization + Per-Stock 权重优化)。

**⭐ v4.5 重要变更**:
- `_bench_ret()` 日历日计数已修正为**交易日计数** (修复系统性偏误)
- `_bench_ret()` 函数已完全移除, 改为 `_index_ret()`
- 基准加载改用 `app.core.market_data.get_benchmark_closes()` (模块级缓存)
- ⚠️ **旧 shadow 训练结果需重训**: param_library 中 is_shadow=true 的权重基于旧 (日历日) 标签

---

### `app/api/result.py`

**职责**: 推荐结果 API (`GET /result/final`)。

**连带影响**:

| 如果你改了 | 必须同步检查 |
|-----------|------------|
| `base_select` SQL 加列 | 列索引偏移 — `r[17]` 之后所有列的 index 都要 +1 |
| | 最安全做法: 新列放最后, `r[-1]` 取值 |
| `details` JSON 字段增删 | `frontend/src/pages/ResultPage.tsx` — 渲染该字段 |
| `rec_index` 权重 | 前端 `ResultPage.tsx:57` sortKey 默认排序 |

---

### `app/api/scan.py`

**职责**: TG 信号扫描 + SSE 进度回传 (POST /scan/trigger)。

**进度回调**: ⭐ v4.5 标准 `progress_cb(phase, current, total, message)` — 4 参数。如需适配旧代码用 `make_progress_adapter()`。

---

## 二、⭐ DNA 个性化模型 (v4.5 新增)

### `app/services/stock_dna/` 包 (10 个模块)

**包位置**: `app/services/stock_dna/`
**API 路由**: `app/api/dna.py` (`/api/dna/*`, 7 端点)
**数据库**: `stock_dna.*` schema (3 表, 独立于现有系统)
**前端**: `frontend/src/components/DnaLab.tsx` (4 Tab: 概览/单股档案/对比矩阵/表情历史)
**模型文件**: `backend/models/dna/{symbol}_model.json` (Per-Stock XGBoost)

**关键约定**:
- ⭐ DNA 系统**完全并行**，不修改任何现有代码
- 特征维度: 146 维 (73日线 + 15表情 + 15市场 + 12转移 + 8周期 + 15历史 + 8交互)
- Per-Stock XGBoost: 80树 × depth=3, Huber δ=3.0
- 日线伪表情降级: 无分时数据时用 OHLCV 计算简化表情
- 周期检测: 评分制 (≥2/3条件 + 5日滑动窗口), 非 AND 制

**连带影响**:

| 如果你改了 | 必须同步检查 |
|-----------|------------|
| `features.py` 增删维度 | `model.py` ALL_FEAT_NAMES 同步 |
| | `inference.py` `_build_today_features()` 同步 |
| | `data_builder.py` 特征组合同步 |
| `emotion.py` 表情逻辑 | `data_builder.py` 聚类调用 + `inference.py` 伪表情降级 |
| `cycle.py` 周期阈值 | `data_builder.py` 周期统计 + `inference.py` 周期特征 |
| `data_builder.py` 样本生成 | `model.py` 训练数据读取列名 |

---

## 三、数据库表

### `signal_history`

**列**: `symbol, scan_date, composite_score, archetype, market, push_count_30d, price_zone_*, ret_t1/2/3/5, max_gain/loss_pct, outcome_label, deception_type, relative_position, sector_direction, sector_lifecycle, sector_rank_5d, market_5d, predicted_return, predicted_win_prob, excess_return`

### `analysis_scores`

**列**: `scan_date, symbol, name, tech/kline/fund_score, sector_bonus, composite_score, fundamental_adjustment, market_correction, details(JSONB), archetype, weight_snapshot, adjustment_reasons, dimension_scores, win_probability, downside_risk`

**⭐ v4.5**: `details` JSONB 序列化已加 `sanitize_for_json()` 边界守卫，NaN/Inf 自动转为 null。

### `daily_kline`

**⭐ v4.5 新增列**: `adj_factor DOUBLE PRECISION DEFAULT 1.0` — 复权因子。全量数据已通过 `resync_all_kline.py` 前复权。

### `stock_dna.daily_samples` / `stock_dna.profiles` / `stock_dna.predictions`

**独立 schema**，与现有系统零交叉污染。详见 `architecture.md` §5.2。

---

## 四、前端页面

### `ResultPage.tsx`

**读取字段** (20+): `symbol, name, composite_score, rec_index, relative_position, strategy_label, peer_rank, sector_tier, resonance_type, ...`

A 股配色: 红涨绿跌: rec_index ≥ 80 → 红, < 40 → 绿。

### `DnaLab.tsx` ⭐ v4.5 新增

4 个子 Tab，集成在 `LearningPage.tsx` 的 "🧬 DNA实验室"。

---

## 五、跨模块依赖速查

### 改"评分→推荐"链路

```
deep_scorer._deep_enrich_phase
  → deep_scorer._deep_persist_phase (details JSON, ⭐ sanitize_for_json guarded)
    → result.py get_final_results (SELECT → data dict)
      → ResultPage.tsx (渲染)
```

### 改"训练→预测"链路

```
predictive_features.build_training_data
  → train_predictive_model (fit + save)
    → predictive_scorer.batch_predict (load + infer)
      → deep_scorer._deep_enrich_phase (predict blend)
```

### 改"超额收益计算" ⭐ v4.5

```
任何地方需要超额收益 → 统一使用 app.core.market_data.compute_excess_return()
  → 内部调用 get_benchmark_closes() (模块级缓存, 全系统共享)
  → 交易日计数 (非日历日!)
```

### 改"数据库表结构"

```
① ALTER TABLE (DB)
② ORM model 更新
③ 所有 INSERT/UPDATE 语句更新
④ result/analysis API SELECT 更新
```

---

## 六、常见补丁原因速查

| 补丁类型 | 原因 | 预防 |
|---------|------|------|
| "字段透出缺失" | 后端加了字段但 result/analysis 没加 | 改 details JSON 时同步改 SQL SELECT |
| "前端不渲染" | 后端透出了但前端不读 | 改 API 响应时同步改前端 |
| "模型特征数不匹配" | FEAT_NAMES 加了但模型没重训 | 改 FEAT_NAMES 后立即跑 train |
| "progress_cb 参数不匹配" | 新模块传错参数数量 | ⭐ 使用 `make_progress_adapter()` |
| "NaN 导致 JSON 崩溃" | 评分维度产生 NaN → json.dumps 崩溃 | ⭐ 所有 json.dumps 前调用 `sanitize_for_json()` |
| "除权数据污染" | 新模块直接用 daily_kline 原始数据 | ⭐ 系统已全局前复权, 直接用即可 |
| "BJ 股票被丢弃" | `else: continue` 丢弃北交所代码 | ⭐ 使用 `normalize_ts_code()` |

---

## 七、全局约定 ⭐ v2.0

| 约定 | 值 |
|------|-----|
| 大盘基准 | `700001.TI` (同花顺全A等权), 不是 `000001.SH` |
| 训练标签 | 超额收益 = stock_ret - market_ret (700001) ⭐ 统一交易日计数 |
| 模型文件 | `models/predictive_scorer.json` (回归) + `predictive_ranker.json` (排序) |
| A 股配色 | 红涨绿跌 (rec_index ≥ 80→红, < 40→绿) |
| SSE 进度 | `progress_cb(phase, current, total, message)` — **必须 4 参数** |
| L1 过滤 | TG 扫描后 L1 级信号不进入 deep_analyze |
| 股票代码 | `normalize_ts_code()` — 支持 6xxxxx.SH / 0xxxxx.SZ / 8xxxxx.BJ / 920xxx.BJ |
| NaN 处理 | `safe_float()/sanitize_array()` — 不要再写 `np.nan_to_num` |
| JSON 序列化 | `sanitize_for_json()` — 在 json.dumps 之前调用 |
| 除权 | ⭐ 系统已全局前复权 (daily_kline.adj_factor 列)。**不要再加任何除权检测代码** |
| 代码规范 | `normalize_ts_code()` — 不要写 `startswith('6') → .SH` |

---

## 八、⭐ 统一工具库 (v2.0 新增)

### 数值安全 (`app/utils/numpy_utils.py`)

```python
from app.utils.numpy_utils import (
    safe_float,        # val → float, NaN/Inf/None → default (0.0)
    safe_auc,          # AUC NaN → 0.5 (随机基线)
    safe_rsi,          # RSI/KDJ NaN → 50 (中性)
    sanitize_array,    # arr NaN/Inf → fill (默认 0.0)
    sanitize_for_json, # dict/list/numpy → JSON-safe (NaN→null)
    div0,              # a/b, b≈0 → default
    safe_corrcoef,     # Pearson r, 常数序列→0.0
)
```

### 基准数据 (`app/core/market_data.py`)

```python
from app.core.market_data import (
    get_benchmark_closes,     # → dict[date, float] (700001.TI, 模块级缓存)
    compute_excess_return,    # 交易日计数超额收益 (数据不足→0.0)
    compute_excess_return_or_fallback,  # 数据不足→纯股票收益 (向后兼容)
)
```

### 进度回调 (`app/core/progress.py`)

```python
from app.core.progress import ProgressCallback, make_progress_adapter, NoopProgress
# ProgressCallback: cb(phase: str, current: int, total: int, message: str = "")
# make_progress_adapter(cb): 将任意回调包装为标准 4 参数
```

### 股票代码 (`app/utils/stock_code.py`)

```python
from app.utils.stock_code import normalize_ts_code, strip_suffix, classify_board
# normalize_ts_code('600519') → '600519.SH'
# normalize_ts_code('920123') → '920123.BJ'
# strip_suffix('002594.SZ')  → '002594'
```

### 名称解析 (`app/core/name_resolver.py`)

```python
from app.core.name_resolver import get_stock_name, batch_get_stock_names, ensure_name_cache
```

### 前复权K线 (`app/services/kline_utils.py`)

```python
from app.services.kline_utils import (
    get_adjusted_kline,        # 获取前复权K线 (含 adj_factor)
    get_ex_rights_dates,       # 从 adj_factor 精确识别除权日 (不再靠阈值猜测!)
    iter_non_exrights_chunks,  # 按除权日切分连续K线段
)
```

### 大神仙空 (`app/services/big_fairy.py`) ⭐ v4.7

```python
from app.services.big_fairy import (
    _big_fairy_from_arrays,  # 纯NumPy计算 (closes,highs,lows,volumes,symbol) → dict, 无DB I/O
    compute_big_fairy,        # DB查询版 (symbol, session) → dict
)
# 返回: {score(0-5), signal(normal/weak/sell/strong_sell), bearish(bool),
#         dimensions(list), k,d,j, macd_hist, rsi14, close, ma5,ma10,ma20, details}
# score≥2 = 卖出信号 (偏空), score≥3 = 强空
# 7 维度: KDJ + MACD + MA均线 + RSI + 量价关系 + 短期动量 + 超买综合
```

### 信号计算规则 (`app/services/alphaflow_pool_service.py`) ⭐ v4.7

```python
# 锁死判定 — lock_detector.py v2.3
from app.services.lock_detector import detect_lock_simple
# 返回包含 state 字段: "locked" | "breakout_up" | "breakout_down"

# AlphaFlow 信号优先级:
# 1. 锁死中 → watch (TG/BF 都不看)
# 2. 主升浪 + TG买入(10天延续) → buy
# 3. 主升浪 + BF卖出(10天延续) → sell  
# 4. TG+BF 同时活跃 → 按日期offset比较, 最新信号胜出
# 5. 破位下跌 → sell
```

### 事件过滤 (`app/services/event_detector.py`) ⭐ v4.7

```python
# LLM分析前已过滤: 商品期货/汇率/宏观指标类新闻
# 命中关键词但有公司级白名单(中标/签约/减持/业绩/公告/涨停) → 保留
# 过滤逻辑在 analyze_all_sources() 中, Stage 1 标签之前
```
