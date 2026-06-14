# Stock Analyst 系统架构文档

> **版本**: v4.8 | **日期**: 2026-06-14 | **核心依赖**: DeepSeek API + XGBoost + PostgreSQL + DNA 个性化模型 + 大神仙空 v2.0
> **审计状态**: v4.8 — DNA实验室自动化 + 新闻采集优化 + 宏观数据改造 + TG扫描阶段重组 + 新闻去重修复

---

## 0. 系统级 P0 工具基础设施 ⭐ v4.5 新增

v4.5 完成了 **7 个系统级 P0 能力升级**，将数十处分散的防御代码收敛为统一工具模块：

| 工具模块 | 位置 | 替代的分散实现 |
|---------|------|---------------|
| **`app/utils/numpy_utils.py`** | NaN/Inf/JSON 安全 | 14 处 `nan_to_num`/`isnan`/`fillna` (4种不同策略) |
| **`app/core/market_data.py`** | 基准加载 + 超额收益 | 3 处独立公式 + 14 处 700001.TI SQL + **影子训练日历日 bug** |
| **`app/core/progress.py`** | 进度回调协议 | 3 种回调签名 (2/3/4参数混用) |
| **`app/utils/stock_code.py`** | 代码规范化 | 9 处 `startswith('6')→.SH` 复制 + **6 处 BJ 代码丢弃 bug** |
| **`app/core/name_resolver.py`** | 名称三级缓存 | 5 处绕过缓存直接查 scan_results |
| **`scripts/resync_all_kline.py`** | 全局前复权 | **9 个除权补丁** (3种阈值: 15%/18%/20%) |
| **`app/services/kline_utils.py`** | 前复权K线工具 | `get_adjusted_kline()` / `get_ex_rights_dates()` 精确识别 |

**核心原则**: 每个 P0 问题都在数据入口或边界统一解决，而非在每个模块中打补丁。

### ⭐ DNA 个性化模型实验室 (v4.5 新增)

