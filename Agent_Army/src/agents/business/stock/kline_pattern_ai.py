"""
K线共性分析AI - Kline Pattern Analysis AI

职责：
- 叠加3年K线图，识别共同特征
- 发现关键支撑位、阻力位
- 预测价格走势

核心方法：
- K线数据叠加
- 价格聚集区分析
- 季节性规律识别

输入：
- 股票代码
- 历史年数（默认3年）

输出：
- 支撑位/阻力位列表
- 季节性规律
- K线共性报告
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import numpy as np
import pandas as pd
from collections import defaultdict

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool


class KlinePatternAI(BaseAgent, LoggerMixin):
    """
    K线共性分析AI

    核心功能：
    1. 叠加3年K线图，识别共同特征
    2. 发现关键支撑位、阻力位（价格聚集区）
    3. 识别季节性规律

    算法：
    - K线数据叠加
    - 价格聚集区分析（支撑位/阻力位）
    - 季节性分解（季度趋势）
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.financial_tool = FinancialTool()

        super().__init__(
            name="K线共性分析AI",
            role="叠加多年K线图，识别价格共性规律，预测支撑阻力位",
            capabilities=[
                AgentCapability(
                    name="kline_overlay",
                    description="K线图叠加分析",
                    input_type="stock_code",
                    output_type="overlay_report"
                ),
                AgentCapability(
                    name="support_resistance",
                    description="支撑阻力位识别",
                    input_type="stock_code",
                    output_type="price_levels"
                ),
                AgentCapability(
                    name="seasonal_pattern",
                    description="季节性规律识别",
                    input_type="stock_code",
                    output_type="seasonal_report"
                )
            ],
            tools=[
                AgentTool(
                    name="price_data",
                    description="价格数据工具",
                    tool_type="system",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("K线共性分析AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze_kline_patterns":
            return await self.analyze_kline_patterns(
                kwargs.get("stock_code"),
                kwargs.get("years", 3)
            )
        elif task == "identify_support_resistance":
            return await self.identify_support_resistance(
                kwargs.get("stock_code"),
                kwargs.get("years", 3)
            )
        elif task == "analyze_seasonal":
            return await self.analyze_seasonal(
                kwargs.get("stock_code"),
                kwargs.get("years", 3)
            )
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 核心功能 ==========

    async def analyze_kline_patterns(
        self,
        stock_code: str,
        years: int = 3
    ) -> Dict[str, Any]:
        """
        分析K线共性规律

        分析内容：
        1. 支撑位/阻力位（价格聚集区）
        2. 季节性规律（Q1-Q4趋势）
        3. 多年K线叠加

        Args:
            stock_code: 股票代码
            years: 叠加年数

        Returns:
            {
                "stock_code": "601669",
                "analysis_date": "2026-03-15",
                "support_levels": [5.2, 5.5, 6.0],
                "resistance_levels": [6.5, 7.8, 8.5],
                "seasonal_patterns": {
                    "q1_trend": "上涨",
                    "q2_trend": "震荡",
                    "q3_trend": "上涨",
                    "q4_trend": "下跌"
                },
                "overlapped_klines": {
                    "year_2023": {...},
                    "year_2024": {...},
                    "year_2025": {...}
                },
                "key_findings": [...]
            }
        """
        self.logger.info(
            f"开始分析K线共性",
            extra={"stock_code": stock_code, "years": years}
        )

        # 1. 获取历史K线数据
        kline_data = await self._fetch_kline_data(stock_code, years)

        if not kline_data:
            return {
                "stock_code": stock_code,
                "error": "无法获取K线数据"
            }

        # 2. 分析支撑位/阻力位
        price_levels = await self.identify_support_resistance(stock_code, years)

        # 3. 分析季节性规律
        seasonal_patterns = await self.analyze_seasonal(stock_code, years)

        # 4. 生成多年K线叠加
        overlapped_klines = self._generate_overlapped_klines(kline_data)

        # 5. 生成关键发现
        key_findings = self._generate_key_findings(
            price_levels,
            seasonal_patterns,
            overlapped_klines
        )

        # 6. 生成报告
        report = {
            "stock_code": stock_code,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "support_levels": price_levels.get("support_levels", []),
            "resistance_levels": price_levels.get("resistance_levels", []),
            "seasonal_patterns": seasonal_patterns,
            "overlapped_klines": overlapped_klines,
            "key_findings": key_findings,
            "summary": self._generate_pattern_summary(
                price_levels,
                seasonal_patterns
            )
        }

        self.logger.info(
            f"K线共性分析完成",
            extra={
                "stock_code": stock_code,
                "support_count": len(report["support_levels"]),
                "resistance_count": len(report["resistance_levels"])
            }
        )

        return report

    async def identify_support_resistance(
        self,
        stock_code: str,
        years: int = 3
    ) -> Dict[str, Any]:
        """
        识别支撑位和阻力位

        方法：
        1. 获取历史价格数据
        2. 计算价格聚集区（高频价格区间）
        3. 识别支撑位（底部聚集区）
        4. 识别阻力位（顶部聚集区）

        Returns:
            {
                "support_levels": [5.2, 5.5, 6.0],
                "resistance_levels": [6.5, 7.8, 8.5],
                "current_price": 6.2,
                "nearest_support": 5.5,
                "nearest_resistance": 6.5
            }
        """
        self.logger.info(f"识别支撑阻力位: {stock_code}")

        # 1. 获取K线数据
        kline_data = await self._fetch_kline_data(stock_code, years)

        if not kline_data:
            return {"error": "无法获取K线数据"}

        # 2. 提取价格数据
        prices = []
        for item in kline_data:
            prices.extend([
                item.get("open", 0),
                item.get("close", 0),
                item.get("high", 0),
                item.get("low", 0)
            ])

        prices = np.array(prices)

        # 3. 计算价格聚集区（使用直方图）
        n_bins = 50
        hist, bin_edges = np.histogram(prices, bins=n_bins)

        # 4. 找到高频区间（聚集区）
        threshold = np.mean(hist) + np.std(hist)
        peak_indices = np.where(hist > threshold)[0]

        # 5. 提取价格水平
        price_levels = []
        for idx in peak_indices:
            price_level = (bin_edges[idx] + bin_edges[idx+1]) / 2
            price_levels.append(price_level)

        # 6. 分类支撑位和阻力位
        current_price = prices[-1] if len(prices) > 0 else 0

        support_levels = []
        resistance_levels = []

        for level in sorted(price_levels):
            if level < current_price:
                support_levels.append(level)
            else:
                resistance_levels.append(level)

        # 7. 找到最近的支撑位和阻力位
        nearest_support = max(support_levels) if support_levels else None
        nearest_resistance = min(resistance_levels) if resistance_levels else None

        return {
            "support_levels": sorted(support_levels, reverse=True),
            "resistance_levels": sorted(resistance_levels),
            "current_price": float(current_price),
            "nearest_support": float(nearest_support) if nearest_support else None,
            "nearest_resistance": float(nearest_resistance) if nearest_resistance else None
        }

    async def analyze_seasonal(
        self,
        stock_code: str,
        years: int = 3
    ) -> Dict[str, Any]:
        """
        分析季节性规律

        方法：
        1. 按季度分组K线数据
        2. 计算每个季度的平均涨跌幅
        3. 识别季度趋势

        Returns:
            {
                "q1_trend": "上涨",
                "q2_trend": "震荡",
                "q3_trend": "上涨",
                "q4_trend": "下跌",
                "best_quarter": "Q1",
                "worst_quarter": "Q4",
                "seasonal_strength": 0.65
            }
        """
        self.logger.info(f"分析季节性规律: {stock_code}")

        # 1. 获取K线数据
        kline_data = await self._fetch_kline_data(stock_code, years)

        if not kline_data:
            return {"error": "无法获取K线数据"}

        # 2. 按季度分组
        quarterly_returns = defaultdict(list)

        for item in kline_data:
            try:
                date_str = item.get("date", "")
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")

                # 判断季度
                quarter = (date_obj.month - 1) // 3 + 1
                quarter_key = f"q{quarter}"

                # 计算涨跌幅
                open_price = item.get("open", 0)
                close_price = item.get("close", 0)

                if open_price > 0:
                    daily_return = (close_price - open_price) / open_price
                    quarterly_returns[quarter_key].append(daily_return)
            except:
                continue

        # 3. 计算季度平均涨跌幅
        quarterly_avg = {}
        for q in ["q1", "q2", "q3", "q4"]:
            if quarterly_returns[q]:
                avg_return = np.mean(quarterly_returns[q])
                quarterly_avg[q] = avg_return
            else:
                quarterly_avg[q] = 0.0

        # 4. 判断趋势
        trends = {}
        for q, avg_return in quarterly_avg.items():
            if avg_return > 0.02:
                trends[f"{q}_trend"] = "上涨"
            elif avg_return < -0.02:
                trends[f"{q}_trend"] = "下跌"
            else:
                trends[f"{q}_trend"] = "震荡"

        # 5. 找到最好和最差的季度
        best_quarter = max(quarterly_avg, key=quarterly_avg.get)
        worst_quarter = min(quarterly_avg, key=quarterly_avg.get)

        # 6. 计算季节性强度（方差）
        seasonal_strength = np.std(list(quarterly_avg.values()))

        return {
            **trends,
            "best_quarter": best_quarter.upper(),
            "worst_quarter": worst_quarter.upper(),
            "quarterly_returns": {k: round(v, 4) for k, v in quarterly_avg.items()},
            "seasonal_strength": round(float(seasonal_strength), 4)
        }

    # ========== 内部方法 ==========

    async def _fetch_kline_data(
        self,
        stock_code: str,
        years: int
    ) -> List[Dict[str, Any]]:
        """
        获取K线数据

        注意：当前使用模拟数据
        TODO: 集成真实的Tushare接口（pro.daily）
        """
        # 模拟数据：生成随机K线数据
        today = datetime.now()
        kline_data = []

        base_price = 6.0  # 基准价格

        for i in range(years * 250):  # 每年约250个交易日
            days_ago = i
            date = today - timedelta(days=days_ago)

            # 随机生成K线数据
            open_price = base_price + np.random.uniform(-0.5, 0.5)
            close_price = open_price + np.random.uniform(-0.3, 0.3)
            high_price = max(open_price, close_price) + np.random.uniform(0, 0.2)
            low_price = min(open_price, close_price) - np.random.uniform(0, 0.2)
            volume = np.random.randint(1000000, 10000000)

            kline_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(open_price), 2),
                "close": round(float(close_price), 2),
                "high": round(float(high_price), 2),
                "low": round(float(low_price), 2),
                "volume": int(volume)
            })

        # 按时间排序（倒序）
        kline_data = sorted(kline_data, key=lambda x: x["date"], reverse=True)

        return kline_data

    def _generate_overlapped_klines(
        self,
        kline_data: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        生成多年K线叠加

        按年度分组K线数据
        """
        overlapped = defaultdict(list)

        for item in kline_data:
            try:
                date_str = item["date"]
                year = datetime.strptime(date_str, "%Y-%m-%d").year

                # 只保留日期（不含年份），用于叠加
                month_day = date_str[5:]  # MM-DD

                kline_item = {
                    "date": month_day,
                    "open": item["open"],
                    "close": item["close"],
                    "high": item["high"],
                    "low": item["low"]
                }

                overlapped[f"year_{year}"].append(kline_item)
            except:
                continue

        return dict(overlapped)

    def _generate_key_findings(
        self,
        price_levels: Dict[str, Any],
        seasonal_patterns: Dict[str, Any],
        overlapped_klines: Dict[str, List[Dict[str, Any]]]
    ) -> List[str]:
        """
        生成关键发现
        """
        findings = []

        # 1. 支撑位发现
        support_levels = price_levels.get("support_levels", [])
        if support_levels:
            nearest_support = price_levels.get("nearest_support")
            current_price = price_levels.get("current_price", 0)
            distance_to_support = ((current_price - nearest_support) / current_price * 100) if current_price > 0 else 0

            if distance_to_support < 5:
                findings.append(f"距离最近支撑位{nearest_support:.2f}元仅{distance_to_support:.1f}%，注意风险")

        # 2. 阻力位发现
        resistance_levels = price_levels.get("resistance_levels", [])
        if resistance_levels:
            nearest_resistance = price_levels.get("nearest_resistance")
            findings.append(f"上方阻力位{nearest_resistance:.2f}元，突破需放量")

        # 3. 季节性发现
        best_quarter = seasonal_patterns.get("best_quarter", "")
        worst_quarter = seasonal_patterns.get("worst_quarter", "")

        if best_quarter and worst_quarter:
            findings.append(f"季节性规律：{best_quarter}表现最好，{worst_quarter}表现最差")

        # 4. 强度发现
        seasonal_strength = seasonal_patterns.get("seasonal_strength", 0)
        if seasonal_strength > 0.05:
            findings.append(f"季节性特征明显（强度{seasonal_strength:.3f}），可把握季度机会")
        else:
            findings.append(f"季节性特征较弱（强度{seasonal_strength:.3f}），主要受基本面驱动")

        return findings

    def _generate_pattern_summary(
        self,
        price_levels: Dict[str, Any],
        seasonal_patterns: Dict[str, Any]
    ) -> str:
        """
        生成K线共性分析摘要
        """
        summary_parts = []

        # 1. 支撑阻力位
        support_levels = price_levels.get("support_levels", [])
        resistance_levels = price_levels.get("resistance_levels", [])

        if support_levels:
            summary_parts.append(f"下方支撑位：{', '.join([f'{s:.2f}' for s in support_levels[:3]])}元")
        if resistance_levels:
            summary_parts.append(f"上方阻力位：{', '.join([f'{r:.2f}' for r in resistance_levels[:3]])}元")

        # 2. 季节性规律
        best_quarter = seasonal_patterns.get("best_quarter", "")
        worst_quarter = seasonal_patterns.get("worst_quarter", "")

        if best_quarter and worst_quarter:
            summary_parts.append(f"季节性：{best_quarter}最佳，{worst_quarter}最差")

        if not summary_parts:
            return "K线共性特征不明显，建议结合其他维度分析"

        return "；".join(summary_parts) + "。"
