"""
财务健康AI - Financial Health AI

职责：
- 分析企业财务健康度
- 评估财务风险等级
- 识别财务异常信号

输入：
- 股票代码
- 时间范围

输出：
- 财务健康度评分（0-100）
- 风险等级评估
- 财务异常信号
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools import FinancialTool


class FinancialHealthAI(BaseAgent, LoggerMixin):
    """财务健康AI - 分析企业财务健康度"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.financial_tool = FinancialTool()

        super().__init__(
            name="财务健康AI",
            role="分析企业财务健康度，评估财务风险等级，识别财务异常信号",
            capabilities=[
                AgentCapability(
                    name="financial_health_analysis",
                    description="分析财务健康度",
                    input_type="stock_code",
                    output_type="health_report"
                ),
                AgentCapability(
                    name="risk_assessment",
                    description="评估财务风险",
                    input_type="stock_code",
                    output_type="risk_report"
                ),
                AgentCapability(
                    name="anomaly_detection",
                    description="识别财务异常",
                    input_type="stock_code",
                    output_type="anomaly_report"
                )
            ],
            tools=[
                AgentTool(
                    name="financial_analyzer",
                    description="财务数据分析工具",
                    tool_type="system",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("财务健康AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        if task == "analyze_health":
            return await self.analyze_health(
                kwargs.get("stock_code"),
                kwargs.get("years", 3)
            )
        elif task == "assess_risk":
            return await self.assess_risk(
                kwargs.get("stock_code")
            )
        elif task == "detect_anomaly":
            return await self.detect_anomaly(
                kwargs.get("stock_code")
            )
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 核心功能 ==========

    async def analyze_health(
        self,
        stock_code: str,
        years: int = 3
    ) -> Dict[str, Any]:
        """分析财务健康度"""
        self.logger.info(
            f"开始分析财务健康度",
            extra={"stock_code": stock_code, "years": years}
        )

        # 1. 获取财务数据
        financial_data = await self._fetch_financial_data(stock_code, years)

        # 2. 计算健康度指标
        health_metrics = self._calculate_health_metrics(financial_data)

        # 3. 生成健康度评分
        health_score = self._calculate_health_score(health_metrics)

        # 4. 生成报告
        report = {
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat(),
            "analysis_period": f"{years}年",
            "health_score": health_score,
            "health_grade": self._get_health_grade(health_score),
            "health_metrics": health_metrics,
            "summary": self._generate_health_summary(health_score, health_metrics),
            "recommendation": self._generate_health_recommendation(health_score)
        }

        self.logger.info(
            f"财务健康度分析完成",
            extra={"stock_code": stock_code, "health_score": health_score}
        )

        return report

    async def assess_risk(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """评估财务风险"""
        self.logger.info(f"评估财务风险", extra={"stock_code": stock_code})

        # 获取财务数据
        financial_data = await self._fetch_financial_data(stock_code, 3)

        # 分析风险因素
        risk_factors = self._analyze_risk_factors(financial_data)

        # 计算风险等级
        risk_level = self._calculate_risk_level(risk_factors)

        return {
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat(),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "warning_signals": self._extract_warnings(risk_factors),
            "summary": f"财务风险等级：{risk_level}",
            "recommendation": self._generate_risk_recommendation(risk_level)
        }

    async def detect_anomaly(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """识别财务异常"""
        self.logger.info(f"识别财务异常", extra={"stock_code": stock_code})

        # 获取财务数据
        financial_data = await self._fetch_financial_data(stock_code, 3)

        # 检测异常
        anomalies = self._detect_financial_anomalies(financial_data)

        return {
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat(),
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "severity": self._assess_anomaly_severity(anomalies),
            "summary": f"发现{len(anomalies)}个财务异常信号",
            "recommendation": self._generate_anomaly_recommendation(anomalies)
        }

    # ========== 辅助方法 ==========

    async def _fetch_financial_data(
        self,
        stock_code: str,
        years: int
    ) -> Dict[str, Any]:
        """获取财务数据（模拟）"""
        import random

        # 模拟财务指标
        return {
            "资产负债率": round(random.uniform(30, 70), 2),
            "流动比率": round(random.uniform(0.8, 2.5), 2),
            "速动比率": round(random.uniform(0.5, 2.0), 2),
            "毛利率": round(random.uniform(10, 50), 2),
            "净利率": round(random.uniform(2, 20), 2),
            "ROE": round(random.uniform(5, 25), 2),
            "营收增长率": round(random.uniform(-10, 30), 2),
            "净利润增长率": round(random.uniform(-20, 40), 2),
            "经营现金流": round(random.uniform(-1000, 5000), 2),
            "应收账款周转率": round(random.uniform(3, 15), 2)
        }

    def _calculate_health_metrics(
        self,
        financial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算健康度指标"""
        metrics = {}

        # 偿债能力
        debt_ratio = financial_data["资产负债率"]
        current_ratio = financial_data["流动比率"]

        if debt_ratio < 50 and current_ratio > 1.5:
            solvency = "优秀"
            solvency_score = 90
        elif debt_ratio < 60 and current_ratio > 1.2:
            solvency = "良好"
            solvency_score = 75
        elif debt_ratio < 70 and current_ratio > 1.0:
            solvency = "一般"
            solvency_score = 60
        else:
            solvency = "较差"
            solvency_score = 40

        metrics["偿债能力"] = {
            "status": solvency,
            "score": solvency_score,
            "资产负债率": debt_ratio,
            "流动比率": current_ratio
        }

        # 盈利能力
        net_margin = financial_data["净利率"]
        roe = financial_data["ROE"]

        if net_margin > 15 and roe > 15:
            profitability = "优秀"
            profitability_score = 90
        elif net_margin > 10 and roe > 10:
            profitability = "良好"
            profitability_score = 75
        elif net_margin > 5 and roe > 5:
            profitability = "一般"
            profitability_score = 60
        else:
            profitability = "较差"
            profitability_score = 40

        metrics["盈利能力"] = {
            "status": profitability,
            "score": profitability_score,
            "净利率": net_margin,
            "ROE": roe
        }

        # 成长能力
        revenue_growth = financial_data["营收增长率"]
        profit_growth = financial_data["净利润增长率"]

        if revenue_growth > 20 and profit_growth > 20:
            growth = "优秀"
            growth_score = 90
        elif revenue_growth > 10 and profit_growth > 10:
            growth = "良好"
            growth_score = 75
        elif revenue_growth > 0 and profit_growth > 0:
            growth = "一般"
            growth_score = 60
        else:
            growth = "较差"
            growth_score = 40

        metrics["成长能力"] = {
            "status": growth,
            "score": growth_score,
            "营收增长率": revenue_growth,
            "利润增长率": profit_growth
        }

        # 现金流
        cash_flow = financial_data["经营现金流"]

        if cash_flow > 2000:
            cash = "优秀"
            cash_score = 90
        elif cash_flow > 1000:
            cash = "良好"
            cash_score = 75
        elif cash_flow > 0:
            cash = "一般"
            cash_score = 60
        else:
            cash = "较差"
            cash_score = 40

        metrics["现金流"] = {
            "status": cash,
            "score": cash_score,
            "经营现金流": cash_flow
        }

        return metrics

    def _calculate_health_score(
        self,
        health_metrics: Dict[str, Any]
    ) -> float:
        """计算综合健康度评分"""
        weights = {
            "偿债能力": 0.25,
            "盈利能力": 0.30,
            "成长能力": 0.25,
            "现金流": 0.20
        }

        total_score = 0
        for metric_name, weight in weights.items():
            score = health_metrics[metric_name]["score"]
            total_score += score * weight

        return round(total_score, 2)

    def _get_health_grade(self, score: float) -> str:
        """获取健康度等级"""
        if score >= 85:
            return "A+"
        elif score >= 75:
            return "A"
        elif score >= 65:
            return "B"
        elif score >= 55:
            return "C"
        else:
            return "D"

    def _analyze_risk_factors(
        self,
        financial_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """分析风险因素"""
        risks = []

        # 资产负债率过高
        if financial_data["资产负债率"] > 70:
            risks.append({
                "type": "高负债",
                "severity": "高",
                "description": f"资产负债率{financial_data['资产负债率']:.1f}%，超过70%警戒线"
            })

        # 流动比率过低
        if financial_data["流动比率"] < 1.0:
            risks.append({
                "type": "流动性风险",
                "severity": "高",
                "description": f"流动比率{financial_data['流动比率']:.2f}，低于1.0存在偿债风险"
            })

        # 营收负增长
        if financial_data["营收增长率"] < 0:
            risks.append({
                "type": "营收下滑",
                "severity": "中",
                "description": f"营收增长率{financial_data['营收增长率']:.1f}%，出现负增长"
            })

        # 净利润负增长
        if financial_data["净利润增长率"] < -10:
            risks.append({
                "type": "利润下滑",
                "severity": "高",
                "description": f"净利润增长率{financial_data['净利润增长率']:.1f}%，大幅下滑"
            })

        # 现金流为负
        if financial_data["经营现金流"] < 0:
            risks.append({
                "type": "现金流风险",
                "severity": "高",
                "description": f"经营现金流{financial_data['经营现金流']:.0f}万元，为负值"
            })

        return risks

    def _calculate_risk_level(self, risk_factors: List[Dict[str, Any]]) -> str:
        """计算风险等级"""
        high_count = sum(1 for r in risk_factors if r["severity"] == "高")
        medium_count = sum(1 for r in risk_factors if r["severity"] == "中")

        if high_count >= 3:
            return "极高风险"
        elif high_count >= 2:
            return "高风险"
        elif high_count >= 1 or medium_count >= 2:
            return "中风险"
        elif medium_count >= 1:
            return "低风险"
        else:
            return "安全"

    def _extract_warnings(self, risk_factors: List[Dict[str, Any]]) -> List[str]:
        """提取警告信号"""
        return [r["description"] for r in risk_factors]

    def _detect_financial_anomalies(
        self,
        financial_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """检测财务异常"""
        anomalies = []

        # 毛利率与净利率不匹配
        gross_margin = financial_data["毛利率"]
        net_margin = financial_data["净利率"]
        if gross_margin > 40 and net_margin < 5:
            anomalies.append({
                "type": "毛利率与净利率背离",
                "description": f"毛利率{gross_margin:.1f}%但净利率仅{net_margin:.1f}%，费用控制可能存在问题"
            })

        # 营收增长但利润下降
        revenue_growth = financial_data["营收增长率"]
        profit_growth = financial_data["净利润增长率"]
        if revenue_growth > 20 and profit_growth < 0:
            anomalies.append({
                "type": "增收不增利",
                "description": f"营收增长{revenue_growth:.1f}%但利润下降{abs(profit_growth):.1f}%"
            })

        # ROE异常高
        roe = financial_data["ROE"]
        if roe > 30:
            anomalies.append({
                "type": "ROE异常高",
                "description": f"ROE达到{roe:.1f}%，可能存在财务杠杆或数据异常"
            })

        return anomalies

    def _assess_anomaly_severity(self, anomalies: List[Dict[str, Any]]) -> str:
        """评估异常严重程度"""
        count = len(anomalies)
        if count >= 3:
            return "严重"
        elif count >= 2:
            return "中等"
        elif count >= 1:
            return "轻微"
        else:
            return "无异常"

    def _generate_health_summary(
        self,
        health_score: float,
        health_metrics: Dict[str, Any]
    ) -> str:
        """生成健康度摘要"""
        grade = self._get_health_grade(health_score)

        summary = f"财务健康度评分{health_score:.1f}分（{grade}级），"
        summary += f"偿债能力{health_metrics['偿债能力']['status']}，"
        summary += f"盈利能力{health_metrics['盈利能力']['status']}，"
        summary += f"成长能力{health_metrics['成长能力']['status']}，"
        summary += f"现金流{health_metrics['现金流']['status']}。"

        return summary

    def _generate_health_recommendation(self, health_score: float) -> str:
        """生成投资建议"""
        if health_score >= 75:
            return "财务健康，可以关注"
        elif health_score >= 65:
            return "财务状况良好，适度关注"
        elif health_score >= 55:
            return "财务状况一般，谨慎对待"
        else:
            return "财务状况较差，建议规避"

    def _generate_risk_recommendation(self, risk_level: str) -> str:
        """生成风险建议"""
        recommendations = {
            "极高风险": "财务风险极高，强烈建议规避",
            "高风险": "财务风险较高，谨慎投资",
            "中风险": "存在一定风险，需要关注",
            "低风险": "风险较低，可以适当关注",
            "安全": "财务状况安全，可以放心投资"
        }
        return recommendations.get(risk_level, "未知风险等级")

    def _generate_anomaly_recommendation(
        self,
        anomalies: List[Dict[str, Any]]
    ) -> str:
        """生成异常建议"""
        if not anomalies:
            return "未发现明显财务异常"

        count = len(anomalies)
        if count >= 3:
            return f"发现{count}个异常信号，建议深入调查后再做决策"
        elif count >= 1:
            return f"发现{count}个异常信号，需要关注"
        else:
            return "财务数据正常"