股票 DNA 系统实现了 AlphaGo 风格的个性化分析：
- **理念**: 不是 5507 只股票共享一套规则，每只股票从自己的历史中学到"残局棋谱"
- **两层突破**: 打掉 TG 信号枷锁（每天都是数据点） + 打掉 T+2 枷锁（多窗口自适应）
- **五维特征**: 日线截面(73维) + 分时表情(15维) + 市场情绪(15维) + 转移矩阵(12维) + 周期节律(8维) + 历史统计(15维) + 交互(8维) = 146维
- **表情聚类**: 15维→KMeans++ 轮廓系数选 K→5-8种个性化表情→马尔可夫转移矩阵→明日情绪预测
- **老兵周期**: 评分制锁死检测 (ATR<0.8 + MA<0.04 + VOL<0.8, ≥2/3条件+5日滑动窗口容错)
- **Per-Stock XGBoost**: 80树×depth=3, Huber loss δ=3.0, 4窗口联合输出 (T+2/5/10/20)
- **贝叶斯置信度**: `confidence = n / (n+500)`，样本<500天向原型收缩
- **独立并行**: 独立 API (/api/dna/*)、独立 DB (stock_dna.*)、不修改现有代码

### ⭐ 全局前复权 (v4.5 新增)

```
resync_all_kline.py —
  Tushare adj_factor API → 前向填充逐日复权因子 → 手动前复权公式
  close_adj[t] = close_raw[t] × (adj_factor[t] / adj_factor[latest])
  → daily_kline 全量覆盖 + adj_factor 列标记
```

退役了 **9 个除权补丁**: `find_last_ex_rights()`, `_is_ex_rights_day()`, `_adjust_ex_rights()`, 及 6 个调用方。

---

## 1. 系统概述

### 两大核心管线

Stock Analyst 目前运行 **两条独立又互补的管线**，并通过交叉反哺机制联动。v4.3 新增 **个股历史复盘 + 四维共振 + 操盘手法反推**：

```
管线 1: TG 日线扫描 (成熟)          管线 2: AlphaFlow 主升浪捕获 (v4.3)
─────────────────────────────      ────────────────────────────────────
日线 TG 指标 18 步计算              ① 锁死检测 (双窗口 + 除权免疫)
→ ★ Phase 1.5 周线 TG 扫描         → ~200 只锁死候选
→ 双周期信号匹配 (共振/日线/周线)   ② 老兵识别 (4+ 周期统计分析)
→ 14 维深度评分（分段权重+衰减）    ③ 历史评估 (A-G 8项过滤)
→ 策略原型分类                    ④ ★ 48维特征 + XGBoost V3 概率
→ ★ QUALITY_GATE 自适应放宽        ⑤ 策略分类 (8种 strategy_label)
→ 推荐排序（三级优先级）            ⑥ 筹码吸收 (三区模型 + 除权免疫)
                                   ⑦ 波段目标预测 (退市股排除 + 3σ过滤)
         ┌── 交叉反哺 ──┐           ⑧ 池管理 (老兵豁免 + 结构维护)
  分钟线 N/M 检测 ✅      │          ⑨ ★ 量能历史参考范围 (锁死周期分布)
  板块联盟验证 ✅         │
  信号质量评分 ✅         │
  市场门控 v2.0 ✅        │
  多周期验证 ✅           │
  ★ 周线共振评分 ✅       │
  ★ AlphaFlow 净买力 ────┘  (TG composite_score + TG→AlphaFlow 第48维)
                          │
  ★★★ v4.3 智能研判层 ★★★  │
  个股历史复盘 (7项)       │
  四维共振 (指数/板块/消息/筹码)  │
  操盘手法反推 (5分钟线)    │
  系统健康自动激活          │
  空仓建议 (force_empty)    │
```

### 核心能力矩阵

| 能力 | 管线 | 说明 |
|------|------|------|
| **TG 全市场扫描** | 管线 1 | 每日对 5000+ A 股运行 TG 精准买卖指标 V11.2，主板/创业板/科创板差异化阈值 |
| **14 维深度评分** | 管线 1 | ★ v4.3 按市场状态分段权重 + 软衰减 (regime>60天混入全局) + 安全门控 (n≥50/params≥10/AUC≥0.55) |
| **策略原型分类** | 管线 1 | K-means 聚类将股票分为 5 个策略原型，不同原型使用不同评分权重偏移 |
| **★ 个股历史复盘** | 管线 1 | ★ v4.3 7 项子复盘: 信号回溯+形态匹配+关键位置+筹码模拟+市场敏感性+四维共振+操盘手法 |
| **★ 四维共振分析** | 管线 1 | ★ v4.3 指数/板块/消息/筹码 四维度信号归因 → 独立率/领先率/伪强势率/技术驱动率 |
| **★ 操盘手法反推** | 管线 1 | ★ v4.3 5分钟线检测快速拉升/砸盘/托单/尾盘偷袭/开盘冲锋 → 提升度分析 → 触发条件发现 |
| **★ QUALITY_GATE 自适应** | 管线 1 | ★ v4.3 L1/L2 两级自适应放宽 (通过<10→降sq/wp/ts→仍<8→降sc/wp) |
| **★ 强制空仓** | 管线 1 | ★ v4.3 恐慌杀跌+胜率<25%+上涨<20% → force_empty → 前端红色横幅 |
| **★ 系统健康自动激活** | 管线 1 | ★ v4.3 每日检测分段权重/校准器/原型偏移达标 → 自动标记is_active + sync_log |
| **★ 信号异常检测** | 管线 1 | ★ v4.3 每日检测买入信号数量/win_probability偏离历史3σ → WARNING + sync_log |
| **★ 影子模型对比** | 管线 1 | ★ v4.3 每周日 evaluate_shadow_vs_main() → 连胜3周自动切换 |
| **AlphaFlow 锁死检测** | 管线 2 | ⭐ v2.2 双窗口锁死 (15-20日≤15% + 20-40日≤17%) + 除权免疫 |
| **老兵检测** | 管线 2 | ⭐ 4+锁死周期统计 (周期延长/振幅收敛/量萎缩) → pre_breakout/late_stage/monitoring |
| **历史评估+策略分类** | 管线 2 | ⭐ A-G 8项过滤 × quality_label → 8种 strategy_label |
| **XGBoost V3 概率** | 管线 2 | ⭐ ★ 48维特征 (含板块锁死期% + 6老兵增强 + TG反哺第48维), 版本校验 |
| **★ 量能历史参考** | 管线 2 | ★ v4.3 lock-detail 量能变化对比历史锁死周期分布 → 分位+标签 |
| **筹码吸收分析** | 管线 2 | ⭐ 三区模型 (Z_LOCK/Z_OVER/Z_BELOW) + 除权免疫, 吸收率 |
| **波段目标预测** | 管线 2 | ⭐ 历史浪幅统计 + 退市股排除 + 3σ极端值过滤 → target_zone + risk_levels |
| **5 分钟线分析** | 管线 2 | 底延/顶延/VWAP 计算 + T 模式网格建议 + 振幅收敛检测 |
| **结构性趋势检测** | 管线 2 | 摆动分析 → 关键支撑位 → 趋势破坏/崩塌判定 |
| **乏力度 5 阶段** | 管线 2 | 平台跌破逐层追踪 → 活跃→预警→破位→崩塌 四级判定 |
| **SXQS 资金博弈** | 共享 | ZIG 拐点 + H1/H2/H3 三级 EMA + VAR6/VAR7/VAR8 买卖力 + D/W 信号 |
| **分钟线反哺 TG** | 交叉 | N/M 形态检测 + 板块联盟验证 + 信号质量评分 |
| **AlphaFlow 净买力反哺** | ★ 交叉 v4.1 | XGBoost 最强特征 (25% importance) 作为 TG composite_score 修正因子 |
| **市场门控 v2.0** | 管线 1 | ⭐ 7市场体制 + 涨跌比 + 风格偏向(大小盘) + 双阈值 |
| **多周期验证** | 管线 1 | ⭐ 周MACD + 月趋势 + 背离检测 |
| **概率校准** | 管线 1 | ★ v4.1 T+3标签统一 + regime-aware分段校准 (数据不足自动回退) |
| **评分权重训练** | 管线 1 | ★ v4.1 Logistic Regression 真实盈亏训练 + 分段(bull/bear/range) + Bayesian持久化 |
| **周线双周期共振** | ★ 管线 1 v4.2 | 日线 TG + 周线 TG 独立信号 → resonance_type (weekly_resonance/daily_only/weekly_driven) → 三级排序 |
| **LLM 新闻分析** | 管线 1 | 爬取 4 源财经新闻 → DeepSeek 分类 → 深度分析 → 事件入库 |
| **LLM 精选反哺** | 管线 1 | 14 维结构化提示词 + 筹码硬指标 → DeepSeek 深度分析 → 批量横向评分 |
| **老兵突破率回测** | 管线 2 | ★ v4.1 按级别/分段的 T+5/T+20 突破率统计 (每周六自动) |
| **原型偏移校准** | 管线 1 | ★ v4.1 collect_archetype_calibration_data() 已就绪, 等待数据积累 |
| **退出信号** | 管线 1 | 止盈/止损/移动止盈/时间退出四类信号 |
| **持仓管理** | 管线 1 | ⭐ 资金账户 + 自动清仓(qty=0) + 待清仓 + 持股天数 + 筹码诊断 |

### DeepSeek 底座角色

DeepSeek 在系统中扮演 **三类角色**：

1. **新闻分析引擎**（Stage1 打标签 + Stage2 深度分析 + 晨报生成）—— **v4.8: Stage1 用 Flash, Stage2 公司级用 Pro, 行业/政策/商品用 Flash**
2. **个股深度分析师**（精选反哺/自动分析/持仓策略）—— 调用 chat 模型，含筹码硬指标附件
3. **结构化数据提取器**（持仓导入解析/反哺文本解析/批量横向评分）—— 调用 chat 模型

### v4.8 核心能力 (本次新增)

| 能力 | 模块 | 说明 |
|------|------|------|
| **DNA 实验室自动化加入** | `stock_dna_auto_join.py` | 3 机制: AlphaFlow突破+TG买入 / L3级 / 持仓变动, 异步训练不阻塞 |
| **新闻分类去重** | `news_classifier.py` | SimHash 跨源去重 + 三级分类 (company/sector/macro/garbage), macro_only 跳过 LLM |
| **龙虎榜精细化 v2.0** | `toplist_analyzer.py` | 机构 4 子类 (公募/北向/社保/QFII) + 游资 4 级 (顶级/一线/二线/三线) + 5 级共振 + 净买持续性 |
| **龙虎榜智能缓存** | `get_cached_daily_toplist()` | 历史永久 / 当日交易 5min / 休市 1h, 避免休市期间重复计算 |
| **龙虎榜 SSE 刷新** | `/api/scan/toplist-refresh` | 流式 sync → analyze → sector 3 阶段进度 |
| **新闻聚合接口** | `/api/scan/news-dashboard` | 6 请求 → 1 请求, 加载时间大幅减少 |
| **新闻新鲜度** | `/api/scan/news-freshness` | skip / crawl_only / analyze_only / full 4 种建议 |
| **新闻增量更新** | `news_pipeline.py` | 2h 内爬过跳过, 6h 内分析过跳过 LLM |
| **融资融券重写** | `get_margin_sentiment()` | 改用 rzye (融资余额) 直接判断亢奋/正常/谨慎 + 颜色 |
| **市场过滤 (后端)** | `trigger_scan?market_filter=` | 主板/中小板/创业板 服务端真过滤, 不再仅前端展示 |
| **DNA 异步训练** | `asyncio.create_task` | 60-180秒/只训练放入后台队列, 不阻塞 done 事件 |
| **进度推送节流** | `tg_engine.py` | scan phase 5% 步长推送, 5000只 → 100 事件 |
| **accuracy 隔离元参数** | `accuracy_tracker.py` | `isolated_meta=True` 写入独立列, 不覆盖主 discrimination |

### 技术栈

| 层 | 技术 | 版本/说明 |
|----|------|----------|
| 后端框架 | FastAPI | Python 3.13 |
| 异步数据库 | SQLAlchemy 2.0 + asyncpg | PostgreSQL |
| LLM 客户端 | httpx (async) | DeepSeek API v1 |
| 机器学习 | XGBoost + scikit-learn (LogisticRegression/StandardScaler) | AlphaFlow V2.1 (47维), TG 权重训练 |
| 数据分析 | pandas, numpy, scipy | TG 指标、K-means、Bayesian Opt |
| 浏览器自动化 | playwright | 新闻爬虫 |
| 数据源 | Tushare Pro | 日线/分钟线/财务/龙虎榜/申万指数/大盘指数 |
| 前端 | React 19 + TypeScript + Vite 8 | Ant Design 6 |
| 部署 | uvicorn | 单 worker（`--workers 1`） |

---

## 2. 目录结构与文件清单

```
Stock/
├── StockAnalyst.bat                      # 一键启动脚本
├── 系统自检.bat                          # 系统自检入口
├── README.md
├── backend/
│   ├── .env                              # 环境变量 (DB/DeepSeek/Tushare/百度千帆)
│   ├── requirements.txt                  # Python 依赖 (含 xgboost, scikit-learn)
│   ├── system_check.py                   # 6 维度系统自检 (DB/评分/学习/一致性/API/前端)
│   ├── _check.py                         # 快速检查
│   ├── models/                           # 模型文件
│   │   ├── alphaflow_xgb.json            # ★ XGBoost V2.1 47 维模型
│   │   ├── alphaflow_xgb_meta.json       # ★ V2.1 元信息 (training_date/feature_names/feature_hash)
│   │   ├── angel_model.json              # 天使模型 (待加载)
│   │   ├── guardian_model.json           # 守护模型 (signal_quality_scorer 已加载)
│   │   ├── dual_channel_meta.json        # 双通道元信息
│   │   └── backups/                      # ★ 模型备份目录 (retrain_xgb.ps1 自动创建)
│   ├── app/
│   │   ├── main.py                       # FastAPI 入口 + lifespan + 路由注册 + 后台调度
│   │   ├── core/
│   │   │   ├── config.py                 # Pydantic Settings (含 DEEPSEEK_PRO_MODEL)
│   │   │   ├── database.py               # async engine + session factory (pool_size=10)
│   │   │   ├── market_data.py            # ⭐ v4.5 统一基准加载 + 超额收益计算 (含缓存)
│   │   │   ├── progress.py               # ⭐ v4.5 进度回调协议 + 适配器工厂
│   │   │   ├── name_resolver.py          # ⭐ v4.5 名称解析三级缓存 (内存→DB→fallback)
│   │   │   ├── auth.py                   # X-User-ID Header 认证
│   │   │   └── security.py              # HTTPBearer 可选认证
│   │   ├── utils/                        # ⭐ v4.5 系统级工具模块
│   │   │   ├── numpy_utils.py            # NaN/Inf/JSON 安全 (safe_float/sanitize_for_json/safe_auc 等)
│   │   │   └── stock_code.py             # 代码规范化 (normalize_ts_code/strip_suffix/classify_board)
│   │   ├── models/
│   │   │   ├── base.py                   # DeclarativeBase + BaseMixin
│   │   │   └── data_models.py           # ScanResult, AnalysisScore, StockFundamentalSnapshot
│   │   ├── api/
│   │   │   ├── __init__.py               # 路由聚合 + /health (15 个路由)
│   │   │   ├── scan.py                   # TG 扫描 (SSE 两阶段) + 新闻 + NM验证 + 数据新鲜度
│   │   │   ├── result.py                 # 最终推荐 (市场门控 v2.0 + S3风险分类 + 板块感知)
│   │   │   ├── analysis.py              # 深度分析 + 手动加股(完整管线) + 删除
│   │   │   ├── comprehensive.py          # ★ 一键综合分析 (个股+板块+宏观+判定)
│   │   │   ├── alphaflow.py             # ★ AlphaFlow (pool/lock-detail/chip/wave/veteran-backtest)
│   │   │   ├── feedback.py              # ★ DeepSeek 反哺 + 批量横向评分(含筹码硬指标)
│   │   │   ├── holdings.py              # ★ 持仓 CRUD + 资金账户 + 自动清仓 + 筹码诊断
│   │   │   ├── learning.py              # ★ 学习面板 (训练/升级/回测/原型校准/权重)
│   │   │   ├── llm_analysis.py          # LLM 提示词生成 + 自动分析
│   │   │   ├── dna.py                   # ⭐ v4.5 DNA 实验室 API (7 端点: status/profile/predict/scan/compare/emotion/add-stock)
│   │   │   ├── ambush.py                # 潜伏猎手信号
│   │   │   ├── decisions.py             # 用户决策记录
│   │   │   └── settings.py              # 系统设置 (读写 .env)
│   │   └── services/
│   │       ├── tg_engine.py             # TG 全市场扫描引擎 (两阶段 SSE)
│   │       ├── tg_indicator.py          # TG V11.2 18 步指标计算 + 板块差异化参数
│   │       ├── tdx_functions.py         # 通达信指标函数 (MA/EMA/HHV/LLV/CROSS 等)
│   │       ├── deep_scorer.py           # ★ 14 维深度评分引擎 (1796 行, v4.1)
│   │       │                            #   含: 分段权重加载+安全门控+AlphaFlow净买力反哺
│   │       ├── enhanced_scorer.py       # 增强 6 维评分
│   │       ├── ma_scorer.py             # 均线趋势质量评分 + 支撑/压力位
│   │       ├── fingerprint_builder.py   # 11 维指纹构建器 (5 表预加载)
│   │       ├── archetype_classifier.py  # K-means 原型分类器 (5 原型)
│   │       ├── archetype_param_resolver.py # ★ 原型→权重/阈值解析 (5 原型偏移表 + 校准数据收集)
│   │       ├── probability_calibrator.py # ★ v4.1 概率校准 (T+3 + regime分段 + 小样本降权)
│   │       ├── scoring_trainer.py       # ★ v4.1 评分权重训练器 (552 行, 真实盈亏反馈)
│   │       │                            #   Logistic Regression + 分段训练 + Bayesian持久化
│   │       ├── market_gate.py           # ★ v2.0 市场门控 (7体制+涨跌比+风格偏向)
│   │       ├── multi_timeframe.py       # ★ 多周期验证 (周MACD+月趋势+背离)
│   │       ├── exit_signal_detector.py  # 退出信号检测 (止盈/止损/移动止盈/时间退出)
│   │       ├── event_detector.py        # 新闻事件分析引擎 v4.0
│   │       ├── news_crawler.py          # 新闻爬虫 (playwright)
│   │       ├── sector_heat_engine.py    # ★ 板块热度5阶段 (萌芽→发酵→高潮→分化→退潮)
│   │       ├── sector_alliance.py       # ★ 板块联动 + 涨停联盟检测
│   │       │
│   │       │ # ── AlphaFlow 核心服务 (v4.1) ──
│   │       ├── lock_detector.py         # ★ v2.3 双窗口锁死 (除权免疫已退役: 系统全局前复权)
│   │       ├── kline_utils.py            # ⭐ v4.5 前复权 K 线工具 (get_adjusted_kline/get_ex_rights_dates)│   │       │
│   │       │ # ── ⭐ DNA 个性化模型实验室 (v4.5) ──
│   │       ├── stock_dna/                # ⭐ v4.5 DNA 包 (10 个模块, 完全并行, 零现有代码侵入)
│   │       │   ├── __init__.py           # 包导出
│   │       │   ├── features.py           # 146 维特征工程 (73日线 + 15表情 + 15市场 + 12转移 + 8周期 + 15历史 + 8交互)
│   │       │   ├── emotion.py            # 日内表情聚类 (KMeans++ + 轮廓系数) + Laplace 平滑转移矩阵
│   │       │   ├── cycle.py              # 老兵周期检测 v2 (评分制, ATR<0.8/MA<0.04/VOL<0.8, 5日滑动窗口)
│   │       │   ├── market_context.py     # 大盘分时联动特征 (15维)
│   │       │   ├── data_builder.py       # 训练样本生成器 (daily_kline + min_kline → daily_samples)
│   │       │   ├── model.py              # Per-Stock XGBoost (80树×depth=3, Huber δ=3.0, 4窗口输出)
│   │       │   ├── inference.py          # DNA 推理服务 (模型缓存 + 特征重建)
│   │       │   ├── similarity.py         # 跨股票 DNA 余弦相似度
│   │       │   └── dna_models.py         # ORM (stock_dna.daily_samples/profiles/predictions)
│   │       ├── alphaflow_veteran.py     # ★ 老兵检测 (含 backtest_veteran_breakout_rate)
│   │       ├── alphaflow_evaluator.py   # ★ 历史评估 A-G 过滤 + strategy_label 策略分类
│   │       ├── alphaflow_features.py    # ★ 47 维特征提取 (含真实板块锁死期% + 6老兵增强)
│   │       ├── alphaflow_pool.py        # ★ 完整管线 + _load_xgb_model() 版本校验 (719 行)
│   │       ├── chip_analyzer.py         # ★ 筹码吸收三区模型 + 除权免疫 (338 行)
│   │       ├── wave_predictor.py        # ★ 波段预测 + 退市股排除 + 3σ过滤 (374 行)
│   │       ├── fatigue_detector.py      # 乏力度 5 阶段 (浪顶→破平台→加速下跌)
│   │       ├── structure_break_detector.py # 结构性破坏 (摆动分析+关键支撑)
│   │       ├── micro_pattern_detector.py  # 3 分钟微剧本 (5 维吸筹评分)
│   │       ├── five_stage_detector.py   # 5 阶段检测
│   │       ├── intraday_analyzer.py     # 盘中异动分析 (2%+涨幅出货/吸筹判定)
│   │       ├── minute_nm_detector.py    # ★ N/M 形态检测引擎 (分时段对比法+跨日聚合)
│   │       ├── signal_quality_scorer.py # 信号质量评分 (含 NM 验证入口)
│   │       │
│   │       │ # ── 自学习服务 ──
│   │       ├── learning_engine.py       # 学习引擎 (T+5 滚动回测+Bayesian 调度)
│   │       ├── bayesian_optimizer.py    # Bayesian 参数优化 (Normal-Normal 共轭, 4 参数组)
│   │       ├── shadow_trainer.py        # 影子训练引擎 (Bayesian Opt)
│   │       ├── contextual_bandit.py     # 上下文 Bandit (Thompson Sampling, 待接入)
│   │       ├── replay_buffer.py         # 经验回放缓冲 (6280 条经验)
│   │       ├── dual_channel_trainer.py  # 双通道训练器 (天使+守护, 待调度)
│   │       ├── self_learning_bootstrap.py # ★ 自学习 Bootstrap (对接 scoring_trainer)
│   │       │
│   │       │ # ── 数据与通用服务 ──
│   │       ├── deepseek.py              # DeepSeek API 客户端 (httpx, 180s)
│   │       ├── llm_deep_analyzer.py     # ★ LLM 深度分析 (提示词+解析+筹码段生成)
│   │       ├── feedback_parser.py       # 反哺文本解析
│   │       ├── feedback_integration.py  # 反馈评分融合
│   │       ├── baidu_search.py          # 百度千帆 AI Search (日配额 50/6h 缓存)
│   │       ├── tushare.py               # Tushare K 线数据
│   │       ├── tushare_common.py        # Tushare API 封装 (重试+QPS 控制)
│   │       ├── realtime_quote.py        # 东方财富实时行情
│   │       ├── stock_name_cache.py      # 股票名称缓存
│   │       ├── background_sync.py       # ★ 每日调度 (含周度训练/校准/回测, 403 行)
│   │       ├── toplist_analyzer.py      # 龙虎榜分析
│   │       ├── trend_filter.py          # 趋势过滤器
│   │       ├── tail_market_scanner.py   # 隔天尾盘扫描
│   │       ├── ambush_scanner.py        # 潜伏猎手 (4 阶段过滤)
│   │       ├── pattern_engine.py        # 形态扫描引擎
│   │       ├── pattern_scanner.py       # K 线形态量化检测
│   │       ├── comprehensive_analyzer.py # ★ 一键综合分析引擎
│   │       ├── session_manager.py       # ⚠️ 已简化: 仅 MAX(scan_date) 查询
│   │       └── accuracy_tracker.py      # 推荐准确率追踪
│   └── scripts/
│       ├── download_today.py            # 下载当日行情
│       ├── backfill_history.py          # 历史回填
│       ├── sync_min_kline.py            # ★ 分钟 K 线同步 (pool + holdings 股票)
│       ├── sync_toplist_detail.py       # ★ 龙虎榜明细同步
│       ├── refresh_fundamental_snapshot.py # 基本面快照刷新
│       ├── add_weekly_columns.py        # ★ 方案 B 迁移脚本 (周线字段) (v4.2)
backtest_weekly_resonance.py # ★ 方案 B 回测验证 (v4.2)
test_drill.py              # ★ v4.3 个股复盘测试脚本
test_full_drill.py         # ★ v4.3 全维度复盘测试
│       ├── backtest_weekly_resonance.py # ★ 方案 B 回测验证 (v4.2)
│       │
│       │ # ── AlphaFlow 脚本 ──
│       ├── alphaflow_train_v2.py        # ★★ XGBoost V2.1 训练 (47维, 含 sector_closes, 版本元信息)
│       ├── alphaflow_train.py           # V1 训练脚本
│       ├── alphaflow_label.py           # 训练标签生成
│       ├── alphaflow_mins.py            # 分钟线特征提取
│       ├── alphaflow_stats.py           # 统计特征
│       │
│       │ # ── 分钟线反哺 TG ──
│       ├── tg_mins_experiment.py        # 交易员视角: 20 天分时图→T+2 涨跌预测
│       ├── mins_egg_train.py            # 蛋期分时训练 (批量下载+特征提取)
│       ├── mins_egg_vs_goose.py         # 蛋 vs 大雁分时特征对比
│       │
│       │ # ── 其他脚本 ──
│       ├── phase0_migrate.py            # Phase 0 迁移 (申万指数/牛熊/退市股)
│       ├── phase0_sync.py               # 行业指数同步 + 牛熊阶段划分
│       ├── phase1_migrate.py            # Phase 1 迁移 (原型扩展)
│       ├── rebuild_archetypes.py        # 重建 K-means 质心
│       ├── rebuild_archetypes_market.py # 按市场重建原型
│       ├── bootstrap_train.py           # Bootstrap 训练
│       ├── build_dimension_tags.py      # 维度标签构建
│       ├── extend_dimension_tags.py     # 标签扩展
│       ├── analyze_recommendations.py   # 推荐胜率分析
│       ├── analyze_stratification.py    # Top-N 分层分析
│       ├── analyze_win_factors.py       # 赢家特征分析
│       ├── analyze_exit_timing.py       # 退出时机分析
│       ├── backtest_gate.py             # 门控回测
│       ├── backtest_exit_signals.py     # 退出信号回测
│       ├── backtest_benchmark.py        # 基准回测
│       ├── grid_search_gates.py         # 门控网格搜索
│       ├── transform_scores.py          # 分数变换
│       ├── backfill_cashflow.py         # 现金流回填
│       ├── backfill_fingerprint_dims.py # 回填指纹维度
│       ├── test_ma_score.py             # 均线评分测试
│       ├── test_feedback_parse.py       # 反哺解析测试
│       ├── test_e2e_feedback.py         # 端到端反哺测试
│       ├── test_deepseek_api.py         # DeepSeek API 测试
│       ├── test_news_llm.py             # 新闻 LLM 测试
│       ├── test_news_by_source.py       # 分源新闻测试
│       └── test_bootstrap.py            # Bootstrap 测试
├── frontend/
│   ├── package.json                     # React 19 + Vite 8 + Ant Design 6
│   ├── vite.config.ts                   # Vite 配置 (/api → 127.0.0.1:8000 代理)
│   ├── src/
│   │   ├── main.tsx                     # ReactDOM.createRoot
│   │   ├── App.tsx                      # 根组件 + BrowserRouter + 导航 + 13 Routes
│   │   ├── lib/
│   │   │   ├── api.ts                   # axios 封装 (5 次重试 502/503/504)
│   │   │   └── useDeepAnalysis.ts       # 深度分析 Hook (最多 3 只)
│   │   ├── pages/
│   │   │   ├── ScanPage.tsx             # TG 扫描页 (SSE 两阶段 + NM Defense + ★周线共振标签)
ResultPage.tsx           # ★ v4.3 最终推荐 (老股民研判区域+综合评级+正负分栏+操作建议)
AlphaFlowPage.tsx        # ★ v4.3 AlphaFlow (结论先行+四层信息架构+量能历史参考)
│   │   │   ├── ResultPage.tsx           # ★ 最终推荐 (市场门控 v2.0 + 信号质量徽章)
│   │   │   ├── AlphaFlowPage.tsx        # ★ AlphaFlow (老兵层级/策略标签/天时分/盘面分析)
│   │   │   ├── DeepAnalysisPage.tsx     # LLM 深度分析 (含重试单股按钮)
│   │   │   ├── HoldingsPage.tsx         # ★ 持仓管理 (资金账户/清仓/待清仓/筹码诊断)
│   │   │   ├── AnalysisPage.tsx         # 分析结果
│   │   │   ├── LearningPage.tsx         # 自学习面板 (概览/参数/经验/★分段权重)
MonitorPage.tsx           # ★ v4.3 系统监控 (老兵回测+校准+就绪状态)
│   │   │   ├── MonitorPage.tsx           # ★ 系统监控面板 (老兵回测/原型校准/权重状态) (v4.2)
│   │   │   ├── BlueprintPage.tsx        # 6 阶段流水线
│   │   │   ├── SettingsPage.tsx         # 系统设置
│   │   │   ├── AmbushPage.tsx           # 潜伏猎手
│   │   │   ├── StockSelectPage.tsx      # 股票选择
│   │   │   ├── TailMarketPage.tsx       # 尾盘战法
│   │   │   └── NewsPage.tsx             # 新闻速报
│   │   └── components/
│   │       ├── DeepAnalysisModal.tsx     # 深度分析弹窗
│   │       ├── FeedbackModal.tsx         # 反哺弹窗 (粘贴→解析→预览→提交)
│   │       └── PromptModal.tsx           # 提示词弹窗
│   └── dist/                            # 生产构建产物
├── browser-extension/                    # Edge/Chrome 扩展 (Manifest V3)
│   ├── manifest.json
│   ├── content.js                       # 逐消息注入按钮 + 股票代码对话框
│   ├── style.css                        # 暗色主题
│   ├── popup.html + popup.js            # 健康检查
│   ├── background.js                    # Service Worker
│   └── INSTALL.md                       # 安装指南
├── docs/
│   ├── architecture.md                  # 本文档 (v4.1)
│   ├── CHANGELOG.md                     # 变更日志
│   ├── news.md                          # 新闻模块文档
│   ├── 自学习升级.md                    # 自学习升级设计方案 v2.2 (13 章)
│   └── post_deployment_monitoring.md    # ★ 部署后日志监控指南
├── retrain_xgb.ps1                      # ★ XGBoost 重训脚本 (特征#41真实化 + 版本校验)
└── verify_all.ps1                       # ★ 完整部署验证脚本
```

---

## 3. 模块架构

系统分为 **10 个逻辑模块**：

### 3.1 数据采集层

| 职责 | 入口文件 | 关键函数 | 输出 |
|------|---------|---------|------|
| K 线下载 | `tg_engine.py` | `download_latest_kline()` | `daily_kline` 表 |
| 分钟 K 线同步 | `sync_min_kline.py` | — | `min_kline` 表 (pool + holdings 股票) |
| Tushare 分钟线 | API 内联 | `fetch_3min_bars()` / Tushare `stk_mins` | 内存 (不落库) |
| 新闻爬取 | `news_crawler.py` | `crawl_all_sources()` | `news_raw` 表 |
| 实时行情 | `realtime_quote.py` | `get_batch_realtime_quotes()` | 内存 dict |
| 名称缓存 | `stock_name_cache.py` | `load_from_tushare()` | `stock_name_cache` 表 |
| 基本面快照 | `refresh_fundamental_snapshot.py` | — | `stock_fundamental_snapshot` 表 |
| 龙虎榜同步 | `sync_toplist_detail.py` | — | `toplist_daily` / `toplist_detail` 表 |
| 申万指数 | `phase0_sync.py` | — | `sw_sector_index` 表 |
| 大盘指数 | `background_sync.py` | — | `index_daily` 表 (000300.SH/000852.SH) |

### 3.2 TG 扫描评分层 (管线 1)

| 职责 | 入口文件 | 关键函数 | 输出 |
|------|---------|---------|------|
| TG 扫描 | `tg_engine.py` | `scan_all_stocks()` (5% 步长推送) | `scan_results` 表 |
| TG 指标 | `tg_indicator.py` | `TGIndicator(df).compute()` | 18 步指标 + 买入/卖出信号 |
| 深度评分 | `deep_scorer.py` | `deep_analyze()` (14 维) | `analysis_scores` 表 (含 dimension_scores, win_probability) |
| 形态识别 | `pattern_engine.py` | `run_pattern_scan()` | `pattern_signals` 表 |
| 潜伏猎手 | `ambush_scanner.py` | `run_ambush_scan()` (用最新 scan_date) | `ambush_signals` 表 |

**v4.8 扫描阶段流程 (10 阶段, 修复 toplist_sync 重复 + DNA 异步化)**：

```
POST /api/scan/trigger
  ① toplist        → ensure_toplist_fresh() (skip_download 时跳过, 与 ⑧ 合并)
  ② download       → tg_engine 内部: download_latest_kline() + 覆盖率回退 365 天
  ③ scan           → 本地 TG 计算 (5% 步长推送 SSE, 5000只 → 100 事件)
  ④ ambush_scan    → 潜伏猎手 (用 scan_results 最新日期, 非历史最早)
  ⑤ pattern_scan   → 形态识别
  ⑥ deep_score     → 14 维深度评分 (文案修正: 12→14)
  ⑦ nm_defense     → 分钟线防伪 (异常不影响后续, 仍受 try/except 保护)
  ⑧ toplist_sync   → ⛔ v4.8 移除 (与 ① 重复, 合并到 toplist)
  ⑨ accuracy_feedback → isolated_meta=True 写独立列, 不覆盖主 discrimination
  ⑩ dna_auto_join  → asyncio.create_task 异步训练, 60-180s/只不阻塞 done
  done 事件 ────→ 前端 currentPhase='done' 触发 load()
```

**市场过滤 (v4.8 后端真正过滤)**：

```
前端: 主板/中小板/创业板 按钮
  ↓ market_filter query param
后端: /api/scan/trigger?market_filter=主板
  ↓ classify_board(ts_code) → '上海主板'|'深圳主板'|'中小板'|'创业板'
  ↓ results = results[results['symbol'].apply(in allowed)]
  ↓ 日志: market_filter=主板 (allowed=['上海主板', '深圳主板']): 5500 -> 3500
```

**TG 指标差异化阈值** (`tg_indicator.py:29-51`)：

| 板块 | 涨跌幅 | 量比归一化 | 卖价偏 A | 大卖跌幅 |
|------|--------|-----------|---------|---------|
| 主板 (±10%) | buy≥3%, sell≥3% | 2.0→1.0 | ≤5% | >3% |
| 创业板/科创板 (±20%) | buy≥5%, sell≥5% | 3.0→1.0 | ≤8% | >5% |

**评分管线调用链 (v4.1 含分段权重 + 交叉反哺)**：

```
deep_analyze()
  ├── 加载 scan_results
  ├── 构建指纹 → 原型分类
  ├── ★ 市场状态感知: get_market_state() → regime ∈ {bull, bear, range}
  │   ├── 尝试加载 regime-specific 权重 (get_beliefs(regime))
  │   ├── ★ 三重安全门控: n≥50 / params≥10 / AUC≥0.55
  │   └── 不满足 → WARNING + 回退 get_beliefs("__global__")
  ├── 权重解析: resolve_scoring_weights(archetype, beliefs)
  ├── 预加载: 基本面 / 形态 / 资金流 / 行业 Alpha / 大盘涨跌 / 多周期
  ├── 四层过滤: 涨停 / ST / 新股 / 资金流出
  └── 逐股评分 (14 个维度)
       ├── score_technical()        # RSI+MACD+Bollinger
       ├── score_kline_game()       # K 线博弈
       ├── score_fund_flow()        # 资金面
       ├── score_vol_ratio()        # 量比
       ├── score_arbr()             # ARBR 情绪
       ├── score_sector_alpha()     # 行业 Alpha
       ├── score_market_relative()  # 大盘相对强度
       ├── score_valuation()        # 估值
       ├── score_ma_trend()         # 均线趋势
       ├── score_pattern_signal()   # 形态信号
       ├── score_trend_deviation()  # 趋势偏离
       ├── score_bbi()              # BBI 多空
       ├── score_multi_box()        # 箱体结构
       ├── score_downside_risk()    # 下跌风险
       └── get_fundamental_score()  # 基本面修正
       → composite = weighted_sum + top3_boost + sector_bonus
       → ★ 跨周期验证: multi_timeframe.verify_multi_timeframe() → ± adjustment
       → ★ 龙虎榜质量注入: toplist_analyzer (三日陷阱/散户陷阱/单席位控盘)
       → ★ AlphaFlow 净买力修正: compute_sxqs_features().net_power / 50 (最多±3分)
       → ★ 概率校准: calibrate_with_regime(composite, archetype, regime)
```

### 3.3 AlphaFlow 主升浪捕获层 (管线 2) ★★★

#### 3.3.1 核心管线 (v4.1)

```
全市场 5500+ 股票
    │
    ▼
[1] lock_detector.py — 双窗口锁死检测 ★ 先于 XGBoost
    窗口1: 15-20日振幅≤15% + 窗口2: 20-40日振幅≤17%
    两窗口锁死价区重合 → lock_detected
    find_last_ex_rights(): |close[i]/close[i-1]-1| > 20% → 除权截断
    → ~200 只锁死候选
    │
    ▼
[2] alphaflow_veteran.py — 老兵识别 ★
    4+ 锁死周期统计分析:
      周期持续时间延长 → 锁死在加深
      振幅逐周期收敛 → 爆发在逼近
      量能逐周期萎缩 → 浮筹在减少
    → level: pre_breakout / late_stage / monitoring / none
    → score + verdict
    ★ 每周六自动回测: backtest_veteran_breakout_rate() 验证阈值
    │
    ▼
[3] alphaflow_evaluator.py — 历史评估 + 策略分类 ★
    A-G 8项历史过滤 + quality_label → strategy_label (8种) → strategy_group
    │
    ▼
[4] alphaflow_features.py — 47 维特征计算 ★ V2.1
    41 原始特征 + 6 老兵增强特征
    ★ 特征 #41 (板块锁死期%): 从 sw_sector_index 真实计算, 不再是占位符
    │
    ▼
[5] alphaflow_xgb.json — XGBoost V2.1 模型打分 ★
    ★ _load_xgb_model() 含三阶段版本校验:
      校验1: model_n_features == len(FEAT_NAMES) → 不匹配阻止加载
      校验2a: meta.feature_names 逐位比对
      校验2b: meta.feature_hash == runtime_hash → 不匹配 ERROR
      校验2c: meta.training_date 存在性检查
    │
    ▼
[6] alphaflow_pool.py — 池管理 ★
    INSERT/UPDATE alphaflow_pool (含 strategy_group, strategy_label, veteran_tier)
    结构维护 + 老兵豁免
    │
    ▼
[7] chip_analyzer.py — 筹码吸收分析 ★ 除权免疫
    三区模型 + find_last_ex_rights() 截断
    │
    ▼
[8] wave_predictor.py — 波段目标预测 ★ 幸存者偏差防护
    退市股排除 (查 delisted_stocks) + 3σ 极端浪幅过滤
```

#### 3.3.2 关键设计决策

| # | 决策 | 原因 |
|---|------|------|
| 1 | **锁死扫描先于 XGBoost** | 5500→200 筛选后 XGBoost 只对锁死候选打分，避免全市场盲打 |
| 2 | **老兵强制入池** | V1 模型仅在早期蛋上训练，老兵得分仅 15.2%，完全漏检。V2 修复 + 老兵豁免 |
| 3 | **strategy_group 是 DB 列** | 不再用 micro_score 负编码，直接写入 VARCHAR 列 |
| 4 | **除权免疫贯穿全管线** | lock_detector, veteran, evaluator, wave_predictor, chip_analyzer 均调用 find_last_ex_rights() |
| 5 | **筹码为硬指标** | 吸收率是客观数据，不依赖 LLM 主观评分 |
| 6 | **三区模型替代 profit_ratio** | 初版 profit_ratio 被用户否决（无意义），改用锁死区/上方/下方三区量能对比 |
| 7 | ★ **退市股排除** | wave_predictor 在加载历史数据时检查 delisted_stocks 表 |
| 8 | ★ **3σ 极端值过滤** | 浪幅统计中剔除 >3σ 的异常值 (ST异动/重组噪音) |
| 9 | ★ **板块数据真实化** | 训练+预测双管线接入 sw_sector_index, 特征#41 不再为 0.0 |
| 10 | ★ **版本校验** | _load_xgb_model() 自动比对运行时 FEAT_NAMES 与模型元信息 |

#### 3.3.3 相关服务清单

| 职责 | 入口文件 | 行数 | 关键函数 | 输出 |
|------|---------|------|---------|------|
| 锁死检测 | `lock_detector.py` | 167 | `detect_lock_simple()` + `find_last_ex_rights()` | 振幅/锁死天数/相对强度/判决 |
| 老兵识别 | `alphaflow_veteran.py` | 331 | `detect_veteran()` + `backtest_veteran_breakout_rate()` | level/score/verdict/cycle_stats + 回测报告 |
| 历史评估 | `alphaflow_evaluator.py` | 332 | `evaluate_history()` + `classify_strategy()` | history_label/quality_label/strategy_label |
| 特征提取 | `alphaflow_features.py` | 370 | `compute_wave_features()` (47维) + `compute_sxqs_features()` | FEAT_NAMES 向量 |
| 池管理 | `alphaflow_pool.py` | 719 | `daily_scan()` + `_load_xgb_model()` (版本校验) | `alphaflow_pool` 表 |
| 筹码分析 | `chip_analyzer.py` | 338 | `analyze_chip_absorption()` (含除权免疫) | absorption 三区数据 |
| 波段预测 | `wave_predictor.py` | 374 | `predict_wave_target()` + `detect_distribution()` | target_zone/risk_levels (含退市股排除+3σ过滤) |
| 乏力度 | `fatigue_detector.py` | — | `detect_fatigue()` | 浪平台逐层跌破 → 4 级判定 |
| 结构破坏 | `structure_break_detector.py` | — | `detect_trend_break()` | 摆动分析 → 关键支撑位 → 4 级判定 |
| 微剧本 | `micro_pattern_detector.py` | — | `detect_accumulation()` | 3 分钟线 5 维 0-5 分 |
| 盘中异动 | `intraday_analyzer.py` | — | `analyze_intraday_move()` | 2%+涨幅出货/吸筹判定 |

#### 3.3.4 策略分类体系 (8 种 strategy_label)

```
强势锁死: history_label=E/F(有利) + quality_label=strong
标准锁死: history_label=E/F + quality_label=normal
增量锁死: history_label=E(周期延长, 锁死在加深)
观察锁死: history_label=other + quality_label=watch
老兵锁死: veteran_detected → 强制入池, strategy_group='老兵锁死'
风险锁死: history_label=B/C(崩盘/闷杀) + quality_label=risky
底部锁死: history_label=A(无波段) + quality_label=bottom
未分类:   default fallback
```

#### 3.3.5 SXQS 资金博弈信号体系

基于 ZIG(3,10) 转向指标 + H1/H2/H3 三级 EMA + VAR6/VAR7/VAR8 买卖力：

| 信号 | 条件 | 含义 |
|------|------|------|
| **买入** | D 信号 + H1>H2 + ZIG 上升 | 趋势反转确认，强烈买入 |
| **ZIG 买入** | D 信号 + ZIG 上升 | ZIG 拐点买入 |
| **卖出** | W 信号 + ZIG 下降 | 趋势反转向下 |
| **持有** | W 信号 + ZIG 上升 | 上升中的正常回调 |
| **强势** | H1>H2 + A 信号 | 资金博弈偏多 |
| **观望** | 无明确信号 | 等待方向明确 |

### 3.4 分钟线反哺 TG 层 (交叉管线) ★

> **状态**: ✅ 已完成 (2026-05-31)

#### 3.4.1 核心思想

TG 日线信号可能被主力做出来（日线级别的假突破），但分钟线无法伪装——主力在分钟线上的每一笔进出都会留下痕迹。

```
TG 日线买入信号
       │
       ▼
  下载该股信号前 15 天的 5 分钟线 (Tushare stk_mins)
       │
       ├── 分时段 N/M 检测 (minute_nm_detector.py)
       │    上午最大跌幅 / 下午最大跌幅 → N型条件
       │    上午最大涨幅 / 下午最大涨幅 → M型条件
       │    收盘 vs VWAP / 收盘位置 → 验证
       │
       ├── 板块联盟放大 (sector_alliance.py)
       │    同行业 ≥3 只信号股 → 对比 N/M
       │    板块共识 > 0.15 + 一致性 > 60% → 联盟确认
       │    个股 vs 板块方向一致 → 加分 | 相反 → 减分
       │
       └── 信号质量调整 (signal_quality_scorer.py)
           NM分 × 0.25 + 联盟分 × 0.30 → 质量修正
           高置信(≥10天数据) → 修正权重 100%
           中置信(≥5天) → 60% | 低置信 → 20%
```

#### 3.4.2 N/M 形态定义

**N型 (吸筹)** — 两低夹一高, 低点抬高:
| 条件 | 说明 |
|------|------|
| 上午跌幅 > 1.2% | 早盘有显著抛压 |
| 下午跌幅 < 上午跌幅 × 0.7 | 下午抛压减小 (低点抬高) |
| 下午低点 > 上午低点 | 支撑位上移 |
| 收盘 > 开盘 | 最终买方获胜 |
| 收盘 > VWAP | 收盘在均价上方 |

**M型 (出货)** — 两高夹一低, 高点降低:
| 条件 | 说明 |
|------|------|
| 上午涨幅 > 1.2% | 早盘有显著拉升 (诱多) |
| 下午涨幅 < 上午涨幅 × 0.7 | 下午买力减弱 (高点降低) |
| 下午高点 < 上午高点 | 阻力位下移 |
| 收盘 < 开盘 | 最终卖方获胜 |
| 收盘 < VWAP | 收盘在均价下方 |

### 3.5 学习与训练层 (v4.1 重大升级) ★★★

#### 3.5.1 评分权重训练器 (scoring_trainer.py)

**这是学习闭环的核心引擎**，替换了过去人工猜测的 DEFAULT_WEIGHTS。

```
数据流:
  recommendation_tracking (真实盈亏标签)
      + analysis_scores (dimension_scores JSON)
      + market_status_log (市场阶段)
        │
        ▼
  load_training_data_with_regime()
    ├── JOIN bayesian_beliefs 获取市场阶段
    ├── 按 bull/bear/range 分组
    └── 每组 X(维度评分矩阵), y(was_profitable_3d)
        │
        ▼
  _fit_logistic_regression()
    ├── StandardScaler → LogisticRegression (C=0.5, class_weight='balanced')
    ├── 5-fold CV → AUC
    ├── 系数 → 权重映射 (0.5 ~ 4.0)
    └── 返回 {n_samples, cv_auc, coefficients, new_weights}
        │
        ▼
  persist_weights(regime="bull/bear/range/__global__")
    ├── param_library (strategy="scoring_{regime}", is_active=true)
    ├── bayesian_beliefs (archetype=regime, n_observations=N)
    ├── ★ __regime_auc__ 元参数 (用于 deep_scorer 安全门控)
    └── ★ __trained_at__ 时间戳
        │
        ▼
  deep_scorer 评分时自动加载:
    get_beliefs(regime) → resolve_scoring_weights(archetype, beliefs)
    ★ 三重安全门控: n≥50 / params≥10 / AUC≥0.55
```

**关键安全设计**：
- `MIN_SAMPLES_FOR_TRAINING = 30` (数据加载层拦截)
- `persist_weights()`: AUC < 0.52 拒绝写入
- `deep_scorer` 加载: `MIN_REGIME_SAMPLES = 50`, `MIN_REGIME_PARAMS = 10`, `MIN_REGIME_AUC = 0.55`
- 任一条件不满足 → WARNING 日志 + 回退全局权重

#### 3.5.2 概率校准器 (probability_calibrator.py v4.1)

```
v4.1 升级:
  1. ★ 标签统一: T+2 → T+3 (与 scoring_trainer was_profitable_3d 对齐)
  2. ★ regime 分段校准: build_calibration_by_regime()
     - 每个 regime ≥ 100 样本才启用分段校准
     - 不足时自动回退全局校准器
  3. ★ calibrate_with_regime(composite, archetype, regime, signal_quality)
     - 优先加载 regime-specific 校准曲线
     - 不可用时回退全局
  4. ★ scheduled_recalibrate_with_regime() (每周日自动)
  5. 小样本降权: bucket_weight = min(1.0, bucket_n / 10)
  6. 硬底: score>20 → min 8%, score>35 → min 15%
```

#### 3.5.3 原型与学习层

| 职责 | 入口文件 | 关键函数 | 输出 |
|------|---------|---------|------|
| 指纹构建 | `fingerprint_builder.py` | `build_fingerprints()` | 11 维向量 + 原型标签 |
| 原型分类 | `archetype_classifier.py` | `classify_stocks()` | 5 原型标签 |
| 权重解析 | `archetype_param_resolver.py` | `resolve_scoring_weights()` | ★ 含 ARCHETYPE_OFFSETS (待校准) + 校准数据收集 |
| 影子训练 | `shadow_trainer.py` | `train_shadow()` | `param_library` 表 |
| 学习引擎 | `learning_engine.py` | `run_rolling_backtest()` | T+5 回测指标 |
| 权重训练 | `scoring_trainer.py` | `full_training_pipeline()` (by_regime=True) | ★ 分段权重 + Bayesian 持久化 |
| 概率校准 | `probability_calibrator.py` | `calibrate_with_regime()` | ★ T+3 分段概率 |
| 自学习启动 | `self_learning_bootstrap.py` | `daily_incremental_train()` | ★ 对接 scoring_trainer |

**原型偏移表** (`archetype_param_resolver.py:31-111`)：
5 个原型 (large_bluechip, small_speculative, growth_tech, value_defensive, cyclical_resource) 约 70 个偏移值。
★ 标注为 "待校准 (2026-06-03): 从未基于真实盈亏数据回测校准"。
`collect_archetype_calibration_data()` 已就绪，按原型统计实际胜率 vs 全局胜率并生成建议偏移量。

### 3.6 DeepSeek 调用层

| 职责 | 入口文件 | 使用模型 | 调用场景 |
|------|---------|---------|---------|
| API 客户端 | `deepseek.py` | — | 统一封装 (httpx, 180s timeout, temperature=0.2) |
| 新闻打标签 | `event_detector.py` | deepseek-chat | Stage1: 250 条/批, 2 批并发 |
| 新闻深度分析 | `event_detector.py` | deepseek-chat | Stage2: 4 分类, 各 100 条 |
| 个股分析提示词 | `llm_deep_analyzer.py` | deepseek-chat | 用户精选后反哺 (含筹码段) |
| 反哺解析 | `feedback_parser.py` | deepseek-chat | 文本→结构化 JSON |
| 板块热度分析 | `sector_heat_engine.py` | deepseek-chat | 龙虎榜→板块热度 |
| 批量横向评分 | `feedback.py` | DEEPSEEK_PRO_MODEL | ★ 多只股票横向对比 (含筹码吸收率硬指标) |

### 3.7 API 路由层 (15 个路由) ⭐ v4.5 DNA Lab 新增

| 路由前缀 | 文件 | 端点数 | 主要功能 |
|---------|------|-------|---------|
| `/api/scan` | `scan.py` | 7 | TG 扫描 (SSE)、新闻、数据新鲜度、NM验证 |
| `/api/result` | `result.py` | 3 | 最终推荐 (市场门控 v2.0 + S3风险分类) + 融合 |
| `/api/alphaflow` | `alphaflow.py` | 7 | ★ 候选池/锁死详情/筹码分析/波段预测/统计/老兵回测 |
| `/api/analysis` | `analysis.py` | 3 | 深度分析 + 手动加股(完整管线) + 删除 |
| `/api/comprehensive` | `comprehensive.py` | 1 | ★ 一键综合分析 (symbol→4段报告) |
| `/api/feedback` | `feedback.py` | 5 | 反哺提交/解析/列表/批量检查/★批量横向评分 |
| `/api/holdings` | `holdings.py` | 10+ | ★ 持仓CRUD + 资金账户 + 自动清仓 + 筹码诊断 |
| `/api/learning` | `learning.py` | 20+ | ★ 训练/升级/回测/维度/原型/权重/校准数据 |
| `/api/llm` | `llm_analysis.py` | 1 | 深度分析提示词生成 |
| `/api/ambush-signals` | `ambush.py` | 1 | 潜伏猎手信号 |
| `/api/user-decisions` | `decisions.py` | 1 | 用户决策记录 |
| `/api/settings` | `settings.py` | 2 | 系统设置/密钥管理 |

**v4.1 新增端点**:
- `POST /api/learning/train-weights?force=true` — 触发权重训练
- `GET /api/learning/weights-trained` — 查看 Bayesian 训练参数
- `GET /api/learning/archetypes/calibration-data?days=180` — 原型校准数据
- `GET /api/alphaflow/veteran-backtest?days=180` — 老兵突破率回测

### 3.8 门控与风控层

| 职责 | 入口文件 | 关键函数 | 触发时机 |
|------|---------|---------|---------|
| 市场门控 v2.0 | `market_gate.py` | `get_gate_config()` | 每次 `/result/final` 调用 |
| 多周期验证 | `multi_timeframe.py` | `verify_multi_timeframe()` | 深度评分时 (参与 composite_score) |
| 概率校准 | `probability_calibrator.py` | `calibrate_with_regime()` | ★ 评分后, 按 regime 选择校准器 |
| 板块热度 | `sector_heat_engine.py` | — | 板块5阶段判定 + sector_factor 注入 |
| 退出信号 | `exit_signal_detector.py` | `detect_exit_signals()` | 用户主动查询 |
| 准确率追踪 | `accuracy_tracker.py` | `verify_all_periods()` | 每次全市场扫描后 |
| 信号质量 | `signal_quality_scorer.py` | `verify_signals_with_minute_bars()` | TG 信号筛选时 + NM验证 |
| 结构破坏 | `structure_break_detector.py` | `detect_trend_break()` | AlphaFlow 池更新时 (老兵豁免) |
| 乏力度 | `fatigue_detector.py` | `detect_fatigue()` | 用户主动查询 |

**市场门控 v2.0 逻辑**:

```
get_gate_config()
  ├── get_market_state()       → ★ 7 市场体制 + regime 判定
  ├── _get_market_breadth()    → ★ 涨跌家数比 + 新高新低比
  ├── _get_style_bias()        → ★ 风格偏向 (沪深300 vs 中证1000)
  ├── _get_volume_trend()      → ★ 成交额趋势
  ├── check_market_breadth()   → 合格股票数骤降 → 收紧
  └── check_self_feedback()    → 近期胜率 < 30% → 收紧
```

**7 市场体制判定**:
| 体制 | 条件 | 风险 | min_prob | max_stocks |
|------|------|------|----------|------------|
| 趋势上涨 | adv_pct>65% + 成交额扩张 + 20日涨幅>3% | low | 0.28 | 120 |
| 结构行情 | adv_pct>50% + 小盘风格 + 波动率<1.3 | normal | 0.30 | 100 |
| 缩量博弈 | 成交额萎缩>20% + abs(20日涨幅)<3% | elevated | 0.38 | 60 |
| 恐慌杀跌 | adv_pct<30% + 20日跌幅>3% + 波动率>1.5 | high | 0.45 | 40 |
| 维稳行情 | abs(20日涨幅)<2% + 波动率<0.8 | normal | 0.35 | 80 |
| 弱势探底 | adv_pct<30% (含双阈值) | high | 0.42 | 50 |
| 震荡整理 | 默认 fallback | normal | 0.32 | 90 |

### 3.9 后台调度层 (v4.1 扩展)

| 职责 | 入口文件 | 触发时间 | 任务 |
|------|---------|---------|------|
| 每日调度 | `background_sync.py` | 16:00 | 基本面快照 + 龙虎榜 + 回测 + 影子训练 + 融资融券 + 商品期货 + ★持股天数+1 + ★min_kline同步 |
| ★ 权重训练 | `background_sync.py` | 周一 16:00 | `full_training_pipeline(by_regime=True)` → 分段权重训练 + Bayesian 持久化 |
| ★ 老兵回测 | `background_sync.py` | 周六 16:00 | `backtest_veteran_breakout_rate()` → 突破率统计 |
| ★ 概率重校准 | `background_sync.py` | 周日 16:00 | `scheduled_recalibrate_with_regime()` → 全局+regime 双重重校准 |

### 3.10 部署验证层 ★ v4.1 新增

| 文件 | 用途 |
|------|------|
| `retrain_xgb.ps1` | XGBoost V2.1 重新训练脚本 (切换目录→备份→训练→验证meta→特征一致性) |
| `verify_all.ps1` | 完整部署验证链 (安全门控→模型一致性→API端点→校准→回测) |
| `docs/post_deployment_monitoring.md` | 部署后日志监控指南 (关键字/安全门控样例/回滚流程) |

---

## 4. 数据流与调用链路

### 4.1 TG 全市场扫描 → 推荐 完整链路 (v4.2 含 Phase 1.5 周线共振)

```
用户点击 "全市场扫描"
        │
        ▼
POST /api/scan/trigger (SSE 流式)
        │
        ├── Phase 1: TG 日线扫描
        │   ├── download_latest_kline()     → Tushare API → daily_kline 表
        │   ├── TGIndicator(df).compute()   → 逐股计算 TG 动量/买卖点
        │   └── save_scan_results()         → scan_results 表 (含 resonance_type)
        │
        ├── ★ Phase 1.5: 周线独立信号叠加 (v4.2)
        │   ├── scan_weekly_signals()       → 全市场逐股日线→周线重采样
        │   │   ├── resample_daily_to_weekly() → ISO周分组 → 周一开/周高低/周五收
        │   │   ├── TGIndicator(weekly_df).compute() → 周线买方向信号
        │   │   └── 质量过滤: 周成交量>0, 周收盘价≥2.0
        │   └── 双周期匹配:
        │       日线买入 AND 周线买入  → "weekly_resonance" (共振)
        │       日线买入 AND NOT 周线  → "daily_only"      (仅日线)
        │       写入: results[i]["resonance_type"] + ["weekly_tg_momentum"]
        │
        ├── Phase 2: 并行扫描
        │   ├── run_ambush_scan()           → ambush_signals 表
        │   └── run_pattern_scan()          → pattern_signals 表
        │
        ├── Phase 3: 深度评分
        │   └── deep_analyze()
        │       ├── 加载 scan_results (含 resonance_type)
        │       ├── ★ score_weekly_resonance() → resonance × weight → composite
        │       ├── ★ CALibrate_with_regime() → T+3 分段概率校准
        │       ├── ★ AlphaFlow 净买力修正 (net_power / 50)
        │       ├── ★ QUALITY_GATE 自适应放宽: 通过<10 → L1(sq≥0.55) → L2(sc≥35)
        │       ├── INSERT analysis_scores
        │       └── INSERT recommendation_tracking
        │
        ├── Phase 4: 准确率验证
        │   ├── verify_all_periods()
        │   └── ★ apply_accuracy_feedback() → T+5不足时降级到T+3
        │
        └── SSE 事件流返回给前端
                │
                ▼
GET /api/result/final?limit=20
        │
        ├── ★ ORDER BY resonance_priority ASC, composite_score DESC
        │   (weekly_resonance=0 > daily_only=1 > weekly_driven=2)
        ├── S3 风险分类 + ★ 板块感知门控 (安全阀扩展到所有体制)
        └── 返回: data[] (含 resonance_type)
```

### 4.1b 方案 B 周线共振数据流 ★ v4.2

```
resample_daily_to_weekly(kline_df):
  日线 DataFrame → df['week_label'] = dt.strftime('%G-W%V')
  └── 按 week_label 分组:
        Open  = 该周首日开盘
        High  = max(周内所有high)
        Low   = min(周内所有low)
        Close = 该周末日收盘 (周五/最后交易日)
        Volume = sum(周内所有volume)
  └── 至少产生 20 根周线 → 传给 TGIndicator

双周期信号匹配 (Phase 1.5 末尾):
  for r in 日线results:
      if ws := weekly_signals.get(r["symbol"]):
          if ws["has_weekly_buy"]: → "weekly_resonance" (共振)
          else:                    → "daily_only"      (仅日线)
      else:                        → "daily_only"      (无周线)

score_weekly_resonance(resonance_type):
  "weekly_resonance" → 1.0 + min(0.3, |momentum|/100) → × weight=2.0 → composite
  "weekly_driven"    → 0.6 → × weight=2.0 → composite
  "daily_only"       → 0.0 → 无影响
```

### 4.2 AlphaFlow 全市场扫描 → 候选池 完整链路 (v4.1)

```
POST /api/alphaflow/scan (或后台自动)
        │
        ├── ★ 0. 预加载板块指数数据
        │   ├── sw_sector_index (28 个 SW 一级行业)
        │   └── ths_member → stock→sector 映射
        │
        ├── ★ 1. 锁死检测 (5500+ → ~200) ★ 先于 XGBoost
        │   ├── 加载全市场日线数据
        │   ├── find_last_ex_rights() → 除权截断
        │   ├── 窗口1: 15-20日振幅≤15%
        │   ├── 窗口2: 20-40日振幅≤17%
        │   └── detect_lock_simple() → 锁死候选列表
        │
        ├── ★ 2. 老兵检测 ★
        │   └── detect_veteran() 对每个锁死候选
        │       ├── 4+ 锁死周期统计
        │       └── → level: pre_breakout/late_stage/monitoring
        │
        ├── ★ 3. 历史评估 + 策略分类 ★
        │   └── → strategy_label (8种) + strategy_group
        │
        ├── ★ 4. XGBoost V2.1 打分 ★
        │   ├── _load_xgb_model() → ★ 三阶段版本校验
        │   ├── compute_wave_features(..., sector_closes=板块日线)
        │   │   └── ★ 特征#41: _lock_sector_return() 真实板块收益率
        │   ├── model.predict_proba() → 主升浪概率
        │   └── 阈值 0.167+ → 入池候选
        │
        ├── 5. 池更新
        │   ├── 新入池: 通过阈值 + 在锁死状态
        │   ├── ★ 老兵强制入池: 检测到 veteran → 绕过 XGBoost 阈值
        │   ├── INSERT/UPDATE alphaflow_pool
        │   ├── 结构清理: detect_trend_break() → 踢出破位股
        │   └── ★ 老兵豁免: veteran 股票不被结构维护踢出
        │
        └── 返回: {new_entries, total_pool, veteran_count, tiers}
```

### 4.3 学习闭环数据流 (v4.1 真实训练)

```
recommendation_tracking (103+ 条真实盈亏)
   + analysis_scores (dimension_scores JSON)
   + market_status_log (phase 牛/熊/震荡)
        │
        ▼
scoring_trainer.load_training_data_with_regime()
   ├── 按 regime 分组: bull/bear/range
   └── 每组 X, y (was_profitable_3d)
        │
        ▼
_fit_logistic_regression()
   ├── StandardScaler + LogisticRegression (C=0.5, balanced)
   ├── 5-fold CV AUC
   └── 系数 → 0.5~4.0 权重
        │
        ▼
persist_weights(regime)
   ├── param_library (strategy="scoring_{regime}")
   ├── bayesian_beliefs (archetype=regime)
   └── __regime_auc__ / __trained_at__ 元信息
        │
        ▼
deep_scorer.deep_analyze()
   ├── get_beliefs(regime) → ★ 三重安全门控
   ├── resolve_scoring_weights(archetype, beliefs)
   └── 下次评分自动使用训练后的分段权重
```

---

## 5. 数据库架构

### 5.1 核心数据表

| 表 | 行数 (约) | 用途 |
|----|----------|------|
| `daily_kline` | 4,000,000+ | 日 K 线 (含上证/创业板/沪深300/中证1000指数) |
| `daily_basic` | 177,000+ | 每日估值指标 |
| `moneyflow` | 242,000+ | 资金流向 |
| `fina_indicator` | 7,000+ | 财务指标 |
| `margin_trading` | 7,000+ | 融资融券 |
| `cashflow` | 15,000+ | 经营现金流 |
| `min_kline` | — | ★ 分钟 K 线 (pool + holdings 股票, 5min × 60天) |
| `stock_name_cache` | — | 股票名称缓存 |
| `ths_member` | 18,000+ | 同花顺行业分类 |
| `sw_sector_index` | — | ★ 申万行业指数 (用于特征#41计算) |
| `index_daily` | 580+ | ★ 大盘指数日线 (000300.SH/000852.SH) |
| `trade_cal` | — | 交易日历 |
| `hk_hold` | 24,000+ | 北向持股 |
| `stk_holdernumber` | 10,000+ | 股东户数 |
| `toplist_daily` | — | 龙虎榜日数据 |
| `toplist_detail` | — | ★ 龙虎榜明细 |
| `suspend_d` | 200+ | 暂停/退市股票 |
| `delisted_stocks` | — | ★ 退市股 (波段预测排除 + S3 负样本) |
| `commodity_futures` | — | ★ 商品期货日线 (铜/铝/锌/螺纹/热卷等) |

### 5.2 DNA 个性化模型表 ⭐ v4.5 新增

独立 schema `stock_dna`，与现有系统**完全并行**：

| 表 | 用途 |
|----|------|
| `stock_dna.daily_samples` | 每日训练样本 (symbol×trade_date, 含 emotion_label/cycle_phase/多窗口标签/daily_features JSONB) |
| `stock_dna.profiles` | Per-Stock DNA 档案 (表情指纹/周期节律/最佳窗口/特征重要度/行为指纹/转移矩阵) |
| `stock_dna.predictions` | DNA 多窗口预测记录 (T+2/5/10/20 超额收益+胜率+置信度) |

### 5.3 业务数据表

| 表 | 行数 (约) | 用途 |
|----|----------|------|
| `scan_results` | 5,700+ | ★ TG 扫描结果 (含 level, market, tg_momentum, resonance_type, weekly_has_buy, weekly_tg_momentum) |
| `analysis_scores` | 4,900+ | ★ 14 维深度评分 (含 dimension_scores JSON, win_probability) |
| `stock_fingerprints` | 3,300+ | 11 维指纹向量 |
| `pattern_signals` | — | K 线形态信号 |
| `ambush_signals` | — | 潜伏猎手信号 |
| `stock_fundamental_snapshot` | — | 基本面快照 (从 fina_indicator/cashflow 聚合) |
| `stock_deep_feedback` | — | 外部分析反哺 |
| `recommendation_tracking` | — | ★ 推荐追踪 (was_profitable_3d/5d, verified_3d/5d) |

### 5.3 AlphaFlow 专用表 ★

| 表 | 用途 |
|----|------|
| `alphaflow_pool` | ★ 候选池主表 (含 strategy_group, strategy_label, veteran_tier, veteran_level, veteran_score) |
| `alphaflow_snapshots` | ★ 每日池快照 |
| `goose_archive` | 大雁归档 (涨幅>100%的已毕业股票) |
| `egg_phase_samples` | 蛋期样本 (蛋期中段快照) |
| `mins_train_samples` | 分钟线训练样本 (待消费) |

### 5.4 持仓专用表 ★

| 表 | 用途 |
|----|------|
| `holdings` | ★ 持仓主表 (含 holding_days, pending_close, capital) |
| `closed_positions` | ★ 已清仓记录 (含 t_trade_count, pnl) |
| `capital_accounts` | ★ 资金账户 |

### 5.5 自学习相关表

| 表 | 用途 |
|----|------|
| `archetype_profiles` | 原型中心点 + 可训练标记 |
| `param_library` | ★ 评分权重库 (strategy="scoring_{regime}", is_shadow, converge_status) |
| `bayesian_beliefs` | ★ Bayesian 信念参数 (archetype=regime, mu, sigma, n_observations, lo, hi) |
| `experience_replay` | 经验回放缓冲 (6280 条) |
| `learning_predictions` | 回测预测记录 |
| `learning_dimension_registry` | 维度注册表 |
| `learning_models` | 模型版本链 |
| `strategy_daily_score` | 策略日评分 |
| `prediction_log` | 预测日志 |
| `market_status_log` | ★ 市场状态日志 (含 phase 牛/熊/震荡, ma60_value, phase_duration) |
| `sync_log` | 同步任务日志 |

---

## 6. DeepSeek 底座集成细节

### 6.1 API 调用封装

**文件**: `app/services/deepseek.py`

```python
async def call_deepseek(prompt: str, max_tokens: int = 4096, model: str = None) -> str
```

| 参数 | 说明 |
|------|------|
| 端点 | `POST {DEEPSEEK_BASE_URL}/chat/completions` (默认 `https://api.deepseek.com/v1`) |
| 认证 | `Authorization: Bearer {DEEPSEEK_API_KEY}` |
| 超时 | **180 秒** (httpx.AsyncClient) |
| 温度 | 固定 **0.2** |
| 重试 | **无自动重试**，失败返回 `"[LLM 调用失败: {e}]"` |
| 模型 | deepseek-chat (默认) / DEEPSEEK_PRO_MODEL (批量评分) / deepseek-reasoner |

### 6.2 并发控制

- **新闻 Stage1**: `asyncio.Semaphore(2)` 并行 2 批，单批超时 `asyncio.wait_for(120s)`
- **AlphaFlow 全市场扫描**: 顺序逐股，`asyncio.sleep(0)` 每 10 股释放事件循环
- **批量横向评分**: 最多 20 只股票，单次调用 4096 tokens

---

## 7. 配置与部署

### 7.1 配置文件

**`.env` 文件** (由 `app/core/config.py` 的 `Settings` 类加载)：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@127.0.0.1:15432/stock_data` | PostgreSQL 连接 |
| `DEEPSEEK_API_KEY` | `""` | DeepSeek API 密钥 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | API 端点 |
| `TUSHARE_TOKEN` | `""` | Tushare API token |
| `BAIDU_QIANFAN_API_KEY` | `""` | 百度千帆 API 密钥 |
| `API_AUTH_KEY` | `""` | API 认证密钥 (⚠ 待启用) |
| `DEBUG` | `true` | 调试模式 (SQL echo) |

### 7.2 启动命令

```bash
# 后端 (端口 8000)
cd C:\AI-Agent-Local\Stock\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 600

# 前端 (端口 3456 — AlphaFlow 专用)
cd C:\AI-Agent-Local\Stock\frontend
npm run dev

# 一键启动
StockAnalyst.bat

# 部署验证
.\retrain_xgb.ps1      # XGBoost 重训 + 版本校验
.\verify_all.ps1       # 完整验证链 (需后端先启动)
```

### 7.3 关键约束

- **uvicorn 必须单 worker** (`--workers 1`)：扫描状态存在进程内存中
- **SSE 超时**：`--timeout-keep-alive 600` (10 分钟)
- **DB 连接池**：pool_size=10, max_overflow=20
- **Tushare 分钟线** (`stk_mins`)：每次 API 调用约 1-2 秒，5 只并发
- **XGBoost 模型版本校验**：启动时自动检查 `alphaflow_xgb_meta.json` 与运行时 `FEAT_NAMES` 一致性

---

## 8. 未来开发指南

### 8.1 新增 AlphaFlow 特征 (含版本校验)

```python
# 1. 在 alphaflow_features.py 的 compute_wave_features() 中添加
# 2. 更新 FEAT_NAMES 列表以匹配维度数 (当前 47 维)
# 3. 重新训练模型:
#    .\retrain_xgb.ps1
#    (自动备份旧模型、训练、更新 meta、验证特征一致性)
# 4. 重启后端后 _load_xgb_model() 自动校验新模型
```

### 8.2 新增 TG 评分维度

```python
# 1. 在 deep_scorer.py 添加评分函数
# 2. 在 deep_analyze() 循环中调用
# 3. 在 scoring_trainer.py 的 DIM_KEYS 中添加
# 4. 在 WEIGHT_PARAM_NAMES 中添加映射
# 5. Model 将自动学习该维度的权重
```

### 8.3 可扩展设计点

| 扩展点 | 位置 | 机制 |
|--------|------|------|
| TG 评分维度 | `scoring_trainer.py::DIM_KEYS` | 添加 dim key → 自动参与 Logistic Regression 训练 |
| AlphaFlow 特征 | `alphaflow_features.py::FEAT_NAMES` | 添加特征 → 重新训练 XGBoost (V3) |
| 策略原型 | `archetype_classifier.py` | 修改 K 值 → 重新聚类 |
| 原型权重偏移 | `archetype_param_resolver.py::ARCHETYPE_OFFSETS` | 待数据积累后校准 (collect_archetype_calibration_data 已就绪) |
| 市场门控阈值 | `market_gate.py` | 修改 7 体制参数 |
| 分段训练参数 | `deep_scorer.py::MIN_REGIME_SAMPLES/AUC/PARAMS` | 调整安全门控阈值 |
| AlphaFlow 策略分类 | `alphaflow_evaluator.py` | 扩展 strategy_label 枚举 |

### 8.4 待完成的改进项

| # | 改进项 | 状态 | 优先级 |
|---|--------|------|--------|
| 1 | XGBoost 重新训练 (特征 #41 真实化) | ⏳ `retrain_xgb.ps1` 就绪, 待执行 | P0 |
| 2 | 推荐追踪准确率累积 | ✅ 已训练, 214 条样本, AUC 0.6452 (2026-06-03) | P0 |
| 3 | 推荐准确率反馈闭环 | ✅ apply_accuracy_feedback T+5不足时降级到T+3 (v4.2) | — |
| 4 | 质量门控自适应放宽 | ✅ QUALITY_GATE L1/L2 两级放宽 (v4.2) | — |
| 5 | 周线双周期共振 | ✅ 方案 B 已合入 (Phase 1.5 + 三级排序) (v4.2) | — |
| 6 | ScanPage 周线标签 + sync_log 表 | ✅ 断裂点修复完成 (v4.2) | — |
| 7 | 原型偏移自动校准 | ⏳ `collect_archetype_calibration_data()` 就绪, 等数据积累 | P1 |
| 3 | 原型偏移自动校准 | ⏳ `collect_archetype_calibration_data()` 就绪, 等数据积累 | P1 |
| 4 | contextual_bandit 接入影子训练 | ⏳ select_arm() 已实现, 缺 update() | P1 |
| 5 | angel_model.json 由 signal_quality_scorer 加载 | ⏳ 模型文件存在, 未消费 | P1 |
| 6 | dual_channel_trainer 定期调度 | ⏳ train() 已实现, 缺调度入口 | P1 |
| 7 | mins_train_samples → 分钟线分类器 | ⏳ 表有数据, 缺训练消费 | P2 |
| 8 | 未挂接模块清理 | ⏳ 6 个模块零引用 (baidu_search/contextual_bandit 等) | P2 |
| 9 | API_AUTH_KEY 启用 | ⏳ 配置为空, 生产需启用 | P2 |
| 10 | 提示词模板集中管理 | 💡 重构建议 | P3 |

---

## 9. 已知问题与审计状态

### 9.1 审计修复记录 (2026-06-03)

| # | 审计项 | 修复前 | 修复后 |
|---|--------|--------|--------|
| 1 | 分段训练安全门控 | `trained_params >= 5` | n≥50 + params≥10 + AUC≥0.55 三重检查 + WARNING 回退 |
| 2 | XGBoost 特征 #41 | 占位符 0.0 | 训练+预测双管线接入 sw_sector_index 真实板块数据 |
| 3 | XGBoost 版本校验 | 无 | 三阶段校验 (特征数/特征名/特征哈希) |
| 4 | 概率校准标签窗口 | T+2 (与训练器 T+3 不一致) | 统一为 T+3 |
| 5 | 概率校准 regime 分段 | 无 | build_calibration_by_regime + calibrate_with_regime (不足自动回退) |
| 6 | 跨管线信号断裂 | 净买力 25% importance 在 TG 完全缺失 | AlphaFlow net_power 作为 composite_score 修正因子 |
| 7 | 筹码三区除权偏移 | 无保护 | find_last_ex_rights() 截断 |
| 8 | 波段预测幸存者偏差 | 退市股/极端值未过滤 | delisted_stocks 排除 + 3σ 极端浪幅过滤 |
| 9 | 模型元信息 | 无 training_date/feature_hash | 增加完整元信息 + 版本校验 |
| 10 | 原型偏移 | 全人工猜测 | 标注待校准 + collect_archetype_calibration_data() 就绪 |

### 9.2 已知技术债务

| # | 问题 | 位置 | 严重度 | 建议 |
|---|------|------|--------|------|
| 1 | 提示词模板分散在多个文件中 | 多处 | 中 | 统一到 `prompts/` 目录 |
| 2 | `call_deepseek` 无自动重试/退避 | `deepseek.py` | 中 | 添加 exponential backoff |
| 3 | 无 API token 用量追踪 | 全部 LLM 调用 | 中 | 添加 token 计数和成本估算 |
| 4 | `_active_scan` 全局变量限制多 worker | `scan.py` | 低 | 迁移到数据库状态表 |
| 5 | param_library 全部 is_shadow=false | `param_library` | 中 | self_learning_bootstrap 冷启动 |
| 6 | stock_basic 表可能不存在 | `sector_alliance.py` | 中 | 已 fallback 到 scan_results.industry |
| 7 | feedback_parser.py 绕过 `call_deepseek` | `feedback_parser.py` | 低 | 统一到共享客户端 |
| 8 | 训练数据量 | `scoring_trainer.py` | 低 | 持续增长中 |
| 9 | ARCHETYPE_OFFSETS 全人工猜测 | `archetype_param_resolver.py` | 中 | 校准基础设施已就绪, 等待数据 |
| 10 | ⚠️ 影子训练权重需重训 | `shadow_trainer.py` | **高** | 日历日 bug 已修复，旧 param_library 权重基于错误标签，需清空后全部重训 |
| 11 | ⚠️ 6 个分析脚本丢失 BJ 股票 | `analyze_*.py` 等 | 中 | 引入 `normalize_ts_code()` 替代 `else: continue` |
| 12 | ⚠️ stock_dna.best_emotion_ret 列类型 | `dna_models.py` | 低 | 已修 (Float→JSONB + ALTER TABLE 迁移) |

## 10. 变更日志

**⭐ 新闻页面重复标题修复 (v4.9)**:
- `app/services/event_aggregator.py`: 新增 SimHash 相似度去重
- `_dedup_similar_events()`: 同一股票内相似标题去重
- 阈值: 汉明距离 < 8 判定为相似，每股同主题只保留最高 display_score 的一条
- 修复同一股票多条重复显示问题

**⭐ 新闻分类去重 (v2.1)**:
- `app/services/news_classifier.py`: SimHash 指纹 + 智能分类服务
- **去重**: 跨源 SimHash (汉明距离<10) + 数据库唯一约束
- **分类**: 三级 (company/sector/macro/garbage) - macro_only 跳过 LLM (避免与宏观数据重复)
- **个股摘要保留**: `get_stock_news_summary()` 从 `news_raw` + `stock_events` 合并, 不丢失 title/summary

**⭐ 龙虎榜精细化 (v2.1)**:
- 机构细分: 公募/私募/QFII/北向/社保
- 游资分级: 顶级(95-87分) / 一线(80-60分) / 二线(55-45分) / 三线(40分)
- 共振强度: 5级 (extreme/strong/moderate/weak/minimal)
- 共振标签: 机构入场/顶级游资/一线游资/合力买入/净买普遍
- 净买持续性: 1/3/5日统计
- **智能缓存 (v2.1)**: 历史永久/当日交易时段5min/休市1h
- **SSE 刷新接口 (v2.1)**: POST /api/scan/toplist-refresh
- **新鲜度检查**: GET /api/scan/toplist-freshness
- **前端 SSE 集成**: 进度条 + 刷新按钮 + 缓存标识

**LLM 模型明确化 (v2.1)**:
- 新闻 Stage1 (打标签): DEEPSEEK_FLASH_MODEL (deepseek-v4-flash)
- 新闻 Stage2 公司级: DEEPSEEK_PRO_MODEL (深度分析)
- 新闻 Stage2 行业/政策/商品: DEEPSEEK_FLASH_MODEL (轻量任务)

**修复**:
- `news_crawler.py`: 浏览器启动加超时 (10s/15s), 防止按钮卡死
- `news_crawler.py`: 进度回调 (init/crawl_X/dedup/store) 让前端实时反馈

**前端**:
- NewsPage: 板块共振 5 级强度 + 共振标签展示
- NewsPage: 个股席位精细化 (北向/公募/社保/顶级/一线/二线) 标签

### v4.8 (2026-06-13) — DNA 实验室自动化 + 新闻采集优化 + 宏观数据改造 + TG 扫描阶段重组

**⭐ DNA 自动加入三种机制**:
- `app/services/stock_dna_auto_join.py`: 独立服务模块, 提供三个自动加入函数
- **机制1 (AlphaFlow)**: lock_state=breakout_up + TG买入信号 → 自动加入 DNA
- **机制2 (TG扫描)**: 每日扫描完成后, L3级股票自动加入 DNA (L1/L2不加入) — **v4.8.2 改为异步后台执行, 不阻塞 done 事件**
- **机制3 (持仓变动)**: 持仓新增或清仓 → 相关股票自动加入 DNA (保留模型用于后续分析)

**⭐ 新闻特征系统改造 (枯竭数据 → Tushare 宏观数据)**:
- 旧问题: `stock_events` / `news_aggregated` / `news_verify` 表数据稀疏, 新闻特征长期空缺
- 旧方案: `score_event_impact()` 读取空表, 返回 0
- 新方案: 使用 `compute_sector_macro_score()` + Tushare 宏观数据
- 改造位置:
  - `deep_scorer.py`: `score_event_impact()` → `compute_sector_macro_score()` (板块宏观得分 × 3)
  - `deep_scorer.py`: 新闻信号加权从 `news_aggregated` 改为宏观数据
  - `holdings.py`: `news_signal` 字段用 `sector_macro_cache` 预计算
  - `LearningPage.tsx`: 新闻验证标签 → 宏观快照展示 (MacroSnapshotView 组件)

**⭐ 新闻采集优化**:
- **聚合接口**: `GET /scan/news-dashboard` 一次返回所有数据
- **新鲜度API**: `GET /scan/news-freshness` 返回 should_crawl/should_analyze/recommendation
- **增量更新**: `news_pipeline.py` 根据新鲜度智能跳过爬取或LLM分析
- **前端分类工具**: `classifyMarket()` / `filterByMarket()` 统一市场分类逻辑

**⭐ 新闻分类去重 v2.1**:
- `app/services/news_classifier.py`: SimHash 指纹 + 智能分类
- **去重**: 跨源 SimHash (汉明距离<10) + 数据库唯一约束
- **分类**: 三级 (company/sector/macro/garbage) - macro_only 跳过 LLM
- **个股摘要保留**: `get_stock_news_summary()` 从 `news_raw` + `stock_events` 合并, 不丢失 title/summary
- **修复新闻速报按钮**: 浏览器启动加超时 (10s/15s), 防止按钮卡死

**⭐ 龙虎榜精细化 v2.0**:
- 机构细分: 公募/私募/QFII/北向/社保
- 游资分级: 顶级(95-87分) / 一线(80-60分) / 二线(55-45分) / 三线(40分)
- 共振强度: 5级 (extreme/strong/moderate/weak/minimal)
- 共振标签: 机构入场/顶级游资/一线游资/合力买入/净买普遍
- 净买持续性: 1/3/5日统计
- **智能缓存**: 历史永久/当日交易时段5min/休市1h
- **SSE 刷新接口**: POST /api/scan/toplist-refresh
- **新鲜度检查**: GET /api/scan/toplist-freshness

**⭐ 融资融券情绪重写**:
- 旧问题: `trend_pct`/`detail`/`sentiment` 字段 undefined, 返回 0
- 新方案: 改用 `rzye` (融资余额) 直接判断
- **判定标准**: > 1.6万亿=亢奋 (注意风险), 1.2-1.6万亿=正常, < 1.2万亿=谨慎
- 同步数据: `margin_trading` 表 (ts_code='TOTAL' 汇总)

**⭐ TG 扫描阶段重组 v4.8.2 (本次修复 P0/P1/P2 共 15 项问题)**:

| 修复 | 文件 | 说明 |
|------|------|------|
| **P0-1** | `ScanPage.tsx` | `setCurrentPhase` 类型从 `'download'\|'scan'\|null` 扩展为 10 个 `ScanPhase` |
| **P0-2** | `scan.py` | DNA auto-join 用 `asyncio.create_task()` 异步执行, 不阻塞 done 事件 |
| **P1-1** | `scan.py` | 移除 `toplist_sync` 阶段 (与 `toplist` 重复), 合并到 ① |
| **P1-2** | `ScanPage.tsx` | phaseMessages slice(-8) → slice(-20), maxHeight 120 → 280 |
| **P1-3** | `scan.py` + `ScanPage.tsx` | `trigger_scan` 接受 `market_filter` 参数, 后端用 `classify_board` 真过滤 |
| **P1-4** | `scan.py` | `skip_download=True` 同时跳过龙虎榜 + DNA, 不调 Tushare API |
| **P1-5** | `tg_engine.py` | scan phase 节流: `% 200/500` → `% max(1, total//20)` (5% 步长), `asyncio_sleep(0)` `% 10` → `% 50` |
| **P1-6** | `accuracy_tracker.py` | `apply_accuracy_feedback(isolated_meta=True)` 写入独立 `accuracy_feedback_factor` 列, 不覆盖主 discrimination |
| **P2-1** | `scan.py` | 文案 "12维评分" → "14维评分" |
| **P2-2** | `scan.py` | 所有 phase `extra` 异常信息统一改为 "异常: {e}" |
| **P2-3** | `tg_engine.py` | 覆盖率 < 95% 时回退 `latest_date` → 回退 365 天, 避免漏掉中间日 |
| **P2-4** | `scan.py` | ambush_scan 用 `scan_results.MAX(scan_date)` 而非 `analysis_scores.MAX(scan_date)` |
| **P2-5** | `tg_engine.py` | ST 过滤正则 `[*]?ST` → `name ~* '[* ]?ST' OR name LIKE '%ST%' OR name LIKE '%退%'` |
| **P2-6** | `ScanPage.tsx` | phaseLabel 新增 `'🧬DNA训练'` 标签, 阶段指示器含 dna_auto_join |
| **DB** | `param_library` | 新增列 `accuracy_feedback_factor`, `accuracy_feedback_at` |

**市场过滤 v4.8 (后端真过滤)**:

```
前端 ScanPage 主板/中小板/创业板 按钮
  ↓ market_filter=主板  (URL query)
后端 trigger_scan
  ↓ classify_board(ts_code) → '上海主板'|'深圳主板'|'中小板'|'创业板'
  ↓ 主板允许列表: ['上海主板', '深圳主板']
  ↓ results = results[results['symbol'].apply(in allowed)]
  ↓ 日志: market_filter=主板 (allowed=['上海主板', '深圳主板']): 5500 -> 3500
```

### v4.7 (2026-06-09) — AlphaFlow 信号重构 + 大神仙空全局部署 + 两期扫描

**⭐ 大神仙空 v2.0 — 全局卖出指标**:
- `app/services/big_fairy.py`: 7 维度评分 (KDJ + MACD + MA均线 + RSI + 量价 + 动量 + 超买综合), score≥2=sell, ≥3=strong_sell
- 13/13 同花顺卖出信号校准 (000881/000333/600329/600167 四股全部日期匹配)
- `_big_fairy_from_arrays()`: 纯 NumPy 计算, 批量模式下无 DB I/O, pool_service 一次查询加载全池 K 线后内存计算
- API: `GET /api/alphaflow/big-fairy` + `GET /api/holdings/big-fairy`

**⭐ AlphaFlow 信号逻辑重构**:
- `lock_detector.py v2.3`: `state` 字段区分 `locked` / `breakout_up` / `breakout_down`, 通过 close vs MA20 + 20日趋势判定方向
- `alphaflow_pool_service.py v4.7`: 批量加载全池 K 线+成交量, 一次查询加载所有 TG scan_results
- 信号规则: 锁死中→watch, 主升浪+TG(10天延续)→buy, 主升浪+BF(10天延续)→sell, TG/BF同时活跃→最新胜出, 破位→sell
- 大神仙空≥2 直接覆盖所有信号为卖出, ≥3 从分析页剔除, =2 打六折

**⭐ 两期 SSE 扫描**:
- `alphaflow_pool.py`: `daily_scan()` 新增 `restrict_symbols` 参数, 支持定向扫描
- `alphaflow.py /scan`: Phase 1 扫池内~100只 (秒级), 前端立即刷新; Phase 2 后台扫全市场~5400只找新蛋
- 前端 SSE 流式接收进度 (锁死检测/XGBoost/策略/清理 各阶段百分比)

**⭐ 富宏观上下文**:
- `llm_deep_analyzer.py`: 旧 3 值 (M2/SHIBOR/PMI) → 8 段 25+ 指标 (货币/通胀/PMI/GDP/利率曲线/杠杆/汇率/10商品/5概念/综合判读)
- 所有值来自 macro_cache, 杜绝 LLM 虚构宏观叙事

**⭐ 事件管道净化**:
- `event_detector.py v4.7`: LLM Stage 1 前加入商品/宏观关键词预过滤 (期货/原油/沪铜/人民币/美元/SHIBOR/PMI/CPI/国债...)
- 命中关键词但含公司级白名单 (中标/签约/减持/业绩/公告/涨停) → 保留; 否则丢弃
- 存量清理: 58 条 LLM 虚构 sector_events 已删除, 86→28

**修复**:
- `tg_engine.py`: 涨停过滤改用 `close/prev_close` 替代 `(close-open)/open`, 修复一字板漏检
- 科创板 20% / 北交所 30% 阈值已内置
- `DeepAnalysisPage.tsx`: localStorage 持久化恢复修复 (individual/batchScores/completed 完整恢复)

**前端**:
- AlphaFlowPage: +大神仙空列, SSE 扫描进度, 两期事件处理
- AnalysisPage: 趋势列→大神仙空列, BF 过滤
- HoldingsPage: 大神仙空信号展示

### v4.6 (2026-06-05~08) — 影子训练器升级 + 宏观数据扩展 + 新闻管线退役

**⭐ 影子训练器 66 维升级** (`shadow_trainer.py`):
- DEFAULT_WEIGHTS: 23→66 维 (23 技术 + 14 Tier1 大盘 + 18 Tier2 板块 + 11 Tier3 个股)
- 三级漏斗: Tier1 (宏观指标直接乘) → Tier2 (乘板块暴露系数) → Tier3 (个股 ROE/资金流)
- `build_macro_context()`: 从 macro_cache 批量加载, `score_stock(row, weights, macro_context)`
- `factor_exposure.py`: 27 板块 × 30 因子矩阵 + 12 商品 × 84 链路 + DEFAULT_EXPOSURE 回退

**⭐ 宏观数据扩展** (`macro_data.py`):
- INDICATORS: 16→50+ 指标 (新增 M1-M2剪刀差/SHIBOR利差/PMI细分/CPI核心/PPI产端/GDP分项/汇率/国债)
- `_sync_commodity_prices()`: 12 品种期货主力合约日线同步到 macro_cache
- `_sync_sector_indices()`: 28 SW 行业 + 概念指数 5 日涨跌幅
- `get_macro_snapshot()`: 含 direction (bullish/bearish/neutral) 和 unit 字段

**⭐ 新闻管线 M-5 退役** (`event_detector.py`):
- 删除 6 个宏观/政策/商品 LLM 分析入口 (`get_macro_adjustment`/`score_sector_news`)
- TAG_TO_SYSTEM 精简为仅保留公司级 4 类 (company_announcement/stock_market/leaderboard/tech_innovation)
- `deep_scorer.py`: 替换为 `score_macro_impact()` 数据驱动宏观修正
- `news_crawler.py`: 加 DEPRECATED 标记

**AlphaFlow 页面改造**:
- 表头 8→5 列 (移除 层级/趋势), 字体放大, 抽屉重写 (4 卡片 + 周期历史 + breakout_pct + 预判)
- Pool limit: 50→500 只
- `lock_detail_service.py`: 突破后 40 日 rally peak 计算

**其他修复**:
- TG lockup→lockup_score (评分制, 5日滑动窗口 ≥2/3 条件)
- `stock_dna` 中文前缀原型名 SQL 修复 (`SPLIT_PART(archetype, '_', 2)`)
- `shadow_trainer` 日历日→交易日修正 (compute_excess_return)

### v4.5 (2026-06-07) — 系统级 P0 能力升级 + DNA 个性化模型

**⭐ 系统级 P0 7 阶段升级**:
- **Phase 1 NaN 统一**: `app/utils/numpy_utils.py` (safe_float/safe_auc/safe_rsi/sanitize_array/sanitize_for_json/div0/safe_corrcoef) — 替代 14 处分散 NaN 守卫 (4 种不一致策略)
- **Phase 2 超额收益**: `app/core/market_data.py` (get_benchmark_closes/compute_excess_return) — 统一 3 处独立实现 + **修正 shadow_trainer 日历日 counting bug** (日历日→交易日)
- **Phase 3 Progress**: `app/core/progress.py` (ProgressCallback 协议 + make_progress_adapter) — 统一 3 种回调签名为 4 参数标准
- **Phase 4 基准**: `get_benchmark_closes()` 模块级缓存替代 14 处 700001.TI 分散 SQL
- **Phase 5 代码**: `app/utils/stock_code.py` (normalize_ts_code) — 替代 9 处 `startswith('6')→.SH` 复制 + 修复 6 处 BJ 丢弃 bug + 920xxx 支持
- **Phase 6 名称**: `app/core/name_resolver.py` (三级缓存: 内存→DB→fallback) — 替代 5 处绕过缓存
- **Phase 7 NumPy**: JSON 序列化统一 (Phase 1 中已做)

**⭐ 全局前复权**:
- `scripts/resync_all_kline.py`: Tushare adj_factor API → 前向填充 → 手动前复权公式 (close_adj = close_raw × af[t] / af[latest])
- `daily_kline` 表新增 `adj_factor DOUBLE PRECISION` 列
- `app/services/kline_utils.py`: get_adjusted_kline() / get_ex_rights_dates() / iter_non_exrights_chunks()
- **退役 9 个除权补丁**: find_last_ex_rights (20%阈值), _is_ex_rights_day (15%+10%), _adjust_ex_rights (18%), 及 6 个调用方全部移除

**⭐ DNA 个性化模型实验室**:
- 10 文件 `stock_dna` 包 (features/emotion/cycle/market_context/data_builder/model/inference/similarity/dna_models)
- 独立 API `/api/dna/*` 7 端点 + 独立 DB `stock_dna.*` 3 表 + 前端 `DnaLab.tsx` 4 Tab
- Per-Stock XGBoost (80树×depth=3, Huber δ=3.0, T+2/5/10/20 四窗口)
- 表情聚类 (15维→KMeans++ 轮廓系数→5-8种个性化表情→马尔可夫转移矩阵)
- 老兵周期 v2 (ATR<0.8/MA<0.04/VOL<0.8, ≥2/3条件+5日滑动窗口容错)
- 日线伪表情降级 (无分时数据时用 OHLCV 计算简化表情)
- DNA 穿透测试: API 12/12 + 数据 14/14 + 隔离 1/1 全部通过

**验证**: numpy_utils 65/65 PASS | market_data 14/14 PASS | 模块编译 20+ PASS | 路由 125 条 | API 全线正常

**个股历史深度复盘 (stock_historical_drill.py)**:
- 7 项子复盘: 信号有效性回溯 + K线形态匹配 + 关键位置博弈 + 筹码吸收模拟 + 市场敏感性 + 四维共振 + 操盘手法反推
- 缓存: 同日同股内存缓存, 避免重复计算
- 集成: result.py 中在推荐返回前执行, drill_summary/drill_resonance/drill_micro_behavior 注入 API 响应

**四维共振分析 (resonance_analyzer.py)**:
- 指数共振: 个股 vs 上证 T+5 收益分类 (独立上涨/共振/伪强势)
- 板块共振: 个股 vs SW行业 T+5 收益分类 (领先/跟随/背离)
- 消息共振: 信号日前后3天新闻方向 vs 涨跌一致性
- 筹码共振: 信号前20天三区吸收率 vs 后续胜率
- 应用到评分: 独立率+2, 伪强势率-3, 领先率+2, 高吸收+3, 低吸收-4

**操盘手法反推 (micro_behavior_analyzer.py)**:
- 5类动作检测: 快速拉升/砸盘/托单横盘/尾盘偷袭/开盘冲锋
- 10个嫌疑指标快照 (VWAP距离/布林分位/整数关口/上影占比等)
- 触发条件发现: 动作组 vs 随机对照组 → 提升度统计
- 当前状态扫描: 最近50根K线是否满足历史触发条件
- API: GET /api/drill/micro-behavior/active-signals
- 应用到评分: 拉升触发+2, 砸盘触发-3

**系统自动激活 + 异常检测**:
- system_health.py: check_and_upgrade_components() 每日16:00检测并自动激活达标组件
- anomaly_detector.py: check_signal_distribution() 信号数量/win_probability偏离3σ告警
- shadow_trainer.py: evaluate_shadow_vs_main() 每周日对比, 连胜3周自动切换
- background_sync 每日调度增加: 健康自检 + 异常检测 + 影子评估

**TG→AlphaFlow 反向特征注入 (48维)**:
- alphaflow_features.py: FEAT_NAMES 增至48, compute_wave_features 新增 tg_score 参数
- alphaflow_pool.py: daily_scan 前预加载 analysis_scores 的 composite_score 作为第48维
- alphaflow_train_v2.py: 训练管线同步接入 TG score

**质量控制 + 风控升级**:
- deep_scorer.py: QUALITY_GATE L1/L2 两级自适应放宽 (通过<10逐级降门槛)
- deep_scorer.py: 分段权重 regime 持续>60天软衰减混入全局权重
- market_gate.py: force_empty 判定 (恐慌杀跌+胜率<25%+上涨<20%)
- result.py: 安全阀扩展到全部体制, _sanitize_numpy() 清洗numpy类型防止500
- accuracy_tracker.py: apply_accuracy_feedback T+5不足时降级到T+3

**AlphaFlow 量能历史参考**:
- alphaflow.py lock-detail: volume_trend 增加 reference 字段 (历史锁死周期量变分布)
- 前端: 量能条下方展示历史范围 + 中位线 + 当前分位标签 (偏上/偏下/中等)

**前端重大改造**:
- AlphaFlowPage: 四层信息架构 (结论Banner→关键价格→锁死历史→可折叠详情)
- ResultPage: 老股民研判区域重设计 (综合评级+正负分栏+关键指标仪表盘+操作建议)
- MonitorPage: 组件就绪状态面板 (分段权重/校准器/原型偏移进度条)
- DeepAnalysisPage: localStorage 持久化, 页面跳转后可恢复分析结果
- ScanPage: 新增周线共振标签
- ResultPage: 历史入口修复 (date参数+snapshot_date查询)

**训练数据更新**:
- 推荐追踪: 214 条样本, Logistic Regression AUC 0.6452 (v4.2: 103条, AUC 0.60)
- 分段权重: range 段已训练, bull/bear 段等待积累 (需≥50条/段)
- 概率校准器: T+3 标签统一 + regime分段框架就绪 (等待≥100样本/段)

**新增API端点**:
- POST /api/drill/analyze — 批量复盘
- GET /api/drill/report/{symbol} — 单股复盘
- GET /api/drill/micro-behavior/active-signals — 操盘触发扫描
- GET /api/learning/system-readiness — 组件就绪

### v4.2 (2026-06-03) — 方案 B 周线共振 + 质量控制优化 + 断裂点修复

**方案 B — 周线双周期共振**:
- tg_engine: 新增 `resample_daily_to_weekly()` (日线→周线重采样) + `scan_weekly_signals()` (全市场周线TG扫描)
- tg_engine: 新增 Phase 1.5 — 在日线扫描完成后无条件执行周线扫描 + 双周期信号匹配
- deep_scorer: 新增 `score_weekly_resonance()` 评分函数 + `DEFAULT_WEIGHTS["weekly_resonance_weight"]=2.0`
- result.py: ORDER BY 改为三级优先级排序 (resonance=0 > daily_only=1 > weekly_driven=2)
- data_models.py: ScanResult 新增 3 个字段 (resonance_type, weekly_has_buy, weekly_tg_momentum)
- 前端: ScanPage + ResultPage 新增 ⭐周线共振/📅周线驱动 标签

**质量控制优化**:
- deep_scorer: QUALITY_GATE 新增 L1/L2 两级自适应放宽 (通过<10→降sq/wp/ts门槛→放宽→仍<8→降sc/wp门槛)
- deep_scorer: 质量过滤增加逐股失败日志 (sq_low/wp_low/ts_low 统计 + 前5条被过滤股详情)
- result.py: 安全阀从仅3种弱势体制扩展到全部体制 (>5只推荐兜底)

**断裂点修复 (全链路审计)**:
- scan.py: GET /api/scan/results 新增 resonance_type/weekly_tg_momentum 字段
- background_sync.py: `run_daily_backtest()` 增加 `CREATE TABLE IF NOT EXISTS sync_log` 保护
- deep_scorer.py: AlphaFlow 净买力修正 catch 块增加 `logger.debug()` 日志
- alphaflow.py: `get_pool()` 增加 `model_status` 字段 ("ok"/"degraded")
- accuracy_tracker.py: `apply_accuracy_feedback()` T+5 不足时自动降级到 T+3

**新增脚本**:
- `scripts/add_weekly_columns.py` — 为 scan_results 表添加周线三列
- `scripts/backtest_weekly_resonance.py` — 按共振类型统计 T+5/T+10/T+20 收益和胜率

**训练数据更新**:
- 推荐追踪从 103 条增至 214 条 (05-28 + 05-29 数据)
- Logistic Regression AUC 从 0.60 提升至 0.6452
- `full_training_pipeline(by_regime=True)` 支持分段训练，range 段 214 条

### v4.1 (2026-06-03) — 第二阶段安全审计修复

**学习闭环升级**:
- scoring_trainer: 新增 `load_training_data_with_regime()`, `train_weights_by_regime()`, `_fit_logistic_regression()` — 按市场状态分段训练
- scoring_trainer: `persist_weights()` 写入 `__regime_auc__` 和 `__trained_at__` 元信息
- deep_scorer: 三重安全门控 (MIN_REGIME_SAMPLES=50, MIN_REGIME_PARAMS=10, MIN_REGIME_AUC=0.55)
- deep_scorer: AlphaFlow 净买力接入 composite_score 作为交叉反哺修正因子
- probability_calibrator: T+2→T+3 标签统一, 新增 `build_calibration_by_regime()`, `calibrate_with_regime()`, `scheduled_recalibrate_with_regime()`
- archetype_param_resolver: ARCHETYPE_OFFSETS 标注待校准 + `collect_archetype_calibration_data()`

**AlphaFlow 升级**:
- alphaflow_train_v2: 训练管线接入 sector_closes (特征#41真实化), meta 增加 training_date/feature_names/feature_hash
- alphaflow_pool: `_load_xgb_model()` 三阶段版本校验 (特征数/特征名/特征哈希)
- chip_analyzer: 新增 `find_last_ex_rights()` 除权免疫
- wave_predictor: 新增 delisted_stocks 排除 + 3σ 极端浪幅过滤
- alphaflow_veteran: 新增 `backtest_veteran_breakout_rate()` + API 端点

**后台调度扩展**:
- background_sync: 周一权重分段训练 + 周六老兵回测 + 周日 regime 概率重校准

**新增端点**:
- `GET /api/alphaflow/veteran-backtest`
- `GET /api/learning/archetypes/calibration-data`

**部署工具**:
- `retrain_xgb.ps1` — XGBoost 重训脚本
- `verify_all.ps1` — 完整部署验证链
- `docs/post_deployment_monitoring.md` — 监控指南

### v4.0 (2026-06-02) — AlphaFlow 全面重写

- AlphaFlow 锁死→老兵→评估→XGBoost→策略→池 完整管线
- 筹码吸收三区模型 + 波段目标预测
- XGBoost V2 47维 (含6维老兵增强) AUC 0.7898
- 市场门控 v2.0 (7体制+涨跌比+风格偏向)
- 持仓管理升级 (资金账户/自动清仓/待清仓/筹码诊断)
- 一键综合分析引擎

---

> **文档维护**：本文件随系统升级持续更新。最后更新：2026-06-07 (v4.5: P0 系统级升级 + DNA 实验室)。
