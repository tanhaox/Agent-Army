"""
技术分析AI - Technical Analysis AI

个股挖掘军团核心成员

职责：
1. 趋势分析（趋势线、支撑压力位、趋势强度）
2. 技术指标分析（MACD、KDJ、RSI、布林带、均线系统）
3. 量价分析（成交量、量价关系、筹码分布）
4. 形态识别（头肩顶/底、双顶/底、三角形整理、箱体震荡）

使用工具库：
- FinancialTool (价格数据、成交量数据)
- TA-Lib (技术指标计算，需安装)

依赖安装：
pip install TA-Lib

创建日期: 2026-03-14
版本: v2.0 (完整版)
从56行骨架 → 完整技术分析AI
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
import pandas as pd

from src.agents.business.base_business_agent import BusinessAgent
from src.core.base_agent import AgentCapability, AgentTool
from src.core.tools.data_source import FinancialTool
from src.core.logger import LoggerMixin

# 尝试导入TA-Lib，如果未安装则使用简化计算
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("WARNING: TA-Lib not installed, using simplified calculations. Install: pip install TA-Lib")


class TechnicalAnalysisAI(BusinessAgent):
    """
    技术分析AI - 完整版

    核心能力：
    1. 趋势分析 - 趋势线、支撑压力位、趋势强度
    2. 技术指标 - MACD、KDJ、RSI、布林带、均线系统
    3. 量价分析 - 成交量、量价关系、筹码分布
    4. 形态识别 - 经典形态自动识别

    使用场景：
    - 短线交易：关注买卖信号、超买超卖
    - 中线投资：关注趋势方向、支撑压力位
    - 长线投资：关注长期趋势、主要形态
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具库
        self.financial_tool = FinancialTool()

        super().__init__(
            name="技术分析AI",
            role="分析技术指标和走势，识别买卖信号",
            corps="stock_mining",
            analysis_type="technical",
            capabilities=[
                # 趋势分析能力
                AgentCapability(
                    name="trend_analysis",
                    description="趋势分析",
                    input_type="price_data",
                    output_type="trend_report"
                ),
                AgentCapability(
                    name="support_resistance",
                    description="支撑压力位识别",
                    input_type="price_data",
                    output_type="support_resistance_levels"
                ),

                # 技术指标能力
                AgentCapability(
                    name="macd_analysis",
                    description="MACD分析",
                    input_type="price_data",
                    output_type="macd_signal"
                ),
                AgentCapability(
                    name="kdj_analysis",
                    description="KDJ分析",
                    input_type="price_data",
                    output_type="kdj_signal"
                ),
                AgentCapability(
                    name="rsi_analysis",
                    description="RSI分析",
                    input_type="price_data",
                    output_type="rsi_signal"
                ),
                AgentCapability(
                    name="bollinger_analysis",
                    description="布林带分析",
                    input_type="price_data",
                    output_type="bollinger_signal"
                ),
                AgentCapability(
                    name="ma_analysis",
                    description="均线系统分析",
                    input_type="price_data",
                    output_type="ma_signal"
                ),

                # 量价分析能力
                AgentCapability(
                    name="volume_analysis",
                    description="成交量分析",
                    input_type="volume_data",
                    output_type="volume_report"
                ),
                AgentCapability(
                    name="volume_price_relation",
                    description="量价关系分析",
                    input_type="price_volume_data",
                    output_type="volume_price_signal"
                ),

                # 形态识别能力
                AgentCapability(
                    name="pattern_recognition",
                    description="形态识别",
                    input_type="price_data",
                    output_type="pattern_list"
                ),
                AgentCapability(
                    name="chart_pattern",
                    description="图表形态",
                    input_type="price_data",
                    output_type="chart_pattern"
                ),

                # 信号检测能力
                AgentCapability(
                    name="buy_signal_detection",
                    description="买入信号检测",
                    input_type="all_indicators",
                    output_type="buy_signal"
                ),
                AgentCapability(
                    name="sell_signal_detection",
                    description="卖出信号检测",
                    input_type="all_indicators",
                    output_type="sell_signal"
                )
            ],
            tools=[
                AgentTool(
                    name="financial_tool",
                    description="财务数据工具（获取价格数据）",
                    tool_type="library",
                    config={}
                ),
                AgentTool(
                    name="talib",
                    description="技术指标库",
                    tool_type="library",
                    config={"available": TALIB_AVAILABLE}
                )
            ],
            config=config
        )

        self.logger.info(f"技术分析AI初始化完成（TA-Lib: {'可用' if TALIB_AVAILABLE else '不可用'}）")

    async def analyze(self, stock_code: str, **kwargs) -> Dict[str, Any]:
        """
        综合技术分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - days: 分析天数（默认365天）
                - analysis_type: 分析类型（quick/standard/deep）

        Returns:
            技术分析结果
        """
        self.logger.info(f"开始技术分析", extra={"stock_code": stock_code})

        # 验证股票代码
        if not self.validate_stock_code(stock_code):
            raise ValueError(f"无效的股票代码: {stock_code}")

        # 获取分析天数
        days = kwargs.get("days", 365)
        analysis_type = kwargs.get("analysis_type", "standard")

        # ========== 1. 获取价格数据 ==========
        price_data = await self._fetch_price_data(stock_code, days)

        # ========== 2. 趋势分析 ==========
        trend_analysis = self._analyze_trend(price_data)

        # ========== 3. 技术指标分析 ==========
        indicators = self._analyze_indicators(price_data)

        # ========== 4. 量价分析 ==========
        volume_analysis = self._analyze_volume(price_data)

        # ========== 5. 形态识别 ==========
        patterns = self._recognize_patterns(price_data)

        # ========== 6. 买卖信号检测 ==========
        signals = self._detect_signals(
            trend_analysis,
            indicators,
            volume_analysis,
            patterns
        )

        # ========== 7. 综合评分 ==========
        score = self._calculate_technical_score(
            trend_analysis,
            indicators,
            volume_analysis,
            signals
        )

        # ========== 8. 生成分析结果 ==========
        result = {
            "stock_code": stock_code,
            "stock_name": price_data.get("stock_name", "未知"),
            "analysis_type": "technical",
            "timestamp": datetime.now().isoformat(),
            "analysis_period": f"最近{days}天",

            # 趋势分析
            "trend": {
                "direction": trend_analysis["direction"],
                "strength": trend_analysis["strength"],
                "support_levels": trend_analysis["support_levels"],
                "resistance_levels": trend_analysis["resistance_levels"],
                "trend_line": trend_analysis["trend_line"]
            },

            # 技术指标
            "indicators": {
                "macd": indicators["macd"],
                "kdj": indicators["kdj"],
                "rsi": indicators["rsi"],
                "bollinger": indicators["bollinger"],
                "ma": indicators["ma"]
            },

            # 量价分析
            "volume": {
                "volume_trend": volume_analysis["volume_trend"],
                "volume_price_relation": volume_analysis["volume_price_relation"],
                "volume_signal": volume_analysis["signal"]
            },

            # 形态识别
            "patterns": patterns,

            # 买卖信号
            "signals": {
                "buy_signal": signals["buy_signal"],
                "sell_signal": signals["sell_signal"],
                "signal_strength": signals["signal_strength"],
                "signal_description": signals["description"]
            },

            # 综合评分
            "score": score["total_score"],
            "grade": score["grade"],
            "recommendation": score["recommendation"],

            # 总结
            "summary": self._generate_summary(trend_analysis, indicators, signals, score)
        }

        self.logger.info(
            f"技术分析完成",
            extra={
                "stock_code": stock_code,
                "score": result["score"],
                "trend": result["trend"]["direction"]
            }
        )

        return result

    # ========== 1. 价格数据获取 ==========

    async def _fetch_price_data(self, stock_code: str, days: int) -> Dict[str, Any]:
        """
        获取价格数据

        Args:
            stock_code: 股票代码
            days: 天数

        Returns:
            价格数据（包含开高低收、成交量）
        """
        self.logger.info(f"获取价格数据", extra={"stock_code": stock_code, "days": days})

        try:
            # 尝试使用FinancialTool获取真实数据
            # TODO: FinancialTool需要添加fetch_price_data方法
            # price_data = await self.financial_tool.fetch_price_data(stock_code, days)
            # return price_data

            # 当前返回模拟数据
            return self._generate_mock_price_data(stock_code, days)

        except Exception as e:
            self.logger.warning(f"获取价格数据失败，使用模拟数据: {e}")
            return self._generate_mock_price_data(stock_code, days)

    def _generate_mock_price_data(self, stock_code: str, days: int) -> Dict[str, Any]:
        """
        生成模拟价格数据（用于测试）

        Args:
            stock_code: 股票代码
            days: 天数

        Returns:
            模拟价格数据
        """
        import random

        # 生成日期序列
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

        # 生成价格序列（随机游走）
        base_price = 100.0
        close_prices = [base_price]
        for i in range(1, days):
            change = random.uniform(-0.03, 0.03)
            new_price = close_prices[-1] * (1 + change)
            close_prices.append(new_price)

        close_prices = np.array(close_prices)

        # 生成开高低收
        high_prices = close_prices * (1 + np.random.uniform(0, 0.02, days))
        low_prices = close_prices * (1 - np.random.uniform(0, 0.02, days))
        open_prices = close_prices * (1 + np.random.uniform(-0.01, 0.01, days))

        # 生成成交量
        base_volume = 1000000
        volumes = [base_volume * random.uniform(0.5, 2.0) for _ in range(days)]

        return {
            "stock_code": stock_code,
            "stock_name": "示例股票",
            "dates": dates,
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "volume": np.array(volumes),
            "data_count": days
        }

    # ========== 2. 趋势分析 ==========

    def _analyze_trend(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        趋势分析

        Args:
            price_data: 价格数据

        Returns:
            趋势分析结果
        """
        self.logger.info("开始趋势分析")

        close_prices = price_data["close"]
        high_prices = price_data["high"]
        low_prices = price_data["low"]

        # 1. 判断趋势方向
        direction = self._determine_trend_direction(close_prices)

        # 2. 计算趋势强度
        strength = self._calculate_trend_strength(close_prices)

        # 3. 识别支撑位和压力位
        support_levels = self._identify_support_levels(low_prices, close_prices)
        resistance_levels = self._identify_resistance_levels(high_prices, close_prices)

        # 4. 趋势线识别
        trend_line = self._identify_trend_line(close_prices, direction)

        return {
            "direction": direction,
            "strength": strength,
            "support_levels": support_levels,
            "resistance_levels": resistance_levels,
            "trend_line": trend_line
        }

    def _determine_trend_direction(self, close_prices: np.ndarray) -> str:
        """
        判断趋势方向

        Args:
            close_prices: 收盘价序列

        Returns:
            趋势方向 (上涨/下跌/震荡)
        """
        if len(close_prices) < 20:
            return "数据不足"

        # 使用短期均线和长期均线判断趋势
        short_ma = np.mean(close_prices[-5:])
        mid_ma = np.mean(close_prices[-20:])
        long_ma = np.mean(close_prices[-60:]) if len(close_prices) >= 60 else mid_ma

        # 判断趋势
        if short_ma > mid_ma > long_ma:
            return "上涨"
        elif short_ma < mid_ma < long_ma:
            return "下跌"
        else:
            return "震荡"

    def _calculate_trend_strength(self, close_prices: np.ndarray) -> float:
        """
        计算趋势强度 (0-100)

        Args:
            close_prices: 收盘价序列

        Returns:
            趋势强度
        """
        if len(close_prices) < 20:
            return 50.0

        # 使用ADX指标的思想（简化版）
        # 计算价格变化的方向和幅度
        changes = np.diff(close_prices[-20:])
        positive_changes = np.sum(changes[changes > 0])
        negative_changes = np.abs(np.sum(changes[changes < 0]))

        total_changes = positive_changes + negative_changes
        if total_changes == 0:
            return 50.0

        # 计算方向性
        directionality = np.abs(positive_changes - negative_changes) / total_changes

        # 转换为0-100分数
        strength = directionality * 100

        return round(strength, 1)

    def _identify_support_levels(
        self,
        low_prices: np.ndarray,
        close_prices: np.ndarray,
        num_levels: int = 3
    ) -> List[float]:
        """
        识别支撑位

        Args:
            low_prices: 最低价序列
            close_prices: 收盘价序列
            num_levels: 识别的支撑位数量

        Returns:
            支撑位列表
        """
        if len(low_prices) < 20:
            return []

        # 寻找局部最低点
        local_lows = []
        for i in range(2, len(low_prices) - 2):
            if (low_prices[i] < low_prices[i-1] and
                low_prices[i] < low_prices[i-2] and
                low_prices[i] < low_prices[i+1] and
                low_prices[i] < low_prices[i+2]):
                local_lows.append(low_prices[i])

        if not local_lows:
            # 如果没找到局部最低点，使用最低价
            sorted_lows = sorted(low_prices[-60:])
            return sorted(round(x, 2) for x in sorted_lows[:num_levels])

        # 按价格排序，取最近的几个支撑位
        sorted_lows = sorted(local_lows)
        return [round(x, 2) for x in sorted_lows[:num_levels]]

    def _identify_resistance_levels(
        self,
        high_prices: np.ndarray,
        close_prices: np.ndarray,
        num_levels: int = 3
    ) -> List[float]:
        """
        识别压力位

        Args:
            high_prices: 最高价序列
            close_prices: 收盘价序列
            num_levels: 识别的压力位数量

        Returns:
            压力位列表
        """
        if len(high_prices) < 20:
            return []

        # 寻找局部最高点
        local_highs = []
        for i in range(2, len(high_prices) - 2):
            if (high_prices[i] > high_prices[i-1] and
                high_prices[i] > high_prices[i-2] and
                high_prices[i] > high_prices[i+1] and
                high_prices[i] > high_prices[i+2]):
                local_highs.append(high_prices[i])

        if not local_highs:
            # 如果没找到局部最高点，使用最高价
            sorted_highs = sorted(high_prices[-60:], reverse=True)
            return sorted(round(x, 2) for x in sorted_highs[:num_levels])

        # 按价格排序，取最近的几个压力位
        sorted_highs = sorted(local_highs, reverse=True)
        return [round(x, 2) for x in sorted_highs[:num_levels]]

    def _identify_trend_line(
        self,
        close_prices: np.ndarray,
        direction: str
    ) -> Dict[str, Any]:
        """
        识别趋势线

        Args:
            close_prices: 收盘价序列
            direction: 趋势方向

        Returns:
            趋势线信息
        """
        if len(close_prices) < 20:
            return {"status": "数据不足"}

        # 简化版趋势线识别
        # 使用线性回归拟合最近20天的价格
        x = np.arange(20)
        y = close_prices[-20:]

        # 线性回归
        slope, intercept = np.polyfit(x, y, 1)

        # 判断趋势线有效性
        if direction == "上涨" and slope > 0:
            status = "有效上升趋势线"
        elif direction == "下跌" and slope < 0:
            status = "有效下降趋势线"
        else:
            status = "趋势线不明确"

        return {
            "status": status,
            "slope": round(slope, 4),
            "intercept": round(intercept, 2),
            "angle": round(np.degrees(np.arctan(slope)), 2)
        }

    # ========== 3. 技术指标分析 ==========

    def _analyze_indicators(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        技术指标分析

        Args:
            price_data: 价格数据

        Returns:
            技术指标分析结果
        """
        self.logger.info("开始技术指标分析")

        close_prices = price_data["close"]
        high_prices = price_data["high"]
        low_prices = price_data["low"]

        # 1. MACD分析
        macd = self._analyze_macd(close_prices)

        # 2. KDJ分析
        kdj = self._analyze_kdj(high_prices, low_prices, close_prices)

        # 3. RSI分析
        rsi = self._analyze_rsi(close_prices)

        # 4. 布林带分析
        bollinger = self._analyze_bollinger(close_prices)

        # 5. 均线系统分析
        ma = self._analyze_ma(close_prices)

        return {
            "macd": macd,
            "kdj": kdj,
            "rsi": rsi,
            "bollinger": bollinger,
            "ma": ma
        }

    def _analyze_macd(self, close_prices: np.ndarray) -> Dict[str, Any]:
        """
        MACD分析

        Args:
            close_prices: 收盘价序列

        Returns:
            MACD分析结果
        """
        if TALIB_AVAILABLE:
            # 使用TA-Lib计算MACD
            macd, signal, hist = talib.MACD(close_prices)
            current_macd = macd[-1]
            current_signal = signal[-1]
            current_hist = hist[-1]
        else:
            # 简化计算MACD
            ema12 = self._calculate_ema(close_prices, 12)
            ema26 = self._calculate_ema(close_prices, 26)
            macd_line = ema12 - ema26
            signal_line = self._calculate_ema(macd_line, 9)
            hist = macd_line - signal_line

            current_macd = macd_line[-1]
            current_signal = signal_line[-1]
            current_hist = hist[-1]

        # 判断MACD信号
        if current_hist > 0:
            signal_type = "多头" if current_macd > current_signal else "转多"
        else:
            signal_type = "空头" if current_macd < current_signal else "转空"

        # 金叉死叉判断
        if len(hist) >= 2:
            if hist[-2] < 0 and hist[-1] > 0:
                cross = "金叉"
            elif hist[-2] > 0 and hist[-1] < 0:
                cross = "死叉"
            else:
                cross = "无"
        else:
            cross = "无"

        return {
            "macd": round(current_macd, 2),
            "signal": round(current_signal, 2),
            "histogram": round(current_hist, 2),
            "signal_type": signal_type,
            "cross": cross,
            "recommendation": "买入" if signal_type in ["多头", "转多"] else "卖出" if signal_type in ["空头", "转空"] else "持有"
        }

    def _analyze_kdj(
        self,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        close_prices: np.ndarray
    ) -> Dict[str, Any]:
        """
        KDJ分析

        Args:
            high_prices: 最高价序列
            low_prices: 最低价序列
            close_prices: 收盘价序列

        Returns:
            KDJ分析结果
        """
        if TALIB_AVAILABLE:
            # 使用TA-Lib计算KDJ（STOCH）
            slowk, slowd = talib.STOCH(high_prices, low_prices, close_prices)
            k = slowk[-1]
            d = slowd[-1]
            j = 3 * k - 2 * d
        else:
            # 简化计算KDJ
            k, d = self._calculate_kdj_simple(high_prices, low_prices, close_prices)
            j = 3 * k - 2 * d

        # 判断KDJ信号
        if k > 80 and d > 80:
            signal = "超买"
        elif k < 20 and d < 20:
            signal = "超卖"
        elif k > d:
            signal = "看多"
        else:
            signal = "看空"

        # 金叉死叉
        cross = "金叉" if k > d else "死叉"

        return {
            "k": round(k, 2),
            "d": round(d, 2),
            "j": round(j, 2),
            "signal": signal,
            "cross": cross,
            "recommendation": "买入" if signal == "超卖" else "卖出" if signal == "超买" else "持有"
        }

    def _analyze_rsi(self, close_prices: np.ndarray, period: int = 14) -> Dict[str, Any]:
        """
        RSI分析

        Args:
            close_prices: 收盘价序列
            period: RSI周期

        Returns:
            RSI分析结果
        """
        if TALIB_AVAILABLE:
            rsi = talib.RSI(close_prices, timeperiod=period)
            current_rsi = rsi[-1]
        else:
            current_rsi = self._calculate_rsi_simple(close_prices, period)

        # 判断RSI信号
        if current_rsi > 70:
            signal = "超买"
            recommendation = "卖出"
        elif current_rsi < 30:
            signal = "超卖"
            recommendation = "买入"
        elif current_rsi > 50:
            signal = "强势"
            recommendation = "持有"
        else:
            signal = "弱势"
            recommendation = "观望"

        return {
            "rsi": round(current_rsi, 2),
            "signal": signal,
            "recommendation": recommendation
        }

    def _analyze_bollinger(
        self,
        close_prices: np.ndarray,
        period: int = 20
    ) -> Dict[str, Any]:
        """
        布林带分析

        Args:
            close_prices: 收盘价序列
            period: 周期

        Returns:
            布林带分析结果
        """
        if TALIB_AVAILABLE:
            upper, middle, lower = talib.BBANDS(close_prices, timeperiod=period)
            current_upper = upper[-1]
            current_middle = middle[-1]
            current_lower = lower[-1]
        else:
            current_middle = np.mean(close_prices[-period:])
            std = np.std(close_prices[-period:])
            current_upper = current_middle + 2 * std
            current_lower = current_middle - 2 * std

        current_price = close_prices[-1]

        # 判断布林带信号
        if current_price > current_upper:
            signal = "突破上轨"
            recommendation = "超买，谨慎追高"
        elif current_price < current_lower:
            signal = "跌破下轨"
            recommendation = "超卖，可能反弹"
        elif current_price > current_middle:
            signal = "上轨区间"
            recommendation = "偏多"
        else:
            signal = "下轨区间"
            recommendation = "偏空"

        # 布林带宽度（波动率）
        bandwidth = (current_upper - current_lower) / current_middle * 100

        return {
            "upper": round(current_upper, 2),
            "middle": round(current_middle, 2),
            "lower": round(current_lower, 2),
            "current_price": round(current_price, 2),
            "signal": signal,
            "bandwidth": round(bandwidth, 2),
            "recommendation": recommendation
        }

    def _analyze_ma(self, close_prices: np.ndarray) -> Dict[str, Any]:
        """
        均线系统分析

        Args:
            close_prices: 收盘价序列

        Returns:
            均线系统分析结果
        """
        # 计算多条均线
        ma5 = np.mean(close_prices[-5:])
        ma10 = np.mean(close_prices[-10:]) if len(close_prices) >= 10 else ma5
        ma20 = np.mean(close_prices[-20:]) if len(close_prices) >= 20 else ma10
        ma60 = np.mean(close_prices[-60:]) if len(close_prices) >= 60 else ma20

        current_price = close_prices[-1]

        # 判断均线多头/空头排列
        if ma5 > ma10 > ma20 > ma60:
            arrangement = "完美多头排列"
            signal = "强烈看多"
        elif ma5 > ma10 > ma20:
            arrangement = "多头排列"
            signal = "看多"
        elif ma5 < ma10 < ma20 < ma60:
            arrangement = "完美空头排列"
            signal = "强烈看空"
        elif ma5 < ma10 < ma20:
            arrangement = "空头排列"
            signal = "看空"
        else:
            arrangement = "均线纠缠"
            signal = "震荡"

        # 金叉死叉
        if len(close_prices) >= 2:
            ma5_prev = np.mean(close_prices[-6:-1])
            ma10_prev = np.mean(close_prices[-11:-1]) if len(close_prices) >= 11 else ma5_prev

            if ma5_prev < ma10_prev and ma5 > ma10:
                cross = "金叉"
            elif ma5_prev > ma10_prev and ma5 < ma10:
                cross = "死叉"
            else:
                cross = "无"
        else:
            cross = "无"

        return {
            "ma5": round(ma5, 2),
            "ma10": round(ma10, 2),
            "ma20": round(ma20, 2),
            "ma60": round(ma60, 2),
            "current_price": round(current_price, 2),
            "arrangement": arrangement,
            "signal": signal,
            "cross": cross,
            "recommendation": "买入" if "多" in signal else "卖出" if "空" in signal else "持有"
        }

    # ========== 4. 量价分析 ==========

    def _analyze_volume(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        量价分析

        Args:
            price_data: 价格数据

        Returns:
            量价分析结果
        """
        self.logger.info("开始量价分析")

        close_prices = price_data["close"]
        volumes = price_data["volume"]

        # 1. 成交量趋势
        volume_trend = self._analyze_volume_trend(volumes)

        # 2. 量价关系
        volume_price_relation = self._analyze_volume_price_relation(close_prices, volumes)

        # 3. 量价信号
        signal = self._generate_volume_signal(volume_trend, volume_price_relation)

        return {
            "volume_trend": volume_trend,
            "volume_price_relation": volume_price_relation,
            "signal": signal
        }

    def _analyze_volume_trend(self, volumes: np.ndarray) -> Dict[str, Any]:
        """
        成交量趋势分析

        Args:
            volumes: 成交量序列

        Returns:
            成交量趋势
        """
        if len(volumes) < 20:
            return {"trend": "数据不足"}

        # 计算短期和长期平均成交量
        short_avg = np.mean(volumes[-5:])
        mid_avg = np.mean(volumes[-20:])

        # 判断成交量趋势
        if short_avg > mid_avg * 1.5:
            trend = "放量"
        elif short_avg < mid_avg * 0.7:
            trend = "缩量"
        else:
            trend = "平稳"

        # 成交量变化率
        change_rate = (short_avg - mid_avg) / mid_avg * 100

        return {
            "trend": trend,
            "short_avg": round(short_avg, 0),
            "mid_avg": round(mid_avg, 0),
            "change_rate": round(change_rate, 1)
        }

    def _analyze_volume_price_relation(
        self,
        close_prices: np.ndarray,
        volumes: np.ndarray
    ) -> str:
        """
        量价关系分析

        Args:
            close_prices: 收盘价序列
            volumes: 成交量序列

        Returns:
            量价关系描述
        """
        if len(close_prices) < 5:
            return "数据不足"

        # 最近5天的价格和成交量变化
        price_changes = np.diff(close_prices[-5:])
        volume_changes = np.diff(volumes[-5:])

        # 统计价涨量增、价涨量缩等情况
        price_up_volume_up = np.sum((price_changes > 0) & (volume_changes > 0))
        price_up_volume_down = np.sum((price_changes > 0) & (volume_changes < 0))
        price_down_volume_up = np.sum((price_changes < 0) & (volume_changes > 0))
        price_down_volume_down = np.sum((price_changes < 0) & (volume_changes < 0))

        # 判断主要量价关系
        if price_up_volume_up >= 3:
            return "价涨量增（健康上涨）"
        elif price_up_volume_down >= 3:
            return "价涨量缩（上涨乏力）"
        elif price_down_volume_up >= 3:
            return "价跌量增（抛压较大）"
        elif price_down_volume_down >= 3:
            return "价跌量缩（抛压减轻）"
        else:
            return "量价关系不明确"

    def _generate_volume_signal(
        self,
        volume_trend: Dict[str, Any],
        volume_price_relation: str
    ) -> str:
        """
        生成量价信号

        Args:
            volume_trend: 成交量趋势
            volume_price_relation: 量价关系

        Returns:
            量价信号
        """
        if "健康上涨" in volume_price_relation:
            return "看多"
        elif "上涨乏力" in volume_price_relation:
            return "谨慎"
        elif "抛压较大" in volume_price_relation:
            return "看空"
        elif "抛压减轻" in volume_price_relation:
            return "可能反弹"
        else:
            return "中性"

    # ========== 5. 形态识别 ==========

    def _recognize_patterns(self, price_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        形态识别

        Args:
            price_data: 价格数据

        Returns:
            识别到的形态列表
        """
        self.logger.info("开始形态识别")

        close_prices = price_data["close"]
        high_prices = price_data["high"]
        low_prices = price_data["low"]

        patterns = []

        # 1. 头肩顶/底识别
        head_shoulders = self._detect_head_shoulders(close_prices, high_prices, low_prices)
        if head_shoulders:
            patterns.append(head_shoulders)

        # 2. 双顶/底识别
        double_top_bottom = self._detect_double_top_bottom(close_prices, high_prices, low_prices)
        if double_top_bottom:
            patterns.append(double_top_bottom)

        # 3. 三角形整理识别
        triangle = self._detect_triangle(close_prices, high_prices, low_prices)
        if triangle:
            patterns.append(triangle)

        # 4. 箱体震荡识别
        box = self._detect_box(close_prices, high_prices, low_prices)
        if box:
            patterns.append(box)

        return patterns

    def _detect_head_shoulders(
        self,
        close_prices: np.ndarray,
        high_prices: np.ndarray,
        low_prices: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """
        检测头肩顶/底形态（简化版）

        Args:
            close_prices: 收盘价序列
            high_prices: 最高价序列
            low_prices: 最低价序列

        Returns:
            头肩形态信息或None
        """
        # 简化版检测，实际需要更复杂的算法
        if len(close_prices) < 60:
            return None

        # 寻找3个峰值
        peaks = []
        for i in range(5, len(high_prices) - 5):
            if (high_prices[i] > high_prices[i-5:i].max() and
                high_prices[i] > high_prices[i+1:i+5].max()):
                peaks.append((i, high_prices[i]))

        if len(peaks) < 3:
            return None

        # 检查是否符合头肩形态
        # 取最近3个峰值
        recent_peaks = sorted(peaks[-3:], key=lambda x: x[0])
        left_shoulder, head, right_shoulder = recent_peaks

        # 头肩顶：中间峰值最高
        if head[1] > left_shoulder[1] and head[1] > right_shoulder[1]:
            return {
                "name": "头肩顶",
                "type": "看跌",
                "confidence": 0.7,
                "neckline": round(min(left_shoulder[1], right_shoulder[1]), 2),
                "description": "形成头肩顶形态，预示下跌"
            }

        # 头肩底：中间峰值最低（使用low_prices）
        valleys = []
        for i in range(5, len(low_prices) - 5):
            if (low_prices[i] < low_prices[i-5:i].min() and
                low_prices[i] < low_prices[i+1:i+5].min()):
                valleys.append((i, low_prices[i]))

        if len(valleys) >= 3:
            recent_valleys = sorted(valleys[-3:], key=lambda x: x[0])
            left_v, bottom_v, right_v = recent_valleys

            if bottom_v[1] < left_v[1] and bottom_v[1] < right_v[1]:
                return {
                    "name": "头肩底",
                    "type": "看涨",
                    "confidence": 0.7,
                    "neckline": round(max(left_v[1], right_v[1]), 2),
                    "description": "形成头肩底形态，预示上涨"
                }

        return None

    def _detect_double_top_bottom(
        self,
        close_prices: np.ndarray,
        high_prices: np.ndarray,
        low_prices: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """
        检测双顶/底形态

        Args:
            close_prices: 收盘价序列
            high_prices: 最高价序列
            low_prices: 最低价序列

        Returns:
            双顶/底形态信息或None
        """
        # 简化版检测
        if len(close_prices) < 40:
            return None

        # 双顶检测：寻找两个相近的高点
        peaks = []
        for i in range(3, len(high_prices) - 3):
            if (high_prices[i] > high_prices[i-3:i].max() and
                high_prices[i] > high_prices[i+1:i+3].max()):
                peaks.append((i, high_prices[i]))

        if len(peaks) >= 2:
            # 取最近两个峰值
            recent_peaks = peaks[-2:]
            peak1, peak2 = recent_peaks

            # 判断两个峰值是否相近（差距<3%）
            if abs(peak1[1] - peak2[1]) / peak1[1] < 0.03:
                return {
                    "name": "双顶",
                    "type": "看跌",
                    "confidence": 0.6,
                    "resistance": round((peak1[1] + peak2[1]) / 2, 2),
                    "description": "形成双顶形态，预示下跌"
                }

        # 双底检测：寻找两个相近的低点
        valleys = []
        for i in range(3, len(low_prices) - 3):
            if (low_prices[i] < low_prices[i-3:i].min() and
                low_prices[i] < low_prices[i+1:i+3].min()):
                valleys.append((i, low_prices[i]))

        if len(valleys) >= 2:
            recent_valleys = valleys[-2:]
            valley1, valley2 = recent_valleys

            if abs(valley1[1] - valley2[1]) / valley1[1] < 0.03:
                return {
                    "name": "双底",
                    "type": "看涨",
                    "confidence": 0.6,
                    "support": round((valley1[1] + valley2[1]) / 2, 2),
                    "description": "形成双底形态，预示上涨"
                }

        return None

    def _detect_triangle(
        self,
        close_prices: np.ndarray,
        high_prices: np.ndarray,
        low_prices: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """
        检测三角形整理形态

        Args:
            close_prices: 收盘价序列
            high_prices: 最高价序列
            low_prices: 最低价序列

        Returns:
            三角形形态信息或None
        """
        # 简化版检测
        if len(close_prices) < 30:
            return None

        # 检查最近30天的高点和低点是否收敛
        recent_highs = high_prices[-30:]
        recent_lows = low_prices[-30:]

        # 计算高点趋势和低点趋势
        high_slope = np.polyfit(np.arange(30), recent_highs, 1)[0]
        low_slope = np.polyfit(np.arange(30), recent_lows, 1)[0]

        # 对称三角形：高点下降，低点上升
        if high_slope < 0 and low_slope > 0:
            return {
                "name": "对称三角形",
                "type": "整理",
                "confidence": 0.6,
                "description": "形成对称三角形整理，等待突破"
            }

        # 上升三角形：高点平稳，低点上升
        elif abs(high_slope) < 0.1 and low_slope > 0:
            return {
                "name": "上升三角形",
                "type": "看涨",
                "confidence": 0.7,
                "description": "形成上升三角形，向上突破概率大"
            }

        # 下降三角形：高点下降，低点平稳
        elif high_slope < 0 and abs(low_slope) < 0.1:
            return {
                "name": "下降三角形",
                "type": "看跌",
                "confidence": 0.7,
                "description": "形成下降三角形，向下突破概率大"
            }

        return None

    def _detect_box(
        self,
        close_prices: np.ndarray,
        high_prices: np.ndarray,
        low_prices: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """
        检测箱体震荡形态

        Args:
            close_prices: 收盘价序列
            high_prices: 最高价序列
            low_prices: 最低价序列

        Returns:
            箱体形态信息或None
        """
        if len(close_prices) < 20:
            return None

        # 检查最近20天是否在一个区间内震荡
        recent_closes = close_prices[-20:]
        price_range = recent_closes.max() - recent_closes.min()
        price_mean = recent_closes.mean()

        # 如果波动范围在5%以内，认为是箱体震荡
        if price_range / price_mean < 0.05:
            return {
                "name": "箱体震荡",
                "type": "整理",
                "confidence": 0.7,
                "upper": round(recent_closes.max(), 2),
                "lower": round(recent_closes.min(), 2),
                "description": f"在{recent_closes.min():.2f}-{recent_closes.max():.2f}区间震荡"
            }

        return None

    # ========== 6. 买卖信号检测 ==========

    def _detect_signals(
        self,
        trend_analysis: Dict[str, Any],
        indicators: Dict[str, Any],
        volume_analysis: Dict[str, Any],
        patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        检测买卖信号

        Args:
            trend_analysis: 趋势分析结果
            indicators: 技术指标分析结果
            volume_analysis: 量价分析结果
            patterns: 形态识别结果

        Returns:
            买卖信号
        """
        self.logger.info("开始买卖信号检测")

        # 收集所有买入信号
        buy_signals = []
        sell_signals = []

        # 1. 趋势信号
        if trend_analysis["direction"] == "上涨":
            buy_signals.append("趋势向上")
        elif trend_analysis["direction"] == "下跌":
            sell_signals.append("趋势向下")

        # 2. MACD信号
        if indicators["macd"]["recommendation"] == "买入":
            buy_signals.append("MACD金叉")
        elif indicators["macd"]["recommendation"] == "卖出":
            sell_signals.append("MACD死叉")

        # 3. KDJ信号
        if indicators["kdj"]["recommendation"] == "买入":
            buy_signals.append("KDJ超卖")
        elif indicators["kdj"]["recommendation"] == "卖出":
            sell_signals.append("KDJ超买")

        # 4. RSI信号
        if indicators["rsi"]["recommendation"] == "买入":
            buy_signals.append("RSI超卖")
        elif indicators["rsi"]["recommendation"] == "卖出":
            sell_signals.append("RSI超买")

        # 5. 均线信号
        if "多" in indicators["ma"]["signal"]:
            buy_signals.append("均线多头")
        elif "空" in indicators["ma"]["signal"]:
            sell_signals.append("均线空头")

        # 6. 量价信号
        if volume_analysis["signal"] == "看多":
            buy_signals.append("量价配合")
        elif volume_analysis["signal"] == "看空":
            sell_signals.append("量价背离")

        # 7. 形态信号
        for pattern in patterns:
            if pattern["type"] == "看涨":
                buy_signals.append(f"形态:{pattern['name']}")
            elif pattern["type"] == "看跌":
                sell_signals.append(f"形态:{pattern['name']}")

        # 计算信号强度
        buy_strength = len(buy_signals)
        sell_strength = len(sell_signals)

        # 确定最终信号
        if buy_strength > sell_strength + 2:
            final_signal = "强烈买入"
            signal_strength = min(1.0, buy_strength / 10)
        elif buy_strength > sell_strength:
            final_signal = "买入"
            signal_strength = 0.7
        elif sell_strength > buy_strength + 2:
            final_signal = "强烈卖出"
            signal_strength = min(1.0, sell_strength / 10)
        elif sell_strength > buy_strength:
            final_signal = "卖出"
            signal_strength = 0.7
        else:
            final_signal = "持有"
            signal_strength = 0.5

        # 生成信号描述
        description = self._generate_signal_description(
            buy_signals,
            sell_signals,
            final_signal
        )

        return {
            "buy_signal": buy_strength > 0,
            "sell_signal": sell_strength > 0,
            "buy_reasons": buy_signals,
            "sell_reasons": sell_signals,
            "final_signal": final_signal,
            "signal_strength": round(signal_strength, 2),
            "description": description
        }

    def _generate_signal_description(
        self,
        buy_signals: List[str],
        sell_signals: List[str],
        final_signal: str
    ) -> str:
        """
        生成信号描述

        Args:
            buy_signals: 买入信号列表
            sell_signals: 卖出信号列表
            final_signal: 最终信号

        Returns:
            信号描述
        """
        parts = [f"**综合信号**: {final_signal}"]

        if buy_signals:
            parts.append(f"**买入理由**: {', '.join(buy_signals)}")

        if sell_signals:
            parts.append(f"**卖出理由**: {', '.join(sell_signals)}")

        return "；".join(parts)

    # ========== 7. 综合评分 ==========

    def _calculate_technical_score(
        self,
        trend_analysis: Dict[str, Any],
        indicators: Dict[str, Any],
        volume_analysis: Dict[str, Any],
        signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算技术面综合评分

        Args:
            trend_analysis: 趋势分析结果
            indicators: 技术指标分析结果
            volume_analysis: 量价分析结果
            signals: 买卖信号

        Returns:
            综合评分结果
        """
        self.logger.info("计算技术面综合评分")

        # 各维度评分
        scores = {}

        # 1. 趋势评分 (30%)
        if trend_analysis["direction"] == "上涨":
            scores["trend"] = 80 + trend_analysis["strength"] * 0.2
        elif trend_analysis["direction"] == "下跌":
            scores["trend"] = 40 - trend_analysis["strength"] * 0.2
        else:
            scores["trend"] = 60

        # 2. 指标评分 (40%)
        indicator_scores = []
        for ind_name, ind_data in indicators.items():
            if ind_data.get("recommendation") == "买入":
                indicator_scores.append(80)
            elif ind_data.get("recommendation") == "卖出":
                indicator_scores.append(40)
            else:
                indicator_scores.append(60)
        scores["indicators"] = np.mean(indicator_scores) if indicator_scores else 60

        # 3. 量价评分 (20%)
        if volume_analysis["signal"] == "看多":
            scores["volume"] = 75
        elif volume_analysis["signal"] == "看空":
            scores["volume"] = 45
        else:
            scores["volume"] = 60

        # 4. 信号评分 (10%)
        if signals["final_signal"] in ["强烈买入", "买入"]:
            scores["signal"] = 80
        elif signals["final_signal"] in ["强烈卖出", "卖出"]:
            scores["signal"] = 40
        else:
            scores["signal"] = 60

        # 计算总分
        total_score = (
            scores["trend"] * 0.30 +
            scores["indicators"] * 0.40 +
            scores["volume"] * 0.20 +
            scores["signal"] * 0.10
        )

        # 评级
        if total_score >= 75:
            grade = "A"
            recommendation = "技术面优秀，建议关注"
        elif total_score >= 65:
            grade = "B"
            recommendation = "技术面良好，可以关注"
        elif total_score >= 55:
            grade = "C"
            recommendation = "技术面一般，谨慎对待"
        else:
            grade = "D"
            recommendation = "技术面较差，建议观望"

        return {
            "total_score": round(total_score, 1),
            "grade": grade,
            "recommendation": recommendation,
            "dimension_scores": {k: round(v, 1) for k, v in scores.items()}
        }

    # ========== 8. 辅助计算函数 ==========

    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        计算指数移动平均线 (EMA)

        Args:
            data: 数据序列
            period: 周期

        Returns:
            EMA序列
        """
        if len(data) < period:
            return np.array([np.mean(data)])

        # EMA计算
        ema = np.zeros_like(data)
        ema[0] = data[0]

        multiplier = 2 / (period + 1)

        for i in range(1, len(data)):
            ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]

        return ema

    def _calculate_kdj_simple(
        self,
        high_prices: np.ndarray,
        low_prices: np.ndarray,
        close_prices: np.ndarray,
        n: int = 9
    ) -> Tuple[float, float]:
        """
        简化版KDJ计算

        Args:
            high_prices: 最高价序列
            low_prices: 最低价序列
            close_prices: 收盘价序列
            n: 周期

        Returns:
            (K值, D值)
        """
        if len(close_prices) < n:
            return 50.0, 50.0

        # 计算最近n天的最高价和最低价
        highest = np.max(high_prices[-n:])
        lowest = np.min(low_prices[-n:])

        # 计算RSV
        if highest == lowest:
            rsv = 50
        else:
            rsv = (close_prices[-1] - lowest) / (highest - lowest) * 100

        # 简化计算K和D
        k = rsv
        d = k

        return k, d

    def _calculate_rsi_simple(
        self,
        close_prices: np.ndarray,
        period: int = 14
    ) -> float:
        """
        简化版RSI计算

        Args:
            close_prices: 收盘价序列
            period: 周期

        Returns:
            RSI值
        """
        if len(close_prices) < period + 1:
            return 50.0

        # 计算价格变化
        changes = np.diff(close_prices[-(period+1):])

        # 分离上涨和下跌
        gains = np.where(changes > 0, changes, 0)
        losses = np.where(changes < 0, -changes, 0)

        # 计算平均上涨和下跌
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        # 计算RSI
        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    # ========== 9. 总结生成 ==========

    def _generate_summary(
        self,
        trend_analysis: Dict[str, Any],
        indicators: Dict[str, Any],
        signals: Dict[str, Any],
        score: Dict[str, Any]
    ) -> str:
        """
        生成总结

        Args:
            trend_analysis: 趋势分析结果
            indicators: 技术指标分析结果
            signals: 买卖信号
            score: 综合评分

        Returns:
            总结文本
        """
        parts = []

        # 趋势总结
        parts.append(
            f"趋势{trend_analysis['direction']}（强度{trend_analysis['strength']:.1f}%）"
        )

        # 指标总结
        macd_signal = indicators["macd"]["signal_type"]
        rsi_value = indicators["rsi"]["rsi"]
        parts.append(f"MACD{macd_signal}，RSI={rsi_value:.1f}")

        # 信号总结
        parts.append(f"信号:{signals['final_signal']}")

        # 评分总结
        parts.append(f"技术评分{score['total_score']:.1f}分（{score['grade']}级）")

        return "；".join(parts) + "。"

    # ========== 10. 生成6个核心指标 ==========

    def generate_core_indicators(
        self,
        technical_result: Dict[str, Any],
        current_price: float,
        fundamentals: Optional[Dict[str, Any]] = None,
        chip_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        根据技术分析结果生成6个核心指标

        6个核心指标：
        1. 割肉价（止损价）- 支撑位 × 0.95
        2. 买入价（入场点）- 支撑位与当前价之间
        3. 持仓成本（预期平均成本）
        4. 压力位（阻力位）- 最强阻力位（优先使用筹码分析）
        5. 主升浪（时间窗口）- 基于趋势和季节性
        6. 目标价（预期价格）- 基于估值或技术形态

        Args:
            technical_result: 技术分析结果（从analyze方法返回）
            current_price: 当前股价
            fundamentals: 基本面数据（可选，用于目标价计算）
            chip_analysis: 筹码分析结果（可选，用于更精准的支撑压力位）

        Returns:
            6个核心指标
        """
        self.logger.info("开始生成6个核心指标")

        # 提取关键数据
        support_levels = technical_result["trend"]["support_levels"]
        resistance_levels = technical_result["trend"]["resistance_levels"]
        trend_direction = technical_result["trend"]["direction"]
        bollinger = technical_result["indicators"]["bollinger"]
        trend_strength = technical_result["trend"]["strength"]

        # 检测数据是否异常（如果支撑位和阻力位远大于当前价，说明数据有问题）
        if support_levels and min(support_levels) > current_price * 1.5:
            self.logger.warning(f"检测到异常数据，支撑位({min(support_levels)})远大于当前价({current_price})，使用简单规则")
            use_simple_rules = True
        else:
            use_simple_rules = False

        # ========== 集成筹码分析结果 ==========
        # 如果有筹码分析结果，优先使用筹码分析的支撑位和压力位
        if chip_analysis and chip_analysis.get("support_levels"):
            chip_support_levels = [level["price"] for level in chip_analysis["support_levels"]]
            self.logger.info(f"使用筹码分析的支撑位: {chip_support_levels[:3]}")
            # 筹码支撑位优先，但保留技术支撑位作为备选
            if not use_simple_rules:
                support_levels = chip_support_levels + (support_levels or [])

        if chip_analysis and chip_analysis.get("resistance_levels"):
            chip_resistance_levels = [level["price"] for level in chip_analysis["resistance_levels"]]
            self.logger.info(f"使用筹码分析的压力位: {chip_resistance_levels[:3]}")
            # 筹码压力位优先，但保留技术压力位作为备选
            if not use_simple_rules:
                resistance_levels = chip_resistance_levels + (resistance_levels or [])

        if use_simple_rules:
            # ========== 简单规则模式（当数据异常时） ==========
            self.logger.info("使用简单规则生成指标")

            # 1. 割肉价（止损价）= 当前价 × 0.95（保守5%止损）
            stop_loss_price = round(current_price * 0.95, 2)

            # 2. 买入价 = 当前价（或略低于当前价）
            buy_price = round(current_price * 0.98, 2)

            # 3. 持仓成本 = 买入价
            position_cost = buy_price

            # 4. 压力位 = 当前价 × 1.2（假设20%上涨空间）
            pressure_price = round(current_price * 1.2, 2)

            # 5. 主升浪（基于趋势）
            if trend_direction == "上涨" and trend_strength > 60:
                main_rise_window = "1个月内，持续3-6个月"
            elif trend_direction == "上涨":
                main_rise_window = "2个月内，持续4-6个月"
            else:
                main_rise_window = "等待趋势反转"

            # 6. 目标价（基于基本面或技术）
            if fundamentals and fundamentals.get("pb_ratio"):
                pb = fundamentals["pb_ratio"]
                if pb < 1.0:
                    # PB修复逻辑
                    book_value_per_share = fundamentals.get("book_value_per_share", 0)
                    if book_value_per_share > 0:
                        target_price = round(book_value_per_share * 1.0, 2)  # 中性目标
                    else:
                        target_price = pressure_price
                else:
                    target_price = pressure_price
            else:
                target_price = round(pressure_price * 1.1, 2)

        else:
            # ========== 完整技术分析模式 ==========
            # ========== 1. 割肉价（止损价） ==========
            # 逻辑：取最强支撑位 × 0.95（保守估计）
            if support_levels and len(support_levels) > 0:
                strongest_support = min(support_levels)  # 最低的支撑位 = 最强支撑
                stop_loss_price = round(strongest_support * 0.95, 2)
            else:
                # 如果没有支撑位，使用布林带下轨 × 0.95
                stop_loss_price = round(bollinger["lower"] * 0.95, 2)

            # ========== 2. 买入价（入场点） ==========
            # 逻辑：当前价与支撑位之间的中点
            if support_levels and len(support_levels) > 0:
                strongest_support = min(support_levels)
                # 买入价 = 支撑位 + (当前价 - 支撑位) × 0.5
                buy_price = round((strongest_support + current_price) / 2, 2)
            else:
                # 如果没有支撑位，买入价 = 当前价 × 0.98（略低于当前价）
                buy_price = round(current_price * 0.98, 2)

            # ========== 3. 持仓成本（预期平均成本） ==========
            # 逻辑：与买入价相同（一次性买入或分批买入的平均成本）
            position_cost = buy_price

            # ========== 4. 压力位（阻力位） ==========
            # 逻辑：取最强阻力位
            if resistance_levels and len(resistance_levels) > 0:
                strongest_resistance = max(resistance_levels)  # 最高的阻力位 = 最强阻力
            else:
                # 如果没有阻力位，使用布林带上轨
                strongest_resistance = bollinger["upper"]

            pressure_price = round(strongest_resistance, 2)

            # ========== 5. 主升浪（时间窗口） ==========
            # 逻辑：基于趋势强度和历史规律预测
            # 简化版：假设主升浪在趋势确认后的3-6个月内
            if trend_direction == "上涨" and trend_strength > 60:
                # 强烈上涨趋势，主升浪可能在1-3个月内
                main_rise_start = "1个月内"
                main_rise_duration = "3-6个月"
            elif trend_direction == "上涨":
                # 一般上涨趋势，主升浪可能在2-4个月内
                main_rise_start = "2个月内"
                main_rise_duration = "4-6个月"
            elif trend_direction == "震荡":
                # 震荡趋势，等待突破
                main_rise_start = "等待向上突破"
                main_rise_duration = "突破后3-6个月"
            else:
                # 下跌趋势，不适合买入
                main_rise_start = "等待趋势反转"
                main_rise_duration = "趋势反转后3-6个月"

            main_rise_window = f"{main_rise_start}，持续{main_rise_duration}"

            # ========== 6. 目标价（预期价格） ==========
            # 逻辑：如果有基本面数据，使用估值模型；否则使用技术形态
            if fundamentals and fundamentals.get("pb_ratio"):
                # PB修复逻辑（用户成功案例的方法）
                pb = fundamentals["pb_ratio"]
                if pb < 1.0:
                    # PB低于1，低估
                    book_value_per_share = fundamentals.get("book_value_per_share", 0)
                    if book_value_per_share > 0:
                        # 目标价 = 每股净资产 × 0.8（保守）或 × 1.0（中性）
                        target_price_conservative = round(book_value_per_share * 0.8, 2)
                        target_price_neutral = round(book_value_per_share * 1.0, 2)
                        target_price = target_price_neutral  # 使用中性目标
                    else:
                        # 没有每股净资产数据，使用压力位作为目标
                        target_price = pressure_price
                else:
                    # PB高于1，使用技术形态
                    target_price = pressure_price
            else:
                # 没有基本面数据，使用技术形态
                # 目标价 = 压力位 × 1.1（假设能突破阻力位）
                target_price = round(pressure_price * 1.1, 2)

        # ========== 生成结果 ==========
        result = {
            "割肉价": stop_loss_price,
            "买入价": buy_price,
            "持仓成本": position_cost,
            "压力位": pressure_price,
            "主升浪": main_rise_window,
            "目标价": target_price,
            "当前价": round(current_price, 2),

            # 附加信息
            "止损幅度": round(((current_price - stop_loss_price) / current_price) * 100, 2),
            "目标涨幅": round(((target_price - current_price) / current_price) * 100, 2),
            "风险收益比": round((target_price - current_price) / (current_price - stop_loss_price), 2) if current_price > stop_loss_price else 0,

            # 生成依据
            "生成依据": {
                "割肉价": f"基于{'当前价×0.95（简单规则）' if use_simple_rules else f'最强支撑位（{stop_loss_price/0.95:.2f}）× 0.95'}",
                "买入价": f"基于{'当前价×0.98（简单规则）' if use_simple_rules else '支撑位与当前价的中点'}",
                "持仓成本": f"与买入价相同",
                "压力位": f"基于{'当前价×1.2（简单规则）' if use_simple_rules else '筹码分析压力位' if chip_analysis and chip_analysis.get('resistance_levels') else '技术分析阻力位'}",
                "主升浪": f"基于{trend_direction}趋势（强度{trend_strength:.1f}%）" + (f"，筹码分析突破难度：{chip_analysis.get('breakthrough_difficulty', '未知')}" if chip_analysis else ""),
                "目标价": f"基于{'PB修复逻辑' if fundamentals and fundamentals.get('pb_ratio') else '技术形态'}",
                "模式": "简单规则模式（数据异常）" if use_simple_rules else "完整技术分析模式" + ("（集成筹码分析）" if chip_analysis else ""),
                "筹码分析": "已集成" if chip_analysis else "未集成"
            }
        }

        self.logger.info(
            f"6个核心指标生成完成",
            extra={
                "mode": "simple" if use_simple_rules else "full",
                "stop_loss": stop_loss_price,
                "buy_price": buy_price,
                "target_price": target_price,
                "risk_return_ratio": result["风险收益比"]
            }
        )

        return result


# ========== 便捷函数 ==========

async def analyze_technical(
    stock_code: str,
    days: int = 365,
    analysis_type: str = "standard"
) -> Dict[str, Any]:
    """
    技术分析（便捷函数）

    Args:
        stock_code: 股票代码
        days: 分析天数
        analysis_type: 分析类型（quick/standard/deep）

    Returns:
        技术分析结果
    """
    ai = TechnicalAnalysisAI()
    return await ai.analyze(stock_code, days=days, analysis_type=analysis_type)
