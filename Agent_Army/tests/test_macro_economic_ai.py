"""
宏观经济AI测试 - Macro Economic AI Tests

测试内容：
1. 基础功能测试（初始化、能力检查）
2. 经济增长分析测试（GDP、PMI）
3. 货币政策分析测试（利率、流动性）
4. 财政政策分析测试（财政收支）
5. 通胀分析测试（CPI、PPI）
6. 汇率分析测试
7. 综合评估测试
8. 异常处理测试（无数据、API失败）

创建日期: 2026-03-15
版本: v1.0
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from src.agents.business.industry_analysis.macro_economic_ai import MacroEconomicAI


class TestMacroEconomicAI:
    """宏观经济AI测试类"""

    @pytest.fixture
    def macro_ai(self):
        """创建宏观经济AI实例"""
        return MacroEconomicAI()

    @pytest.fixture
    def mock_economic_growth_data(self):
        """模拟经济增长数据"""
        return {
            "gdp": {
                "value": 6.3,
                "trend": "平稳"
            },
            "pmi": {
                "manufacturing": 51.2,
                "non_manufacturing": 53.5,
                "composite": 52.0
            },
            "industrial_added_value": {
                "value": 5.8,
                "trend": "平稳"
            },
            "fixed_asset_investment": {
                "value": 5.2,
                "trend": "平稳"
            },
            "data_source": "mock_data",
            "update_time": "2026-03-15"
        }

    @pytest.fixture
    def mock_monetary_data(self):
        """模拟货币政策数据"""
        return {
            "interest_rate": {
                "lpr_1y": 3.45,
                "lpr_5y": 4.20,
                "mlf": 2.50,
                "trend": "降息"
            },
            "m2": {
                "value": 9.5,
                "trend": "平稳"
            },
            "social_financing": {
                "total": 35000,
                "yoy_growth": 11.2
            },
            "reserve_ratio": {
                "large_banks": 10.5,
                "trend": "降准"
            },
            "data_source": "mock_data",
            "update_time": "2026-03-15"
        }

    @pytest.fixture
    def mock_fiscal_data(self):
        """模拟财政政策数据"""
        return {
            "fiscal_revenue": {
                "total": 210000,
                "yoy_growth": 3.5
            },
            "fiscal_expenditure": {
                "total": 250000,
                "yoy_growth": 5.8
            },
            "deficit_rate": {
                "value": 2.8,
                "trend": "平稳"
            },
            "tax_revenue": {
                "total": 180000,
                "yoy_growth": 2.8
            },
            "data_source": "mock_data",
            "update_time": "2026-03-15"
        }

    @pytest.fixture
    def mock_inflation_data(self):
        """模拟通胀数据"""
        return {
            "cpi": {
                "value": 1.8,
                "trend": "平稳"
            },
            "ppi": {
                "value": -0.5,
                "trend": "平稳"
            },
            "core_cpi": {
                "value": 1.5
            },
            "inflation_expectation": {
                "value": 2.0
            },
            "data_source": "mock_data",
            "update_time": "2026-03-15"
        }

    @pytest.fixture
    def mock_exchange_rate_data(self):
        """模拟汇率数据"""
        return {
            "usd_cny": {
                "value": 7.20,
                "change": -0.02,
                "change_pct": -0.28,
                "trend": "平稳"
            },
            "eur_cny": {
                "value": 7.85,
                "change": 0.01,
                "change_pct": 0.13
            },
            "foreign_reserve": {
                "value": 31500,
                "change": -50
            },
            "data_source": "mock_data",
            "update_time": "2026-03-15"
        }

    # ========== 基础功能测试 ==========

    def test_initialization(self, macro_ai):
        """测试初始化"""
        assert macro_ai.name == "宏观经济AI"
        assert macro_ai.role == "分析宏观经济形势，评估投资环境"
        assert len(macro_ai.capabilities) == 6
        assert len(macro_ai.tools) == 2

    def test_capabilities(self, macro_ai):
        """测试能力列表"""
        capability_names = [cap.name for cap in macro_ai.capabilities]

        assert "economic_growth_analysis" in capability_names
        assert "monetary_policy_analysis" in capability_names
        assert "fiscal_policy_analysis" in capability_names
        assert "inflation_analysis" in capability_names
        assert "exchange_rate_analysis" in capability_names
        assert "macro_comprehensive_assessment" in capability_names

    def test_tools(self, macro_ai):
        """测试工具列表"""
        tool_names = [tool.name for tool in macro_ai.tools]

        assert "macro_tool" in tool_names
        assert "financial_tool" in tool_names

    # ========== 经济增长分析测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_economic_growth(self, macro_ai, mock_economic_growth_data):
        """测试经济增长分析"""
        with patch.object(
            macro_ai.macro_tool,
            'fetch_economic_growth_data',
            return_value=mock_economic_growth_data
        ):
            result = await macro_ai._analyze_economic_growth("1y")

            # 验证结构
            assert "gdp" in result
            assert "pmi" in result
            assert "industrial_added_value" in result
            assert "fixed_asset_investment" in result
            assert "total_score" in result
            assert "overall_assessment" in result

            # 验证GDP分析
            assert result["gdp"]["value"] == 6.3
            assert result["gdp"]["score"] > 0

            # 验证PMI分析
            assert result["pmi"]["manufacturing"] == 51.2
            assert result["pmi"]["composite"] == 52.0
            assert result["pmi"]["score"] > 0

            # 验证综合评分
            assert 0 <= result["total_score"] <= 100

    @pytest.mark.asyncio
    async def test_gdp_assessment(self, macro_ai):
        """测试GDP评估逻辑"""
        # 高增长
        assessment_high = macro_ai._assess_gdp(6.8)
        assert "强劲" in assessment_high or "强劲" == assessment_high

        # 平稳增长
        assessment_mid = macro_ai._assess_gdp(6.0)
        assert "平稳" in assessment_mid

        # 低增长
        assessment_low = macro_ai._assess_gdp(4.0)
        assert "乏力" in assessment_low or "放缓" in assessment_low

    @pytest.mark.asyncio
    async def test_pmi_assessment(self, macro_ai):
        """测试PMI评估逻辑"""
        # 高景气度
        assessment_high = macro_ai._assess_pmi(53.0)
        assert "高" in assessment_high

        # 扩张区间
        assessment_mid = macro_ai._assess_pmi(50.5)
        assert "扩张" in assessment_mid

        # 收缩区间
        assessment_low = macro_ai._assess_pmi(49.0)
        assert "收缩" in assessment_low

    @pytest.mark.asyncio
    async def test_economic_growth_scoring(self, macro_ai):
        """测试经济增长评分"""
        # 高GDP得分
        score_high = macro_ai._score_gdp(6.8)
        assert score_high >= 85

        # 中等GDP得分
        score_mid = macro_ai._score_gdp(6.0)
        assert 70 <= score_mid < 85

        # 低GDP得分
        score_low = macro_ai._score_gdp(4.5)
        assert score_low < 70

    # ========== 货币政策分析测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_monetary_policy(self, macro_ai, mock_monetary_data):
        """测试货币政策分析"""
        with patch.object(
            macro_ai.macro_tool,
            'fetch_monetary_policy_data',
            return_value=mock_monetary_data
        ):
            result = await macro_ai._analyze_monetary_policy("1y")

            # 验证结构
            assert "interest_rate" in result
            assert "m2" in result
            assert "social_financing" in result
            assert "reserve_ratio" in result
            assert "total_score" in result
            assert "policy_stance" in result

            # 验证利率分析
            assert result["interest_rate"]["lpr_1y"] == 3.45
            assert result["interest_rate"]["trend"] == "降息"

            # 验证M2分析
            assert result["m2"]["value"] == 9.5

            # 验证政策立场
            assert result["policy_stance"] in ["宽松", "偏紧缩", "中性"]

    @pytest.mark.asyncio
    async def test_interest_rate_scoring(self, macro_ai):
        """测试利率评分"""
        # 降息得分高
        score_cut = macro_ai._score_interest_rate("降息")
        assert score_cut >= 75

        # 持平中等
        score_hold = macro_ai._score_interest_rate("持平")
        assert 65 <= score_hold < 80

        # 加息得分低
        score_hike = macro_ai._score_interest_rate("加息")
        assert score_hike < 65

    @pytest.mark.asyncio
    async def test_m2_assessment(self, macro_ai):
        """测试M2评估"""
        assessment_high = macro_ai._assess_m2(10.0)
        assert "充裕" in assessment_high

        assessment_low = macro_ai._assess_m2(8.0)
        assert "一般" in assessment_low

    @pytest.mark.asyncio
    async def test_monetary_stance_determination(self, macro_ai):
        """测试货币政策立场判断"""
        # 宽松
        interest = {"score": 85}
        m2 = {"score": 85}
        stance = macro_ai._determine_monetary_stance(interest, m2, {})
        assert stance == "宽松"

        # 中性
        interest_mid = {"score": 70}
        m2_mid = {"score": 70}
        stance_mid = macro_ai._determine_monetary_stance(interest_mid, m2_mid, {})
        assert stance_mid == "中性"

    # ========== 财政政策分析测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_fiscal_policy(self, macro_ai, mock_fiscal_data):
        """测试财政政策分析"""
        with patch.object(
            macro_ai.macro_tool,
            'fetch_fiscal_policy_data',
            return_value=mock_fiscal_data
        ):
            result = await macro_ai._analyze_fiscal_policy("1y")

            # 验证结构
            assert "fiscal_revenue" in result
            assert "fiscal_expenditure" in result
            assert "deficit_rate" in result
            assert "tax_revenue" in result
            assert "total_score" in result
            assert "policy_stance" in result

            # 验证赤字率
            assert result["deficit_rate"]["value"] == 2.8

            # 验证财政支出
            assert result["fiscal_expenditure"]["yoy_growth"] == 5.8

    @pytest.mark.asyncio
    async def test_deficit_assessment(self, macro_ai):
        """测试赤字率评估"""
        # 低赤字
        assessment_low = macro_ai._assess_deficit(2.5)
        assert "可控" in assessment_low

        # 高赤字
        assessment_high = macro_ai._assess_deficit(4.0)
        assert "较高" in assessment_high

    @pytest.mark.asyncio
    async def test_fiscal_stance_determination(self, macro_ai):
        """测试财政政策立场判断"""
        # 积极
        expenditure = {"score": 85}
        deficit = {"score": 80}
        stance = macro_ai._determine_fiscal_stance(expenditure, deficit)
        assert stance == "积极"

        # 中性
        expenditure_mid = {"score": 65}
        deficit_mid = {"score": 70}
        stance_mid = macro_ai._determine_fiscal_stance(expenditure_mid, deficit_mid)
        assert stance_mid == "中性"

    # ========== 通胀分析测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_inflation(self, macro_ai, mock_inflation_data):
        """测试通胀分析"""
        with patch.object(
            macro_ai.macro_tool,
            'fetch_inflation_data',
            return_value=mock_inflation_data
        ):
            result = await macro_ai._analyze_inflation("1y")

            # 验证结构
            assert "cpi" in result
            assert "ppi" in result
            assert "core_cpi" in result
            assert "inflation_expectation" in result
            assert "total_score" in result
            assert "inflation_environment" in result

            # 验证CPI
            assert result["cpi"]["value"] == 1.8

            # 验证PPI
            assert result["ppi"]["value"] == -0.5

    @pytest.mark.asyncio
    async def test_cpi_assessment(self, macro_ai):
        """测试CPI评估"""
        # 温和通胀
        assessment_good = macro_ai._assess_cpi(2.0)
        assert "温和" in assessment_good

        # 通胀压力
        assessment_high = macro_ai._assess_cpi(3.5)
        assert "压力" in assessment_high

        # 通缩风险
        assessment_low = macro_ai._assess_cpi(-0.5)
        assert "通缩" in assessment_low

    @pytest.mark.asyncio
    async def test_inflation_environment_determination(self, macro_ai):
        """测试通胀环境判断"""
        cpi = {"score": 85}
        ppi = {"score": 80}
        core_cpi = {"score": 85}

        environment = macro_ai._determine_inflation_environment(cpi, ppi, core_cpi)
        assert "温和" in environment or "有利于" in environment

    # ========== 汇率分析测试 ==========

    @pytest.mark.asyncio
    async def test_analyze_exchange_rate(self, macro_ai, mock_exchange_rate_data):
        """测试汇率分析"""
        with patch.object(
            macro_ai.macro_tool,
            'fetch_exchange_rate_data',
            return_value=mock_exchange_rate_data
        ):
            result = await macro_ai._analyze_exchange_rate("1y")

            # 验证结构
            assert "usd_cny" in result
            assert "eur_cny" in result
            assert "foreign_reserve" in result
            assert "total_score" in result
            assert "exchange_environment" in result

            # 验证美元汇率
            assert result["usd_cny"]["value"] == 7.20

            # 验证外汇储备
            assert result["foreign_reserve"]["value"] == 31500

    @pytest.mark.asyncio
    async def test_usd_rate_assessment(self, macro_ai):
        """测试美元汇率评估"""
        # 升值
        assessment_appreciate = macro_ai._assess_usd_rate(7.0, "升值")
        assert "升值" in assessment_appreciate

        # 贬值
        assessment_depreciate = macro_ai._assess_usd_rate(7.5, "贬值")
        assert "贬值" in assessment_depreciate

        # 平稳
        assessment_stable = macro_ai._assess_usd_rate(7.2, "平稳")
        assert "稳定" in assessment_stable

    # ========== 综合评估测试 ==========

    @pytest.mark.asyncio
    async def test_comprehensive_analysis(
        self,
        macro_ai,
        mock_economic_growth_data,
        mock_monetary_data,
        mock_fiscal_data,
        mock_inflation_data,
        mock_exchange_rate_data
    ):
        """测试综合分析"""
        # Mock所有数据获取
        with patch.object(
            macro_ai.macro_tool,
            'fetch_economic_growth_data',
            return_value=mock_economic_growth_data
        ), patch.object(
            macro_ai.macro_tool,
            'fetch_monetary_policy_data',
            return_value=mock_monetary_data
        ), patch.object(
            macro_ai.macro_tool,
            'fetch_fiscal_policy_data',
            return_value=mock_fiscal_data
        ), patch.object(
            macro_ai.macro_tool,
            'fetch_inflation_data',
            return_value=mock_inflation_data
        ), patch.object(
            macro_ai.macro_tool,
            'fetch_exchange_rate_data',
            return_value=mock_exchange_rate_data
        ):
            result = await macro_ai.analyze("1y")

            # 验证整体结构
            assert result["analysis_type"] == "macro_economic"
            assert "timestamp" in result
            assert "time_range" in result

            # 验证五大维度
            assert "economic_growth" in result
            assert "monetary_policy" in result
            assert "fiscal_policy" in result
            assert "inflation" in result
            assert "exchange_rate" in result

            # 验证综合评分
            assert "macro_score" in result
            assert "total_score" in result["macro_score"]
            assert "rating" in result["macro_score"]
            assert result["macro_score"]["rating"] in ["A", "B", "C", "D", "E"]

            # 验证投资环境评估
            assert "investment_environment" in result
            assert "environment" in result["investment_environment"]
            assert "risk_level" in result["investment_environment"]

            # 验证政策导向
            assert "policy_orientation" in result
            assert "orientation" in result["policy_orientation"]

            # 验证风险预警
            assert "risk_warnings" in result
            assert isinstance(result["risk_warnings"], list)

            # 验证投资建议
            assert "investment_suggestion" in result
            assert "action" in result["investment_suggestion"]
            assert "position_suggestion" in result["investment_suggestion"]

    @pytest.mark.asyncio
    async def test_macro_score_calculation(self, macro_ai):
        """测试宏观经济综合评分计算"""
        # 创建模拟的五大维度数据
        economic_growth = {"total_score": 75.0}
        monetary_policy = {"total_score": 70.0}
        fiscal_policy = {"total_score": 68.0}
        inflation = {"total_score": 72.0}
        exchange_rate = {"total_score": 65.0}

        result = macro_ai._calculate_macro_score(
            economic_growth,
            monetary_policy,
            fiscal_policy,
            inflation,
            exchange_rate
        )

        # 验证加权平均计算
        expected_score = (
            75.0 * 0.30 +
            70.0 * 0.25 +
            68.0 * 0.20 +
            72.0 * 0.15 +
            65.0 * 0.10
        )

        assert abs(result["total_score"] - expected_score) < 0.1
        assert "rating" in result
        assert "dimension_scores" in result

    @pytest.mark.asyncio
    async def test_investment_environment_assessment(self, macro_ai):
        """测试投资环境评估"""
        # 高分环境
        macro_score_high = {"total_score": 80}
        env_high = macro_ai._assess_investment_environment(macro_score_high)
        assert env_high["environment"] == "积极"
        assert env_high["risk_level"] == "低"

        # 中等环境
        macro_score_mid = {"total_score": 60}
        env_mid = macro_ai._assess_investment_environment(macro_score_mid)
        assert env_mid["environment"] == "中性"
        assert env_mid["risk_level"] == "中"

        # 低分环境
        macro_score_low = {"total_score": 40}
        env_low = macro_ai._assess_investment_environment(macro_score_low)
        assert env_low["environment"] == "谨慎"
        assert env_low["risk_level"] == "高"

    @pytest.mark.asyncio
    async def test_policy_orientation_analysis(self, macro_ai):
        """测试政策导向分析"""
        # 双宽松
        monetary = {"policy_stance": "宽松"}
        fiscal = {"policy_stance": "积极"}
        orientation = macro_ai._analyze_policy_orientation(monetary, fiscal)
        assert orientation["orientation"] == "双宽松"
        assert "利好" in orientation["market_impact"]

        # 中性
        monetary_mid = {"policy_stance": "中性"}
        fiscal_mid = {"policy_stance": "中性"}
        orientation_mid = macro_ai._analyze_policy_orientation(monetary_mid, fiscal_mid)
        assert orientation_mid["orientation"] == "中性"

    @pytest.mark.asyncio
    async def test_risk_warnings_generation(self, macro_ai):
        """测试风险预警生成"""
        # 创建触发预警的场景
        economic_growth = {"total_score": 55.0}  # 低于60
        monetary_policy = {}
        fiscal_policy = {"deficit_rate": {"value": 3.5}}  # 高于3.0
        inflation = {"cpi": {"value": 3.5}}  # 高于3.0
        exchange_rate = {"usd_cny": {"trend": "贬值"}}

        warnings = macro_ai._generate_risk_warnings(
            economic_growth,
            monetary_policy,
            fiscal_policy,
            inflation,
            exchange_rate
        )

        # 应该生成多个预警
        assert len(warnings) >= 2

        # 验证预警结构
        for warning in warnings:
            assert "type" in warning
            assert "level" in warning
            assert "description" in warning
            assert "suggestion" in warning

    @pytest.mark.asyncio
    async def test_investment_suggestion_generation(self, macro_ai):
        """测试投资建议生成"""
        # 创建高分场景
        macro_score = {
            "total_score": 80.0,
            "rating": "A"
        }
        investment_environment = {
            "environment": "积极",
            "risk_level": "低"
        }
        policy_orientation = {
            "market_impact": "利好股市",
            "confidence": "高"
        }
        risk_warnings = []

        suggestion = macro_ai._generate_investment_suggestion(
            macro_score,
            investment_environment,
            policy_orientation,
            risk_warnings
        )

        # 验证建议结构
        assert "action" in suggestion
        assert "position_suggestion" in suggestion
        assert "sector_suggestion" in suggestion
        assert "strategy" in suggestion
        assert suggestion["action"] == "积极投资"

    # ========== 异常处理测试 ==========

    @pytest.mark.asyncio
    async def test_empty_data_handling(self, macro_ai):
        """测试空数据处理"""
        empty_data = {}

        with patch.object(
            macro_ai.macro_tool,
            'fetch_economic_growth_data',
            return_value=empty_data
        ):
            result = await macro_ai._analyze_economic_growth("1y")

            # 应该能处理空数据而不崩溃
            assert result is not None
            assert "total_score" in result

    @pytest.mark.asyncio
    async def test_api_failure_handling(self, macro_ai):
        """测试API失败处理"""
        # Mock API抛出异常
        with patch.object(
            macro_ai.macro_tool,
            'fetch_economic_growth_data',
            side_effect=Exception("API Error")
        ):
            # 应该抛出异常或返回错误结果
            with pytest.raises(Exception):
                await macro_ai._analyze_economic_growth("1y")

    @pytest.mark.asyncio
    async def test_missing_indicators(self, macro_ai):
        """测试缺失指标"""
        partial_data = {
            "gdp": {"value": 6.3},
            "pmi": {},  # 缺失PMI数据
            "industrial_added_value": {},
            "fixed_asset_investment": {}
        }

        with patch.object(
            macro_ai.macro_tool,
            'fetch_economic_growth_data',
            return_value=partial_data
        ):
            result = await macro_ai._analyze_economic_growth("1y")

            # 应该能处理缺失数据
            assert result is not None
            assert "total_score" in result

    @pytest.mark.asyncio
    async def test_execute_method_routing(self, macro_ai):
        """测试execute方法路由"""
        # 测试analyze任务
        with patch.object(
            macro_ai,
            'analyze',
            return_value={"test": "result"}
        ):
            result = await macro_ai.execute("analyze", time_range="1y")
            assert result == {"test": "result"}

        # 测试analyze_growth任务
        with patch.object(
            macro_ai,
            '_analyze_economic_growth',
            return_value={"growth": "analysis"}
        ):
            result = await macro_ai.execute("analyze_growth", time_range="1y")
            assert result == {"growth": "analysis"}

        # 测试未知任务
        with pytest.raises(ValueError, match="未知任务"):
            await macro_ai.execute("unknown_task")

    # ========== 边界情况测试 ==========

    @pytest.mark.asyncio
    async def test_extreme_high_scores(self, macro_ai):
        """测试极端高分情况"""
        # 所有维度都满分
        economic_growth = {"total_score": 100.0}
        monetary_policy = {"total_score": 100.0}
        fiscal_policy = {"total_score": 100.0}
        inflation = {"total_score": 100.0}
        exchange_rate = {"total_score": 100.0}

        result = macro_ai._calculate_macro_score(
            economic_growth,
            monetary_policy,
            fiscal_policy,
            inflation,
            exchange_rate
        )

        assert result["total_score"] == 100.0
        assert result["rating"] == "A"

    @pytest.mark.asyncio
    async def test_extreme_low_scores(self, macro_ai):
        """测试极端低分情况"""
        # 所有维度都最低分
        economic_growth = {"total_score": 0.0}
        monetary_policy = {"total_score": 0.0}
        fiscal_policy = {"total_score": 0.0}
        inflation = {"total_score": 0.0}
        exchange_rate = {"total_score": 0.0}

        result = macro_ai._calculate_macro_score(
            economic_growth,
            monetary_policy,
            fiscal_policy,
            inflation,
            exchange_rate
        )

        assert result["total_score"] == 0.0
        assert result["rating"] == "E"

    @pytest.mark.asyncio
    async def test_boundary_score_ratings(self, macro_ai):
        """测试边界评分等级"""
        test_cases = [
            (80, "A"),  # A级边界
            (70, "B"),  # B级边界
            (60, "C"),  # C级边界
            (50, "D"),  # D级边界
            (49, "E"),  # E级边界
        ]

        for score, expected_rating in test_cases:
            result = macro_ai._calculate_macro_score(
                {"total_score": score},
                {"total_score": score},
                {"total_score": score},
                {"total_score": score},
                {"total_score": score}
            )
            assert result["rating"] == expected_rating

    # ========== 集成测试 ==========

    @pytest.mark.asyncio
    async def test_full_workflow_with_realistic_data(
        self,
        macro_ai,
        mock_economic_growth_data,
        mock_monetary_data,
        mock_fiscal_data,
        mock_inflation_data,
        mock_exchange_rate_data
    ):
        """测试完整工作流程（使用真实模拟数据）"""
        with patch.object(
            macro_ai.macro_tool,
            'fetch_economic_growth_data',
            return_value=mock_economic_growth_data
        ), patch.object(
            macro_ai.macro_tool,
            'fetch_monetary_policy_data',
            return_value=mock_monetary_data
        ), patch.object(
            macro_ai.macro_tool,
            'fetch_fiscal_policy_data',
            return_value=mock_fiscal_data
        ), patch.object(
            macro_ai.macro_tool,
            'fetch_inflation_data',
            return_value=mock_inflation_data
        ), patch.object(
            macro_ai.macro_tool,
            'fetch_exchange_rate_data',
            return_value=mock_exchange_rate_data
        ):
            result = await macro_ai.analyze("1y")

            # 验证数据完整性
            assert "timestamp" in result
            assert result["time_range"] == "1y"

            # 验证所有维度都有评分
            assert result["economic_growth"]["total_score"] > 0
            assert result["monetary_policy"]["total_score"] > 0
            assert result["fiscal_policy"]["total_score"] > 0
            assert result["inflation"]["total_score"] > 0
            assert result["exchange_rate"]["total_score"] > 0

            # 验证综合评分合理
            macro_score = result["macro_score"]["total_score"]
            assert 0 <= macro_score <= 100

            # 验证投资建议与评分匹配
            suggestion = result["investment_suggestion"]
            if macro_score >= 75:
                assert "积极" in suggestion["action"]
            elif macro_score <= 45:
                assert "观望" in suggestion["action"]

    @pytest.mark.asyncio
    async def test_different_time_ranges(self, macro_ai):
        """测试不同时间范围"""
        time_ranges = ["1y", "5y", "10y"]

        for time_range in time_ranges:
            with patch.object(
                macro_ai.macro_tool,
                'fetch_economic_growth_data',
                return_value={"gdp": {"value": 6.0}}
            ), patch.object(
                macro_ai.macro_tool,
                'fetch_monetary_policy_data',
                return_value={"interest_rate": {"lpr_1y": 3.45}}
            ), patch.object(
                macro_ai.macro_tool,
                'fetch_fiscal_policy_data',
                return_value={"fiscal_revenue": {"total": 210000}}
            ), patch.object(
                macro_ai.macro_tool,
                'fetch_inflation_data',
                return_value={"cpi": {"value": 2.0}}
            ), patch.object(
                macro_ai.macro_tool,
                'fetch_exchange_rate_data',
                return_value={"usd_cny": {"value": 7.2}}
            ):
                result = await macro_ai.analyze(time_range)
                assert result["time_range"] == time_range


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src/agents/business/industry_analysis/macro_economic_ai", "--cov-report=html"])
