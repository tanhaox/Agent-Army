# OpenClaw Server Files Analysis Report
**Generated**: 2026-04-08
**Server**: 157.245.195.58:2323

---

## 1. coordinator_agent.py - Weight Definitions

### Current Weights (Lines 30-35)
```python
self.weights = weights or {
    "technical": 0.40,      # 40%
    "fundamental": 0.30,    # 30%
    "capital": 0.20,        # 20%
    "news": 0.10            # 10%
}
```

### How Weights Are Used (Lines 77-94)
The `coordinate()` method calculates total score:
```python
# Line 78-83: Base 4 dimensions (100% total)
total_score = (
    tech_score * self.weights.get("technical", 0) +
    fund_score * self.weights.get("fundamental", 0) +
    cap_score * self.weights.get("capital", 0) +
    news_score * self.weights.get("news", 0)
)

# Line 86-87: K-line game analysis (ADDITIONAL)
if kline_score is not None and "kline_game" in self.weights:
    total_score += kline_score * self.weights["kline_game"]

# Line 89-90: Relative strength (ADDITIONAL)
if rs_score is not None and "rs" in self.weights:
    total_score += rs_score * self.weights["rs"]

# Line 93-94: ML prediction (ADDITIONAL adjustment)
if ml_score is not None and "ml" in self.weights:
    total_score += ml_score * self.weights["ml"]
```

**KEY FINDING**: The code does NOT use `macro` weight at all. No mention of macro analysis anywhere in coordinator_agent.py.

### Prediction Verification (Lines 125-154)
The `_extract_ml_score()` method converts ML predictions to 0-10 scores:
```python
# Line 139-141: Extract ML prediction data
direction = ml_result.get('direction', 'unknown')
confidence = float(ml_result.get('confidence', 0))
accuracy = float(ml_result.get('accuracy', 0))

# Line 143-144: Skip low confidence
if direction == 'unknown' or confidence < 0.1:
    return None

# Line 146-148: Calculate adjustment (0.5~2.5 points)
adj = confidence * max(0.3, accuracy) * 5.0

# Line 150-153: Map direction to score
if direction == 'up':
    return 5.0 + adj
elif direction == 'down':
    return 5.0 - adj
```

**No prediction verification logic found** - only confidence filtering.

---

## 2. monitor.py - Alert Thresholds

### Stop Loss Configuration (Lines 401-407)
```python
STOP_LOSS_CONFIG = {
    'enabled': True,
    'threshold': 0.95,     # 95% of cost price = 5% loss
    'apply_to_holdings': True,
    'apply_to_watchlist': True,  # Also alert for watchlist
}
```

### Price Limit Alert Thresholds (Lines 698-750)
```python
# Line 728-736: Near limit up (>= 98%)
if ratio_up >= 0.98:
    signals.append({
        'level': 'medium',
        'type': '接近涨停',
        'msg': f'接近度{ratio_up:.1%}'
    })

# Line 739-747: Near limit down (<= 102%)
if ratio_down <= 1.02:
    signals.append({
        'level': 'high',
        'type': '接近跌停',
        'msg': f'接近度{ratio_down:.1%}'
    })
```

### Capital Flow Thresholds (Lines 525-586)
```python
# Line 536-538: Main net inflow > 10 million
if inflow > 1e7:
    signals.append({'level': 'medium', 'type': '主力大幅流入'})

# Line 539-541: Main net outflow < -10 million
elif inflow < -1e7:
    signals.append({'level': 'high', 'type': '主力大幅流出'})

# Line 576-582: North money consecutive outflow (3 days)
if negative_days >= 3:
    signals.append({'level': 'high', 'type': '北向连续流出'})
```

### Technical Indicators (Lines 465-490)
```python
# Line 466-468: RSI overbought (> 70)
if rsi > 70:
    signals.append({'level': 'medium', 'type': '技术超买'})

# Line 469-471: RSI oversold (< 30)
elif rsi < 30:
    signals.append({'level': 'medium', 'type': '技术超卖'})

# Line 476-478: MACD golden cross
if macd > 0 and macd_prev <= 0:
    signals.append({'level': 'medium', 'type': 'MACD金叉'})

# Line 479-481: MACD death cross
elif macd < 0 and macd_prev >= 0:
    signals.append({'level': 'medium', 'type': 'MACD死叉'})

# Line 484-489: Trend detection
if trend == 'up':
    signals.append({'level': 'low', 'type': '上升趋势'})
elif trend == 'down':
    signals.append({'level': 'high', 'type': '下降趋势'})
```

### Turnover Rate Alerts (Lines 491-519)
```python
# Line 499-505: Abnormal turnover (> 2x 20-day average)
if turnover_ratio > 2:
    signals.append({
        'level': 'high',
        'type': '换手率异常放大'
    })

# Line 506-512: High turnover (> 1.5x)
elif turnover_ratio > 1.5:
    signals.append({'level': 'medium', 'type': '换手率放大'})

# Line 513-519: Low turnover (< 0.3x)
elif turnover_ratio < 0.3:
    signals.append({'level': 'low', 'type': '换手率极低'})
```

