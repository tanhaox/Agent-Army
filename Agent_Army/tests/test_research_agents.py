"""
研究部Agent单元测试

测试产业链研究AI和宏观政策研究AI的所有功能。
"""

import pytest
from src.agents.business.research.industry_chain_ai import IndustryChainResearchAI
from src.agents.business.research.macro_policy_ai import MacroPolicyResearchAI


class TestIndustryChainResearchAI:
    """测试产业链研究AI"""

    def test_init(self):
        """测试初始化"""
        ai = IndustryChainResearchAI()
        assert ai.name == "industry_chain_research_ai"
        assert ai.department == "research_department"

    def test_analyze_moutai(self):
        """测试贵州茅台产业链分析"""
        ai = IndustryChainResearchAI()

        result = ai.analyze("600519")

        # 检查基本信息
        assert result['stock_code'] == "600519"
        assert result['agent'] == "industry_chain_research_ai"

        # 检查产业链分析
        assert 'industry_chain' in result
        assert result['industry_chain']['industry'] == "白酒"

        # 检查上游分析
        assert 'upstream' in result['industry_chain']
        assert result['industry_chain']['upstream']['status'] == "稳定"

        # 检查中游分析
        assert 'midstream' in result['industry_chain']
        assert result['industry_chain']['midstream']['position'] == "行业龙头"

        # 检查下游分析
        assert 'downstream' in result['industry_chain']
        assert result['industry_chain']['downstream']['status'] == "强势"

        # 检查行业周期
        assert 'industry_cycle' in result
        assert result['industry_cycle']['current_stage'] == "成熟期"

        # 检查竞争格局
        assert 'competitive_landscape' in result
        assert result['competitive_landscape']['market_concentration'] == "HIGH"

        # 检查综合评估
        assert result['summary'] is not None
        assert result['confidence'] > 0.0
        assert result['recommendation'] is not None

    def test_analyze_byd(self):
        """测试比亚迪产业链分析"""
        ai = IndustryChainResearchAI()

        result = ai.analyze("002594")

        # 检查行业
        assert result['industry_chain']['industry'] == "新能源汽车"

        # 检查行业周期
        assert result['industry_cycle']['current_stage'] == "成长期"

        # 检查竞争强度
        assert result['competitive_landscape']['competition_intensity'] == "HIGH"

    def test_analyze_unknown_stock(self):
        """测试未知股票"""
        ai = IndustryChainResearchAI()

        result = ai.analyze("999999")

        # 应该返回默认值
        assert result['stock_code'] == "999999"
        assert result['industry_chain']['industry'] == "未知行业"

    def test_get_industry_name(self):
        """测试获取行业名称"""
        ai = IndustryChainResearchAI()

        assert ai._get_industry_name("600519") == "白酒"
        assert ai._get_industry_name("002594") == "新能源汽车"
        assert ai._get_industry_name("999999") == "未知行业"

    def test_analyze_upstream(self):
        """测试上游分析"""
        ai = IndustryChainResearchAI()

        # 白酒上游
        upstream = ai._analyze_upstream("600519")
        assert 'materials' in upstream
        assert 'suppliers' in upstream
        assert upstream['bargaining_power'] == "LOW"

        # 新能源汽车上游
        upstream = ai._analyze_upstream("002594")
        assert upstream['bargaining_power'] == "MEDIUM"

    def test_analyze_midstream(self):
        """测试中游分析"""
        ai = IndustryChainResearchAI()

        midstream = ai._analyze_midstream("600519")
        assert midstream['position'] == "行业龙头"
        assert midstream['market_share'] == "30%+"

    def test_analyze_downstream(self):
        """测试下游分析"""
        ai = IndustryChainResearchAI()

        downstream = ai._analyze_downstream("600519")
        assert 'customers' in downstream
        assert 'channels' in downstream

    def test_analyze_industry_cycle(self):
        """测试行业周期分析"""
        ai = IndustryChainResearchAI()

        cycle = ai._analyze_industry_cycle("600519")
        assert cycle['current_stage'] == "成熟期"
        assert cycle['growth_rate'] == "5-10%"

        cycle = ai._analyze_industry_cycle("002594")
        assert cycle['current_stage'] == "成长期"
        assert cycle['growth_rate'] == "30%+"

    def test_analyze_competitive_landscape(self):
        """测试竞争格局分析"""
        ai = IndustryChainResearchAI()

        competition = ai._analyze_competitive_landscape("600519")
        assert competition['market_concentration'] == "HIGH"
        assert competition['major_competitors'] is not None

    def test_generate_summary(self):
        """测试生成摘要"""
        ai = IndustryChainResearchAI()

        result = {
            'industry_chain': {
                'industry': '白酒'
            },
            'industry_cycle': {
                'current_stage': '成熟期'
            },
            'competitive_landscape': {
                'competition_intensity': 'MEDIUM'
            }
        }

        summary = ai._generate_summary(result)
        assert "白酒" in summary
        assert "成熟期" in summary

    def test_calculate_confidence(self):
        """测试计算置信度"""
        ai = IndustryChainResearchAI()

        # 高置信度场景
        result_high = {
            'industry_chain': {'industry': '白酒'},
            'industry_cycle': {'current_stage': '成熟期'},
            'competitive_landscape': {'competition_intensity': 'MEDIUM'}
        }
        confidence_high = ai._calculate_confidence(result_high)
        assert confidence_high == 0.9

        # 低置信度场景
        result_low = {
            'industry_chain': {'industry': '未知行业'},
            'industry_cycle': {'current_stage': '待分析'},
            'competitive_landscape': {'competition_intensity': 'UNKNOWN'}
        }
        confidence_low = ai._calculate_confidence(result_low)
        assert confidence_low == 0.7

    def test_generate_recommendation(self):
        """测试生成建议"""
        ai = IndustryChainResearchAI()

        # 成长期 + 低竞争
        result1 = {
            'industry_cycle': {'current_stage': '成长期'},
            'competitive_landscape': {'competition_intensity': 'LOW'}
        }
        rec1 = ai._generate_recommendation(result1)
        assert "建议关注" in rec1

        # 成熟期 + 低竞争
        result2 = {
            'industry_cycle': {'current_stage': '成熟期'},
            'competitive_landscape': {'competition_intensity': 'LOW'}
        }
        rec2 = ai._generate_recommendation(result2)
        assert "长期持有" in rec2

        # 衰退期
        result3 = {
            'industry_cycle': {'current_stage': '衰退期'},
            'competitive_landscape': {'competition_intensity': 'HIGH'}
        }
        rec3 = ai._generate_recommendation(result3)
        assert "谨慎" in rec3

    def test_get_system_status(self):
        """测试获取系统状态"""
        ai = IndustryChainResearchAI()

        status = ai.get_system_status()

        assert status['name'] == "industry_chain_research_ai"
        assert status['department'] == "research_department"
        assert status['status'] == "READY"


