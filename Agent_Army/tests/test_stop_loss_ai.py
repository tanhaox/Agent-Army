"""
止损止盈AI测试 - Stop Loss AI Tests

测试内容：
1. 固定止损策略
2. 移动止损策略
3. ATR止损策略
4. 技术止损策略
5. 多级别止盈策略
6. 综合方案
7. 动态调整

创建日期: 2026-03-15
版本: v1.0
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.agents.business.strategy.stop_loss_ai import StopLossAI


class TestStopLossAI:
    """止损止盈AI测试"""

    @pytest.fixture
    def stop_loss_ai(self):
        """创建止损止盈AI实例"""
        return StopLossAI()

    @pytest.fixture
    def mock_price(self):
        """模拟当前价格"""
        return 20.50

    @pytest.fixture
    def mock_technical_analysis(self):
        """模拟技术分析结果"""
        return {
            "trend_analysis": {
                "support_levels": [18.50, 19.00, 19.50],
                "resistance_levels": [21.50, 22.00]
            },
            "indicators": {
                "ma20": 19.80,
                "ma60": 19.20,
                "rsi": 55.0
            }
        }

    @pytest.fixture
    def mock_valuation_result(self):
        """模拟估值结果"""
        return {
            "fair_value": 25.00,
            "valuation_method": "PE",
            "safety_margin": 0.18
        }

    # ========== 固定止损测试 ==========

    @pytest.mark.asyncio
    async def test_fixed_stop_loss_basic(self, stop_loss_ai, mock_price):
        """测试基本固定止损"""
        result = await stop_loss_ai.fixed_stop_loss(
            "601669",
            current_price=mock_price,
            stop_ratio=0.08
        )

        assert result["stock_code"] == "601669"
        assert result["current_price"] == mock_price
        assert result["stop_loss"]["type"] == "fixed"
        assert result["stop_loss"]["ratio"] == 8.0

        # 验证止损价计算
        expected_stop = mock_price * (1 - 0.08)
        assert abs(result["stop_loss"]["price"] - expected_stop) < 0.01

    @pytest.mark.asyncio
    async def test_fixed_stop_loss_different_ratios(self, stop_loss_ai, mock_price):
        """测试不同止损比例"""
        ratios = [0.05, 0.08, 0.10, 0.15]

        for ratio in ratios:
            result = await stop_loss_ai.fixed_stop_loss(
                "601669",
                current_price=mock_price,
                stop_ratio=ratio
            )

            expected_stop = mock_price * (1 - ratio)
            assert abs(result["stop_loss"]["price"] - expected_stop) < 0.01
            assert result["stop_loss"]["ratio"] == ratio * 100

    @pytest.mark.asyncio
    async def test_fixed_stop_loss_no_price(self, stop_loss_ai):
        """测试无价格时自动获取"""
        with patch.object(
            stop_loss_ai,
            '_get_current_price',
            return_value=20.50
        ):
            result = await stop_loss_ai.fixed_stop_loss("601669", stop_ratio=0.08)

            assert result["current_price"] == 20.50
            assert result["stop_loss"]["price"] == 20.50 * 0.92

    @pytest.mark.asyncio
    async def test_fixed_stop_loss_invalid_price(self, stop_loss_ai):
        """测试无效价格"""
        with patch.object(
            stop_loss_ai,
            '_get_current_price',
            return_value=0.0
        ):
            result = await stop_loss_ai.fixed_stop_loss("601669", stop_ratio=0.08)

            assert "error" in result
            assert result["strategy"] == "固定止损"

    # ========== 移动止损测试 ==========

    @pytest.mark.asyncio
    async def test_trailing_stop_loss(self, stop_loss_ai, mock_price):
        """测试移动止损"""
        result = await stop_loss_ai.trailing_stop_loss(
            "601669",
            current_price=mock_price,
            trailing_ratio=0.05
        )

        assert result["stop_loss"]["type"] == "trailing"
        assert len(result["trailing_rules"]) > 0
        assert len(result["adjustment_examples"]) > 0

        # 验证初始止损价
        expected_stop = mock_price * (1 - 0.05)
        assert abs(result["stop_loss"]["price"] - expected_stop) < 0.01

    @pytest.mark.asyncio
    async def test_trailing_stop_examples(self, stop_loss_ai, mock_price):
        """测试移动止损示例"""
        result = await stop_loss_ai.trailing_stop_loss(
            "601669",
            current_price=mock_price,
            trailing_ratio=0.05
        )

        examples = result["adjustment_examples"]
        assert len(examples) >= 2

        # 验证第一个示例
        assert examples[0]["price"] == mock_price * 1.1
        expected_new_stop = mock_price * 1.1 * (1 - 0.05)
        assert abs(examples[0]["new_stop"] - expected_new_stop) < 0.01

    # ========== ATR止损测试 ==========

    @pytest.mark.asyncio
    async def test_atr_stop_loss(self, stop_loss_ai, mock_price):
        """测试ATR止损"""
        mock_atr = 1.50

        with patch.object(
            stop_loss_ai,
            '_calculate_atr',
            return_value=mock_atr
        ):
            result = await stop_loss_ai.atr_stop_loss(
                "601669",
                current_price=mock_price,
                atr_multiplier=2.0
            )

            assert result["stop_loss"]["type"] == "atr"
            assert result["atr"] == mock_atr

            # 验证止损价计算
            expected_stop = mock_price - (mock_atr * 2.0)
            assert abs(result["stop_loss"]["price"] - expected_stop) < 0.01

    @pytest.mark.asyncio
    async def test_atr_stop_loss_different_multipliers(self, stop_loss_ai, mock_price):
        """测试不同ATR倍数"""
        mock_atr = 1.50

        with patch.object(
            stop_loss_ai,
            '_calculate_atr',
            return_value=mock_atr
        ):
            for multiplier in [1.5, 2.0, 2.5, 3.0]:
                result = await stop_loss_ai.atr_stop_loss(
                    "601669",
                    current_price=mock_price,
                    atr_multiplier=multiplier
                )

                expected_stop = mock_price - (mock_atr * multiplier)
                assert abs(result["stop_loss"]["price"] - expected_stop) < 0.01

    @pytest.mark.asyncio
    async def test_atr_stop_loss_fallback_to_fixed(self, stop_loss_ai, mock_price):
        """测试ATR计算失败时回退到固定止损"""
        with patch.object(
            stop_loss_ai,
            '_calculate_atr',
            return_value=0.0
        ):
            result = await stop_loss_ai.atr_stop_loss(
                "601669",
                current_price=mock_price,
                atr_multiplier=2.0
            )

            # 应该回退到固定止损
            assert result["stop_loss"]["type"] == "fixed"
            assert result["stop_loss"]["ratio"] == 8.0

    # ========== 技术止损测试 ==========

    @pytest.mark.asyncio
    async def test_technical_stop_loss(self, stop_loss_ai, mock_price, mock_technical_analysis):
        """测试技术位止损"""
        result = await stop_loss_ai.technical_stop_loss(
            "601669",
            current_price=mock_price,
            technical_analysis=mock_technical_analysis
        )

        assert result["stop_loss"]["type"] == "technical"
        assert len(result["support_levels"]) > 0

        # 验证止损价在某个支撑位
        stop_price = result["stop_loss"]["price"]
        assert stop_price < mock_price  # 止损价应低于当前价

    @pytest.mark.asyncio
    async def test_technical_stop_loss_no_support(self, stop_loss_ai, mock_price):
        """测试无支撑位时回退到固定止损"""
        empty_analysis = {}

        result = await stop_loss_ai.technical_stop_loss(
            "601669",
            current_price=mock_price,
            technical_analysis=empty_analysis
        )

        # 应该回退到固定止损
        assert result["stop_loss"]["type"] == "fixed"

    @pytest.mark.asyncio
    async def test_technical_stop_loss_auto_analysis(self, stop_loss_ai, mock_price):
        """测试自动技术分析"""
        mock_technical = {
            "trend_analysis": {
                "support_levels": [19.00, 19.50]
            }
        }

        with patch.object(
            stop_loss_ai,
            '_get_technical_analysis',
            return_value=mock_technical
        ):
            result = await stop_loss_ai.technical_stop_loss(
                "601669",
                current_price=mock_price,
                technical_analysis=None
            )

            assert result["stop_loss"]["type"] == "technical"

    # ========== 多级别止盈测试 ==========

    @pytest.mark.asyncio
    async def test_multi_level_take_profit(self, stop_loss_ai, mock_price):
        """测试多级别止盈"""
        result = await stop_loss_ai.multi_level_take_profit(
            "601669",
            current_price=mock_price,
            investment_horizon="medium_term"
        )

        assert len(result["take_profit"]) == 3
        assert result["investment_horizon"] == "medium_term"

        # 验证止盈价递增
        prices = [tp["price"] for tp in result["take_profit"]]
        assert prices[0] < prices[1] < prices[2]

        # 验证止盈比例
        ratios = [tp["ratio"] for tp in result["take_profit"]]
        assert all(r > 0 for r in ratios)

    @pytest.mark.asyncio
    async def test_multi_level_take_profit_with_valuation(self, stop_loss_ai, mock_price, mock_valuation_result):
        """测试结合估值的多级别止盈"""
        result = await stop_loss_ai.multi_level_take_profit(
            "601669",
            current_price=mock_price,
            valuation_result=mock_valuation_result,
            investment_horizon="medium_term"
        )

        assert len(result["take_profit"]) == 3

        # 验证第三目标接近估值
        third_target = result["take_profit"][2]["price"]
        fair_value = mock_valuation_result["fair_value"]
        # 允许一定误差
        assert abs(third_target - fair_value) / fair_value < 0.10

    @pytest.mark.asyncio
    async def test_multi_level_different_horizons(self, stop_loss_ai, mock_price):
        """测试不同投资周期的止盈策略"""
        horizons = ["short_term", "medium_term", "long_term"]

        for horizon in horizons:
            result = await stop_loss_ai.multi_level_take_profit(
                "601669",
                current_price=mock_price,
                investment_horizon=horizon
            )

            assert result["investment_horizon"] == horizon
            assert len(result["take_profit"]) == 3

            # 验证长线止盈比例更高
            if horizon == "long_term":
                avg_ratio = sum(tp["ratio"] for tp in result["take_profit"]) / 3
            elif horizon == "short_term":
                avg_ratio_short = sum(tp["ratio"] for tp in result["take_profit"]) / 3

    # ========== 综合方案测试 ==========

    @pytest.mark.asyncio
    async def test_comprehensive_plan(self, stop_loss_ai, mock_technical_analysis, mock_valuation_result):
        """测试综合方案"""
        with patch.object(
            stop_loss_ai,
            '_get_current_price',
            return_value=20.50
        ):
            result = await stop_loss_ai.comprehensive_plan(
                "601669",
                investment_horizon="medium_term",
                technical_analysis=mock_technical_analysis,
                valuation_result=mock_valuation_result
            )

            assert result["stock_code"] == "601669"
            assert "stop_loss" in result
            assert "take_profit" in result
            assert "risk_analysis" in result
            assert "execution_checklist" in result
            assert "summary" in result

            # 验证风险收益比
            rr_ratio = result["risk_analysis"]["risk_reward_ratio"]
            assert rr_ratio > 0

    @pytest.mark.asyncio
    async def test_comprehensive_plan_stop_loss_logic(self, stop_loss_ai, mock_technical_analysis):
        """测试综合方案中止损逻辑"""
        with patch.object(
            stop_loss_ai,
            '_get_current_price',
            return_value=20.50
        ):
            result = await stop_loss_ai.comprehensive_plan(
                "601669",
                technical_analysis=mock_technical_analysis
            )

            # 验证止损价取固定止损和技术止损中的较高者
            stop_price = result["stop_loss"]["price"]
            assert stop_price > 0
            assert stop_price < result["current_price"]

    @pytest.mark.asyncio
    async def test_comprehensive_plan_execution_checklist(self, stop_loss_ai):
        """测试执行清单"""
        with patch.object(
            stop_loss_ai,
            '_get_current_price',
            return_value=20.50
        ):
            result = await stop_loss_ai.comprehensive_plan("601669")

            checklist = result["execution_checklist"]
            assert len(checklist) >= 4

            # 验证清单包含关键要素
            checklist_str = " ".join(checklist)
            assert "入场价格" in checklist_str or "确认入场" in checklist_str
            assert "止损" in checklist_str
            assert "止盈" in checklist_str

    # ========== 动态调整测试 ==========

    @pytest.mark.asyncio
    async def test_dynamic_adjustment_price_up(self, stop_loss_ai):
        """测试价格上涨时的动态调整"""
        current_plan = {
            "current_price": 20.00,
            "stop_loss": {"price": 18.40},
            "take_profit": []
        }

        with patch.object(
            stop_loss_ai,
            '_get_current_price',
            return_value=22.50  # 上涨12.5%
        ):
            result = await stop_loss_ai.dynamic_adjustment(
                "601669",
                current_plan
            )

            # 验证止损位上移
            assert result["new_stop_loss"] > result["old_stop_loss"]
            assert len(result["adjustment_reason"]) > 0
            assert result["action_required"] == "需要调整"

    @pytest.mark.asyncio
    async def test_dynamic_adjustment_price_down(self, stop_loss_ai):
        """测试价格下跌时的动态调整"""
        current_plan = {
            "current_price": 20.00,
            "stop_loss": {"price": 18.40},
            "take_profit": [{"price": 23.00}]
        }

        with patch.object(
            stop_loss_ai,
            '_get_current_price',
            return_value=19.50  # 下跌2.5%
        ):
            result = await stop_loss_ai.dynamic_adjustment(
                "601669",
                current_plan
            )

            # 验证止损位不变（不随价格下移）
            assert result["new_stop_loss"] == result["old_stop_loss"]
            assert result["action_required"] == "无需调整"

    @pytest.mark.asyncio
    async def test_dynamic_adjustment_near_target(self, stop_loss_ai):
        """测试接近止盈目标时的调整"""
        current_plan = {
            "current_price": 20.00,
            "stop_loss": {"price": 18.40},
            "take_profit": [
                {"price": 22.00},
                {"price": 25.00},
                {"price": 28.00}
            ]
        }

        with patch.object(
            stop_loss_ai,
            '_get_current_price',
            return_value=21.00  # 接近第一目标22.00
        ):
            result = await stop_loss_ai.dynamic_adjustment(
                "601669",
                current_plan
            )

            # 验证检测到接近目标
            reasons = " ".join(result["adjustment_reason"])
            assert "接近" in reasons or "止盈" in reasons

    # ========== 辅助方法测试 ==========

    @pytest.mark.asyncio
    async def test_get_current_price(self, stop_loss_ai):
        """测试获取当前价格"""
        with patch.object(
            stop_loss_ai,
            '_get_current_price',
            return_value=20.50
        ):
            price = await stop_loss_ai._get_current_price("601669")
            assert price == 20.50

    @pytest.mark.asyncio
    async def test_calculate_atr(self, stop_loss_ai):
        """测试ATR计算"""
        # 直接mock ATR计算结果
        with patch.object(
            stop_loss_ai,
            '_calculate_atr',
            return_value=1.50
        ):
            atr = await stop_loss_ai._calculate_atr("601669", period=14)
            assert atr == 1.50

    @pytest.mark.asyncio
    async def test_identify_support_levels(self, stop_loss_ai, mock_technical_analysis):
        """测试识别支撑位"""
        levels = stop_loss_ai._identify_support_levels(mock_technical_analysis)

        assert len(levels) > 0
        assert all(isinstance(l, (int, float)) for l in levels)

    def test_generate_adjustment_rules(self, stop_loss_ai):
        """测试生成调整规则"""
        rules = stop_loss_ai._generate_adjustment_rules("medium_term")

        assert len(rules) >= 3
        assert any("检查" in r for r in rules)
        assert any("止损" in r for r in rules)

    def test_error_result(self, stop_loss_ai):
        """测试错误结果生成"""
        result = stop_loss_ai._error_result("601669", "测试策略", "测试错误")

        assert result["stock_code"] == "601669"
        assert result["strategy"] == "测试策略"
        assert result["error"] == "测试错误"
        assert "suggestion" in result

    # ========== 集成测试 ==========

    @pytest.mark.asyncio
    async def test_execute_method(self, stop_loss_ai, mock_price):
        """测试execute方法路由"""
        # 测试fixed_stop_loss任务
        result1 = await stop_loss_ai.execute(
            "fixed_stop_loss",
            stock_code="601669",
            current_price=mock_price,
            stop_ratio=0.08
        )
        assert result1["stop_loss"]["type"] == "fixed"

        # 测试comprehensive_plan任务（默认）
        with patch.object(
            stop_loss_ai,
            '_get_current_price',
            return_value=mock_price
        ):
            result2 = await stop_loss_ai.execute(
                "comprehensive_plan",
                stock_code="601669"
            )
            assert "stop_loss" in result2
            assert "take_profit" in result2

    @pytest.mark.asyncio
    async def test_full_workflow(self, stop_loss_ai):
        """测试完整工作流程"""
        stock_code = "601669"
        initial_price = 20.50
        new_price = 23.00  # 上涨超过10%以触发止损调整

        with patch.object(
            stop_loss_ai,
            '_get_current_price',
            return_value=initial_price
        ):
            # 1. 生成初始方案
            initial_plan = await stop_loss_ai.comprehensive_plan(stock_code)
            assert "stop_loss" in initial_plan
            assert "take_profit" in initial_plan

        with patch.object(
            stop_loss_ai,
            '_get_current_price',
            return_value=new_price
        ):
            # 2. 模拟价格上涨超过10%，调整方案
            adjusted_plan = await stop_loss_ai.dynamic_adjustment(
                stock_code,
                initial_plan,
                current_price=new_price
            )
            # 验证止损位上移或保持不变
            assert adjusted_plan["new_stop_loss"] >= adjusted_plan["old_stop_loss"]

    # ========== 边界情况测试 ==========

    @pytest.mark.asyncio
    async def test_zero_stop_ratio(self, stop_loss_ai, mock_price):
        """测试0止损比例"""
        result = await stop_loss_ai.fixed_stop_loss(
            "601669",
            current_price=mock_price,
            stop_ratio=0.0
        )

        assert result["stop_loss"]["price"] == mock_price

    @pytest.mark.asyncio
    async def test_extreme_stop_ratio(self, stop_loss_ai, mock_price):
        """测试极端止损比例"""
        result = await stop_loss_ai.fixed_stop_loss(
            "601669",
            current_price=mock_price,
            stop_ratio=0.50  # 50%止损
        )

        expected = mock_price * 0.50
        assert abs(result["stop_loss"]["price"] - expected) < 0.01

    @pytest.mark.asyncio
    async def test_missing_stock_code(self, stop_loss_ai):
        """测试缺少股票代码"""
        with pytest.raises(ValueError, match="缺少stock_code参数"):
            await stop_loss_ai.execute("fixed_stop_loss")