### Market Sentiment Alerts (Lines 792-804)
```python
# Line 797-802: Extreme sentiment
if composite < 20 or composite > 80:
    level_str = '极度恐慌' if composite < 20 else '极度乐观'
    signals.append({'level': 'medium', 'type': '市场情绪极端'})
```

### Capital Flow Extreme Alerts (Lines 826-842)
```python
# Line 833-836: ETF heavy inflow (> 800 billion in 5 days)
if etf_5d > 800:
    signals.append({'level': 'medium', 'type': 'ETF资金大幅流入'})

# Line 837-840: Corp capital heavy outflow (< -100 billion)
if corp_5d < -100:
    signals.append({'level': 'medium', 'type': '产业资本大幅减持'})
```

### Macro Environment Alerts (Lines 844-859)
```python
# Line 849-853: Macro deterioration
if _macro_score < 3.0:
    signals.append({'level': 'high', 'type': '宏观环境恶化'})

# Line 854-857: Macro improvement
elif _macro_score > 8.0:
    signals.append({'level': 'medium', 'type': '宏观环境偏暖'})
```

---

## 3. scanner.py - Scoring Parameters

### Auto Add Configuration (Lines 912-918)
```python
AUTO_ADD_CONFIG = {
    'enabled': True,
    'min_score': 4,           # Minimum total score (backtest verified: score>=4 Sharpe=1.17)
    'max_rank': 10,           # Only add top N
    'avoid_duplicates': True, # Avoid duplicates
    'add_reason': '自动扫描机会股'
}
```

### Technical Strategy Scoring (Lines 1161-1279)

**Strategy 1: Break 20-day high (Line 1191-1195)**
```python
if today_close > past_19_high and today_vol > 1.5 * vol_ma20:
    score += 1
    triggers.append('突破20日高点')
```

**Strategy 2: Short-term strength (Line 1198-1202)**
```python
ret_20d = (today_close - close[-21]) / close[-21]
if ret_20d > 0.05:  # 5% gain in 20 days
    score += 1
    triggers.append(f'20日涨{ret_20d*100:.1f}%')
```

**Strategy 3: Bottom volume (Line 1205-1213)**
```python
price_position = (today_close - low_60d) / price_range
if price_position < 0.3 and today_vol > 2.0 * vol_ma20:
    score += 1
    triggers.append(f'底部放量(位{price_position:.0%})')
```

**Strategy 4: Oversold rebound (Line 1216-1219)**
```python
rsi = calc_rsi(close, 14)
if rsi < 30:
    score += 1
    triggers.append(f'RSI={rsi:.0f}超卖')
```

**Strategy 5: Relative strength (Line 1222-1226)**
```python
if index_ret_20d != 0 and stock_ret_20d / index_ret_20d > 1.05:
    score += 1
    triggers.append(f'相对强度{stock_ret_20d/index_ret_20d:.2f}')
```

**Strategy 6: Main net inflow (Line 1229-1277)**
```python
# Real moneyflow data (Line 1238-1251)
if net_mf > 5000:  # > 5000万
    score += 1
elif net_mf > 1000:
    score += 0.5
elif net_mf < -5000:
    score -= 1

# Volume-price proxy (Line 1256-1277)
if consecutive_bullish >= 3:
    score += 1
elif today_return > 0.03 and today_vol_ratio > 1.5:
    score += 1
```

### Fundamental Scoring (Lines 1287-1339)
```python
# Line 1327-1331: ROE scoring
if roe >= 20:
    score += 2
elif roe >= 15:
    score += 1

# Line 1333-1337: Revenue growth scoring
if revenue_growth >= 50:
    score += 2
elif revenue_growth >= 20:
    score += 1
```

### Sector Allocation (Lines 1605-1618)
```python
# Line 1611-1616: Sector strength bonus
sector_strength = ss_result.get('strength_score', 0.0)
if sector_strength > 0:
    score += sector_strength
    triggers.append(f'板块强度+{sector_strength:.1f}')
elif sector_strength < -0.5:
    triggers.append(f'板块弱势({sector_strength:.1f})')
```

---

## 4. config/weights.json - Current Values

```json
{
  "technical": 0.35,      // 35% (decreased from 40%)
  "fundamental": 0.25,    // 25% (decreased from 30%)
  "capital": 0.18,        // 18% (decreased from 20%)
  "news": 0.06,           // 6% (decreased from 10%)
  "game": 0.06,           // 6% (NEW - K-line game)
  "rs": 0.05,             // 5% (NEW - Relative strength)
  "ml": 0.05              // 5% (NEW - ML prediction)
}
```

**SUM**: 35+25+18+6+6+5+5 = **100%** (normalized)

**KEY CHANGES**:
- Reduced base 4 dimensions from 100% to 84%
- Added 3 new dimensions: game (6%), rs (5%), ml (5%)
- Total still 100%

---

## 5. config/scanner_config.json - Current Values

