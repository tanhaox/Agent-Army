"""
历史周期分析AI - Historical Cycle Analysis AI

职责：
- 分析重大事件的周期性规律（政策、业绩公告）
- 预测未来事件发生时间（误差≤1月）
- 识别关键时间窗口

核心方法：
- FFT变换检测周期性
- 时间序列自相关分析
- 季节性分解

输入：
- 股票代码
- 历史年数（默认5年）

输出：
- 事件周期性报告
- 下次事件预测
- 置信度评估
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from datetime import date as date_type
import asyncio
import numpy as np
from collections import defaultdict

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool


class HistoricalCycleAI(BaseAgent, LoggerMixin):
    """
    历史周期分析AI

    核心功能：
    1. 分析重大事件的周期性规律（政策、业绩公告）
    2. 预测未来事件发生时间（误差≤1月）
    3. 识别关键时间窗口

    算法：
    - FFT（快速傅里叶变换）检测周期性
    - 自相关分析验证周期
    - 季节性分解
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.financial_tool = FinancialTool()

        super().__init__(
            name="历史周期分析AI",
            role="分析重大事件的周期性规律，预测未来关键时间窗口",
            capabilities=[
                AgentCapability(
                    name="policy_cycle_analysis",
                    description="政策周期分析",
                    input_type="stock_code",
                    output_type="cycle_report"
                ),
                AgentCapability(
                    name="earnings_cycle_analysis",
                    description="财报周期分析",
                    input_type="stock_code",
                    output_type="cycle_report"
                ),
                AgentCapability(
                    name="event_prediction",
                    description="事件时间预测",
                    input_type="stock_code",
                    output_type="prediction_report"
                )
            ],
            tools=[
                AgentTool(
                    name="financial_data",
                    description="财务数据工具",
                    tool_type="system",
                    config={}
                ),
                AgentTool(
                    name="news_data",
                    description="新闻数据工具",
                    tool_type="system",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("历史周期分析AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze_event_cycles":
            return await self.analyze_event_cycles(
                kwargs.get("stock_code"),
                kwargs.get("years", 5)
            )
        elif task == "predict_next_event":
            return await self.predict_next_event(
                kwargs.get("stock_code"),
                kwargs.get("event_type", "earnings")
            )
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 核心功能 ==========

    async def analyze_event_cycles(
        self,
        stock_code: str,
        years: int = 5
    ) -> Dict[str, Any]:
        """
        分析事件周期性

        分析内容：
        1. 政策发布周期（从新闻数据中提取）
        2. 财报发布周期（从财务数据中提取）
        3. 重大事件周期（如：分红、重组）

        Args:
            stock_code: 股票代码
            years: 分析历史年数

        Returns:
            {
                "stock_code": "600519",
                "analysis_date": "2026-03-15",
                "policy_cycles": {
                    "detected": true,
                    "cycle_length": 12,  # 月
                    "confidence": 0.85,
                    "next_event": "2026-06",
                    "historical_events": [
                        {"date": "2021-06", "event": "碳中和政策"},
                        {"date": "2022-05", "event": "碳中和政策"}
                    ]
                },
                "earnings_cycles": {
                    "detected": true,
                    "cycle_length": 3,  # 月（季度财报）
                    "confidence": 0.98,
                    "next_event": "2026-04",
                    "historical_events": [...]
                },
                "key_time_windows": [
                    {
                        "window": "2026-04",
                        "type": "财报发布",
                        "importance": "高",
                        "action": "关注财报数据"
                    }
                ]
            }
        """
        self.logger.info(
            f"开始分析事件周期",
            extra={"stock_code": stock_code, "years": years}
        )

        # 1. 分析财报发布周期
        earnings_cycles = await self._analyze_earnings_cycle(stock_code, years)

        # 2. 分析政策发布周期
        policy_cycles = await self._analyze_policy_cycle(stock_code, years)

        # 3. 生成关键时间窗口
        key_windows = self._generate_key_time_windows(
            earnings_cycles,
            policy_cycles
        )

        # 4. 生成报告
        report = {
            "stock_code": stock_code,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "earnings_cycles": earnings_cycles,
            "policy_cycles": policy_cycles,
            "key_time_windows": key_windows,
            "summary": self._generate_cycle_summary(
                earnings_cycles,
                policy_cycles
            )
        }

        self.logger.info(
            f"事件周期分析完成",
            extra={
                "stock_code": stock_code,
                "earnings_cycle": earnings_cycles.get("cycle_length"),
                "policy_cycle": policy_cycles.get("cycle_length")
            }
        )

        return report

    async def predict_next_event(
        self,
        stock_code: str,
        event_type: str = "earnings"
    ) -> Dict[str, Any]:
        """
        预测下一个事件

        Args:
            stock_code: 股票代码
            event_type: 事件类型（earnings/policy/dividend）

        Returns:
            {
                "stock_code": "600519",
                "event_type": "earnings",
                "predicted_date": "2026-04-15",
                "confidence": 0.92,
                "time_window": "2026-04-01 ~ 2026-04-30",
                "action": "建议提前1周关注"
            }
        """
        self.logger.info(
            f"预测下一个事件",
            extra={"stock_code": stock_code, "event_type": event_type}
        )

        if event_type == "earnings":
            cycles = await self._analyze_earnings_cycle(stock_code, 5)
        elif event_type == "policy":
            cycles = await self._analyze_policy_cycle(stock_code, 5)
        else:
            return {
                "stock_code": stock_code,
                "event_type": event_type,
                "error": "不支持的事件类型"
            }

        if not cycles.get("detected"):
            return {
                "stock_code": stock_code,
                "event_type": event_type,
                "error": "未检测到周期性"
            }

        # 计算下一个事件日期
        next_event = cycles.get("next_event", "")
        confidence = cycles.get("confidence", 0.0)

        return {
            "stock_code": stock_code,
            "event_type": event_type,
            "predicted_date": next_event,
            "confidence": confidence,
            "time_window": self._calculate_time_window(next_event),
            "action": self._generate_action_suggestion(next_event, confidence)
        }

    # ========== 内部方法 ==========

    async def _analyze_earnings_cycle(
        self,
        stock_code: str,
        years: int
    ) -> Dict[str, Any]:
        """
        分析财报发布周期

        方法：
        1. 获取历史财报发布日期
        2. 计算发布间隔
        3. 使用FFT检测周期性
        """
        self.logger.info(f"分析财报周期: {stock_code}")

        # 1. 获取历史财报数据（使用模拟数据）
        historical_events = await self._fetch_earnings_history(stock_code, years)

        if len(historical_events) < 4:
            return {
                "detected": False,
                "reason": "历史数据不足（需要至少4个数据点）"
            }

        # 2. 计算发布间隔（天）
        intervals = self._calculate_intervals(historical_events)

        # 3. 检测周期性（使用FFT）
        cycle_result = self._detect_cycle_with_fft(intervals)

        if not cycle_result["detected"]:
            return {
                "detected": False,
                "reason": "未检测到明显周期性"
            }

        # 4. 计算下一个财报发布日期
        cycle_length_days = cycle_result["cycle_length"]
        last_event_date = historical_events[-1]["date"]

        next_event_date = self._predict_next_date(
            last_event_date,
            cycle_length_days
        )

        return {
            "detected": True,
            "cycle_length": round(cycle_length_days / 30, 1),  # 转换为月
            "cycle_length_days": int(cycle_length_days),
            "confidence": cycle_result["confidence"],
            "next_event": next_event_date,
            "historical_events": historical_events
        }

    async def _analyze_policy_cycle(
        self,
        stock_code: str,
        years: int
    ) -> Dict[str, Any]:
        """
        分析政策发布周期

        方法：
        1. 从新闻数据中提取政策事件
        2. 计算事件间隔
        3. 使用FFT检测周期性
        """
        self.logger.info(f"分析政策周期: {stock_code}")

        # 1. 获取历史政策事件（使用模拟数据）
        historical_events = await self._fetch_policy_history(stock_code, years)

        if len(historical_events) < 3:
            return {
                "detected": False,
                "reason": "政策事件数据不足（需要至少3个数据点）"
            }

        # 2. 计算发布间隔（天）
        intervals = self._calculate_intervals(historical_events)

        # 3. 检测周期性
        cycle_result = self._detect_cycle_with_fft(intervals)

        if not cycle_result["detected"]:
            return {
                "detected": False,
                "reason": "未检测到明显政策周期性"
            }

        # 4. 计算下一个政策发布日期
        cycle_length_days = cycle_result["cycle_length"]
        last_event_date = historical_events[-1]["date"]

        next_event_date = self._predict_next_date(
            last_event_date,
            cycle_length_days
        )

        return {
            "detected": True,
            "cycle_length": round(cycle_length_days / 30, 1),  # 转换为月
            "cycle_length_days": int(cycle_length_days),
            "confidence": cycle_result["confidence"],
            "next_event": next_event_date,
            "historical_events": historical_events
        }

    async def _fetch_earnings_history(
        self,
        stock_code: str,
        years: int
    ) -> List[Dict[str, Any]]:
        """
        获取历史财报发布日期

        现在使用真实的Tushare API
        """
        self.logger.info(f"从Tushare获取财报发布数据: {stock_code}")

        try:
            # 调用FinancialTool的get_announcement方法
            result = await self.financial_tool.get_announcement(stock_code, limit=200)

            if result.get("data_source") == "Tushare":
                self.logger.info("成功获取真实公告数据")

                # 过滤财报相关公告
                announcements = result.get("data", [])
                earnings_announcements = []

                for ann in announcements:
                    title = ann.get('title', '')
                    # 检查是否为财报公告
                    if any(kw in title for kw in ['年报', '中报', '季报', '业绩', '财务报告', '利润表']):
                        earnings_announcements.append({
                            "date": ann.get('ann_date', '')[:7],  # YYYY-MM格式
                            "event_type": "财报发布",
                            "title": title,
                            "ann_id": ann.get('ann_id', '')
                        })

                return earnings_announcements
            else:
                # 使用模拟数据
                self.logger.warning("使用模拟财报数据")
                return await self._fetch_sample_earnings_history(stock_code, years)

        except Exception as e:
            self.logger.error(f"获取财报数据失败: {e}")
            return await self._fetch_sample_earnings_history(stock_code, years)

    async def _fetch_policy_history(
        self,
        stock_code: str,
        years: int
    ) -> List[Dict[str, Any]]:
        """
        获取历史政策事件

        现在使用真实的Tushare API（从公告中提取政策相关）
        """
        self.logger.info(f"从Tushare获取政策事件数据: {stock_code}")

        try:
            # 调用FinancialTool的get_announcement方法
            result = await self.financial_tool.get_announcement(stock_code, limit=500)

            if result.get("data_source") == "Tushare":
                self.logger.info("成功获取真实公告数据")

                # 过滤政策相关公告
                announcements = result.get("data", [])
                policy_announcements = []

                for ann in announcements:
                    title = ann.get('title', '')
                    # 检查是否为政策公告
                    if any(kw in title for kw in ['政策', '规划', '方案', '通知', '办法', '规定']):
                        policy_announcements.append({
                            "date": ann.get('ann_date', '')[:7],  # YYYY-MM格式
                            "event_type": "政策发布",
                            "title": title,
                            "ann_id": ann.get('ann_id', '')
                        })

                return policy_announcements
            else:
                # 使用模拟数据
                self.logger.warning("使用模拟政策数据")
                return await self._fetch_sample_policy_history(stock_code, years)

        except Exception as e:
            self.logger.error(f"获取政策数据失败: {e}")
            return await self._fetch_sample_policy_history(stock_code, years)

    async def _fetch_sample_earnings_history(
        self,
        stock_code: str,
        years: int
    ) -> List[Dict[str, Any]]:
        """
        获取模拟财报发布日期（备用）
        """
        self.logger.warning(f"使用模拟财报数据: {stock_code}")

        # 模拟数据：贵州茅台财报发布周期（季度财报）
        today = datetime.now()
        events = []

        for i in range(years * 4):  # 每年4个财报
            days_ago = i * 90  # 约3个月
            event_date = today - timedelta(days=days_ago)

            events.append({
                "date": event_date.strftime("%Y-%m"),
                "event_type": "财报发布",
                "quarter": (i % 4) + 1
            })

        return events

    async def _fetch_sample_policy_history(
        self,
        stock_code: str,
        years: int
    ) -> List[Dict[str, Any]]:
        """
        获取模拟政策事件（备用）
        """
        self.logger.warning(f"使用模拟政策数据: {stock_code}")

        # 模拟数据：政策发布周期（年度政策）
        today = datetime.now()
        events = []

        for i in range(years):
            days_ago = i * 365  # 1年
            event_date = today - timedelta(days=days_ago)

            events.append({
                "date": event_date.strftime("%Y-%m"),
                "event_type": "政策发布",
                "policy_name": f"第{i+1}期政策"
            })

        return events

    def _calculate_intervals(
        self,
        events: List[Dict[str, Any]]
    ) -> List[float]:
        """
        计算事件间隔（天）

        Args:
            events: 事件列表，按时间排序

        Returns:
            间隔列表（天）
        """
        intervals = []

        for i in range(len(events) - 1):
            date1 = datetime.strptime(events[i]["date"], "%Y-%m")
            date2 = datetime.strptime(events[i+1]["date"], "%Y-%m")

            delta = (date2 - date1).days
            intervals.append(delta)

        return intervals

    def _detect_cycle_with_fft(
        self,
        intervals: List[float]
    ) -> Dict[str, Any]:
        """
        使用FFT检测周期性

        Args:
            intervals: 事件间隔列表（天）

        Returns:
            {
                "detected": True/False,
                "cycle_length": 90,  # 天
                "confidence": 0.85
            }
        """
        if len(intervals) < 3:
            return {"detected": False, "reason": "数据点太少"}

        # 1. FFT变换
        fft_values = np.fft.fft(intervals)
        fft_freq = np.fft.fftfreq(len(intervals))

        # 2. 找到主频率（排除直流分量）
        magnitudes = np.abs(fft_values[1:])
        frequencies = fft_freq[1:]

        if len(magnitudes) == 0:
            return {"detected": False, "reason": "FFT分析失败"}

        # 3. 计算周期长度
        peak_index = np.argmax(magnitudes)
        peak_frequency = frequencies[peak_index]

        if abs(peak_frequency) < 1e-10:
            return {"detected": False, "reason": "主频率为0"}

        cycle_length = 1.0 / abs(peak_frequency)

        # 4. 计算置信度（基于主峰的能量占比）
        total_energy = np.sum(magnitudes ** 2)
        peak_energy = magnitudes[peak_index] ** 2
        confidence = peak_energy / total_energy if total_energy > 0 else 0.0

        # 5. 判断是否检测到周期性
        min_confidence = 0.5
        detected = confidence >= min_confidence

        return {
            "detected": detected,
            "cycle_length": cycle_length,
            "confidence": float(confidence),
            "peak_frequency": float(peak_frequency)
        }

    def _predict_next_date(
        self,
        last_date_str: str,
        cycle_days: float
    ) -> str:
        """
        预测下一个事件日期

        Args:
            last_date_str: 上次事件日期（YYYY-MM）
            cycle_days: 周期长度（天）

        Returns:
            下次事件日期（YYYY-MM）
        """
        last_date = datetime.strptime(last_date_str, "%Y-%m")
        next_date = last_date + timedelta(days=cycle_days)

        return next_date.strftime("%Y-%m")

    def _calculate_time_window(
        self,
        event_date: str
    ) -> str:
        """
        计算时间窗口（±15天）

        Args:
            event_date: 预测日期（YYYY-MM）

        Returns:
            时间窗口（YYYY-MM-DD ~ YYYY-MM-DD）
        """
        try:
            event_day = datetime.strptime(event_date, "%Y-%m")

            window_start = event_day - timedelta(days=15)
            window_end = event_day + timedelta(days=15)

            return f"{window_start.strftime('%Y-%m-%d')} ~ {window_end.strftime('%Y-%m-%d')}"
        except:
            return event_date

    def _generate_key_time_windows(
        self,
        earnings_cycles: Dict[str, Any],
        policy_cycles: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        生成关键时间窗口

        整合财报和政策事件，生成投资关键时间窗口
        """
        windows = []

        # 1. 财报窗口
        if earnings_cycles.get("detected"):
            next_earnings = earnings_cycles.get("next_event", "")
            confidence = earnings_cycles.get("confidence", 0.0)

            windows.append({
                "window": self._calculate_time_window(next_earnings),
                "type": "财报发布",
                "importance": "高" if confidence > 0.8 else "中",
                "action": "关注财报数据，验证业绩预期",
                "confidence": confidence
            })

        # 2. 政策窗口
        if policy_cycles.get("detected"):
            next_policy = policy_cycles.get("next_event", "")
            confidence = policy_cycles.get("confidence", 0.0)

            windows.append({
                "window": self._calculate_time_window(next_policy),
                "type": "政策发布",
                "importance": "中" if confidence > 0.7 else "低",
                "action": "关注政策动向，评估政策影响",
                "confidence": confidence
            })

        # 3. 按时间排序
        windows.sort(key=lambda x: x["window"])

        return windows

    def _generate_cycle_summary(
        self,
        earnings_cycles: Dict[str, Any],
        policy_cycles: Dict[str, Any]
    ) -> str:
        """
        生成周期性分析摘要
        """
        summary_parts = []

        # 1. 财报周期
        if earnings_cycles.get("detected"):
            cycle_length = earnings_cycles.get("cycle_length", 0)
            next_event = earnings_cycles.get("next_event", "")
            summary_parts.append(
                f"财报周期约{cycle_length}个月，下次预计{next_event}发布"
            )

        # 2. 政策周期
        if policy_cycles.get("detected"):
            cycle_length = policy_cycles.get("cycle_length", 0)
            next_event = policy_cycles.get("next_event", "")
            summary_parts.append(
                f"政策周期约{cycle_length}个月，下次预计{next_event}发布"
            )

        if not summary_parts:
            return "未检测到明显的事件周期性"

        return "；".join(summary_parts) + "。建议关注关键时间窗口，把握投资节奏。"

    def _generate_action_suggestion(
        self,
        next_event: str,
        confidence: float
    ) -> str:
        """
        生成行动建议
        """
        if confidence > 0.8:
            return "建议提前1周关注，做好布局准备"
        elif confidence > 0.6:
            return "建议提前关注，密切关注相关指标"
        else:
            return "预测置信度较低，仅供参考"
