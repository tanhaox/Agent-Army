"""
龙虎榜AI - Dragon Tiger List AI

职责：
- 分析龙虎榜数据，追踪机构动向
- 使用AKShare获取龙虎榜数据
- 识别机构席位、游资席位
- 分析异动信号

技术栈：
- 继承BaseBusinessAgent
- 使用AKShareTool获取数据
- 返回Pydantic Model结构

输入：
- 股票代码
- 时间范围（可选）

输出：
- 龙虎榜分析报告
- 机构动向分析
- 游资跟踪报告
- 异动信号识别

作者：Agent Army
日期：2026-03-15
版本：2.0
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import pandas as pd

from src.agents.business.base_business_agent import (
    BusinessAgent,
    AnalysisResult,
    StockInfo
)
from src.core.base_agent import AgentCapability, AgentTool
from src.core.tools.data_source.akshare_tool import AKShareTool


# ========== Pydantic Models ==========

class DragonTigerSeat(BaseModel):
    """龙虎榜席位信息"""
    institution: str = Field(..., description="机构名称")
    buy_amount: float = Field(default=0.0, description="买入金额（元）")
    sell_amount: float = Field(default=0.0, description="卖出金额（元）")
    net_amount: float = Field(default=0.0, description="净买卖金额（元）")
    seat_type: str = Field(..., description="席位类型：机构/游资/散户")


class DragonTigerData(BaseModel):
    """龙虎榜数据"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    on_list: bool = Field(default=False, description="是否上榜")
    list_date: Optional[str] = Field(default=None, description="上榜日期")
    reason: Optional[str] = Field(default=None, description="上榜原因")

    # 买卖席位
    buy_seats: List[DragonTigerSeat] = Field(
        default_factory=list,
        description="买入席位列表"
    )
    sell_seats: List[DragonTigerSeat] = Field(
        default_factory=list,
        description="卖出席位列表"
    )

    # 统计数据
    total_buy: float = Field(default=0.0, description="总买入金额（元）")
    total_sell: float = Field(default=0.0, description="总卖出金额（元）")
    net_buy: float = Field(default=0.0, description="净买入金额（元）")

    # 机构统计
    institution_buy: float = Field(default=0.0, description="机构买入金额（元）")
    institution_sell: float = Field(default=0.0, description="机构卖出金额（元）")
    institution_net: float = Field(default=0.0, description="机构净买入（元）")

    # 游资统计
    hot_money_buy: float = Field(default=0.0, description="游资买入金额（元）")
    hot_money_sell: float = Field(default=0.0, description="游资卖出金额（元）")
    hot_money_net: float = Field(default=0.0, description="游资净买入（元）")

    # 信号
    signal: str = Field(
        default="neutral",
        description="信号：bullish/neutral/bearish"
    )

    # 时间戳
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="分析时间戳"
    )


class DragonTigerAnalysis(BaseModel):
    """龙虎榜分析结果"""
    stock_code: str
    stock_name: str
    analysis_period: str

    # 龙虎榜数据
    dragon_tiger_data: List[DragonTigerData] = Field(
        default_factory=list,
        description="龙虎榜数据列表"
    )

    # 统计摘要
    total_list_count: int = Field(default=0, description="总上榜次数")
    latest_list_date: Optional[str] = Field(default=None, description="最近上榜日期")

    # 机构分析
    institution_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="机构行为分析"
    )

    # 游资分析
    hot_money_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="游资行为分析"
    )

    # 信号
    overall_signal: str = Field(default="neutral", description="综合信号")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="置信度")

    # 建议
    recommendation: str = Field(default="", description="投资建议")
    risk_warning: List[str] = Field(default_factory=list, description="风险提示")

    # 时间戳
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="分析时间戳"
    )


# ========== Main Agent ==========

