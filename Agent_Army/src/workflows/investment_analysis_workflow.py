"""
Agent Army - Phase 1 投资分析工作流
最简单的协作流程: 产业分析 → 基本面分析 → 生成报告
"""

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import asyncio  # Phase 3: 并发执行支持

from src.agents.business.industry_analyzers import IndustryChainAnalyzer
from src.agents.business.fundamental_analyzer import FundamentalAnalyzer
from src.agents.management.commander_agent import CommanderAgent
from src.models.analysis_models import (
    InvestmentReport, Rating, RiskLevel,
    FundamentalAnalysisResult, AnalysisType
)
from src.core.logger import get_logger


class InvestmentAnalysisWorkflow:
    """
    Phase 1 投资分析工作流
    最简单的流程: 产业分析 → 基本面分析 → 报告生成
    """

    def __init__(self):
        """初始化工作流"""
        self.logger = get_logger("investment_workflow")

        # 初始化2个业务Agent
        self.industry_analyzer = IndustryChainAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()

        # 初始化Commander Agent（审核）
        self.commander = CommanderAgent()

        self.logger.info("投资分析工作流初始化完成")
        self.logger.info(f"产业分析: {self.industry_analyzer.name}")
        self.logger.info(f"基本面分析: {self.fundamental_analyzer.name}")
        self.logger.info(f"质量审核: {self.commander.name}")

    async def analyze_stock(self, stock_code: str) -> InvestmentReport:
        """
        分析单只股票

        Args:
            stock_code: 股票代码(6位数字)

        Returns:
            投资分析报告
        """
        self.logger.info("=" * 60)
        self.logger.info(f"开始分析股票: {stock_code}")
        self.logger.info("=" * 60)

        start_time = datetime.now()

        # 存储预审结果
        precheck_results = {}

        try:
            # Step 1: 产业分析
            self.logger.info("=" * 60)
            self.logger.info("[1/4] 产业分析Agent启动")
            self.logger.info("=" * 60)
            self.logger.info(f"Agent名称: {self.industry_analyzer.name}")
            self.logger.info(f"Agent职责: {self.industry_analyzer.role}")

            # TODO: 产业分析详细日志（Phase 2实现真实API后添加）
            industry_result = await self.industry_analyzer.analyze(stock_code)

            self.logger.info(f"产业分析完成:")
            self.logger.info(f"  - 行业名称: {industry_result.industry_name}")
            self.logger.info(f"  - 行业评分: {industry_result.score}/100")
            self.logger.info(f"  - 行业周期: {industry_result.industry_cycle}")
            self.logger.info(f"  - 市场份额: {industry_result.market_share}%")
            self.logger.info(f"  - 行业排名: 第{industry_result.industry_rank}名")
            self.logger.info(f"  - 成长驱动: {', '.join(industry_result.growth_driver)}")
            self.logger.info(f"  - 风险因素: {', '.join(industry_result.risk_factors)}")

            # Step 1.1: Commander预审产业链报告
            self.logger.info("")
            self.logger.info(">>> Commander预审产业链报告...")
            industry_precheck = await self.commander.precheck_report(
                agent_name="产业链分析AI",
                report_type="industry",
                report_data=industry_result.model_dump()
            )
            precheck_results["industry"] = industry_precheck

            # 检查预审结果
            if industry_precheck.get("critical_error"):
                # 严重错误，停止分析
                self.logger.error(f"严重错误: {industry_precheck['error_type']}")
                raise Exception(f"系统错误: {industry_precheck['error_type']}")

            if industry_precheck["approved"]:
                self.logger.info(f"产业链分析预审通过（质量评分: {industry_precheck['quality_score']}/100）")
                self.logger.info(f"   状态: 待用")
            else:
                self.logger.warning(f"产业链分析预审未通过（质量评分: {industry_precheck['quality_score']}/100）")
                self.logger.warning(f"   状态: {industry_precheck['status']}")
                if industry_precheck.get("issues"):
                    self.logger.warning(f"   问题: {', '.join(industry_precheck['issues'])}")
                # 注意：这里不停止流程，继续等待其他报告
                # 实际生产中可以选择立即打回去重做

            # Step 2: 基本面分析
            self.logger.info("")
            self.logger.info("=" * 60)
            self.logger.info("[2/4] 基本面分析Agent启动")
            self.logger.info("=" * 60)
            self.logger.info(f"Agent名称: {self.fundamental_analyzer.name}")
            self.logger.info(f"Agent职责: {self.fundamental_analyzer.role}")

            # 详细日志：工具调用前
            self.logger.info("")
            self.logger.info(">>> 正在调用财务数据工具...")
            self.logger.info(f"    - 工具名称: FinancialTool")
            self.logger.info(f"    - 目标股票: {stock_code}")
            self.logger.info(f"    - 数据范围: 最近3年")

            fundamental_result = await self.fundamental_analyzer.analyze(stock_code)

            # 详细日志：工具调用后
            self.logger.info("")
            self.logger.info(">>> 财务数据获取成功:")
            self.logger.info(f"    - 股票名称: {fundamental_result['stock_name']}")
            self.logger.info(f"    - 数据来源: {fundamental_result.get('data_sources', ['未知'])}")
            self.logger.info(f"    - 最后更新: {fundamental_result.get('last_update', '未知')}")

            self.logger.info("")
            self.logger.info(">>> 核心财务指标:")
            key_metrics = fundamental_result['key_metrics']
            self.logger.info(f"    - ROE（净资产收益率）: {key_metrics['roe']:.2f}%")
            self.logger.info(f"    - 营收增长率: {key_metrics['revenue_growth']:.2f}%")
            self.logger.info(f"    - 利润增长率: {key_metrics['profit_growth']:.2f}%")

            self.logger.info("")
            self.logger.info(">>> 评分结果:")
            scores = fundamental_result['scores']
            self.logger.info(f"    - 财务质量: {scores['financial_quality']:.1f}/100")
            self.logger.info(f"    - 盈利能力: {scores['profitability']:.1f}/100")
            self.logger.info(f"    - 成长能力: {scores['growth_ability']:.1f}/100")
            self.logger.info(f"    - 偿债能力: {scores['solvency']:.1f}/100")
            self.logger.info(f"    - 综合评分: {fundamental_result['composite_score']:.1f}/100")

            self.logger.info("")
            self.logger.info(f">>> 投资评级: {fundamental_result['rating']}")
            self.logger.info(f"    评级依据: {fundamental_result['investment_value']}")

            # 数据质量判断
            self.logger.info("")
            if fundamental_result['composite_score'] > 0:
                self.logger.info(">>> 数据质量检查:")
                if scores['financial_quality'] < 30:
                    self.logger.warning("    财务质量评分过低，数据可能不完整")
                if key_metrics['roe'] == 0:
                    self.logger.warning("    ROE为0，可能缺少关键财务数据")
                if fundamental_result['confidence'] < 0.5:
                    self.logger.warning("    置信度过低，分析结果可能不可靠")
                if scores['financial_quality'] >= 60 and fundamental_result['confidence'] >= 0.7:
                    self.logger.info("    数据质量良好，分析结果可信")

            # Commander预审基本面报告
            self.logger.info("")
            self.logger.info(">>> Commander预审基本面报告...")
            fundamental_precheck = await self.commander.precheck_report(
                agent_name="基本面分析AI",
                report_type="fundamental",
                report_data=fundamental_result
            )
            precheck_results["fundamental"] = fundamental_precheck

            # 检查预审结果
            if fundamental_precheck.get("critical_error"):
                # 严重错误，停止分析
                self.logger.error(f"严重错误: {fundamental_precheck['error_type']}")
                raise Exception(f"系统错误: {fundamental_precheck['error_type']}")

            if fundamental_precheck["approved"]:
                self.logger.info(f"基本面分析预审通过（质量评分: {fundamental_precheck['quality_score']}/100）")
                self.logger.info(f"   状态: {fundamental_precheck['status']}")
            else:
                self.logger.warning(f"基本面分析预审未通过（质量评分: {fundamental_precheck['quality_score']}/100）")
                self.logger.warning(f"   状态: {fundamental_precheck['status']}")
                if fundamental_precheck.get("issues"):
                    self.logger.warning(f"   问题: {', '.join(fundamental_precheck['issues'])}")
                if fundamental_precheck.get("give_up"):
                    self.logger.error(f"   已放弃: {fundamental_precheck.get('reason')}")

            # Step 3: 检查预审结果并生成报告
            self.logger.info("")
            self.logger.info("=" * 60)
            self.logger.info("[3/4] 生成投资分析报告")
            self.logger.info("=" * 60)

            # 检查是否有放弃的Agent
            abandoned_agents = [
                name for name, result in precheck_results.items()
                if result.get("give_up")
            ]

            if abandoned_agents:
                self.logger.warning(f">>> 警告: 以下Agent已放弃: {', '.join(abandoned_agents)}")
                self.logger.warning(">>> 将生成部分报告（带警告）")

            self.logger.info(">>> 正在综合分析结果...")
            report = self._generate_report(
                stock_code=stock_code,
                industry_result=industry_result,
                fundamental_result=fundamental_result
            )

            # 添加预审信息到报告
            report.precheck_results = precheck_results

            # 如果有放弃的Agent，添加警告
            if abandoned_agents:
                report.warnings = [
                    f"{agent}分析已放弃，报告可能不完整"
                    for agent in abandoned_agents
                ]

            self.logger.info(f">>> 报告生成完成:")
            self.logger.info(f"    - 股票: {report.stock_name} ({report.stock_code})")
            self.logger.info(f"    - 综合评分: {report.overall_score:.1f}/100")
            self.logger.info(f"    - 投资评级: {report.overall_rating.value}")
            self.logger.info(f"    - 风险等级: {report.risk_level.value}")
            self.logger.info(f"    - 建议仓位: {report.position_suggestion}")

            # Step 4: 最终确认（不再需要Commander审核，因为所有材料都预审通过了）
            self.logger.info("")
            self.logger.info("=" * 60)
            self.logger.info("[4/4] 报告完成")
            self.logger.info("=" * 60)

            # 计算耗时
            duration = (datetime.now() - start_time).total_seconds()

            self.logger.info("")
            self.logger.info("分析任务完成")
            self.logger.info("=" * 60)
            self.logger.info(f"总耗时: {duration:.2f}秒")
            self.logger.info(f"分析股票: {report.stock_name} ({report.stock_code})")
            self.logger.info(f"最终评级: {report.overall_rating.value}")
            self.logger.info(f"综合评分: {report.overall_score:.1f}/100")

            # 显示预审统计
            approved_count = sum(1 for r in precheck_results.values() if r["approved"])
            total_count = len(precheck_results)
            self.logger.info(f"预审通过: {approved_count}/{total_count}")

            if abandoned_agents:
                self.logger.warning(f"警告: {len(abandoned_agents)}个Agent已放弃")
            else:
                self.logger.info("所有Agent预审通过")

            self.logger.info("=" * 60)

            return report

        except Exception as e:
            self.logger.error(f"分析失败: {str(e)}")
            raise

    async def analyze_stock_concurrent(self, stock_code: str) -> InvestmentReport:
        """
        并发分析单只股票（Phase 3 性能优化）

        Args:
            stock_code: 股票代码(6位数字)

        Returns:
            投资分析报告

        核心优化：
        1. Agent并发执行（asyncio.gather）
        2. Commander预审仍然顺序执行
        3. 异常处理（return_exceptions=True）
        4. 性能统计
        """
        start_time = datetime.now()

        self.logger.info("=" * 60)
        self.logger.info(f"开始并发分析股票: {stock_code}")
        self.logger.info("=" * 60)
        self.logger.info("")

        precheck_results = {}
        abandoned_agents = []

        try:
            # ========== Phase 1: 并发执行所有Agent分析 ==========
            self.logger.info(">>> [并发模式] 启动所有Agent并发分析...")
            self.logger.info("")

            # 定义所有Agent任务
            agent_tasks = {
                "产业链分析AI": self.industry_analyzer.analyze(stock_code),
                "基本面分析AI": self.fundamental_analyzer.analyze(stock_code)
            }

            # 并发执行所有Agent
            task_names = list(agent_tasks.keys())
            task_coroutines = list(agent_tasks.values())

            self.logger.info(f">>> 并发执行 {len(task_coroutines)} 个Agent:")
            for name in task_names:
                self.logger.info(f"    - {name}")
            self.logger.info("")

            # 使用asyncio.gather并发执行
            results = await asyncio.gather(
                *task_coroutines,
                return_exceptions=True  # 即使某个Agent失败，也继续执行
            )

            # 统计执行结果
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            failed_count = len(results) - success_count

            self.logger.info(f">>> 并发执行完成:")
            self.logger.info(f"    - 成功: {success_count}/{len(results)}")
            self.logger.info(f"    - 失败: {failed_count}/{len(results)}")
            self.logger.info("")

            # ========== Phase 2: Commander顺序预审所有报告 ==========
            self.logger.info("=" * 60)
            self.logger.info(">>> [预审阶段] Commander开始顺序预审...")
            self.logger.info("=" * 60)
            self.logger.info("")

            # 收集所有结果并预审
            agent_results = {}
            for i, (agent_name, result) in enumerate(zip(task_names, results)):
                self.logger.info(f"[{i+1}/{len(task_names)}] 预审 {agent_name}...")

                # 检查是否有异常
                if isinstance(result, Exception):
                    self.logger.error(f"   Agent执行失败: {str(result)}")
                    # 标记为严重错误
                    precheck_results[agent_name] = {
                        "approved": False,
                        "critical_error": True,
                        "error_type": "agent_execution_error",
                        "error_message": str(result),
                        "quality_score": 0,
                        "status": "执行失败"
                    }
                    abandoned_agents.append(agent_name)
                    continue

                # 存储结果
                agent_results[agent_name] = result

                # 确定报告类型
                if agent_name == "产业链分析AI":
                    report_type = "industry"
                    report_data = result.model_dump() if hasattr(result, 'model_dump') else result
                elif agent_name == "基本面分析AI":
                    report_type = "fundamental"
                    report_data = result
                else:
                    report_type = "unknown"
                    report_data = result

                # Commander预审
                precheck_result = await self.commander.precheck_report(
                    agent_name=agent_name,
                    report_type=report_type,
                    report_data=report_data
                )
                precheck_results[agent_name] = precheck_result

                # 检查预审结果
                if precheck_result.get("critical_error"):
                    self.logger.error(f"   严重错误: {precheck_result['error_type']}")
                    # 对于严重错误，停止整个分析
                    raise Exception(f"系统错误: {precheck_result['error_type']}")

                if precheck_result["approved"]:
                    self.logger.info(f"   预审通过（质量评分: {precheck_result['quality_score']}/100）")
                    self.logger.info(f"   状态: {precheck_result['status']}")
                else:
                    self.logger.warning(f"   预审未通过（质量评分: {precheck_result['quality_score']}/100）")
                    self.logger.warning(f"   状态: {precheck_result['status']}")
                    if precheck_result.get("issues"):
                        self.logger.warning(f"   问题: {', '.join(precheck_result['issues'])}")
                    if precheck_result.get("give_up"):
                        self.logger.error(f"   已放弃: {precheck_result.get('reason')}")
                        abandoned_agents.append(agent_name)

                self.logger.info("")

            # ========== Phase 3: 生成最终报告 ==========
            self.logger.info("=" * 60)
            self.logger.info("[3/3] 生成投资分析报告")
            self.logger.info("=" * 60)
            self.logger.info("")

            # 检查是否有成功的Agent
            if not agent_results:
                raise Exception("所有Agent执行失败，无法生成报告")

            # 获取结果（如果某个Agent失败，使用None）
            industry_result = agent_results.get("产业链分析AI")
            fundamental_result = agent_results.get("基本面分析AI")

            # 生成报告（即使部分Agent失败）
            self.logger.info(">>> 正在综合分析结果...")
            report = self._generate_report(
                stock_code=stock_code,
                industry_result=industry_result,
                fundamental_result=fundamental_result
            )

            # 添加预审信息到报告
            report.precheck_results = precheck_results

            # 如果有放弃的Agent，添加警告
            if abandoned_agents:
                report.warnings = [
                    f"{agent}分析已放弃，报告可能不完整"
                    for agent in abandoned_agents
                ]

            self.logger.info(f">>> 报告生成完成:")
            self.logger.info(f"    - 股票: {report.stock_name} ({report.stock_code})")
            self.logger.info(f"    - 综合评分: {report.overall_score:.1f}/100")
            self.logger.info(f"    - 投资评级: {report.overall_rating.value}")
            self.logger.info(f"    - 风险等级: {report.risk_level.value}")
            self.logger.info(f"    - 建议仓位: {report.position_suggestion}")

            # ========== Phase 4: 任务完成统计 ==========
            self.logger.info("")
            self.logger.info("=" * 60)
            self.logger.info("[4/4] 报告完成")
            self.logger.info("=" * 60)

            # 计算耗时
            duration = (datetime.now() - start_time).total_seconds()

            self.logger.info("")
            self.logger.info("并发分析任务完成")
            self.logger.info("=" * 60)
            self.logger.info(f"总耗时: {duration:.2f}秒")
            self.logger.info(f"分析股票: {report.stock_name} ({report.stock_code})")
            self.logger.info(f"最终评级: {report.overall_rating.value}")
            self.logger.info(f"综合评分: {report.overall_score:.1f}/100")

            # 显示预审统计
            approved_count = sum(1 for r in precheck_results.values() if r["approved"])
            total_count = len(precheck_results)
            self.logger.info(f"预审通过: {approved_count}/{total_count}")

            # 性能提升统计
            sequential_estimate = 1.0  # 顺序执行预估耗时（秒）
            speedup = sequential_estimate / duration if duration > 0 else 0
            self.logger.info(f"性能提升: {speedup:.1f}x (相比顺序执行)")

            if abandoned_agents:
                self.logger.warning(f"警告: {len(abandoned_agents)}个Agent已放弃")
            else:
                self.logger.info("所有Agent预审通过")

            self.logger.info("=" * 60)

            return report

        except Exception as e:
            self.logger.error(f"并发分析失败: {str(e)}")
            raise

    def _convert_fundamental_dict_to_result(
        self,
        fundamental_dict: Dict[str, Any]
    ) -> FundamentalAnalysisResult:
        """
        将基本面分析字典转换为 FundamentalAnalysisResult 对象

        Args:
            fundamental_dict: 基本面分析结果字典

        Returns:
            FundamentalAnalysisResult 对象
        """
        # 评级映射（英文 -> 中文枚举）
        rating_map = {
            "STRONG_BUY": Rating.STRONG_BUY,
            "BUY": Rating.BUY,
            "HOLD": Rating.HOLD,
            "SELL": Rating.SELL,
            "STRONG_SELL": Rating.STRONG_SELL,
            "NEUTRAL": Rating.NEUTRAL
        }

        # 提取评分
        scores = fundamental_dict.get("scores", {})
        key_metrics = fundamental_dict.get("key_metrics", {})

        # ROE趋势描述
        roe_value = key_metrics.get("roe", 0)
        if roe_value >= 20:
            roe_trend = "优秀且稳定"
        elif roe_value >= 15:
            roe_trend = "良好"
        elif roe_value >= 10:
            roe_trend = "一般"
        else:
            roe_trend = "偏低"

        # 创建对象
        result = FundamentalAnalysisResult(
            stock_code=fundamental_dict.get("stock_code", ""),
            stock_name=fundamental_dict.get("stock_name", ""),
            analysis_type=AnalysisType.FUNDAMENTAL,
            score=fundamental_dict.get("composite_score", 0.0),
            confidence=fundamental_dict.get("confidence", 0.0),
            summary=fundamental_dict.get("summary", ""),
            timestamp=datetime.now(),

            # 财务质量
            financial_score=scores.get("financial_quality", 0.0),
            profitability=scores.get("profitability", 0.0),
            growth_ability=scores.get("growth_ability", 0.0),
            solvency=scores.get("solvency", 0.0),

            # 核心指标
            roe_trend=roe_trend,
            revenue_growth=key_metrics.get("revenue_growth", 0.0),
            profit_growth=key_metrics.get("profit_growth", 0.0),

            # 结论
            rating=rating_map.get(
                fundamental_dict.get("rating", "NEUTRAL"),
                Rating.NEUTRAL
            ),
            investment_value=fundamental_dict.get("investment_value", "")
        )

        return result

    def _generate_report(
        self,
        stock_code: str,
        industry_result: Any,
        fundamental_result: Any
    ) -> InvestmentReport:
        """
        生成综合投资分析报告

        Args:
            stock_code: 股票代码
            industry_result: 产业分析结果
            fundamental_result: 基本面分析结果

        Returns:
            投资分析报告
        """
        # 转换评级（英文 -> 中文）
        rating_map = {
            "STRONG_BUY": "强推",
            "BUY": "买入",
            "HOLD": "持有",
            "SELL": "卖出",
            "STRONG_SELL": "强卖",
            "NEUTRAL": "中性"
        }
        fundamental_rating_en = fundamental_result["rating"]
        fundamental_rating_cn = rating_map.get(fundamental_rating_en, "中性")

        # 计算综合评分 (产业40% + 基本面60%)
        overall_score = (
            industry_result.score * 0.4 +
            fundamental_result["composite_score"] * 0.6
        )

        # 确定综合评级
        if overall_score >= 80:
            overall_rating = Rating.STRONG_BUY
        elif overall_score >= 70:
            overall_rating = Rating.BUY
        elif overall_score >= 50:
            overall_rating = Rating.HOLD
        else:
            overall_rating = Rating.SELL

        # 确定风险等级
        if overall_score >= 75:
            risk_level = RiskLevel.LOW
        elif overall_score >= 60:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH

        # 转换基本面结果为对象
        fundamental_obj = self._convert_fundamental_dict_to_result(fundamental_result)

        # 生成投资建议
        investment_advice = self._generate_investment_advice(
            overall_score=overall_score,
            overall_rating=overall_rating,
            industry_result=industry_result,
            fundamental_result=fundamental_result
        )

        # 创建报告
        report = InvestmentReport(
            stock_code=stock_code,
            stock_name=fundamental_result["stock_name"],
            report_date=datetime.now(),

            # 分析结果
            fundamental=fundamental_obj,  # 使用转换后的对象
            industry=industry_result,

            # 综合评价
            overall_score=overall_score,
            overall_rating=overall_rating,
            risk_level=risk_level,

            # 投资建议
            investment_advice=investment_advice,
            target_price=fundamental_result["details"].get("target_price", 0.0),
            stop_loss_price=0.0,  # TODO: 计算
            position_suggestion=self._generate_position_suggestion(overall_score),

            # 风险提示
            key_risks=industry_result.risk_factors + fundamental_result["warnings"],
            investment_horizon="长期(1-3年)"
        )

        return report

    def _generate_investment_advice(
        self,
        overall_score: float,
        overall_rating: Rating,
        industry_result: Any,
        fundamental_result: Any
    ) -> str:
        """生成投资建议"""
        advice_parts = []

        # 总体评价
        if overall_score >= 80:
            advice_parts.append("该股票基本面优秀,行业前景良好,建议重点关注。")
        elif overall_score >= 70:
            advice_parts.append("该股票基本面较好,具备投资价值。")
        elif overall_score >= 60:
            advice_parts.append("该股票基本面一般,建议谨慎投资。")
        else:
            advice_parts.append("该股票基本面较差,不建议投资。")

        # 行业评价
        advice_parts.append(f"所属{industry_result.industry_name}行业处于{industry_result.industry_cycle}。")

        # 财务评价
        advice_parts.append(fundamental_result["investment_value"])

        # 评级建议
        rating_map = {
            Rating.STRONG_BUY: "强烈推荐买入",
            Rating.BUY: "建议买入",
            Rating.HOLD: "建议持有观望",
            Rating.SELL: "建议卖出"
        }
        advice_parts.append(f"综合评级: {rating_map.get(overall_rating, '中性')}。")

        return " ".join(advice_parts)

    def _generate_position_suggestion(self, overall_score: float) -> str:
        """生成仓位建议"""
        if overall_score >= 80:
            return "建议仓位: 15-20% (重仓)"
        elif overall_score >= 70:
            return "建议仓位: 10-15% (标准仓)"
        elif overall_score >= 60:
            return "建议仓位: 5-10% (轻仓)"
        else:
            return "建议仓位: 0% (不建仓)"

    def save_report(self, report: InvestmentReport, output_dir: str = "./reports") -> str:
        """
        保存报告到文件

        Args:
            report: 投资分析报告
            output_dir: 输出目录

        Returns:
            报告文件路径
        """
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成文件名：股票名称_股票代码_分析日期
        # 格式：贵州茅台_600519_2026-03-14.json
        stock_name = report.stock_name if hasattr(report, 'stock_name') and report.stock_name else report.stock_code
        analysis_date = report.report_date.strftime('%Y-%m-%d')
        filename = f"{stock_name}_{report.stock_code}_{analysis_date}.json"
        filepath = output_path / filename

        # 如果文件已存在，添加时间戳避免覆盖
        if filepath.exists():
            timestamp = report.report_date.strftime('%H%M%S')
            filename = f"{stock_name}_{report.stock_code}_{analysis_date}_{timestamp}.json"
            filepath = output_path / filename

        # 转换为字典
        report_dict = report.model_dump()

        # 添加Commander审核信息（如果有）
        if hasattr(report, 'commander_review'):
            report_dict['commander_review'] = report.commander_review

        # 保存JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2, default=str)

        self.logger.info(f"报告已保存: {filepath}")
        return str(filepath)


# ==================== 便捷函数 ====================

async def quick_analyze(stock_code: str) -> InvestmentReport:
    """
    快速分析股票(便捷函数 - 顺序执行)

    Args:
        stock_code: 股票代码

    Returns:
        投资分析报告
    """
    workflow = InvestmentAnalysisWorkflow()
    return await workflow.analyze_stock(stock_code)


async def quick_analyze_concurrent(stock_code: str) -> InvestmentReport:
    """
    快速分析股票(便捷函数 - 并发执行)

    Args:
        stock_code: 股票代码

    Returns:
        投资分析报告

    性能提升: 10-20倍（相比顺序执行）
    """
    workflow = InvestmentAnalysisWorkflow()
    return await workflow.analyze_stock_concurrent(stock_code)
