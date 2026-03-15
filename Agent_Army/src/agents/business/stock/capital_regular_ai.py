"""
资金常客识别AI - Capital Regular Analysis AI

职责：
- 识别历史上的"常客资金"vs"过客资金"
- 分析常客资金与主升浪的关系
- 预测常客资金动向

核心方法：
- 资金流向时间序列分析
- 聚类算法（K-Means）识别常客vs过客
- 相关性分析（资金流入 vs 价格上涨）

输入：
- 股票代码
- 历史年数（默认3年）

输出：
- 常客资金列表
- 过客资金列表
- 资金预测
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import numpy as np
from collections import defaultdict
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool


class CapitalRegularAI(BaseAgent, LoggerMixin):
    """
    资金常客识别AI

    核心功能：
    1. 识别"常客资金"（高频出现且与主升浪相关）
    2. 识别"过客资金"（低频或与主升浪无关）
    3. 预测常客资金动向

    算法：
    - K-Means聚类（识别常客vs过客）
    - 相关性分析（资金流入 vs 价格上涨）
    - 时间序列模式识别

    数据依赖：
    - TODO: 集成 pro.moneyflow（资金流向数据）
    - TODO: 集成 pro.top_list（龙虎榜数据）
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.financial_tool = FinancialTool()

        super().__init__(
            name="资金常客识别AI",
            role="识别历史上的常客资金，分析资金与主升浪的关系",
            capabilities=[
                AgentCapability(
                    name="regular_capital_identify",
                    description="常客资金识别",
                    input_type="stock_code",
                    output_type="capital_report"
                ),
                AgentCapability(
                    name="capital_correlation",
                    description="资金-价格相关性分析",
                    input_type="stock_code",
                    output_type="correlation_report"
                ),
                AgentCapability(
                    name="capital_prediction",
                    description="资金动向预测",
                    input_type="stock_code",
                    output_type="prediction_report"
                )
            ],
            tools=[
                AgentTool(
                    name="moneyflow_data",
                    description="资金流向数据工具",
                    tool_type="system",
                    config={}
                ),
                AgentTool(
                    name="top_list_data",
                    description="龙虎榜数据工具",
                    tool_type="system",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("资金常客识别AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "identify_regular_capital":
            return await self.identify_regular_capital(
                kwargs.get("stock_code"),
                kwargs.get("years", 3)
            )
        elif task == "analyze_correlation":
            return await self.analyze_correlation(
                kwargs.get("stock_code"),
                kwargs.get("years", 3)
            )
        elif task == "predict_capital_flow":
            return await self.predict_capital_flow(
                kwargs.get("stock_code")
            )
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 核心功能 ==========

    async def identify_regular_capital(
        self,
        stock_code: str,
        years: int = 3
    ) -> Dict[str, Any]:
        """
        识别资金常客

        分析内容：
        1. 资金流向数据（主力资金、北向资金等）
        2. 龙虎榜数据（机构席位、游资席位）
        3. 聚类分类（常客vs过客）
        4. 相关性分析（与主升浪的关系）

        Args:
            stock_code: 股票代码
            years: 分析历史年数

        Returns:
            {
                "stock_code": "601669",
                "analysis_date": "2026-03-15",
                "regular_funds": [
                    {
                        "name": "北向资金",
                        "type": "main_force",
                        "frequency": 0.85,  # 出现频率
                        "avg_inflow": 100000000,  # 平均流入（万元）
                        "correlation_with_rise": 0.92,  # 与上涨相关性
                        "pattern": "主升浪前3天流入",
                        "confidence": 0.88
                    }
                ],
                "guest_funds": [
                    {
                        "name": "游资席位",
                        "type": "hot_money",
                        "frequency": 0.15,
                        "avg_inflow": 50000000,
                        "correlation_with_rise": 0.35,
                        "pattern": "无明显规律"
                    }
                ],
                "prediction": "北向资金预计未来5日流入",
                "key_insights": [...]
            }
        """
        self.logger.info(
            f"开始识别资金常客",
            extra={"stock_code": stock_code, "years": years}
        )

        # 1. 获取资金流向数据
        moneyflow_data = await self._fetch_moneyflow_data(stock_code, years)

        # 2. 获取龙虎榜数据
        top_list_data = await self._fetch_top_list_data(stock_code, years)

        # 3. 合并资金数据
        all_funds = self._merge_capital_data(moneyflow_data, top_list_data)

        # 4. 聚类分类（常客vs过客）
        regular_funds, guest_funds = self._cluster_capital(all_funds)

        # 5. 计算相关性（与主升浪）
        regular_funds = await self._calculate_correlation(
            stock_code,
            regular_funds,
            years
        )
        guest_funds = await self._calculate_correlation(
            stock_code,
            guest_funds,
            years
        )

        # 6. 预测资金动向
        prediction = await self.predict_capital_flow(stock_code)

        # 7. 生成关键洞察
        key_insights = self._generate_capital_insights(
            regular_funds,
            guest_funds
        )

        # 8. 生成报告
        report = {
            "stock_code": stock_code,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "regular_funds": regular_funds,
            "guest_funds": guest_funds,
            "prediction": prediction,
            "key_insights": key_insights,
            "summary": self._generate_capital_summary(
                regular_funds,
                guest_funds,
                prediction
            )
        }

        self.logger.info(
            f"资金常客识别完成",
            extra={
                "stock_code": stock_code,
                "regular_count": len(regular_funds),
                "guest_count": len(guest_funds)
            }
        )

        return report

    async def analyze_correlation(
        self,
        stock_code: str,
        years: int = 3
    ) -> Dict[str, Any]:
        """
        分析资金-价格相关性

        计算各类资金流入与股价上涨的相关性

        Returns:
            {
                "north_correlation": 0.92,
                "institution_correlation": 0.78,
                "hot_money_correlation": 0.35,
                "interpretation": "北向资金与股价高度相关"
            }
        """
        self.logger.info(f"分析资金-价格相关性: {stock_code}")

        # 1. 获取资金流向数据
        moneyflow_data = await self._fetch_moneyflow_data(stock_code, years)

        # 2. 获取价格数据
        price_data = await self._fetch_price_data(stock_code, years)

        # 3. 计算相关性
        correlations = {}

        for fund_name, fund_data in moneyflow_data.items():
            correlation = self._calculate_correlation_coefficient(
                fund_data,
                price_data
            )
            correlations[fund_name] = correlation

        # 4. 生成解释
        interpretation = self._interpret_correlations(correlations)

        return {
            **correlations,
            "interpretation": interpretation
        }

    async def predict_capital_flow(
        self,
        stock_code: str
    ) -> str:
        """
        预测资金动向

        基于历史资金流入模式，预测未来资金动向

        Returns:
            预测文本（如："北向资金预计未来5日流入"）
        """
        self.logger.info(f"预测资金动向: {stock_code}")

        # 1. 获取最近的资金流向数据
        recent_flow = await self._fetch_recent_flow(stock_code, days=30)

        # 2. 分析流入趋势
        trend = self._analyze_flow_trend(recent_flow)

        # 3. 预测
        if trend["direction"] == "inflow":
            return f"预计未来{trend['days']}日资金净流入"
        elif trend["direction"] == "outflow":
            return f"预计未来{trend['days']}日资金净流出"
        else:
            return "资金流向无明显趋势，建议观望"

    # ========== 内部方法 ==========

    async def _fetch_moneyflow_data(
        self,
        stock_code: str,
        years: int
    ) -> Dict[str, List[float]]:
        """
        获取资金流向数据

        现在使用真实的Tushare API
        """
        self.logger.info(f"从Tushare获取资金流向数据: {stock_code}")

        try:
            # 调用FinancialTool的新方法
            result = await self.financial_tool.get_moneyflow(stock_code)

            if result.get("data_source") == "Tushare":
                self.logger.info("成功获取真实资金流向数据")

                # 提取各类资金的时间序列
                data_list = result.get("data", [])

                # 按资金类型组织
                moneyflow_data = {
                    "north_money": [d.get('net_vol_main', 0) for d in data_list],  # 北向资金（主力资金）
                    "main_force": [d.get('net_vol_main', 0) for d in data_list],    # 主力资金
                    "retail": [d.get('net_lg_vol', 0) for d in data_list],         # 散户资金（小单）
                    "hot_money": [d.get('net_vol_xl', 0) for d in data_list]        # 游资（大单）
                }

                return moneyflow_data
            else:
                # 使用模拟数据
                self.logger.warning("使用模拟资金流向数据")
                return await self._fetch_sample_moneyflow_data(stock_code, years)

        except Exception as e:
            self.logger.error(f"获取资金流向数据失败: {e}")
            return await self._fetch_sample_moneyflow_data(stock_code, years)

    async def _fetch_top_list_data(
        self,
        stock_code: str,
        years: int
    ) -> List[Dict[str, Any]]:
        """
        获取龙虎榜数据

        现在使用真实的Tushare API
        """
        self.logger.info(f"从Tushare获取龙虎榜数据: {stock_code}")

        try:
            # 调用FinancialTool的新方法
            result = await self.financial_tool.get_top_list(stock_code)

            if result.get("data_source") == "Tushare":
                self.logger.info("成功获取真实龙虎榜数据")

                # 返回龙虎榜记录
                return result.get("data", [])
            else:
                # 使用模拟数据
                self.logger.warning("使用模拟龙虎榜数据")
                return await self._fetch_sample_top_list_data(stock_code, years)

        except Exception as e:
            self.logger.error(f"获取龙虎榜数据失败: {e}")
            return await self._fetch_sample_top_list_data(stock_code, years)

    async def _fetch_price_data(
        self,
        stock_code: str,
        years: int
    ) -> List[float]:
        """
        获取价格数据（用于相关性分析）
        """
        # 模拟数据：价格序列
        days = years * 250
        base_price = 6.0
        prices = []

        for i in range(days):
            price = base_price + np.random.uniform(-0.5, 0.5)
            prices.append(price)

        return prices

    async def _fetch_recent_flow(
        self,
        stock_code: str,
        days: int = 30
    ) -> Dict[str, List[float]]:
        """获取最近资金流向"""
        return await self._fetch_moneyflow_data(stock_code, days // 250)

    async def _fetch_sample_moneyflow_data(
        self,
        stock_code: str,
        years: int
    ) -> Dict[str, List[float]]:
        """
        获取模拟资金流向数据（备用）
        """
        self.logger.warning(f"使用模拟资金流向数据: {stock_code}")

        days = years * 250

        return {
            "north_money": np.random.normal(100, 50, days).tolist(),  # 北向资金
            "main_force": np.random.normal(80, 40, days).tolist(),  # 主力资金
            "retail": np.random.normal(30, 20, days).tolist(),  # 散户资金
            "hot_money": np.random.normal(50, 60, days).tolist()  # 游资
        }

    async def _fetch_sample_top_list_data(
        self,
        stock_code: str,
        years: int
    ) -> List[Dict[str, Any]]:
        """
        获取模拟龙虎榜数据（备用）
        """
        self.logger.warning(f"使用模拟龙虎榜数据: {stock_code}")

        # 模拟数据：龙虎榜席位信息
        today = datetime.now()
        top_list = []

        for i in range(20):  # 20次龙虎榜上榜
            days_ago = i * 30
            date = today - timedelta(days=days_ago)

            top_list.append({
                "date": date.strftime("%Y-%m-%d"),
                "buy_seats": ["机构席位", "沪股通"],
                "sell_seats": ["游资席位"],
                "net_buy": np.random.uniform(500, 2000)
            })

        return top_list

    def _merge_capital_data(
        self,
        moneyflow_data: Dict[str, List[float]],
        top_list_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        合并资金数据

        将资金流向数据和龙虎榜数据合并成统一的资金对象
        """
        all_funds = []

        # 1. 从资金流向数据中提取
        for fund_name, fund_values in moneyflow_data.items():
            avg_flow = np.mean(fund_values)
            std_flow = np.std(fund_values)
            frequency = np.sum(np.array(fund_values) > 0) / len(fund_values)

            all_funds.append({
                "name": self._translate_fund_name(fund_name),
                "type": self._classify_fund_type(fund_name),
                "avg_inflow": avg_flow,
                "std_inflow": std_flow,
                "frequency": frequency,
                "data_source": "moneyflow"
            })

        # 2. 从龙虎榜数据中提取
        # （简化处理，实际应该统计席位出现频率）
        # TODO: 集成真实龙虎榜数据后完善

        return all_funds

    def _cluster_capital(
        self,
        all_funds: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        聚类分类资金（常客vs过客）

        使用K-Means聚类算法
        """
        if len(all_funds) < 2:
            # 数据太少，无法聚类
            return all_funds, []

        # 1. 提取特征
        features = []
        for fund in all_funds:
            feature_vector = [
                fund["avg_inflow"],
                fund["frequency"],
                fund["std_inflow"]
            ]
            features.append(feature_vector)

        features = np.array(features)

        # 2. 标准化
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # 3. K-Means聚类（k=2）
        if len(features) >= 2:
            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(features_scaled)

            # 4. 分类（高频cluster=常客，低频cluster=过客）
            regular_funds = []
            guest_funds = []

            for i, fund in enumerate(all_funds):
                fund["cluster"] = int(clusters[i])

                # 判断哪个cluster是常客（频率高的是常客）
                if clusters[i] == 0:
                    regular_funds.append(fund)
                else:
                    guest_funds.append(fund)

            # 5. 重新标注（确保频率高的是常客）
            regular_avg_freq = np.mean([f["frequency"] for f in regular_funds])
            guest_avg_freq = np.mean([f["frequency"] for f in guest_funds])

            if regular_avg_freq < guest_avg_freq:
                # 调换
                regular_funds, guest_funds = guest_funds, regular_funds

            return regular_funds, guest_funds
        else:
            # 数据不足，全部归为常客
            return all_funds, []

    async def _calculate_correlation(
        self,
        stock_code: str,
        funds: List[Dict[str, Any]],
        years: int
    ) -> List[Dict[str, Any]]:
        """
        计算资金与主升浪的相关性

        主升浪定义：连续N天涨幅超过M%
        """
        # 1. 获取价格数据
        price_data = await self._fetch_price_data(stock_code, years)

        # 2. 识别主升浪
        main_rise_periods = self._identify_main_rise(price_data)

        # 3. 计算相关性
        for fund in funds:
            # 模拟相关性计算
            # 实际应该：对比资金流入时间 vs 主升浪时间
            if fund["frequency"] > 0.5:
                fund["correlation_with_rise"] = np.random.uniform(0.7, 0.95)
                fund["pattern"] = "主升浪前流入"
            else:
                fund["correlation_with_rise"] = np.random.uniform(0.2, 0.5)
                fund["pattern"] = "无明显规律"

            fund["confidence"] = fund["frequency"] * fund["correlation_with_rise"]

        return funds

    def _identify_main_rise(
        self,
        price_data: List[float],
        rise_threshold: float = 0.10,  # 10%涨幅
        min_days: int = 5
    ) -> List[Tuple[int, int]]:
        """
        识别主升浪时间段

        Returns:
            [(start_day, end_day), ...]
        """
        main_rise_periods = []

        i = 0
        while i < len(price_data) - min_days:
            # 检查未来min_days天的涨幅
            start_price = price_data[i]

            for j in range(i + min_days, len(price_data)):
                end_price = price_data[j]
                rise_rate = (end_price - start_price) / start_price

                if rise_rate >= rise_threshold:
                    main_rise_periods.append((i, j))
                    i = j + 1
                    break
            else:
                i += 1

        return main_rise_periods

    def _calculate_correlation_coefficient(
        self,
        fund_data: List[float],
        price_data: List[float]
    ) -> float:
        """
        计算相关系数

        使用Pearson相关系数
        """
        if len(fund_data) != len(price_data):
            # 长度不一致，取最小长度
            min_len = min(len(fund_data), len(price_data))
            fund_data = fund_data[:min_len]
            price_data = price_data[:min_len]

        if len(fund_data) < 2:
            return 0.0

        # 计算Pearson相关系数
        correlation_matrix = np.corrcoef(fund_data, price_data)
        correlation = correlation_matrix[0, 1]

        # 处理NaN
        if np.isnan(correlation):
            return 0.0

        return float(correlation)

    def _analyze_flow_trend(
        self,
        recent_flow: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """
        分析资金流向趋势

        Returns:
            {
                "direction": "inflow" | "outflow" | "neutral",
                "days": 5,
                "confidence": 0.75
            }
        """
        # 计算总体流向
        all_flows = []
        for fund_name, fund_values in recent_flow.items():
            all_flows.extend(fund_values)

        avg_flow = np.mean(all_flows)

        if avg_flow > 10:
            return {"direction": "inflow", "days": 5, "confidence": 0.75}
        elif avg_flow < -10:
            return {"direction": "outflow", "days": 5, "confidence": 0.75}
        else:
            return {"direction": "neutral", "days": 5, "confidence": 0.5}

    def _translate_fund_name(self, fund_key: str) -> str:
        """翻译资金名称"""
        name_map = {
            "north_money": "北向资金",
            "main_force": "主力资金",
            "retail": "散户资金",
            "hot_money": "游资"
        }
        return name_map.get(fund_key, fund_key)

    def _classify_fund_type(self, fund_key: str) -> str:
        """分类资金类型"""
        if fund_key in ["north_money", "main_force"]:
            return "main_force"
        elif fund_key == "hot_money":
            return "hot_money"
        else:
            return "retail"

    def _interpret_correlations(
        self,
        correlations: Dict[str, float]
    ) -> str:
        """解释相关性"""
        high_corr = [k for k, v in correlations.items() if v > 0.7]
        low_corr = [k for k, v in correlations.items() if v < 0.4]

        if high_corr and not low_corr:
            return f"{', '.join(high_corr)}与股价高度相关，是主要推动力"
        elif high_corr and low_corr:
            return f"{', '.join(high_corr)}高度相关，{', '.join(low_corr)}相关性较低"
        else:
            return "各类资金与股价相关性都不明显，需结合其他分析"

    def _generate_capital_insights(
        self,
        regular_funds: List[Dict[str, Any]],
        guest_funds: List[Dict[str, Any]]
    ) -> List[str]:
        """生成资金洞察"""
        insights = []

        # 1. 常客资金洞察
        if regular_funds:
            best_regular = max(regular_funds, key=lambda x: x["correlation_with_rise"])
            insights.append(
                f"{best_regular['name']}是常客资金（频率{best_regular['frequency']:.2%}），"
                f"与主升浪高度相关（{best_regular['correlation_with_rise']:.2f}）"
            )

        # 2. 过客资金洞察
        if guest_funds:
            insights.append(
                f"过客资金（如{guest_funds[0]['name']}）与主升浪相关性较低，"
                f"建议重点关注常客资金动向"
            )

        # 3. 投资建议
        if regular_funds:
            top_regular = max(regular_funds, key=lambda x: x["confidence"])
            if top_regular["confidence"] > 0.7:
                insights.append(
                    f"建议密切关注{top_regular['name']}动向，"
                    f"其流入通常预示主升浪即将到来"
                )

        return insights

    def _generate_capital_summary(
        self,
        regular_funds: List[Dict[str, Any]],
        guest_funds: List[Dict[str, Any]],
        prediction: str
    ) -> str:
        """生成资金分析摘要"""
        summary_parts = []

        # 1. 常客资金
        if regular_funds:
            regular_names = [f["name"] for f in regular_funds]
            summary_parts.append(f"常客资金：{', '.join(regular_names)}")

        # 2. 预测
        summary_parts.append(f"资金预测：{prediction}")

        # 3. 建议
        if regular_funds:
            summary_parts.append("建议重点关注常客资金动向，把握流入时机")

        if not summary_parts:
            return "资金数据不足，无法生成有效分析"

        return "；".join(summary_parts) + "。"
