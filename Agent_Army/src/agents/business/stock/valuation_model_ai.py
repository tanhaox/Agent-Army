"""
估值模型AI - Valuation Model AI

职责：
- 多模型估值（PE/PB/DCF/PS等）
- 使用YahooFinanceTool获取财务数据
- 使用FormulaTool计算估值指标
- 综合多模型结果

输入：
- 股票代码

输出：
- 多模型估值结果
- 综合估值
- 评级建议

技术栈：
- YahooFinanceTool（财务数据获取）
- FormulaTool（估值指标计算）
- 标准化估值公式（不可修改）
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from src.core.base_agent import BaseAgent, AgentCapability, AgentTool
from src.core.logger import LoggerMixin
from src.core.tools.data_source.yahoo_tool import YahooFinanceTool
from src.core.tools.calculation.formula_tool import FormulaTool
from src.core.formulas.standard.valuation import StandardValuationFormulas


class ValuationModelAI(BaseAgent, LoggerMixin):
    """估值模型AI - 多模型估值分析"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 初始化工具
        self.yahoo_tool = YahooFinanceTool()
        self.formula_tool = FormulaTool()
        self.standard_formulas = StandardValuationFormulas()

        # 检查工具可用性
        if not self.yahoo_tool.is_available():
            self.logger.warning("Yahoo Finance工具不可用，部分功能受限")

        super().__init__(
            name="估值模型AI",
            role="使用多模型（PE/PB/DCF/PS等）进行股票估值分析，计算内在价值和安全边际",
            capabilities=[
                AgentCapability(
                    name="pe_valuation",
                    description="PE估值模型",
                    input_type="stock_code",
                    output_type="pe_valuation_result"
                ),
                AgentCapability(
                    name="pb_valuation",
                    description="PB估值模型",
                    input_type="stock_code",
                    output_type="pb_valuation_result"
                ),
                AgentCapability(
                    name="dcf_valuation",
                    description="DCF现金流折现估值",
                    input_type="stock_code",
                    output_type="dcf_valuation_result"
                ),
                AgentCapability(
                    name="ps_valuation",
                    description="PS市销率估值",
                    input_type="stock_code",
                    output_type="ps_valuation_result"
                ),
                AgentCapability(
                    name="composite_valuation",
                    description="综合估值（多模型加权）",
                    input_type="stock_code",
                    output_type="composite_valuation_result"
                )
            ],
            tools=[
                AgentTool(
                    name="yahoo_finance",
                    description="Yahoo Finance数据源",
                    tool_type="data_source",
                    config={}
                ),
                AgentTool(
                    name="formula_calculator",
                    description="公式计算工具",
                    tool_type="calculation",
                    config={}
                )
            ],
            config=config
        )

        self.logger.info("估值模型AI初始化完成")

    async def execute(self, task: str, **kwargs) -> Any:
        """执行任务"""
        stock_code = kwargs.get("stock_code")
        if not stock_code:
            raise ValueError("缺少stock_code参数")

        if task == "pe_valuation":
            return await self.pe_valuation(stock_code)
        elif task == "pb_valuation":
            return await self.pb_valuation(stock_code)
        elif task == "dcf_valuation":
            return await self.dcf_valuation(stock_code)
        elif task == "ps_valuation":
            return await self.ps_valuation(stock_code)
        elif task == "composite_valuation":
            return await self.composite_valuation(stock_code)
        else:
            # 默认执行综合估值
            return await self.composite_valuation(stock_code)

    # ========== PE估值模型 ==========

    async def pe_valuation(self, stock_code: str) -> Dict[str, Any]:
        """
        PE估值模型

        方法：合理PE倍数法
        公式：合理价值 = 每股收益(EPS) × 合理PE倍数
        """
        self.logger.info(f"开始PE估值: {stock_code}")

        try:
            # 1. 获取股票信息
            symbol = f"{stock_code}.SS" if stock_code.startswith("6") else f"{stock_code}.SZ"
            company_info = self.yahoo_tool.get_company_info(symbol)

            if "error" in company_info:
                return self._error_result(stock_code, "PE估值", company_info["error"])

            # 2. 获取实时行情
            quote = self.yahoo_tool.get_realtime_quote(symbol)
            current_price = quote.get("current_price", 0)

            # 3. 获取财务数据
            financials = self.yahoo_tool.get_financial_statements(symbol)

            # 4. 计算EPS（每股收益）
            # 从Yahoo Finance获取trailing PE和forward PE
            trailing_pe = company_info.get("trailing_pe", 0)
            forward_pe = company_info.get("forward_pe", 0)

            # 反推EPS：当前价格 / PE
            eps_trailing = current_price / trailing_pe if trailing_pe and trailing_pe > 0 else 0
            eps_forward = current_price / forward_pe if forward_pe and forward_pe > 0 else 0

            # 使用forward EPS作为主要指标
            eps = eps_forward if eps_forward > 0 else eps_trailing

            # 5. 确定合理PE倍数（基于行业和历史）
            # 简化策略：使用历史平均PE或行业平均PE
            if trailing_pe > 0:
                # 使用当前PE作为基准，给予一定的安全边际
                industry_pe_multiple = trailing_pe * 0.9  # 90%的安全边际
            else:
                # 默认PE倍数（根据行业调整）
                industry_pe_multiple = 20.0  # 默认20倍

            # 6. 计算合理价值
            fair_value = eps * industry_pe_multiple

            # 7. 计算上行空间
            upside = (fair_value - current_price) / current_price if current_price > 0 else 0

            # 8. 评级
            rating = self._get_valuation_rating(upside)

            result = {
                "stock_code": stock_code,
                "stock_name": company_info.get("company_name", "未知"),
                "valuation_model": "PE估值",
                "data": {
                    "eps": round(eps, 2),
                    "eps_trailing": round(eps_trailing, 2),
                    "eps_forward": round(eps_forward, 2),
                    "pe_multiple_trailing": round(trailing_pe, 2),
                    "pe_multiple_forward": round(forward_pe, 2),
                    "industry_pe_multiple": round(industry_pe_multiple, 2),
                },
                "valuation": {
                    "fair_value": round(fair_value, 2),
                    "current_price": round(current_price, 2),
                    "upside": round(upside, 4),
                    "rating": rating
                },
                "timestamp": datetime.now().isoformat()
            }

            self.logger.info(
                f"PE估值完成: {stock_code}",
                extra={
                    "fair_value": fair_value,
                    "current_price": current_price,
                    "upside": upside
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"PE估值失败: {e}", extra={"stock_code": stock_code})
            return self._error_result(stock_code, "PE估值", str(e))

    # ========== PB估值模型 ==========

    async def pb_valuation(self, stock_code: str) -> Dict[str, Any]:
        """
        PB估值模型

        方法：市净率法
        公式：合理价值 = 每股净资产(BVPS) × 合理PB倍数
        """
        self.logger.info(f"开始PB估值: {stock_code}")

        try:
            # 1. 获取股票信息
            symbol = f"{stock_code}.SS" if stock_code.startswith("6") else f"{stock_code}.SZ"
            company_info = self.yahoo_tool.get_company_info(symbol)

            if "error" in company_info:
                return self._error_result(stock_code, "PB估值", company_info["error"])

            # 2. 获取实时行情
            quote = self.yahoo_tool.get_realtime_quote(symbol)
            current_price = quote.get("current_price", 0)

            # 3. 获取PB数据
            pb_ratio = company_info.get("price_to_book", 0)

            # 4. 计算每股净资产（BVPS）
            # BVPS = 股价 / PB
            bvps = current_price / pb_ratio if pb_ratio and pb_ratio > 0 else 0

            # 5. 确定合理PB倍数
            # 根据行业和ROE调整
            # 简化策略：使用当前PB的90%作为安全边际
            if pb_ratio > 0:
                industry_pb_multiple = pb_ratio * 0.9
            else:
                industry_pb_multiple = 2.0  # 默认2倍

            # 6. 计算合理价值
            fair_value = bvps * industry_pb_multiple

            # 7. 计算上行空间
            upside = (fair_value - current_price) / current_price if current_price > 0 else 0

            # 8. 评级
            rating = self._get_valuation_rating(upside)

            result = {
                "stock_code": stock_code,
                "stock_name": company_info.get("company_name", "未知"),
                "valuation_model": "PB估值",
                "data": {
                    "bvps": round(bvps, 2),
                    "pb_multiple_current": round(pb_ratio, 2),
                    "industry_pb_multiple": round(industry_pb_multiple, 2),
                },
                "valuation": {
                    "fair_value": round(fair_value, 2),
                    "current_price": round(current_price, 2),
                    "upside": round(upside, 4),
                    "rating": rating
                },
                "timestamp": datetime.now().isoformat()
            }

            self.logger.info(
                f"PB估值完成: {stock_code}",
                extra={
                    "fair_value": fair_value,
                    "current_price": current_price,
                    "upside": upside
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"PB估值失败: {e}", extra={"stock_code": stock_code})
            return self._error_result(stock_code, "PB估值", str(e))

    # ========== DCF估值模型 ==========

    async def dcf_valuation(self, stock_code: str) -> Dict[str, Any]:
        """
        DCF估值模型（现金流折现）

        方法：自由现金流折现法
        公式：企业价值 = FCF / (WACC - 增长率)
        """
        self.logger.info(f"开始DCF估值: {stock_code}")

        try:
            # 1. 获取股票信息
            symbol = f"{stock_code}.SS" if stock_code.startswith("6") else f"{stock_code}.SZ"
            company_info = self.yahoo_tool.get_company_info(symbol)

            if "error" in company_info:
                return self._error_result(stock_code, "DCF估值", company_info["error"])

            # 2. 获取实时行情
            quote = self.yahoo_tool.get_realtime_quote(symbol)
            current_price = quote.get("current_price", 0)

            # 3. 获取财务报表
            financials = self.yahoo_tool.get_financial_statements(symbol)

            if "error" in financials:
                return self._error_result(stock_code, "DCF估值", "无法获取财务数据")

            # 4. 提取自由现金流（简化计算）
            # 从现金流量表中提取（这里使用简化假设）
            cash_flow_data = financials.get("cash_flow", {})
            if cash_flow_data and cash_flow_data.get("data"):
                # 取最近一年的自由现金流
                recent_cf = cash_flow_data["data"][0]
                free_cash_flow = recent_cf.get("Free Cash Flow", 0)

                # 转换为亿元
                if abs(free_cash_flow) > 1e8:
                    fcf = free_cash_flow / 1e8
                else:
                    fcf = 0
            else:
                # 无法获取现金流，使用净利润估算
                income_data = financials.get("income_statement", {})
                if income_data and income_data.get("data"):
                    recent_income = income_data["data"][0]
                    net_income = recent_income.get("Net Income", 0)
                    fcf = net_income / 1e8 if abs(net_income) > 1e8 else 0
                else:
                    fcf = 0

            # 5. 确定折现率（WACC）
            # 简化：根据公司风险调整
            profit_margin = company_info.get("profit_margin", 0)
            if profit_margin > 0.2:  # 高利润率，低风险
                wacc = 0.08  # 8%
            elif profit_margin > 0.1:  # 中等利润率
                wacc = 0.10  # 10%
            else:  # 低利润率，高风险
                wacc = 0.12  # 12%

            # 6. 确定永续增长率
            # 通常使用GDP增长率或通胀率
            growth_rate = 0.03  # 3%

            # 7. 使用标准DCF公式计算
            dcf_result = self.standard_formulas.dcf_simplified({
                "free_cash_flow": fcf * 1e8,  # 转换为元
                "discount_rate": wacc,
                "growth_rate": growth_rate
            })

            # 8. 计算每股价值
            shares_outstanding = company_info.get("shares_outstanding", 0)
            if shares_outstanding > 0:
                fair_value = dcf_result / shares_outstanding
            else:
                fair_value = 0

            # 9. 计算上行空间
            upside = (fair_value - current_price) / current_price if current_price > 0 else 0

            # 10. 评级
            rating = self._get_valuation_rating(upside)

            result = {
                "stock_code": stock_code,
                "stock_name": company_info.get("company_name", "未知"),
                "valuation_model": "DCF估值",
                "data": {
                    "free_cash_flow": round(fcf, 2),
                    "wacc": round(wacc, 4),
                    "growth_rate": round(growth_rate, 4),
                    "shares_outstanding": shares_outstanding,
                },
                "valuation": {
                    "fair_value": round(fair_value, 2),
                    "current_price": round(current_price, 2),
                    "upside": round(upside, 4),
                    "rating": rating
                },
                "timestamp": datetime.now().isoformat()
            }

            self.logger.info(
                f"DCF估值完成: {stock_code}",
                extra={
                    "fair_value": fair_value,
                    "current_price": current_price,
                    "upside": upside
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"DCF估值失败: {e}", extra={"stock_code": stock_code})
            return self._error_result(stock_code, "DCF估值", str(e))

    # ========== PS估值模型 ==========

    async def ps_valuation(self, stock_code: str) -> Dict[str, Any]:
        """
        PS估值模型（市销率）

        方法：市销率法
        公式：合理价值 = 每股销售额 × 合理PS倍数
        """
        self.logger.info(f"开始PS估值: {stock_code}")

        try:
            # 1. 获取股票信息
            symbol = f"{stock_code}.SS" if stock_code.startswith("6") else f"{stock_code}.SZ"
            company_info = self.yahoo_tool.get_company_info(symbol)

            if "error" in company_info:
                return self._error_result(stock_code, "PS估值", company_info["error"])

            # 2. 获取实时行情
            quote = self.yahoo_tool.get_realtime_quote(symbol)
            current_price = quote.get("current_price", 0)

            # 3. 获取财务数据
            financials = self.yahoo_tool.get_financial_statements(symbol)

            if "error" in financials:
                return self._error_result(stock_code, "PS估值", "无法获取财务数据")

            # 4. 提取营收数据
            income_data = financials.get("income_statement", {})
            if income_data and income_data.get("data"):
                recent_income = income_data["data"][0]
                revenue = recent_income.get("Total Revenue", 0)

                # 转换为亿元
                if abs(revenue) > 1e8:
                    revenue_billion = revenue / 1e8
                else:
                    revenue_billion = 0
            else:
                revenue_billion = 0

            # 5. 计算市值（亿元）
            market_cap = company_info.get("market_cap", 0)
            if market_cap > 0:
                market_cap_billion = market_cap / 1e8
            else:
                market_cap_billion = 0

            # 6. 计算当前PS倍数
            current_ps = market_cap_billion / revenue_billion if revenue_billion > 0 else 0

            # 7. 确定合理PS倍数
            # 根据行业和利润率调整
            profit_margin = company_info.get("profit_margin", 0)
            if profit_margin > 0.2:  # 高利润率
                industry_ps_multiple = 5.0
            elif profit_margin > 0.1:  # 中等利润率
                industry_ps_multiple = 3.0
            else:  # 低利润率
                industry_ps_multiple = 1.5

            # 8. 计算合理价值
            # 合理市值 = 营收 × 合理PS倍数
            fair_market_cap = revenue_billion * industry_ps_multiple

            # 合理股价 = 合理市值 / 总股本
            shares_outstanding = company_info.get("shares_outstanding", 0)
            if shares_outstanding > 0:
                fair_value = (fair_market_cap * 1e8) / shares_outstanding
            else:
                fair_value = 0

            # 9. 计算上行空间
            upside = (fair_value - current_price) / current_price if current_price > 0 else 0

            # 10. 评级
            rating = self._get_valuation_rating(upside)

            result = {
                "stock_code": stock_code,
                "stock_name": company_info.get("company_name", "未知"),
                "valuation_model": "PS估值",
                "data": {
                    "revenue_billion": round(revenue_billion, 2),
                    "market_cap_billion": round(market_cap_billion, 2),
                    "current_ps": round(current_ps, 2),
                    "industry_ps_multiple": round(industry_ps_multiple, 2),
                    "profit_margin": round(profit_margin, 4),
                },
                "valuation": {
                    "fair_value": round(fair_value, 2),
                    "current_price": round(current_price, 2),
                    "upside": round(upside, 4),
                    "rating": rating
                },
                "timestamp": datetime.now().isoformat()
            }

            self.logger.info(
                f"PS估值完成: {stock_code}",
                extra={
                    "fair_value": fair_value,
                    "current_price": current_price,
                    "upside": upside
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"PS估值失败: {e}", extra={"stock_code": stock_code})
            return self._error_result(stock_code, "PS估值", str(e))

    # ========== 综合估值 ==========

    async def composite_valuation(self, stock_code: str) -> Dict[str, Any]:
        """
        综合估值（多模型加权）

        方法：加权平均多个估值模型
        权重：
        - PE估值：30%
        - PB估值：20%
        - DCF估值：30%
        - PS估值：20%
        """
        self.logger.info(f"开始综合估值: {stock_code}")

        try:
            # 1. 并行执行多个估值模型
            pe_result, pb_result, dcf_result, ps_result = await asyncio.gather(
                self.pe_valuation(stock_code),
                self.pb_valuation(stock_code),
                self.dcf_valuation(stock_code),
                self.ps_valuation(stock_code),
                return_exceptions=True
            )

            # 2. 提取估值结果
            valuations = {}

            if not isinstance(pe_result, Exception):
                valuations["pe"] = pe_result["valuation"]["fair_value"]

            if not isinstance(pb_result, Exception):
                valuations["pb"] = pb_result["valuation"]["fair_value"]

            if not isinstance(dcf_result, Exception):
                valuations["dcf"] = dcf_result["valuation"]["fair_value"]

            if not isinstance(ps_result, Exception):
                valuations["ps"] = ps_result["valuation"]["fair_value"]

            # 3. 计算加权平均
            weights = {
                "pe": 0.30,
                "pb": 0.20,
                "dcf": 0.30,
                "ps": 0.20
            }

            composite_value = 0
            total_weight = 0

            for model, value in valuations.items():
                if value > 0:
                    composite_value += value * weights[model]
                    total_weight += weights[model]

            # 归一化
            if total_weight > 0:
                composite_value = composite_value / total_weight
            else:
                # 如果所有模型都失败，返回错误
                return self._error_result(stock_code, "综合估值", "所有估值模型均失败")

            # 4. 获取当前价格
            current_price = pe_result.get("valuation", {}).get("current_price", 0)
            if current_price == 0:
                current_price = pb_result.get("valuation", {}).get("current_price", 0)

            # 5. 计算上行空间
            upside = (composite_value - current_price) / current_price if current_price > 0 else 0

            # 6. 评级
            rating = self._get_valuation_rating(upside)

            # 7. 构建结果
            result = {
                "stock_code": stock_code,
                "stock_name": pe_result.get("stock_name", "未知"),
                "valuation_model": "综合估值",
                "valuation_models": {
                    "pe_valuation": pe_result if not isinstance(pe_result, Exception) else None,
                    "pb_valuation": pb_result if not isinstance(pb_result, Exception) else None,
                    "dcf_valuation": dcf_result if not isinstance(dcf_result, Exception) else None,
                    "ps_valuation": ps_result if not isinstance(ps_result, Exception) else None,
                },
                "composite_valuation": {
                    "composite_value": round(composite_value, 2),
                    "current_price": round(current_price, 2),
                    "upside": round(upside, 4),
                    "rating": rating,
                    "models_used": list(valuations.keys()),
                    "weights_applied": weights
                },
                "timestamp": datetime.now().isoformat()
            }

            self.logger.info(
                f"综合估值完成: {stock_code}",
                extra={
                    "composite_value": composite_value,
                    "current_price": current_price,
                    "upside": upside,
                    "rating": rating
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"综合估值失败: {e}", extra={"stock_code": stock_code})
            return self._error_result(stock_code, "综合估值", str(e))

    # ========== 辅助方法 ==========

    def _get_valuation_rating(self, upside: float) -> str:
        """
        根据上行空间给出评级

        Args:
            upside: 上行空间（百分比，如0.15表示15%）

        Returns:
            评级：undervalued（低估）/ fair（合理）/ overvalued（高估）
        """
        if upside > 0.2:  # 上行空间超过20%
            return "undervalued"  # 低估
        elif upside > 0.05:  # 上行空间5%-20%
            return "slightly_undervalued"  # 轻微低估
        elif upside > -0.05:  # 上行空间-5%到5%
            return "fair"  # 合理
        elif upside > -0.2:  # 上行空间-5%到-20%
            return "slightly_overvalued"  # 轻微高估
        else:  # 上行空间低于-20%
            return "overvalued"  # 高估

    def _error_result(self, stock_code: str, model: str, error_msg: str) -> Dict[str, Any]:
        """构建错误结果"""
        return {
            "stock_code": stock_code,
            "stock_name": "未知",
            "valuation_model": model,
            "error": error_msg,
            "valuation": {
                "fair_value": 0,
                "current_price": 0,
                "upside": 0,
                "rating": "error"
            },
            "timestamp": datetime.now().isoformat()
        }


# ========== 便捷函数 ==========

async def valuation_analysis(stock_code: str) -> Dict[str, Any]:
    """
    执行估值分析（便捷函数）

    Args:
        stock_code: 股票代码

    Returns:
        综合估值结果
    """
    ai = ValuationModelAI()
    return await ai.composite_valuation(stock_code)