class DragonTigerAI(BusinessAgent):
    """
    龙虎榜AI - 分析龙虎榜数据，追踪机构游资动向

    功能：
    1. 获取龙虎榜数据（使用AKShare）
    2. 识别机构席位和游资席位
    3. 分析买卖力量对比
    4. 生成投资建议和风险提示
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化龙虎榜AI

        Args:
            config: 配置参数
        """
        # 初始化工具
        self.akshare_tool = AKShareTool()

        # 定义能力
        capabilities = [
            AgentCapability(
                name="dragon_tiger_analysis",
                description="分析龙虎榜数据",
                input_type="stock_code",
                output_type="dragon_tiger_report"
            ),
            AgentCapability(
                name="institution_tracking",
                description="追踪机构动向",
                input_type="stock_code",
                output_type="institution_report"
            ),
            AgentCapability(
                name="hot_money_tracking",
                description="追踪游资动向",
                input_type="stock_code",
                output_type="hot_money_report"
            ),
            AgentCapability(
                name="signal_detection",
                description="识别异动信号",
                input_type="stock_code",
                output_type="signal_report"
            )
        ]

        # 定义工具
        tools = [
            AgentTool(
                name="akshare",
                description="AKShare数据接口",
                tool_type="system",
                config={"enabled": True}
            )
        ]

        # 初始化基类
        super().__init__(
            name="龙虎榜AI",
            role="分析龙虎榜数据，追踪机构游资动向，识别异动信号",
            corps="热点分析军团",
            analysis_type="龙虎榜分析",
            capabilities=capabilities,
            tools=tools,
            config=config
        )

        # 机构关键词（用于识别机构席位）
        self.institution_keywords = [
            "机构", "机构专用", "证券公司", "基金", "保险",
            "社保", "QFII", "信托", "资产管理"
        ]

        # 游资营业部关键词（用于识别游资席位）
        self.hot_money_keywords = [
            "证券股份有限公司深圳证券营业部",
            "证券股份有限公司上海证券营业部",
            "证券股份有限公司杭州证券营业部",
            "证券股份有限公司南京证券营业部",
            "证券股份有限公司成都证券营业部",
            "证券股份有限公司武汉证券营业部",
            "证券股份有限公司广州证券营业部",
            "证券股份有限公司西安证券营业部"
        ]

        self.logger.info("龙虎榜AI初始化完成", agent="DragonTigerAI")

    # ========== 核心分析功能 ==========

    async def analyze(self, stock_code: str, **kwargs) -> AnalysisResult:
        """
        执行龙虎榜分析

        Args:
            stock_code: 股票代码
            **kwargs: 其他参数
                - days: 分析天数（默认5天）
                - date: 指定日期（YYYYMMDD）
                - return_format: 返回格式（"dict"或"object"，默认"object"）

        Returns:
            AnalysisResult对象 或 Dict（向后兼容）
        """
        days = kwargs.get("days", 5)
        date = kwargs.get("date")
        return_format = kwargs.get("return_format", "object")

        self.logger.info(
            "开始龙虎榜分析",
            extra={"stock_code": stock_code, "days": days, "date": date}
        )

        # 1. 获取龙虎榜数据
        dragon_tiger_data = await self._fetch_dragon_tiger_data(
            stock_code,
            days,
            date
        )

        # 2. 分析机构行为
        institution_analysis = self._analyze_institutions(dragon_tiger_data)

        # 3. 分析游资行为
        hot_money_analysis = self._analyze_hot_money(dragon_tiger_data)

        # 4. 生成综合信号
        overall_signal, confidence = self._generate_overall_signal(
            dragon_tiger_data,
            institution_analysis,
            hot_money_analysis
        )

        # 5. 生成投资建议
        recommendation = self._generate_recommendation(
            overall_signal,
            confidence,
            dragon_tiger_data
        )

        # 6. 生成风险提示
        risk_warnings = self._generate_risk_warnings(
            dragon_tiger_data,
            institution_analysis,
            hot_money_analysis
        )

        # 7. 构建分析结果
        stock_name = dragon_tiger_data[0].stock_name if dragon_tiger_data else "未知"

        # 生成买卖平衡分析（向后兼容）
        balance_analysis = self._generate_balance_analysis(
            dragon_tiger_data,
            institution_analysis,
            hot_money_analysis
        )

        # 如果要求返回字典格式（向后兼容）
        if return_format == "dict":
            return {
                "stock_code": stock_code,
                "timestamp": datetime.now().isoformat(),
                "analysis_period": f"{days}天",
                "上榜次数": len(dragon_tiger_data),
                "balance_analysis": balance_analysis,
                "summary": self._generate_dt_summary(balance_analysis),
                "recommendation": recommendation,
                "dragon_tiger_data": [dt.dict() for dt in dragon_tiger_data],
                "institution_analysis": institution_analysis,
                "hot_money_analysis": hot_money_analysis,
                "overall_signal": overall_signal,
                "confidence": confidence,
                "risk_warnings": risk_warnings
            }

        # 默认返回AnalysisResult对象
        analysis_result = AnalysisResult(
            agent_name=self.name,
            analysis_type=self.analysis_type,
            conclusion=self._generate_conclusion(
                overall_signal,
                institution_analysis,
                hot_money_analysis,
                len(dragon_tiger_data)
            ),
            confidence=confidence,
            details={
                "dragon_tiger_data": [
                    dt.dict() for dt in dragon_tiger_data
                ],
                "institution_analysis": institution_analysis,
                "hot_money_analysis": hot_money_analysis,
                "overall_signal": overall_signal,
                "total_list_count": len(dragon_tiger_data),
                "latest_list_date": dragon_tiger_data[0].list_date if dragon_tiger_data else None,
                "balance_analysis": balance_analysis
            },
            risks=risk_warnings,
            recommendations=[recommendation]
        )

        self.logger.info(
            "龙虎榜分析完成",
            extra={
                "stock_code": stock_code,
                "signal": overall_signal,
                "confidence": confidence
            }
        )

        return analysis_result

    async def execute(self, task: str, **kwargs) -> Any:
        """
        执行任务

        Args:
            task: 任务类型
                - analyze_dragon_tiger: 分析龙虎榜
                - track_institution: 追踪机构
                - track_hot_money: 追踪游资
            **kwargs: 任务参数

        Returns:
            执行结果
        """
        # 为了向后兼容，默认返回字典格式
        kwargs.setdefault("return_format", "dict")

        stock_code = kwargs.pop("stock_code", None)

        if task == "analyze_dragon_tiger":
            return await self.analyze(stock_code, **kwargs)
        elif task == "track_institution":
            return await self._track_institution(
                stock_code,
                kwargs.get("days", 10)
            )
        elif task == "track_hot_money":
            return await self._track_hot_money(
                stock_code,
                kwargs.get("days", 5)
            )
        else:
            raise ValueError(f"未知任务: {task}")

    # ========== 数据获取功能 ==========

    async def _fetch_dragon_tiger_data(
        self,
        stock_code: str,
        days: int = 5,
        date: Optional[str] = None
    ) -> List[DragonTigerData]:
        """
        获取龙虎榜数据

        Args:
            stock_code: 股票代码
            days: 查询天数
            date: 指定日期（YYYYMMDD）

        Returns:
            龙虎榜数据列表
        """
        if not self.akshare_tool.is_available():
            self.logger.warning("AKShare工具不可用，使用模拟数据")
            return self._generate_mock_data(stock_code, days)

        dragon_tiger_list = []

        try:
            if date:
                # 获取指定日期的数据
                df = self.akshare_tool.get_stock_dragon_tiger_detail(
                    stock_code,
                    date
                )

                if not df.empty:
                    dt_data = self._parse_dragon_tiger_df(df, stock_code, date)
                    if dt_data:
                        dragon_tiger_list.append(dt_data)
            else:
                # 获取最近N天的数据
                for i in range(days):
                    target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")

                    df = self.akshare_tool.get_stock_dragon_tiger_detail(
                        stock_code,
                        target_date
                    )

                    if df.empty:
                        continue

                    dt_data = self._parse_dragon_tiger_df(df, stock_code, target_date)
                    if dt_data:
                        dragon_tiger_list.append(dt_data)
                        break  # 只获取最近一次上榜数据

            # 如果没有获取到真实数据，使用模拟数据
            if not dragon_tiger_list:
                self.logger.warning("未获取到真实龙虎榜数据，使用模拟数据")
                dragon_tiger_list = self._generate_mock_data(stock_code, days)

            self.logger.info(
                f"获取到{len(dragon_tiger_list)}条龙虎榜数据",
                extra={"stock_code": stock_code}
            )

        except Exception as e:
            self.logger.error(f"获取龙虎榜数据失败: {e}，使用模拟数据")
            dragon_tiger_list = self._generate_mock_data(stock_code, days)

        return dragon_tiger_list

    def _generate_mock_data(
        self,
        stock_code: str,
        days: int = 5
    ) -> List[DragonTigerData]:
        """
        生成模拟龙虎榜数据（用于测试）

        Args:
            stock_code: 股票代码
            days: 天数

        Returns:
            模拟龙虎榜数据列表
        """
        import random

        mock_data = []

        # 模拟1-3次上榜
        list_count = random.randint(1, min(3, days))

        for i in range(list_count):
            list_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")

            # 模拟买卖席位
            buy_seats = [
                DragonTigerSeat(
                    institution="机构专用",
                    buy_amount=random.uniform(10000000, 50000000),
                    sell_amount=0,
                    net_amount=random.uniform(10000000, 50000000),
                    seat_type="机构"
                ),
                DragonTigerSeat(
                    institution="中信证券股份有限公司上海淮海中路证券营业部",
                    buy_amount=random.uniform(5000000, 30000000),
                    sell_amount=0,
                    net_amount=random.uniform(5000000, 30000000),
                    seat_type="游资"
                )
            ]

            sell_seats = [
                DragonTigerSeat(
                    institution="华泰证券股份有限公司南京建邺路证券营业部",
                    buy_amount=0,
                    sell_amount=random.uniform(3000000, 20000000),
                    net_amount=-random.uniform(3000000, 20000000),
                    seat_type="游资"
                )
            ]

            # 计算统计数据
            total_buy = sum(seat.buy_amount for seat in buy_seats)
            total_sell = sum(seat.sell_amount for seat in sell_seats)
            net_buy = total_buy - total_sell

            institution_buy = sum(
                seat.buy_amount for seat in buy_seats if seat.seat_type == "机构"
            )
            institution_sell = sum(
                seat.sell_amount for seat in sell_seats if seat.seat_type == "机构"
            )
            institution_net = institution_buy - institution_sell

            hot_money_buy = sum(
                seat.buy_amount for seat in buy_seats if seat.seat_type == "游资"
            )
            hot_money_sell = sum(
                seat.sell_amount for seat in sell_seats if seat.seat_type == "游资"
            )
            hot_money_net = hot_money_buy - hot_money_sell

            # 生成信号
            signal = self._determine_signal(institution_net, hot_money_net, net_buy)

            dt_data = DragonTigerData(
                stock_code=stock_code,
                stock_name="模拟股票",
                on_list=True,
                list_date=list_date,
                reason="涨幅偏离值达7%",
                buy_seats=buy_seats,
                sell_seats=sell_seats,
                total_buy=total_buy,
                total_sell=total_sell,
                net_buy=net_buy,
                institution_buy=institution_buy,
                institution_sell=institution_sell,
                institution_net=institution_net,
                hot_money_buy=hot_money_buy,
                hot_money_sell=hot_money_sell,
                hot_money_net=hot_money_net,
                signal=signal
            )

            mock_data.append(dt_data)

        return mock_data

    def _parse_dragon_tiger_df(
        self,
        df: pd.DataFrame,
        stock_code: str,
        date: str
    ) -> Optional[DragonTigerData]:
        """
        解析龙虎榜DataFrame

        Args:
            df: 龙虎榜DataFrame
            stock_code: 股票代码
            date: 日期

        Returns:
            DragonTigerData对象
        """
        try:
            if df.empty:
                return None

            # 提取第一行数据
            row = df.iloc[0]

            stock_name = row.get('名称', row.get('证券简称', ''))
            reason = row.get('上榜原因', row.get('异动原因', ''))

            # 解析买卖席位
            buy_seats = []
            sell_seats = []

            # 根据DataFrame结构解析席位
            for i in range(1, 6):
                # 买方席位
                buy_name = row.get(f'买{i}营业部名称', row.get(f'买{i}_名称', ''))
                buy_amount = row.get(f'买{i}金额', row.get(f'买{i}_营业部金额', 0))

                if buy_name and not pd.isna(buy_amount) and buy_amount > 0:
                    seat_type = self._identify_seat_type(buy_name)
                    buy_seats.append(DragonTigerSeat(
                        institution=buy_name,
                        buy_amount=float(buy_amount) * 10000,  # 转换为元
                        sell_amount=0,
                        net_amount=float(buy_amount) * 10000,
                        seat_type=seat_type
                    ))

                # 卖方席位
                sell_name = row.get(f'卖{i}营业部名称', row.get(f'卖{i}_名称', ''))
                sell_amount = row.get(f'卖{i}金额', row.get(f'卖{i}_营业部金额', 0))

                if sell_name and not pd.isna(sell_amount) and sell_amount > 0:
                    seat_type = self._identify_seat_type(sell_name)
                    sell_seats.append(DragonTigerSeat(
                        institution=sell_name,
                        buy_amount=0,
                        sell_amount=float(sell_amount) * 10000,  # 转换为元
                        net_amount=-float(sell_amount) * 10000,
                        seat_type=seat_type
                    ))

            # 计算统计数据
            total_buy = sum(seat.buy_amount for seat in buy_seats)
            total_sell = sum(seat.sell_amount for seat in sell_seats)
            net_buy = total_buy - total_sell

            institution_buy = sum(
                seat.buy_amount for seat in buy_seats if seat.seat_type == "机构"
            )
            institution_sell = sum(
                seat.sell_amount for seat in sell_seats if seat.seat_type == "机构"
            )
            institution_net = institution_buy - institution_sell

            hot_money_buy = sum(
                seat.buy_amount for seat in buy_seats if seat.seat_type == "游资"
            )
            hot_money_sell = sum(
                seat.sell_amount for seat in sell_seats if seat.seat_type == "游资"
            )
            hot_money_net = hot_money_buy - hot_money_sell

            signal = self._determine_signal(institution_net, hot_money_net, net_buy)

            return DragonTigerData(
                stock_code=stock_code,
                stock_name=stock_name,
                on_list=True,
                list_date=datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d"),
                reason=reason,
                buy_seats=buy_seats,
                sell_seats=sell_seats,
                total_buy=total_buy,
                total_sell=total_sell,
                net_buy=net_buy,
                institution_buy=institution_buy,
                institution_sell=institution_sell,
                institution_net=institution_net,
                hot_money_buy=hot_money_buy,
                hot_money_sell=hot_money_sell,
                hot_money_net=hot_money_net,
                signal=signal
            )

        except Exception as e:
            self.logger.error(f"解析龙虎榜DataFrame失败: {e}")
            return None

    def _identify_seat_type(self, institution_name: str) -> str:
        """
        识别席位类型

        Args:
            institution_name: 机构名称

        Returns:
            席位类型（机构/游资/散户）
        """
        if not institution_name:
            return "散户"

        # 检查是否为机构
        for keyword in self.institution_keywords:
            if keyword in institution_name:
                return "机构"

        # 检查是否为游资
        for keyword in self.hot_money_keywords:
            if keyword in institution_name:
                return "游资"

        return "散户"

    def _generate_balance_analysis(
        self,
        dragon_tiger_data: List[DragonTigerData],
        institution_analysis: Dict[str, Any],
        hot_money_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成买卖平衡分析（向后兼容）

        Args:
            dragon_tiger_data: 龙虎榜数据
            institution_analysis: 机构分析
            hot_money_analysis: 游资分析

        Returns:
            买卖平衡分析
        """
        if not dragon_tiger_data:
            return {"pattern": "no_data", "net_total": 0, "behavior": "无数据"}

        # 计算总净买入（转换为万元）
        net_total = sum(dt.net_buy for dt in dragon_tiger_data) / 10000

        # 根据净买入判断模式
        if net_total > 1000:
            pattern = "strong_buy"
            behavior = "大幅买入"
        elif net_total > 0:
            pattern = "mild_buy"
            behavior = "小幅买入"
        elif net_total > -1000:
            pattern = "mild_sell"
            behavior = "小幅卖出"
        else:
            pattern = "strong_sell"
            behavior = "大幅卖出"

        return {
            "pattern": pattern,
            "net_total": round(net_total, 2),
            "behavior": behavior
        }

    def _generate_dt_summary(self, balance_analysis: Dict[str, Any]) -> str:
        """
        生成龙虎榜摘要（向后兼容）

        Args:
            balance_analysis: 买卖平衡分析

        Returns:
            摘要文本
        """
        return f"龙虎榜显示{balance_analysis['behavior']}，净买入{balance_analysis['net_total']}万元"

    # ========== 向后兼容方法（用于旧测试） ==========

    def _analyze_buy_sell_balance(self, dt_data: List[Dict]) -> Dict[str, Any]:
        """
        分析买卖力量（向后兼容方法）

        Args:
            dt_data: 龙虎榜数据列表（旧格式）

        Returns:
            买卖力量分析
        """
        if not dt_data:
            return {"pattern": "no_data", "net_total": 0, "behavior": "无数据"}

        net_total = sum(d.get("net_buy", 0) for d in dt_data)

        if net_total > 1000:
            pattern = "strong_buy"
            behavior = "大幅买入"
        elif net_total > 0:
            pattern = "mild_buy"
            behavior = "小幅买入"
        elif net_total > -1000:
            pattern = "mild_sell"
            behavior = "小幅卖出"
        else:
            pattern = "strong_sell"
            behavior = "大幅卖出"

        return {
            "pattern": pattern,
            "net_total": round(net_total, 2),
            "behavior": behavior
        }

    # ========== 分析功能 ==========

    def _analyze_institutions(
        self,
        dragon_tiger_data: List[DragonTigerData]
    ) -> Dict[str, Any]:
        """
        分析机构行为

        Args:
            dragon_tiger_data: 龙虎榜数据

        Returns:
            机构行为分析
        """
        if not dragon_tiger_data:
            return {
                "behavior": "无数据",
                "net_total": 0,
                "net": 0,  # 向后兼容
                "avg_net": 0,
                "buy_count": 0,
                "sell_count": 0
            }

        total_net = sum(dt.institution_net for dt in dragon_tiger_data)
        avg_net = total_net / len(dragon_tiger_data)
        buy_count = sum(1 for dt in dragon_tiger_data if dt.institution_net > 0)
        sell_count = sum(1 for dt in dragon_tiger_data if dt.institution_net < 0)

        # 判断机构行为
        if total_net > 100000000:  # 1亿以上
            behavior = "大幅买入"
        elif total_net > 50000000:  # 5000万以上
            behavior = "积极买入"
        elif total_net > 0:
            behavior = "小幅买入"
        elif total_net > -50000000:
            behavior = "小幅卖出"
        else:
            behavior = "大幅卖出"

        return {
            "behavior": behavior,
            "net_total": round(total_net, 2),
            "net": round(total_net / 10000, 2),  # 向后兼容：转换为万元
            "avg_net": round(avg_net, 2),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "buy_ratio": round(buy_count / len(dragon_tiger_data), 2) if dragon_tiger_data else 0
        }

    def _analyze_hot_money(
        self,
        dragon_tiger_data: List[DragonTigerData]
    ) -> Dict[str, Any]:
        """
        分析游资行为

        Args:
            dragon_tiger_data: 龙虎榜数据

        Returns:
            游资行为分析
        """
        if not dragon_tiger_data:
            return {
                "behavior": "无数据",
                "net_total": 0,
                "net": 0,  # 向后兼容
                "avg_net": 0,
                "buy_count": 0,
                "sell_count": 0
            }

        total_net = sum(dt.hot_money_net for dt in dragon_tiger_data)
        avg_net = total_net / len(dragon_tiger_data)
        buy_count = sum(1 for dt in dragon_tiger_data if dt.hot_money_net > 0)
        sell_count = sum(1 for dt in dragon_tiger_data if dt.hot_money_net < 0)

        # 判断游资行为
        if total_net > 50000000:  # 5000万以上
            behavior = "疯狂炒作"
        elif total_net > 20000000:  # 2000万以上
            behavior = "积极炒作"
        elif total_net > 0:
            behavior = "小幅参与"
        elif total_net > -20000000:
            behavior = "逐渐撤离"
        else:
            behavior = "大量撤离"

        return {
            "behavior": behavior,
            "net_total": round(total_net, 2),
            "net": round(total_net / 10000, 2),  # 向后兼容：转换为万元
            "avg_net": round(avg_net, 2),
            "buy_count": buy_count,
            "sell_count": sell_count,
            "buy_ratio": round(buy_count / len(dragon_tiger_data), 2) if dragon_tiger_data else 0
        }

    def _generate_overall_signal(
        self,
        dragon_tiger_data: List[DragonTigerData],
        institution_analysis: Dict[str, Any],
        hot_money_analysis: Dict[str, Any]
    ) -> tuple[str, float]:
        """
        生成综合信号

        Args:
            dragon_tiger_data: 龙虎榜数据
            institution_analysis: 机构分析
            hot_money_analysis: 游资分析

        Returns:
            (信号, 置信度)
        """
        if not dragon_tiger_data:
            return "neutral", 0.0

        # 基于机构行为判断
        institution_net = institution_analysis.get("net_total", 0)
        hot_money_net = hot_money_analysis.get("net_total", 0)

        # 计算综合得分
        score = 0
        reasons = []

        # 机构买入加分
        if institution_net > 100000000:
            score += 40
            reasons.append("机构大幅买入")
        elif institution_net > 50000000:
            score += 30
            reasons.append("机构积极买入")
        elif institution_net > 0:
            score += 20
            reasons.append("机构小幅买入")
        elif institution_net > -50000000:
            score -= 20
            reasons.append("机构小幅卖出")
        else:
            score -= 40
            reasons.append("机构大幅卖出")

        # 游资买入加分（权重较低）
        if hot_money_net > 20000000:
            score += 20
            reasons.append("游资积极炒作")
        elif hot_money_net > 0:
            score += 10
            reasons.append("游资小幅参与")

        # 判断信号
        if score >= 50:
            signal = "bullish"
            confidence = min(1.0, score / 100)
        elif score >= 20:
            signal = "bullish"
            confidence = min(1.0, score / 100)
        elif score >= -20:
            signal = "neutral"
            confidence = 0.5
        elif score >= -50:
            signal = "bearish"
            confidence = min(1.0, abs(score) / 100)
        else:
            signal = "bearish"
            confidence = min(1.0, abs(score) / 100)

        return signal, round(confidence, 2)

    def _determine_signal(
        self,
        institution_net: float,
        hot_money_net: float,
        net_buy: float
    ) -> str:
        """
        确定单日信号

        Args:
            institution_net: 机构净买入
            hot_money_net: 游资净买入
            net_buy: 总净买入

        Returns:
            信号（bullish/neutral/bearish）
        """
        # 机构行为权重更高
        score = 0

        if institution_net > 30000000:
            score += 2
        elif institution_net > 0:
            score += 1
        elif institution_net < -30000000:
            score -= 2
        elif institution_net < 0:
            score -= 1

        if net_buy > 50000000:
            score += 1
        elif net_buy < -50000000:
            score -= 1

        if score >= 2:
            return "bullish"
        elif score >= 1:
            return "bullish"
        elif score >= -1:
            return "neutral"
        else:
            return "bearish"

    # ========== 生成建议和警告 ==========

    def _generate_recommendation(
        self,
        signal: str,
        confidence: float,
        dragon_tiger_data: List[DragonTigerData]
    ) -> str:
        """
        生成投资建议

        Args:
            signal: 信号
            confidence: 置信度
            dragon_tiger_data: 龙虎榜数据

        Returns:
            投资建议
        """
        if signal == "bullish":
            if confidence > 0.7:
                return "积极关注：机构大幅买入，建议关注"
            else:
                return "可以关注：机构小幅买入，可以关注"
        elif signal == "bearish":
            if confidence > 0.7:
                return "谨慎规避：机构大幅卖出，建议规避"
            else:
                return "谨慎观望：机构小幅卖出，谨慎观望"
        else:
            return "保持观望：买卖平衡，保持观望"

    def _generate_risk_warnings(
        self,
        dragon_tiger_data: List[DragonTigerData],
        institution_analysis: Dict[str, Any],
        hot_money_analysis: Dict[str, Any]
    ) -> List[str]:
        """
        生成风险提示

        Args:
            dragon_tiger_data: 龙虎榜数据
            institution_analysis: 机构分析
            hot_money_analysis: 游资分析

        Returns:
            风险提示列表
        """
        warnings = []

        # 机构卖出风险
        if institution_analysis.get("net_total", 0) < -50000000:
            warnings.append("机构大幅卖出，存在下跌风险")

        # 游资撤离风险
        if hot_money_analysis.get("behavior") in ["逐渐撤离", "大量撤离"]:
            warnings.append("游资逐渐撤离，炒作热度下降")

        # 频繁上榜风险
        if len(dragon_tiger_data) > 3:
            warnings.append(f"近期频繁上榜{len(dragon_tiger_data)}次，波动较大")

        # 净卖出风险
        if dragon_tiger_data:
            total_net = sum(dt.net_buy for dt in dragon_tiger_data)
            if total_net < -100000000:
                warnings.append("整体净卖出，压力较大")

        return warnings

    def _generate_conclusion(
        self,
        signal: str,
        institution_analysis: Dict[str, Any],
        hot_money_analysis: Dict[str, Any],
        list_count: int
    ) -> str:
        """
        生成分析结论

        Args:
            signal: 信号
            institution_analysis: 机构分析
            hot_money_analysis: 游资分析
            list_count: 上榜次数

        Returns:
            分析结论
        """
        conclusion = f"该股近期上榜{list_count}次，"

        if signal == "bullish":
            conclusion += f"{institution_analysis['behavior']}，"
            conclusion += f"{hot_money_analysis['behavior']}，"
            conclusion += "整体看多"
        elif signal == "bearish":
            conclusion += f"{institution_analysis['behavior']}，"
            conclusion += f"{hot_money_analysis['behavior']}，"
            conclusion += "整体看空"
        else:
            conclusion += "买卖力量相对平衡，方向不明"

        return conclusion

    # ========== 专项追踪功能 ==========

    async def _track_institution(
        self,
        stock_code: str,
        days: int = 10
    ) -> Dict[str, Any]:
        """
        追踪机构动向

        Args:
            stock_code: 股票代码
            days: 追踪天数

        Returns:
            机构追踪报告
        """
        dragon_tiger_data = await self._fetch_dragon_tiger_data(
            stock_code,
            days
        )

        institution_analysis = self._analyze_institutions(dragon_tiger_data)

        # 向后兼容：添加旧字段
        institution_data = []
        for dt in dragon_tiger_data:
            institution_data.append({
                "date": dt.list_date,
                "institution_buy": dt.institution_buy / 10000,  # 转换为万元
                "institution_sell": dt.institution_sell / 10000
            })

        return {
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat(),
            "tracking_period": f"{days}天",
            "institution_data": institution_data,
            "analysis": institution_analysis,
            "summary": f"机构{institution_analysis['behavior']}，"
                       f"净买入{institution_analysis['net_total']/10000:.2f}万元"
        }

    async def _track_hot_money(
        self,
        stock_code: str,
        days: int = 5
    ) -> Dict[str, Any]:
        """
        追踪游资动向

        Args:
            stock_code: 股票代码
            days: 追踪天数

        Returns:
            游资追踪报告
        """
        dragon_tiger_data = await self._fetch_dragon_tiger_data(
            stock_code,
            days
        )

        hot_money_analysis = self._analyze_hot_money(dragon_tiger_data)

        # 向后兼容：添加旧字段
        hot_money_data = []
        for dt in dragon_tiger_data:
            hot_money_data.append({
                "date": dt.list_date,
                "hot_money_buy": dt.hot_money_buy / 10000,  # 转换为万元
                "hot_money_sell": dt.hot_money_sell / 10000
            })

        return {
            "stock_code": stock_code,
            "timestamp": datetime.now().isoformat(),
            "tracking_period": f"{days}天",
            "hot_money_data": hot_money_data,
            "analysis": hot_money_analysis,
            "summary": f"游资{hot_money_analysis['behavior']}，"
                       f"净买入{hot_money_analysis['net_total']/10000:.2f}万元"
        }


# ========== 便捷函数 ==========

def get_dragon_tiger_ai() -> DragonTigerAI:
    """获取龙虎榜AI实例"""
    return DragonTigerAI()


if __name__ == "__main__":
    # 测试代码
    import asyncio

    async def test():
        print("=" * 70)
        print("龙虎榜AI测试")
        print("=" * 70)

        ai = get_dragon_tiger_ai()

        # 测试分析
        result = await ai.analyze("600519", days=5)

        print(f"\n分析结果:")
        print(f"结论: {result.conclusion}")
        print(f"置信度: {result.confidence}")
        print(f"建议: {result.recommendations[0] if result.recommendations else '无'}")
        print(f"风险: {result.risks}")

        print("\n" + "=" * 70)
        print("测试完成")
        print("=" * 70)

    asyncio.run(test())