class TestMacroPolicyResearchAI:
    """测试宏观政策研究AI"""

    def test_init(self):
        """测试初始化"""
        ai = MacroPolicyResearchAI()
        assert ai.name == "macro_policy_research_ai"
        assert ai.department == "research_department"

    def test_analyze_moutai(self):
        """测试贵州茅台宏观政策分析"""
        ai = MacroPolicyResearchAI()

        result = ai.analyze("600519")

        # 检查基本信息
        assert result['stock_code'] == "600519"
        assert result['agent'] == "macro_policy_research_ai"

        # 检查宏观经济分析
        assert 'macro_economy' in result
        assert 'gdp' in result['macro_economy']
        assert 'inflation' in result['macro_economy']
        assert 'interest_rate' in result['macro_economy']

        # 检查政策影响分析
        assert 'policy_impact' in result
        assert 'fiscal_policy' in result['policy_impact']
        assert 'monetary_policy' in result['policy_impact']
        assert 'industry_policy' in result['policy_impact']

        # 检查综合评估
        assert result['summary'] is not None
        assert result['confidence'] > 0.0
        assert result['risk_level'] is not None

    def test_analyze_byd(self):
        """测试比亚迪宏观政策分析"""
        ai = MacroPolicyResearchAI()

        result = ai.analyze("002594")

        # 检查产业政策支持程度
        assert result['policy_impact']['industry_policy']['support_level'] == "HIGH"

        # 检查近期政策
        policies = result['policy_impact']['recent_policies']
        assert len(policies) > 0

    def test_analyze_gdp(self):
        """测试GDP分析"""
        ai = MacroPolicyResearchAI()

        gdp = ai._analyze_gdp()

        assert 'growth_rate' in gdp
        assert 'trend' in gdp
        assert 'forecast' in gdp

    def test_analyze_inflation(self):
        """测试通胀分析"""
        ai = MacroPolicyResearchAI()

        inflation = ai._analyze_inflation()

        assert 'cpi' in inflation
        assert 'ppi' in inflation
        assert 'trend' in inflation

    def test_analyze_interest_rate(self):
        """测试利率分析"""
        ai = MacroPolicyResearchAI()

        interest_rate = ai._analyze_interest_rate()

        assert 'benchmark_rate' in interest_rate
        assert 'trend' in interest_rate
        assert 'future_expectation' in interest_rate

    def test_analyze_exchange_rate(self):
        """测试汇率分析"""
        ai = MacroPolicyResearchAI()

        exchange_rate = ai._analyze_exchange_rate("600519")

        assert 'usd_cny' in exchange_rate
        assert 'trend' in exchange_rate
        assert 'impact_on_company' in exchange_rate

    def test_assess_exchange_rate_impact(self):
        """测试汇率影响评估"""
        ai = MacroPolicyResearchAI()

        # 白酒（内销为主）
        impact1 = ai._assess_exchange_rate_impact("600519")
        assert impact1 == "NEUTRAL"

        # 新能源汽车（有出口）
        impact2 = ai._assess_exchange_rate_impact("002594")
        assert impact2 == "NEGATIVE"

    def test_analyze_industry_macro_impact(self):
        """测试行业宏观影响分析"""
        ai = MacroPolicyResearchAI()

        impact = ai._analyze_industry_macro_impact("600519")

        assert 'sensitivity' in impact
        assert 'correlation' in impact
        assert 'key_factors' in impact

    def test_analyze_fiscal_policy(self):
        """测试财政政策分析"""
        ai = MacroPolicyResearchAI()

        fiscal = ai._analyze_fiscal_policy("600519")

        assert 'tax_policy' in fiscal
        assert 'impact' in fiscal
        assert 'subsidies' in fiscal

    def test_analyze_monetary_policy(self):
        """测试货币政策分析"""
        ai = MacroPolicyResearchAI()

        monetary = ai._analyze_monetary_policy("600519")

        assert 'policy_stance' in monetary
        assert 'liquidity' in monetary

    def test_analyze_industry_policy(self):
        """测试产业政策分析"""
        ai = MacroPolicyResearchAI()

        industry = ai._analyze_industry_policy("002594")

        assert industry['support_level'] == "HIGH"
        assert industry['impact'] == "POSITIVE"
        assert 'key_regulations' in industry

    def test_get_recent_policies(self):
        """测试获取近期政策"""
        ai = MacroPolicyResearchAI()

        policies = ai._get_recent_policies("002594")

        assert len(policies) > 0
        assert 'date' in policies[0]
        assert 'policy' in policies[0]
        assert 'impact' in policies[0]

    def test_assess_policy_risk(self):
        """测试政策风险评估"""
        ai = MacroPolicyResearchAI()

        risk = ai._assess_policy_risk("002594")

        assert risk['overall_risk'] == "LOW"
        assert 'key_risks' in risk
        assert 'mitigation' in risk

    def test_generate_summary(self):
        """测试生成摘要"""
        ai = MacroPolicyResearchAI()

        result = {
            'macro_economy': {
                'gdp': {'trend': 'STABLE'}
            },
            'policy_impact': {
                'industry_policy': {'impact': 'POSITIVE'}
            }
        }

        summary = ai._generate_summary(result)
        assert "宏观经济STABLE" in summary
        assert "政策影响POSITIVE" in summary

    def test_calculate_confidence(self):
        """测试计算置信度"""
        ai = MacroPolicyResearchAI()

        # 高置信度场景
        result_high = {
            'policy_impact': {
                'industry_policy': {'impact': 'POSITIVE'}
            }
        }
        confidence_high = ai._calculate_confidence(result_high)
        assert confidence_high == 0.85

    def test_assess_risk_level(self):
        """测试风险评估"""
        ai = MacroPolicyResearchAI()

        # 低风险场景
        result_low = {
            'policy_impact': {
                'policy_risk': {'overall_risk': 'LOW'}
            },
            'macro_economy': {
                'industry_impact': {'sensitivity': 'LOW'}
            }
        }
        risk_low = ai._assess_risk_level(result_low)
        assert risk_low == "LOW"

        # 高风险场景
        result_high = {
            'policy_impact': {
                'policy_risk': {'overall_risk': 'HIGH'}
            },
            'macro_economy': {
                'industry_impact': {'sensitivity': 'LOW'}
            }
        }
        risk_high = ai._assess_risk_level(result_high)
        assert risk_high == "HIGH"

    def test_get_system_status(self):
        """测试获取系统状态"""
        ai = MacroPolicyResearchAI()

        status = ai.get_system_status()

        assert status['name'] == "macro_policy_research_ai"
        assert status['department'] == "research_department"
        assert status['status'] == "READY"


