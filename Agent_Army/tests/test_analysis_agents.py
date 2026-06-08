"""
分析部Agent单元测试

测试基本面分析AI、估值分析AI、历史分析AI的所有功能。
"""

import pytest
from src.agents.business.analysis.fundamental_analysis_ai import FundamentalAnalysisAI
from src.agents.business.analysis.valuation_analysis_ai import ValuationAnalysisAI
from src.agents.business.analysis.historical_analysis_ai import HistoricalAnalysisAI


class TestFundamentalAnalysisAI:
    """测试基本面分析AI"""

    def test_init(self):
        """测试初始化"""
        ai = FundamentalAnalysisAI()
        assert ai.name == "fundamental_analysis_ai"
        assert ai.department == "analysis_department"

    def test_analyze_moutai(self):
        """测试贵州茅台基本面分析"""
        ai = FundamentalAnalysisAI()

        result = ai.analyze("600519")

        # 检查基本信息
        assert result['stock_code'] == "600519"
        assert result['agent'] == "fundamental_analysis_ai"

        # 检查基本面分析
        assert 'fundamentals' in result
        assert result['fundamentals']['revenue']['total_revenue'] is not None
        assert result['fundamentals']['profit']['net_profit'] is not None

        # 检查成长性分析
        assert 'growth' in result
        assert result['growth']['revenue_growth']['yoy'] is not None

        # 检查财务健康分析
        assert 'financial_health' in result
        assert result['financial_health']['debt_ratio']['current'] is not None

        # 检查综合评估
        assert result['overall_score'] > 0
        assert result['confidence'] > 0.0
        assert result['recommendation'] is not None

    def test_analyze_byd(self):
        """测试比亚迪基本面分析"""
        ai = FundamentalAnalysisAI()

        result = ai.analyze("002594")

        # 检查成长性
        assert result['growth']['revenue_growth']['yoy'] == "42.0%"

        # 检查财务健康
        assert result['financial_health']['debt_ratio']['level'] == "MEDIUM"

    def test_analyze_unknown_stock(self):
        """测试未知股票"""
        ai = FundamentalAnalysisAI()

        result = ai.analyze("999999")

        # 应该返回默认值
        assert result['stock_code'] == "999999"
        assert result['fundamentals']['revenue']['total_revenue'] == "待获取"

    def test_analyze_fundamentals(self):
        """测试基本面分析"""
        ai = FundamentalAnalysisAI()

        # 茅台基本面
        fundamentals = ai._analyze_fundamentals("600519")
        assert fundamentals['roe']['current_roe'] == "31.5%"
        assert fundamentals['gross_margin']['current'] == "91.5%"
        assert fundamentals['score'] > 0

        # 比亚迪基本面
        fundamentals = ai._analyze_fundamentals("002594")
        assert fundamentals['gross_margin']['current'] == "16.2%"
        assert fundamentals['score'] > 0

    def test_analyze_growth(self):
        """测试成长性分析"""
        ai = FundamentalAnalysisAI()

        growth = ai._analyze_growth("002594")
        assert growth['revenue_growth']['yoy'] == "42.0%"
        assert growth['growth_drivers']['sustainability'] == "MEDIUM"

    def test_analyze_financial_health(self):
        """测试财务健康分析"""
        ai = FundamentalAnalysisAI()

        health = ai._analyze_financial_health("600519")
        assert health['debt_ratio']['level'] == "LOW"
        assert health['cash_flow']['quality'] == "EXCELLENT"
        assert health['solvency']['level'] == "EXCELLENT"

    def test_calculate_overall_score(self):
        """测试综合评分计算"""
        ai = FundamentalAnalysisAI()

        result = {
            'fundamentals': {'score': 90},
            'growth': {'score': 85},
            'financial_health': {'score': 95}
        }

        score = ai._calculate_overall_score(result)
        # 90*0.4 + 85*0.35 + 95*0.25 = 36 + 29.75 + 23.75 = 89.5
        assert score == 89.5

    def test_calculate_confidence(self):
        """测试置信度计算"""
        ai = FundamentalAnalysisAI()

        # 高置信度场景
        result_high = {
            'fundamentals': {'score': 90},
            'growth': {'score': 85},
            'financial_health': {'score': 88}
        }
        confidence_high = ai._calculate_confidence(result_high)
        assert confidence_high == 0.9

        # 低置信度场景
        result_low = {
            'fundamentals': {'score': 50},
            'growth': {'score': 55},
            'financial_health': {'score': 58}
        }
        confidence_low = ai._calculate_confidence(result_low)
        assert confidence_low == 0.75

    def test_generate_recommendation(self):
        """测试生成建议"""
        ai = FundamentalAnalysisAI()

        # 高分场景
        result1 = {'overall_score': 90}
        rec1 = ai._generate_recommendation(result1)
        assert "优秀" in rec1

        # 中等分场景
        result2 = {'overall_score': 75}
        rec2 = ai._generate_recommendation(result2)
        assert "良好" in rec2 or "重点关注" in rec2

        # 低分场景
        result3 = {'overall_score': 60}
        rec3 = ai._generate_recommendation(result3)
        assert "谨慎" in rec3 or "风险" in rec3

    def test_get_system_status(self):
        """测试获取系统状态"""
        ai = FundamentalAnalysisAI()

        status = ai.get_system_status()

        assert status['name'] == "fundamental_analysis_ai"
        assert status['department'] == "analysis_department"
        assert status['status'] == "READY"