```json
{
  "min_score": 4,              // Minimum score to add to watchlist
  "max_rank": 10,              // Only add top 10
  "top_n": 20,                 // Output top 20
  "avoid_duplicates": true,
  "auto_add_to_watchlist": true,
  "add_reason": "自动扫描机会股",
  "fundamental_scoring": {
    "enabled": true,
    "roe_thresholds": {"high": 20, "medium": 15},
    "revenue_growth_thresholds": {"high": 50, "medium": 20},
    "max_score": 4             // Maximum fundamental score
  },
  "stock_filter": {
    "main_board_prefixes": ["600", "601", "603", "000", "001", "002"],
    "min_listing_days": 60,
    "exclude_patterns": ["ST", "退"],
    "exclude_etf_prefixes": ["51", "56", "159", "11", "12", "508"]
  },
  "cache": {
    "stock_pool_hours": 24,
    "fundamentals_hours": 24
  }
}
```

---

## 6. config/market_sentiment_config.json - Current Values

```json
{
  "weights": {
    "advance_decline": 0.24,    // 24% - 涨跌比
    "new_high_low": 0.16,       // 16% - 新高新低
    "pcr_option": 0.20,         // 20% - 期权PCR
    "margin_ratio": 0.20,       // 20% - 融资占比
    "short_term": 0.20          // 20% - 短线情绪
  },
  "thresholds": {
    "extreme_optimism": 80,     // > 80: 极度乐观
    "optimism": 60,             // 60-80: 乐观
    "neutral": 40,              // 40-60: 中性
    "panic": 20                 // < 20: 极度恐慌
  },
  "hot_top_n": 10
}
```

---

## 7. config/capital_flow_config.json - Current Values

```json
{
  "individual": {
    "moneyflow_thresholds": {
      "strong_inflow": 10000,      // > 1亿
      "medium_inflow": 5000,       // > 5000万
      "small_inflow": 1000,        // > 1000万
      "small_outflow": -1000,      // < -1000万
      "medium_outflow": -5000,     // < -5000万
      "strong_outflow": -10000,    // < -1亿
      "unit": "万元"
    },
    "big_order_consistency_bonus": 0.5,
    "trend_3d_bonus": 0.5,
    "trend_3d_threshold": 15000    // 3日累计 > 1.5亿
  },
  "market": {
    "weights": {
      "fund": 0.30,
      "etf": 0.30,
      "corp": 0.20,
      "block": 0.20
    },
    "fund_position_levels": {
      "very_high": 85,
      "high": 80,
      "medium": 75,
      "low": 70
    },
    "etf_5d_thresholds_yi": {
      "strong_inflow": 500,        // > 500亿
      "medium_inflow": 200,        // > 200亿
      "medium_outflow": -200       // < -200亿
    },
    "corp_5d_thresholds_yi": {
      "strong": 10,                // > 10亿
      "weak": -10                  // < -10亿
    }
  },
  "north": {
    "strong_inflow": 50000000,     // > 5000万
    "medium_inflow": 20000000,     // > 2000万
    "strong_outflow": -30000000,   // < -3000万
    "medium_outflow": -10000000,   // < -1000万
    "consecutive_outflow_days": 3
  }
}
```

---

## Key Findings Summary

### 1. MACRO ANALYSIS IS NOT INTEGRATED
- `coordinator_agent.py` has NO `macro` weight usage
- `weights.json` has NO macro weight defined
- `monitor.py` calls macro_analyzer but only for alerts (Lines 844-859)
- **Need to add macro to coordinator weights and coordinate() method**

### 2. WEIGHT NORMALIZATION NEEDED
- Current `weights.json`: 35+25+18+6+6+5+5 = 100%
- But `coordinator_agent.py` still uses old 40/30/20/10 base
- **Need to update coordinator_agent.py defaults to match weights.json**

### 3. NO ML PREDICTION VERIFICATION
- `_extract_ml_score()` only filters by confidence
- No actual accuracy tracking or verification
- **Need to add prediction verification logic**

### 4. ALERT THRESHOLDS ARE REASONABLE
- Stop loss: 5% (0.95 threshold)
- Price limit: >= 98% up, <= 102% down
- Capital flow: +/- 1000万 (medium), +/- 1亿 (strong)
- RSI: >70 (overbought), <30 (oversold)
- Turnover: >2x (abnormal), >1.5x (high), <0.3x (low)

### 5. SCANNER PARAMETERS ARE CONSERVATIVE
- min_score: 4 (backtest verified)
- max_rank: 10 (only add top 10)
- Technical max: 6 points
- Fundamental max: 4 points
- Total max: 10+ points (with bonuses)

---

## Recommended Actions

1. **Add macro to coordinator** (coordinator_agent.py Line 30-35)
2. **Update coordinator defaults** to match weights.json
3. **Add ML prediction verification** (track actual vs predicted)
4. **Consider lowering max_rank** from 10 to 5 (more selective)
5. **Document the new weights** in coordinator_agent.py docstring