class TestResearchDepartmentIntegration:
    """测试研究部集成"""

    def test_both_agents_collaboration(self):
        """测试两个Agent协作"""
        # 初始化
        industry_ai = IndustryChainResearchAI()
        macro_ai = MacroPolicyResearchAI()

        # 产业链分析
        industry_result = industry_ai.analyze("600519")
        assert industry_result['confidence'] > 0.0

        # 宏观政策分析
        macro_result = macro_ai.analyze("600519")
        assert macro_result['confidence'] > 0.0

        # 综合评估（模拟总司令汇总）
        combined_confidence = (
            industry_result['confidence'] + macro_result['confidence']
        ) / 2

        assert combined_confidence > 0.7

    def test_full_research_workflow(self):
        """测试完整研究工作流程"""
        industry_ai = IndustryChainResearchAI()
        macro_ai = MacroPolicyResearchAI()

        stock_code = "002594"

        # 1. 产业链研究
        industry_result = industry_ai.analyze(stock_code)

        assert industry_result['industry_chain']['industry'] == "新能源汽车"
        assert industry_result['industry_cycle']['current_stage'] == "成长期"

        # 2. 宏观政策研究
        macro_result = macro_ai.analyze(stock_code)

        assert macro_result['policy_impact']['industry_policy']['support_level'] == "HIGH"

        # 3. 生成综合报告（模拟）
        report = {
            'stock_code': stock_code,
            'industry_analysis': industry_result,
            'macro_analysis': macro_result,
            'overall_recommendation': self._combine_recommendations(
                industry_result['recommendation'],
                macro_result['risk_level']
            )
        }

        assert report['overall_recommendation'] is not None

    def _combine_recommendations(
        self,
        industry_rec: str,
        macro_risk: str
    ) -> str:
        """
        组合建议（辅助方法）

        Args:
            industry_rec: 行业建议
            macro_risk: 宏观风险

        Returns:
            综合建议
        """
        if macro_risk == "LOW":
            return f"{industry_rec}，宏观风险低"
        elif macro_risk == "MEDIUM":
            return f"{industry_rec}，宏观风险中等"
        else:
            return f"{industry_rec}，宏观风险较高"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