class TestValuationAnalysisAI:
    """测试估值分析AI"""

    def test_init(self):
        """测试初始化"""
        ai = ValuationAnalysisAI()
        assert ai.name == "valuation_analysis_ai"
        assert ai.department == "analysis_department"

    def test_analyze_moutai(self):
        """测试贵州茅台估值分析"""
        ai = ValuationAnalysisAI()

        result = ai.analyze("600519")

        # 检查基本信息
        assert result['stock_code'] == "600519"
        assert result['agent'] == "valuation_analysis_ai"

        # 检查估值模型分析
        assert 'valuation_models' in result
        assert 'pe_analysis' in result['valuation_models']
        assert 'pb_analysis' in result['valuation_models']
        assert 'peg_analysis' in result['valuation_models']
        assert 'dcf_analysis' in result['valuation_models']

        # 检查K线形态分析
        assert 'kline_patterns' in result
        assert 'trend_analysis' in result['kline_patterns']
        assert 'support_resistance' in result['kline_patterns']
        assert 'technical_patterns' in result['kline_patterns']

        # 检查综合评估
        assert result['fair_value'] > 0
        assert result['current_price'] > 0
        assert result['upside_potential'] is not None
        assert result['confidence'] > 0.0
        assert result['recommendation'] is not None

    def test_analyze_byd(self):
        """测试比亚迪估值分析"""
        ai = ValuationAnalysisAI()

        result = ai.analyze("002594")

        # 检查PE评估
        assert result['valuation_models']['pe_analysis']['evaluation'] == "SLIGHTLY_OVERVALUED"

        # 检查趋势
        assert result['kline_patterns']['trend_analysis']['mid_term_trend'] == "UP"

    def test_analyze_pe(self):
        """测试PE分析"""
        ai = ValuationAnalysisAI()

        pe = ai._analyze_pe("600519")
        assert pe['current_pe'] == 35.2
        assert pe['evaluation'] == "REASONABLE"

    def test_analyze_pb(self):
        """测试PB分析"""
        ai = ValuationAnalysisAI()

        pb = ai._analyze_pb("600519")
        assert pb['current_pb'] == 8.5
        assert pb['evaluation'] == "REASONABLE"

    def test_analyze_peg(self):
        """测试PEG分析"""
        ai = ValuationAnalysisAI()

        peg = ai._analyze_peg("002594")
        assert peg['peg_ratio'] == 1.5
        assert peg['evaluation'] == "REASONABLE"

    def test_analyze_dcf(self):
        """测试DCF分析"""
        ai = ValuationAnalysisAI()

        dcf = ai._analyze_dcf("600519")
        assert dcf['fair_value'] == 1850.0
        assert dcf['current_price'] == 1750.0
        assert dcf['upside_potential'] == 5.7

    def test_analyze_trend(self):
        """测试趋势分析"""
        ai = ValuationAnalysisAI()

        trend = ai._analyze_trend("600519")
        assert trend['short_term_trend'] == "UP"
        assert trend['mid_term_trend'] == "UP"
        assert trend['trend_strength'] == "STRONG"

    def test_analyze_support_resistance(self):
        """测试支撑阻力分析"""
        ai = ValuationAnalysisAI()

        sr = ai._analyze_support_resistance("600519")
        assert len(sr['support_levels']) > 0
        assert len(sr['resistance_levels']) > 0
        assert sr['risk_reward_ratio'] > 0

    def test_identify_technical_patterns(self):
        """测试技术形态识别"""
        ai = ValuationAnalysisAI()

        patterns = ai._identify_technical_patterns("600519")
        assert patterns['pattern_type'] == "上升三角形"
        assert patterns['reliability'] == "HIGH"
        assert patterns['breakout_probability'] == 70

    def test_analyze_volume(self):
        """测试成交量分析"""
        ai = ValuationAnalysisAI()

        volume = ai._analyze_volume("600519")
        assert volume['volume_trend'] == "INCREASING"
        assert volume['volume_price_relation'] == "量价齐升"

    def test_analyze_technical_indicators(self):
        """测试技术指标分析"""
        ai = ValuationAnalysisAI()

        indicators = ai._analyze_technical_indicators("600519")
        assert indicators['rsi_14'] == 62
        assert indicators['macd_signal'] == "金叉"
        assert indicators['overall_signal'] == "买入"

    def test_calculate_fair_value(self):
        """测试合理估值计算"""
        ai = ValuationAnalysisAI()

        result = {
            'valuation_models': {
                'dcf_analysis': {'fair_value': 1850.0, 'current_price': 1750.0},
                'pe_analysis': {'current_pe': 35.2, 'industry_avg_pe': 28.5}
            }
        }

        fair_value = ai._calculate_fair_value(result)
        assert fair_value == 1850.0

    def test_calculate_upside_potential(self):
        """测试上涨空间计算"""
        ai = ValuationAnalysisAI()

        # 正上涨空间
        upside1 = ai._calculate_upside_potential(1850.0, 1750.0)
        assert upside1 == 5.71

        # 下跌空间
        upside2 = ai._calculate_upside_potential(1700.0, 1750.0)
        assert upside2 == -2.86

    def test_generate_recommendation(self):
        """测试生成建议"""
        ai = ValuationAnalysisAI()

        # 大幅上涨空间 + 技术买入信号
        result1 = {
            'upside_potential': 20,
            'kline_patterns': {
                'technical_indicators': {'overall_signal': '买入'}
            }
        }
        rec1 = ai._generate_recommendation(result1)
        assert "估值偏低且技术面走强" in rec1

        # 小幅上涨空间
        result2 = {
            'upside_potential': 8,
            'kline_patterns': {
                'technical_indicators': {'overall_signal': '中性'}
            }
        }
        rec2 = ai._generate_recommendation(result2)
        assert "估值合理" in rec2

        # 下跌空间
        result3 = {
            'upside_potential': -10,
            'kline_patterns': {
                'technical_indicators': {'overall_signal': '卖出'}
            }
        }
        rec3 = ai._generate_recommendation(result3)
        assert "估值偏高" in rec3

    def test_get_system_status(self):
        """测试获取系统状态"""
        ai = ValuationAnalysisAI()

        status = ai.get_system_status()

        assert status['name'] == "valuation_analysis_ai"
        assert status['department'] == "analysis_department"
        assert status['status'] == "READY"


