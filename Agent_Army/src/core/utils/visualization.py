"""
Agent Army - Visualization Utils
可视化工具模块
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np


class CandlestickChart:
    """K线图绘制工具"""

    @staticmethod
    def create_candlestick(
        df: pd.DataFrame,
        title: str = "K线图",
        show_volume: bool = True,
        show_ma: bool = True,
        ma_periods: list = [5, 10, 20],
        height: int = 600
    ) -> go.Figure:
        """
        创建K线图

        Args:
            df: 包含OHLCV数据的DataFrame
            title: 图表标题
            show_volume: 是否显示成交量
            show_ma: 是否显示均线
            ma_periods: 均线周期列表
            height: 图表高度

        Returns:
            plotly Figure对象
        """
        if df is None or df.empty:
            # 创建空图表
            fig = go.Figure()
            fig.add_annotation(
                text="暂无数据",
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=20)
            )
            return fig

        # 确保数据格式正确
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")

        # 创建K线图
        fig = go.Figure()

        # 添加K线
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="K线"
        ))

        # 添加均线
        if show_ma and ma_periods:
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#96CEB4']
            for i, period in enumerate(ma_periods):
                if len(df) >= period:
                    ma = df['close'].rolling(window=period).mean()
                    fig.add_trace(go.Scatter(
                        x=df.index,
                        y=ma,
                        mode='lines',
                        name=f'MA{period}',
                        line=dict(color=colors[i % len(colors)], width=1)
                    ))

        # 添加成交量
        if show_volume and 'volume' in df.columns:
            fig.add_trace(go.Bar(
                x=df.index,
                y=df['volume'],
                name="成交量",
                marker_color='rgba(0,0,255,0.3)',
                yaxis='y2'
            ))

        # 布局设置
        layout_opts = dict(
            title=title,
            height=height,
            xaxis_rangeslider_visible=True,
            xaxis_rangeslider=dict(visible=True),
            hovermode='x unified',
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Microsoft YaHei, SimHei, Arial")
        )

        if show_volume and 'volume' in df.columns:
            layout_opts['yaxis2'] = dict(
                title='成交量',
                overlaying='y',
                side='right'
            )

        fig.update_layout(**layout_opts)

        return fig


class TechnicalIndicators:
    """技术指标计算工具"""

    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        计算MACD指标

        Args:
            df: 包含close列的DataFrame
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        Returns:
            添加了MACD指标的DataFrame
        """
        if 'close' not in df.columns:
            raise ValueError("DataFrame must contain 'close' column")

        df = df.copy()

        # 计算EMA
        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()

        # MACD线
        df['macd'] = exp1 - exp2

        # 信号线
        df['signal'] = df['macd'].ewm(span=signal, adjust=False).mean()

        # 柱状图
        df['histogram'] = df['macd'] - df['signal']

        return df

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算RSI指标

        Args:
            df: 包含close列的DataFrame
            period: RSI周期

        Returns:
            添加了RSI指标的DataFrame
        """
        if 'close' not in df.columns:
            raise ValueError("DataFrame must contain 'close' column")

        df = df.copy()

        # 计算价格变化
        delta = df['close'].diff()

        # 分离涨跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 计算平均涨跌幅
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # 计算RSI
        rs = avg_gain / avg_loss
        df['rsi'] = 100 - (100 / (1 + rs))

        return df

    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        """
        计算布林带

        Args:
            df: 包含close列的DataFrame
            period: 均线周期
            std_dev: 标准差倍数

        Returns:
            添加了布林带的DataFrame
        """
        if 'close' not in df.columns:
            raise ValueError("DataFrame must contain 'close' column")

        df = df.copy()

        # 计算中线（移动平均）
        df['middle_band'] = df['close'].rolling(window=period).mean()

        # 计算标准差
        std = df['close'].rolling(window=period).std()

        # 计算上下轨
        df['upper_band'] = df['middle_band'] + std_dev * std
        df['lower_band'] = df['middle_band'] - std_dev * std

        return df


class FinancialCharts:
    """财务图表绘制工具"""

    @staticmethod
    def create_radar_chart(scores: dict, title: str = "综合评分雷达图") -> go.Figure:
        """
        创建雷达图

        Args:
            scores: 评分字典，格式为 {维度名: 分数}
            title: 图表标题

        Returns:
            plotly Figure对象
        """
        categories = list(scores.keys())
        values = list(scores.values())

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],  # 闭合图形
            theta=categories + [categories[0]],
            fill='toself',
            name='评分',
            line_color='rgb(99, 110, 250)',
            fillcolor='rgba(99, 110, 250, 0.5)'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title=title,
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Microsoft YaHei, SimHei, Arial")
        )

        return fig

    @staticmethod
    def create_trend_chart(
        df: pd.DataFrame,
        date_col: str = 'date',
        value_col: str = 'score',
        title: str = "评分趋势图"
    ) -> go.Figure:
        """
        创建趋势图

        Args:
            df: 包含日期和数值的DataFrame
            date_col: 日期列名
            value_col: 数值列名
            title: 图表标题

        Returns:
            plotly Figure对象
        """
        if df is None or df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="暂无数据",
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=20)
            )
            return fig

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df[date_col],
            y=df[value_col],
            mode='lines+markers',
            name='趋势',
            line=dict(color='#1E88E5', width=2),
            marker=dict(size=6)
        ))

        fig.update_layout(
            title=title,
            xaxis_title='日期',
            yaxis_title='评分',
            height=400,
            hovermode='x unified',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Microsoft YaHei, SimHei, Arial")
        )

        return fig


def generate_sample_kline_data(days: int = 100) -> pd.DataFrame:
    """
    生成示例K线数据（用于测试）

    Args:
        days: 生成数据的天数

    Returns:
        包含OHLCV数据的DataFrame
    """
    # 生成日期范围
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    # 生成随机价格数据
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(days) * 0.5)

    # 生成OHLCV数据
    df = pd.DataFrame({
        'date': dates,
        'open': close_prices * (1 + np.random.rand(days) * 0.02 - 0.01),
        'high': close_prices * (1 + np.abs(np.random.rand(days) * 0.02)),
        'low': close_prices * (1 - np.abs(np.random.rand(days) * 0.02)),
        'close': close_prices,
        'volume': np.random.randint(1000000, 10000000, days)
    })

    # 确保价格合理（high >= open/low/close, low <= open/close）
    df['high'] = df[['open', 'close', 'low']].max(axis=1) * 1.01
    df['low'] = df[['open', 'close']].min(axis=1) * 0.99

    df.set_index('date', inplace=True)

    return df
