"""
筹码分析AI - Chip Distribution Analysis AI

个股挖掘军团核心成员

职责：
1. 筹码分布计算 - 基于历史价格和成交量计算筹码分布
2. 筹码峰识别 - 识别筹码集中的价格区间（压力位/支撑位）
3. 突破难度评估 - 评估突破上方筹码峰的难度
4. 换手率分析 - 分析换手率和筹码转移

核心功能：
- 计算筹码分布曲线
- 识别筹码峰（峰值、价格区间、筹码占比）
- 计算压力位（上方筹码峰）
- 计算支撑位（下方筹码峰）
- 评估突破难度（基于筹码峰强度）

使用工具库：
- Tushare API (daily接口获取历史价格和成交量)
- NumPy (数值计算)
- Pandas (数据处理)

依赖安装：
pip install tushare numpy pandas

创建日期: 2026-03-15
版本: v1.0
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from src.agents.business.base_business_agent import BusinessAgent
from src.core.base_agent import AgentCapability, AgentTool
from src.core.logger import LoggerMixin


class ChipAnalysisAI(BusinessAgent):
    """
    筹码分析AI - 专门分析筹码分布和筹码峰

    核心能力：
    1. 筹码分布计算 - 基于历史成交量和价格计算筹码分布
    2. 筹码峰识别 - 自动识别筹码集中区间（压力/支撑）
    3. 突破难度评估 - 评估突破筹码峰所需的成交量
    4. 换手率分析 - 分析筹码转移和换手情况

    使用场景：
    - 判断压力位：上方筹码峰 = 压力位
    - 判断支撑位：下方筹码峰 = 支撑位
    - 判断突破难度：筹码峰强度越大，突破越难
    - 判断主升浪：突破强筹码峰 = 主升浪开始
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="筹码分析AI",
            role="分析筹码分布，识别筹码峰和压力支撑位",
            corps="stock_mining",
            analysis_type="chip_distribution",
            capabilities=[
                AgentCapability(
                    name="chip_distribution",
                    description="筹码分布计算",
                    input_schema={
                        "stock_code": "股票代码",
                        "days": "统计天数（默认365天）",
                        "bins": "价格分区数（默认50）"
                    },
                    output_type="chip_distribution_curve"
                ),
                AgentCapability(
                    name="chip_peaks",
                    description="筹码峰识别",
                    input_schema={
                        "stock_code": "股票代码",
                        "num_peaks": "识别筹码峰数量（默认5个）"
                    },
                    output_type="chip_peaks_list"
                ),
                AgentCapability(
                    name="resistance_from_chip",
                    description="基于筹码分析计算压力位",
                    input_schema={
                        "stock_code": "股票代码"
                    },
                    output_type="resistance_levels"
                ),
                AgentCapability(
                    name="breakthrough_difficulty",
                    description="评估突破难度",
                    input_schema={
                        "stock_code": "股票代码",
                        "target_price": "目标价格"
                    },
                    output_type="difficulty_score"
                ),
            ],
            tools=[
                AgentTool(
                    name="TushareAPI",
                    description="获取历史价格和成交量数据",
                    required_params=["stock_code", "start_date", "end_date"]
                ),
            ]
        )

        self.logger.info("筹码分析AI初始化完成")

    async def analyze(
        self,
        stock_code: str,
        days: int = 365,
        bins: int = 50
    ) -> Dict[str, Any]:
        """
        完整的筹码分析

        Args:
            stock_code: 股票代码
            days: 统计天数（默认365天 = 1年）
            bins: 价格分区数（默认50个区间）

        Returns:
            完整的筹码分析结果:
            {
                "stock_code": "601669",
                "current_price": 5.5,
                "chip_distribution": [...],  # 筹码分布曲线
                "support_levels": [...],     # 支撑位列表
                "resistance_levels": [...],  # 压力位列表
                "chip_peaks": [...],         # 筹码峰列表
                "breakthrough_difficulty": "中",
                "main_rise_signal": False    # 是否突破主筹码峰
            }
        """
        self.logger.info(f"开始筹码分析", extra={'stock_code': stock_code, 'days': days})

        try:
            # 1. 获取历史数据
            historical_data = await self._get_historical_data(stock_code, days)

            if historical_data is None or len(historical_data) == 0:
                self.logger.warning(f"无法获取历史数据: {stock_code}")
                return self._get_empty_result(stock_code)

            current_price = float(historical_data.iloc[-1]['close'])

            # 2. 计算筹码分布
            chip_distribution = self._calculate_chip_distribution(
                historical_data, bins, current_price
            )

            # 3. 识别筹码峰
            chip_peaks = self._identify_chip_peaks(chip_distribution)

            # 4. 计算压力位（上方筹码峰）
            resistance_levels = self._calculate_resistance_levels(
                chip_peaks, current_price
            )

            # 5. 计算支撑位（下方筹码峰）
            support_levels = self._calculate_support_levels(
                chip_peaks, current_price
            )

            # 6. 评估突破难度
            breakthrough_difficulty = self._evaluate_breakthrough_difficulty(
                resistance_levels, current_price
            )

            # 7. 判断主升浪信号
            main_rise_signal = self._check_main_rise_signal(
                historical_data, chip_peaks, current_price
            )

            result = {
                'stock_code': stock_code,
                'current_price': current_price,
                'chip_distribution': chip_distribution,
                'chip_peaks': chip_peaks,
                'support_levels': support_levels,
                'resistance_levels': resistance_levels,
                'breakthrough_difficulty': breakthrough_difficulty,
                'main_rise_signal': main_rise_signal,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            self.logger.info(
                f"筹码分析完成",
                extra={
                    'stock_code': stock_code,
                    'resistance_count': len(resistance_levels),
                    'support_count': len(support_levels),
                    'difficulty': breakthrough_difficulty
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"筹码分析失败: {e}", extra={'stock_code': stock_code})
            return self._get_empty_result(stock_code)

    async def _get_historical_data(
        self,
        stock_code: str,
        days: int
    ) -> Optional[pd.DataFrame]:
        """
        获取历史价格和成交量数据

        Args:
            stock_code: 股票代码
            days: 获取天数

        Returns:
            DataFrame包含列: trade_date, open, high, low, close, vol, amount
        """
        try:
            import tushare as ts
            import os

            api_key = os.getenv("TUSHARE_API_KEY", "")
            if not api_key:
                self.logger.warning("TUSHARE_API_KEY未配置，使用模拟数据")
                return self._get_mock_data(stock_code, days)

            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            def call_tushare():
                pro = ts.pro_api(api_key)

                # 转换股票代码格式
                if stock_code.startswith('6'):
                    ts_code = f"{stock_code}.SH"
                else:
                    ts_code = f"{stock_code}.SZ"

                # 获取日线数据
                df = pro.daily(
                    ts_code=ts_code,
                    start_date=start_date.strftime('%Y%m%d'),
                    end_date=end_date.strftime('%Y%m%d')
                )

                return df

            # 调用Tushare API
            import asyncio
            df = await asyncio.get_event_loop().run_in_executor(None, call_tushare)

            if df.empty:
                self.logger.warning(f"Tushare返回空数据，使用模拟数据")
                return self._get_mock_data(stock_code, days)

            # 按日期排序
            df = df.sort_values('trade_date')

            self.logger.info(f"获取历史数据成功: {len(df)}条")

            return df

        except Exception as e:
            self.logger.warning(f"获取历史数据失败: {e}，使用模拟数据")
            return self._get_mock_data(stock_code, days)

    def _get_mock_data(self, stock_code: str, days: int) -> pd.DataFrame:
        """
        生成模拟历史数据（用于测试）

        Args:
            stock_code: 股票代码
            days: 天数

        Returns:
            模拟的历史数据DataFrame
        """
        np.random.seed(42)

        dates = pd.date_range(
            end=datetime.now(),
            periods=days,
            freq='D'
        )

        # 模拟价格走势（随机游走）
        base_price = 5.5
        returns = np.random.normal(0, 0.02, days)
        prices = base_price * (1 + returns).cumprod()

        # 模拟成交量
        volumes = np.random.randint(100000, 1000000, days)

        df = pd.DataFrame({
            'trade_date': dates.strftime('%Y%m%d'),
            'open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
            'high': prices * (1 + np.random.uniform(0, 0.03, days)),
            'low': prices * (1 - np.random.uniform(0, 0.03, days)),
            'close': prices,
            'vol': volumes,
            'amount': prices * volumes
        })

        return df

    def _calculate_chip_distribution(
        self,
        historical_data: pd.DataFrame,
        bins: int,
        current_price: float
    ) -> List[Dict[str, Any]]:
        """
        计算筹码分布

        核心逻辑：
        1. 将价格区间分成bins个区间
        2. 计算每个价格区间的累计成交量（筹码）
        3. 生成筹码分布曲线

        Args:
            historical_data: 历史数据
            bins: 价格分区数
            current_price: 当前价格

        Returns:
            筹码分布列表:
            [
                {"price": 5.0, "chip_percentage": 15.5},
                {"price": 5.2, "chip_percentage": 20.3},
                ...
            ]
        """
        # 获取价格范围
        min_price = historical_data['low'].min()
        max_price = historical_data['high'].max()

        # 创建价格区间
        price_bins = np.linspace(min_price, max_price, bins)

        # 计算每个价格区间的筹码（累计成交量）
        chip_distribution = []

        for i in range(len(price_bins) - 1):
            price_low = price_bins[i]
            price_high = price_bins[i + 1]
            price_mid = (price_low + price_high) / 2

            # 筛选在这个价格区间内的交易日
            mask = (
                (historical_data['low'] <= price_high) &
                (historical_data['high'] >= price_low)
            )

            # 计算累计成交量（筹码）
            total_volume = historical_data[mask]['vol'].sum()

            # 计算筹码占比
            chip_percentage = (total_volume / historical_data['vol'].sum()) * 100

            chip_distribution.append({
                'price': round(price_mid, 2),
                'price_range': f"{price_low:.2f}-{price_high:.2f}",
                'chip_percentage': round(chip_percentage, 2),
                'volume': int(total_volume)
            })

        return chip_distribution

    def _identify_chip_peaks(
        self,
        chip_distribution: List[Dict[str, Any]],
        num_peaks: int = 5
    ) -> List[Dict[str, Any]]:
        """
        识别筹码峰

        核心逻辑：
        1. 使用scipy.signal.find_peaks查找峰值
        2. 按筹码占比排序，返回前num_peaks个筹码峰

        Args:
            chip_distribution: 筹码分布
            num_peaks: 返回筹码峰数量

        Returns:
            筹码峰列表:
            [
                {
                    "price": 6.5,
                    "chip_percentage": 25.3,
                    "strength": "强",
                    "type": "压力位"  # 或 "支撑位"
                },
                ...
            ]
        """
        # 提取筹码占比数据
        percentages = [item['chip_percentage'] for item in chip_distribution]

        # 使用scipy查找峰值
        peaks, properties = find_peaks(
            percentages,
            height=np.mean(percentages),  # 峰值高度必须大于平均值
            distance=3  # 峰值之间至少间隔3个点
        )

        # 提取筹码峰信息
        chip_peaks = []
        for peak_idx in peaks:
            peak_data = chip_distribution[peak_idx]
            chip_peaks.append({
                'price': peak_data['price'],
                'price_range': peak_data['price_range'],
                'chip_percentage': peak_data['chip_percentage'],
                'volume': peak_data['volume'],
                'strength': self._get_strength_level(peak_data['chip_percentage'])
            })

        # 按筹码占比排序，返回前num_peaks个
        chip_peaks = sorted(
            chip_peaks,
            key=lambda x: x['chip_percentage'],
            reverse=True
        )[:num_peaks]

        return chip_peaks

    def _get_strength_level(self, chip_percentage: float) -> str:
        """
        根据筹码占比判断筹码峰强度

        Args:
            chip_percentage: 筹码占比

        Returns:
            强度等级: 强/中/弱
        """
        if chip_percentage > 20:
            return "强"
        elif chip_percentage > 10:
            return "中"
        else:
            return "弱"

    def _calculate_resistance_levels(
        self,
        chip_peaks: List[Dict[str, Any]],
        current_price: float
    ) -> List[Dict[str, Any]]:
        """
        计算压力位（上方筹码峰）

        Args:
            chip_peaks: 筹码峰列表
            current_price: 当前价格

        Returns:
            压力位列表（按价格升序排序）
        """
        # 筛选当前价上方的筹码峰
        resistance_peaks = [
            peak for peak in chip_peaks
            if peak['price'] > current_price
        ]

        # 按价格升序排序
        resistance_peaks = sorted(
            resistance_peaks,
            key=lambda x: x['price']
        )

        # 添加类型标记
        for peak in resistance_peaks:
            peak['type'] = '压力位'

        return resistance_peaks

    def _calculate_support_levels(
        self,
        chip_peaks: List[Dict[str, Any]],
        current_price: float
    ) -> List[Dict[str, Any]]:
        """
        计算支撑位（下方筹码峰）

        Args:
            chip_peaks: 筹码峰列表
            current_price: 当前价格

        Returns:
            支撑位列表（按价格降序排序，最近的在前）
        """
        # 筛选当前价下方的筹码峰
        support_peaks = [
            peak for peak in chip_peaks
            if peak['price'] < current_price
        ]

        # 按价格降序排序（最近的支撑位在前）
        support_peaks = sorted(
            support_peaks,
            key=lambda x: x['price'],
            reverse=True
        )

        # 添加类型标记
        for peak in support_peaks:
            peak['type'] = '支撑位'

        return support_peaks

    def _evaluate_breakthrough_difficulty(
        self,
        resistance_levels: List[Dict[str, Any]],
        current_price: float
    ) -> str:
        """
        评估突破难度

        核心逻辑：
        1. 没有上方筹码峰 = 无压力，容易突破
        2. 1个弱筹码峰 = 难度低
        3. 多个强筹码峰 = 难度高

        Args:
            resistance_levels: 压力位列表
            current_price: 当前价格

        Returns:
            难度等级: 容易/中/高/极高
        """
        if len(resistance_levels) == 0:
            return "容易"

        # 计算筹码峰强度总分
        strength_score = 0
        for level in resistance_levels:
            if level['strength'] == '强':
                strength_score += 3
            elif level['strength'] == '中':
                strength_score += 2
            else:
                strength_score += 1

        # 计算距离最近压力位的距离
        if len(resistance_levels) > 0:
            distance_ratio = (resistance_levels[0]['price'] - current_price) / current_price
        else:
            distance_ratio = 0

        # 综合评估
        if strength_score >= 6 or len(resistance_levels) >= 3:
            return "极高"
        elif strength_score >= 4 or len(resistance_levels) >= 2:
            return "高"
        elif strength_score >= 2:
            return "中"
        else:
            return "容易"

    def _check_main_rise_signal(
        self,
        historical_data: pd.DataFrame,
        chip_peaks: List[Dict[str, Any]],
        current_price: float
    ) -> Dict[str, Any]:
        """
        判断主升浪信号

        核心逻辑：
        1. 如果股价突破强筹码峰 = 主升浪信号
        2. 如果成交量放大 + 突破压力位 = 主升浪确认

        Args:
            historical_data: 历史数据
            chip_peaks: 筹码峰列表
            current_price: 当前价格

        Returns:
            主升浪信号:
            {
                "has_signal": False,
                "reason": "未突破强筹码峰",
                "confidence": "低"
            }
        """
        # 获取最近的强筹码峰
        strong_peaks = [
            peak for peak in chip_peaks
            if peak['strength'] == '强' and peak['price'] > current_price
        ]

        if len(strong_peaks) == 0:
            # 没有上方强筹码峰，可能已经在主升浪中
            return {
                'has_signal': True,
                'reason': '无上方强筹码峰，可能处于主升浪中',
                'confidence': '中'
            }

        # 检查是否接近最近的压力位
        nearest_resistance = strong_peaks[0]
        distance_ratio = (nearest_resistance['price'] - current_price) / current_price

        if distance_ratio < 0.05:  # 距离压力位小于5%
            # 检查最近几天的成交量
            recent_volumes = historical_data.tail(5)['vol'].values
            avg_volume = np.mean(recent_volumes)

            # 如果成交量放大（比平均高50%）
            if recent_volumes[-1] > avg_volume * 1.5:
                return {
                    'has_signal': True,
                    'reason': f'接近强筹码峰({nearest_resistance["price"]}元)，成交量放大',
                    'confidence': '高'
                }
            else:
                return {
                    'has_signal': False,
                    'reason': f'接近强筹码峰({nearest_resistance["price"]}元)，但成交量不足',
                    'confidence': '中'
                }
        else:
            return {
                'has_signal': False,
                'reason': f'距离强筹码峰({nearest_resistance["price"]}元)较远({distance_ratio*100:.1f}%)',
                'confidence': '低'
            }

    def _get_empty_result(self, stock_code: str) -> Dict[str, Any]:
        """
        返回空结果（分析失败时）

        Args:
            stock_code: 股票代码

        Returns:
            空的筹码分析结果
        """
        return {
            'stock_code': stock_code,
            'current_price': 0,
            'chip_distribution': [],
            'chip_peaks': [],
            'support_levels': [],
            'resistance_levels': [],
            'breakthrough_difficulty': '未知',
            'main_rise_signal': {
                'has_signal': False,
                'reason': '数据不足',
                'confidence': '无'
            },
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def format_chip_report(self, analysis_result: Dict[str, Any]) -> str:
        """
        格式化筹码分析报告

        Args:
            analysis_result: 筹码分析结果

        Returns:
            格式化的报告文本
        """
        lines = []
        lines.append("=" * 80)
        lines.append("筹码分析报告")
        lines.append("=" * 80)
        lines.append(f"股票代码: {analysis_result['stock_code']}")
        lines.append(f"当前价格: {analysis_result['current_price']:.2f} 元")
        lines.append(f"分析时间: {analysis_result['analysis_date']}")
        lines.append("")

        # 压力位
        if analysis_result['resistance_levels']:
            lines.append("-" * 80)
            lines.append("压力位（上方筹码峰）:")
            for i, level in enumerate(analysis_result['resistance_levels'][:3], 1):
                lines.append(f"  压力位{i}: {level['price']:.2f} 元")
                lines.append(f"    - 筹码占比: {level['chip_percentage']:.1f}%")
                lines.append(f"    - 强度: {level['strength']}")
            lines.append("")

        # 支撑位
        if analysis_result['support_levels']:
            lines.append("-" * 80)
            lines.append("支撑位（下方筹码峰）:")
            for i, level in enumerate(analysis_result['support_levels'][:3], 1):
                lines.append(f"  支撑位{i}: {level['price']:.2f} 元")
                lines.append(f"    - 筹码占比: {level['chip_percentage']:.1f}%")
                lines.append(f"    - 强度: {level['strength']}")
            lines.append("")

        # 突破难度
        lines.append("-" * 80)
        lines.append(f"突破难度: {analysis_result['breakthrough_difficulty']}")
        lines.append("")

        # 主升浪信号
        signal = analysis_result['main_rise_signal']
        lines.append("-" * 80)
        lines.append(f"主升浪信号: {'是' if signal['has_signal'] else '否'}")
        lines.append(f"  - 理由: {signal['reason']}")
        lines.append(f"  - 置信度: {signal['confidence']}")
        lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)