class TestHistoricalAnalysisAI:
    """测试历史分析AI"""

    def test_init(self):
        """测试初始化"""
        ai = HistoricalAnalysisAI()
        assert ai.name == "historical_analysis_ai"
        assert ai.department == "analysis_department"

    def test_analyze_moutai(self):
        """测试贵州茅台历史分析"""
        ai = HistoricalAnalysisAI()

        result = ai.analyze("600519")

        # 检查基本信息
        assert result['stock_code'] == "600519"
        assert result['agent'] == "historical_analysis_ai"

        # 检查历史周期分析
        assert 'historical_cycles' in result
        assert 'bull_bear_cycles' in result['historical_cycles']
        assert 'industry_cycles' in result['historical_cycles']
        assert 'profit_cycles' in result['historical_cycles']
        assert 'valuation_cycles' in result['historical_cycles']

        # 检查历史节点分析
        assert 'historical_nodes' in result
        assert 'key_events' in result['historical_nodes']
        assert 'turning_points' in result['historical_nodes']
        assert 'policy_impacts' in result['historical_nodes']
        assert 'market_crashes' in result['historical_nodes']

        # 检查综合评估
        assert result['current_cycle_stage'] is not None
        assert result['lesson_learned'] is not None
        assert result['confidence'] > 0.0
        assert result['recommendation'] is not None

    def test_analyze_byd(self):
        """测试比亚迪历史分析"""
        ai = HistoricalAnalysisAI()

        result = ai.analyze("002594")

        # 检查牛熊周期
        assert result['historical_cycles']['bull_bear_cycles']['total_cycles'] == 3

        # 检查行业周期
        assert result['historical_cycles']['industry_cycles']['current_stage'] == "成长期"

    def test_analyze_bull_bear_cycles(self):
        """测试牛熊周期分析"""
        ai = HistoricalAnalysisAI()

        cycles = ai._analyze_bull_bear_cycles("600519")
        assert cycles['total_cycles'] == 5
        assert len(cycles['cycle_phases']) > 0
        assert cycles['current_cycle'] == "第5轮牛市中期"

    def test_analyze_industry_cycles(self):
        """测试行业周期分析"""
        ai = HistoricalAnalysisAI()

        industry = ai._analyze_industry_cycles("600519")
        assert industry['industry'] == "白酒"
        assert industry['current_stage'] == "成熟期"
        assert len(industry['industry_history']) > 0

    def test_analyze_profit_cycles(self):
        """测试盈利周期分析"""
        ai = HistoricalAnalysisAI()

        profit = ai._analyze_profit_cycles("600519")
        assert len(profit['profit_history']) > 0
        assert profit['profit_stability'] == "HIGH"
        assert profit['cyclical'] == "弱周期"

    def test_analyze_valuation_cycles(self):
        """测试估值周期分析"""
        ai = HistoricalAnalysisAI()

        valuation = ai._analyze_valuation_cycles("600519")
        assert len(valuation['pe_history']) > 0
        assert valuation['valuation_stage'] == "合理区间"

    def test_analyze_key_events(self):
        """测试重大事件分析"""
        ai = HistoricalAnalysisAI()

        events = ai._analyze_key_events("600519")
        assert len(events['major_events']) > 0
        assert events['recent_event'] is not None

    def test_analyze_turning_points(self):
        """测试关键转折点分析"""
        ai = HistoricalAnalysisAI()

        turning = ai._analyze_turning_points("600519")
        assert len(turning['turning_points']) > 0
        assert turning['current_status'] is not None

    def test_analyze_policy_impacts(self):
        """测试政策影响分析"""
        ai = HistoricalAnalysisAI()

        policy = ai._analyze_policy_impacts("002594")
        assert len(policy['policy_history']) > 0
        assert policy['policy_sensitivity'] == "HIGH"
        assert policy['current_policy_environment'] == "持续支持"

    def test_analyze_market_crashes(self):
        """测试市场暴跌分析"""
        ai = HistoricalAnalysisAI()

        crashes = ai._analyze_market_crashes("600519")
        assert len(crashes['crash_history']) > 0
        assert crashes['resilience'] == "HIGH"
        assert crashes['avg_decline'] < 0

    def test_determine_current_cycle_stage(self):
        """测试判断当前周期阶段"""
        ai = HistoricalAnalysisAI()

        result = {
            'historical_cycles': {
                'bull_bear_cycles': {
                    'current_cycle': '第5轮牛市初期'
                }
            }
        }

        stage = ai._determine_current_cycle_stage(result)
        assert stage == "第5轮牛市初期"

    def test_extract_lessons(self):
        """测试提取历史教训"""
        ai = HistoricalAnalysisAI()

        result = {
            'historical_nodes': {
                'turning_points': {
                    'turning_points': [
                        {
                            'date': '2024-Q4',
                            'lesson': '估值回归合理后迎来配置窗口'
                        }
                    ]
                }
            }
        }

        lesson = ai._extract_lessons(result)
        assert "估值回归合理后迎来配置窗口" in lesson

    def test_generate_recommendation(self):
        """测试生成建议"""
        ai = HistoricalAnalysisAI()

        # 牛市初期 + 高抗跌能力
        result1 = {
            'current_cycle_stage': '第5轮牛市初期',
            'historical_nodes': {
                'market_crashes': {'resilience': 'HIGH'}
            },
            'lesson_learned': '估值回归合理后迎来配置窗口'
        }
        rec1 = ai._generate_recommendation(result1)
        assert "历史周期处于上升阶段" in rec1
        assert "抗跌能力强" in rec1

        # 熊市
        result2 = {
            'current_cycle_stage': '熊市',
            'historical_nodes': {
                'market_crashes': {'resilience': 'MEDIUM'}
            },
            'lesson_learned': '谨慎观望'
        }
        rec2 = ai._generate_recommendation(result2)
        assert "历史周期处于下行阶段" in rec2

    def test_get_system_status(self):
        """测试获取系统状态"""
        ai = HistoricalAnalysisAI()

        status = ai.get_system_status()

        assert status['name'] == "historical_analysis_ai"
        assert status['department'] == "analysis_department"
        assert status['status'] == "READY"


