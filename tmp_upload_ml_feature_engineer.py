#!/usr/bin/env python3
"""
机器学习特征工程模块

从K线数据和技术指标生成特征矩阵，用于XGBoost预测模型。
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


class MLFeatureEngineer:
    """从K线数据计算机器学习特征"""

    # 特征列名（固定顺序，训练和预测必须一致）
    FEATURE_COLS = [
        'rsi', 'macd', 'macd_signal', 'macd_hist',
        'ma5', 'ma20', 'ma60',
        'ma5_ratio', 'ma20_ratio', 'ma60_ratio',
        'kdj_k', 'kdj_d', 'kdj_j',
        'boll_position', 'boll_width',
        'turnover_ratio', 'volume_ratio',
        'price_position_20d', 'price_position_60d',
        'return_1d', 'return_5d', 'return_10d', 'return_20d',
        'volatility_10d', 'volatility_20d',
        'high_low_ratio_5d', 'open_close_ratio',
        'market_sentiment', 'market_trend_score', 'sector_momentum', 'main_capital_flow',
        'pe', 'pb', 'market_cap_rank', 'pe_percentile', 'pb_percentile',
    ]

    def __init__(self, df: pd.DataFrame, base_date: str = None, stock_code: str = None):
        """
        Args:
            df: 日线DataFrame，需含 close 列，按日期升序排列
                可选: open, high, low, volume, turnover
            base_date: 截止日期(YYYY-MM-DD)，只使用该日期及之前的数据。
                       None表示使用全部数据(实时预测模式)。
            stock_code: 股票代码（如 '600887.SH'），用于查询基本面数据。
                       None时基本面特征填0。
        """
        # 标准化列名为大写首字母格式（兼容 Tushare 小写和 DB 大写）
        col_map = {}
        for col in df.columns:
            lower = col.lower()
            if lower == 'close':
                col_map[col] = 'Close'
            elif lower == 'open':
                col_map[col] = 'Open'
            elif lower == 'high':
                col_map[col] = 'High'
            elif lower == 'low':
                col_map[col] = 'Low'
            elif lower == 'volume':
                col_map[col] = 'Volume'
            elif lower == 'vol':
                col_map[col] = 'Volume'
            elif lower == 'turnover':
                col_map[col] = 'Turnover'
            elif lower in ('date', 'trade_date'):
                col_map[col] = 'Date'
        df = df.rename(columns=col_map)

        if base_date is not None:
            date_col = 'Date'
            df = df[df[date_col] <= pd.Timestamp(base_date)].copy()

        self.df = df.copy()
        self.close = df['Close'].values.astype(float)

        self.has_ohl = all(c in df.columns for c in ['Open', 'High', 'Low'])
        self.has_vol = 'Volume' in df.columns
        self.has_turnover = 'Turnover' in df.columns
        self.stock_code = stock_code
        self.base_date = base_date

    def compute_features(self) -> Dict[str, float]:
        """
        计算当前时刻的特征（用于实时预测）

        Returns:
            dict: 特征字典（全零值如果数据不足）
        """
        f = {}
        c = self.close
        n = len(c)

        if n < 5:
            return {col: 0.0 for col in self.FEATURE_COLS}

        # === RSI (14日) ===
        f['rsi'] = self._calc_rsi(c, 14) if n >= 15 else 50.0

        # === MACD (12,26,9) ===
        macd, signal, hist = self._calc_macd(c)
        f['macd'] = macd
        f['macd_signal'] = signal
        f['macd_hist'] = hist

        # === 均线 ===
        f['ma5'] = np.mean(c[-5:]) if n >= 5 else c[-1]
        f['ma20'] = np.mean(c[-20:]) if n >= 20 else c[-1]
        f['ma60'] = np.mean(c[-60:]) if n >= 60 else np.mean(c) if n > 0 else c[-1]

        f['ma5_ratio'] = c[-1] / f['ma5'] - 1 if f['ma5'] > 0 else 0
        f['ma20_ratio'] = c[-1] / f['ma20'] - 1 if f['ma20'] > 0 else 0
        f['ma60_ratio'] = c[-1] / f['ma60'] - 1 if f['ma60'] > 0 else 0

        # === KDJ ===
        k, d, j = self._calc_kdj(c, self.df, 9)
        f['kdj_k'] = k
        f['kdj_d'] = d
        f['kdj_j'] = j

        # === 布林带 ===
        if n >= 20:
            ma20 = np.mean(c[-20:])
            std20 = np.std(c[-20:])
            bb_upper = ma20 + 2 * std20
            bb_lower = ma20 - 2 * std20
            bb_width = bb_upper - bb_lower
            f['boll_position'] = (c[-1] - bb_lower) / bb_width if bb_width > 0 else 0.5
            f['boll_width'] = bb_width / c[-1] if c[-1] > 0 else 0
        else:
            f['boll_position'] = 0.5
            f['boll_width'] = 0.05

        # === 换手率因子 ===
        if self.has_turnover and n >= 20:
            turnover = self.df['Turnover'].values.astype(float)
            t_ma20 = np.nanmean(turnover[-20:])
            f['turnover_ratio'] = turnover[-1] / t_ma20 if t_ma20 > 0 else 1.0
        else:
            f['turnover_ratio'] = 1.0

        # === 量比 ===
        if self.has_vol and n >= 20:
            vol = self.df['Volume'].values.astype(float)
            v_ma20 = np.nanmean(vol[-20:])
            f['volume_ratio'] = vol[-1] / v_ma20 if v_ma20 > 0 else 1.0
        else:
            f['volume_ratio'] = 1.0

        # === 价格位置 ===
        if n >= 20:
            low20 = np.min(c[-20:])
            high20 = np.max(c[-20:])
            f['price_position_20d'] = (c[-1] - low20) / (high20 - low20) if high20 > low20 else 0.5
        else:
            f['price_position_20d'] = 0.5

        if n >= 60:
            low60 = np.min(c[-60:])
            high60 = np.max(c[-60:])
            f['price_position_60d'] = (c[-1] - low60) / (high60 - low60) if high60 > low60 else 0.5
        else:
            f['price_position_60d'] = 0.5

        # === 收益率（动量） ===
        f['return_1d'] = (c[-1] - c[-2]) / c[-2] if n >= 2 and c[-2] > 0 else 0
        f['return_5d'] = (c[-1] - c[-6]) / c[-6] if n >= 6 and c[-6] > 0 else 0
        f['return_10d'] = (c[-1] - c[-11]) / c[-11] if n >= 11 and c[-11] > 0 else 0
        f['return_20d'] = (c[-1] - c[-21]) / c[-21] if n >= 21 and c[-21] > 0 else 0

        # === 波动率 ===
        if n >= 11:
            rets = np.diff(c[-11:]) / c[-11:-1]
            f['volatility_10d'] = np.std(rets) if len(rets) > 0 else 0
        else:
            f['volatility_10d'] = 0.02

        if n >= 21:
            rets = np.diff(c[-21:]) / c[-21:-1]
            f['volatility_20d'] = np.std(rets) if len(rets) > 0 else 0
        else:
            f['volatility_20d'] = 0.02

        # === K线形态 ===
        if self.has_ohl and n >= 5:
            high5 = np.max(self.df['High'].values[-5:].astype(float))
            low5 = np.min(self.df['Low'].values[-5:].astype(float))
            f['high_low_ratio_5d'] = (high5 - low5) / c[-1] if c[-1] > 0 else 0
        else:
            f['high_low_ratio_5d'] = 0.05

        if self.has_ohl and n >= 2:
            o = self.df['Open'].values[-1]
            f['open_close_ratio'] = (c[-1] - o) / o if o > 0 else 0
        else:
            f['open_close_ratio'] = 0

        # === 市场情绪 (market_sentiment) ===
        rsi_val = f.get('rsi', 50.0)
        if self.has_vol and n >= 20:
            vol = self.df['Volume'].values.astype(float)
            vol_ratio = vol[-1] / np.nanmean(vol[-20:])
            ret_1d = (c[-1] - c[-2]) / c[-2] if n >= 2 and c[-2] > 0 else 0
            vp_signal = ret_1d * vol_ratio * 50
            f['market_sentiment'] = rsi_val + vp_signal
        else:
            f['market_sentiment'] = rsi_val

        # === 市场趋势评分 (market_trend_score) ===
        if n >= 20:
            ma5_val = np.mean(c[-5:])
            ma20_val = np.mean(c[-20:])
            if ma20_val > 0:
                f['market_trend_score'] = max(0, min(1, 0.5 + (ma5_val / ma20_val - 1) * 10))
            else:
                f['market_trend_score'] = 0.5
        else:
            f['market_trend_score'] = 0.5

        # === 板块动量 (sector_momentum) ===
        if n >= 11:
            ret_5d = (c[-1] - c[-6]) / c[-6] if c[-6] > 0 else 0
            ret_10d = (c[-1] - c[-11]) / c[-11] if c[-11] > 0 else 0
            f['sector_momentum'] = ret_5d - ret_10d
        else:
            f['sector_momentum'] = 0

        # === 主力资金流 (main_capital_flow) ===
        if self.has_vol and n >= 20:
            vol = self.df['Volume'].values.astype(float)
            ret_1d = (c[-1] - c[-2]) / c[-2] if n >= 2 and c[-2] > 0 else 0
            v_ma20 = np.nanmean(vol[-20:])
            if v_ma20 > 0:
                f['main_capital_flow'] = ret_1d * (vol[-1] / v_ma20)
            else:
                f['main_capital_flow'] = 0
        else:
            f['main_capital_flow'] = 0

        # === 基本面特征（从 finance 表获取，防止未来函数） ===
        fund_defaults = {'pe': 0, 'pb': 0, 'market_cap_rank': 0.5,
                         'pe_percentile': 0.5, 'pb_percentile': 0.5}
        if self.stock_code:
            try:
                import duckdb
                query_date = self.base_date
                if not query_date:
                    date_col = 'Date' if 'Date' in self.df.columns else 'date'
                    if date_col in self.df.columns and len(self.df) > 0:
                        query_date = str(self.df[date_col].iloc[-1])[:10]

                if query_date:
                    db_path = os.path.join(
                        os.path.dirname(os.path.dirname(
                            os.path.abspath(__file__))), 'data', 'market_data.db')
                    if not os.path.exists(db_path):
                        db_path = '/root/.openclaw/workspace/data/market_data.db'
                    conn = duckdb.connect(db_path, read_only=True)
                    row = conn.execute(f"""
                        SELECT pe, pb, market_cap FROM finance
                        WHERE stock_code = '{self.stock_code}'
                          AND date <= '{query_date}'
                        ORDER BY date DESC LIMIT 1
                    """).fetchone()
                    conn.close()

                    if row and row[0] is not None:
                        pe_val = float(row[0]) if row[0] else 0
                        pb_val = float(row[1]) if row[1] else 0
                        mc = float(row[2]) if row[2] else 0
                        f['pe'] = max(-100, min(200, pe_val)) if pe_val > 0 else 0
                        f['pb'] = max(0, min(50, pb_val))
                        f['market_cap_rank'] = min(1.0, mc / 1e11) if mc > 0 else 0.5
                        f['pe_percentile'] = max(0, min(1, (pe_val - 5) / 60)) if pe_val > 0 else 0.5
                        f['pb_percentile'] = max(0, min(1, pb_val / 10)) if pb_val > 0 else 0.5
                    else:
                        f.update(fund_defaults)
                else:
                    f.update(fund_defaults)
            except Exception:
                f.update(fund_defaults)
        else:
            f.update(fund_defaults)

        return f

    def compute_features_series(self, window: int = 60) -> pd.DataFrame:
        """
        滑动窗口生成多行特征（用于训练）

        Args:
            window: 最小历史窗口

        Returns:
            DataFrame: 每行一个样本
        """
        rows = []
        for i in range(window, len(self.close)):
            sub_df = self.df.iloc[:i]
            engineer = MLFeatureEngineer(sub_df)
            features = engineer.compute_features()
            rows.append(features)
        return pd.DataFrame(rows)

    # --- 技术指标计算 ---

    @staticmethod
    def _calc_rsi(closes, period=14):
        """计算RSI"""
        deltas = np.diff(closes[-(period+1):])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def _calc_macd(closes, fast=12, slow=26, signal_period=9):
        """计算MACD"""
        if len(closes) < slow:
            return 0.0, 0.0, 0.0

        ema_fast = closes[0]
        ema_slow = closes[0]
        alpha_fast = 2.0 / (fast + 1)
        alpha_slow = 2.0 / (slow + 1)

        macd_line = []
        for p in closes:
            ema_fast = alpha_fast * p + (1 - alpha_fast) * ema_fast
            ema_slow = alpha_slow * p + (1 - alpha_slow) * ema_slow
            macd_line.append(ema_fast - ema_slow)

        if len(macd_line) < signal_period:
            return macd_line[-1], macd_line[-1], 0.0

        signal_line = macd_line[0]
        alpha_sig = 2.0 / (signal_period + 1)
        for v in macd_line:
            signal_line = alpha_sig * v + (1 - alpha_sig) * signal_line

        hist = macd_line[-1] - signal_line
        return macd_line[-1], signal_line, hist

    @staticmethod
    def _calc_kdj(closes, df, n=9):
        """计算KDJ"""
        if len(closes) < n or 'High' not in df.columns or 'Low' not in df.columns:
            return 50.0, 50.0, 50.0

        high = df['High'].values[-n:].astype(float)
        low = df['Low'].values[-n:].astype(float)
        highest = np.max(high)
        lowest = np.min(low)

        if highest == lowest:
            rsv = 50.0
        else:
            rsv = (closes[-1] - lowest) / (highest - lowest) * 100

        k = 2.0/3 * 50 + 1.0/3 * rsv
        d = 2.0/3 * 50 + 1.0/3 * k
        j = 3 * k - 2 * d

        return k, d, j