class TestAnalysisDepartmentIntegration:
    """测试分析部集成"""

    def test_three_agents_collaboration(self):
        """测试三个Agent协作"""
        # 初始化
        fundamental_ai = FundamentalAnalysisAI()
        valuation_ai = ValuationAnalysisAI()
        historical_ai = HistoricalAnalysisAI()

        # 基本面分析
        fundamental_result = fundamental_ai.analyze("600519")
        assert fundamental_result['confidence'] > 0.0

        # 估值分析
        valuation_result = valuation_ai.analyze("600519")
        assert valuation_result['confidence'] > 0.0

        # 历史分析
        historical_result = historical_ai.analyze("600519")
        assert historical_result['confidence'] > 0.0

        # 综合评估（模拟总司令汇总）
        combined_confidence = (
            fundamental_result['confidence'] +
            valuation_result['confidence'] +
            historical_result['confidence']
        ) / 3

        assert combined_confidence > 0.7

    def test_full_analysis_workflow(self):
        """测试完整分析工作流程"""
        fundamental_ai = FundamentalAnalysisAI()
        valuation_ai = ValuationAnalysisAI()
        historical_ai = HistoricalAnalysisAI()

        stock_code = "002594"

        # 1. 基本面分析
        fundamental_result = fundamental_ai.analyze(stock_code)
        assert fundamental_result['growth']['growth_drivers']['sustainability'] == "MEDIUM"

        # 2. 估值分析
        valuation_result = valuation_ai.analyze(stock_code)
        assert valuation_result['valuation_models']['pe_analysis']['evaluation'] == "SLIGHTLY_OVERVALUED"

        # 3. 历史分析
        historical_result = historical_ai.analyze(stock_code)
        assert historical_result['historical_cycles']['industry_cycles']['current_stage'] == "成长期"

        # 4. 生成综合报告（模拟）
        report = {
            'stock_code': stock_code,
            'fundamental_analysis': fundamental_result,
            'valuation_analysis': valuation_result,
            'historical_analysis': historical_result,
            'overall_recommendation': self._combine_recommendations(
                fundamental_result['recommendation'],
                valuation_result['recommendation'],
                historical_result['recommendation']
            )
        }

        assert report['overall_recommendation'] is not None

    def _combine_recommendations(
        self,
        fundamental_rec: str,
        valuation_rec: str,
        historical_rec: str
    ) -> str:
        """
        组合建议（辅助方法）

        Args:
            fundamental_rec: 基本面建议
            valuation_rec: 估值建议
            historical_rec: 历史建议

        Returns:
            综合建议
        """
        # 简化版组合逻辑
        if "强烈推荐" in fundamental_rec and "买入" in valuation_rec:
            return "综合建议：强烈推荐买入"
        elif "值得持有" in fundamental_rec:
            return "综合建议：持有为主"
        else:
            return "综合建议：谨慎观望"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
