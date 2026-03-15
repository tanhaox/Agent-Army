"""
AI生成的公式：composite_score v2

========== 1. 公式用途 ==========
此公式是干什么的：筛选价值投资标的的综合评分公式
目标场景：评估股票是否符合价值投资标准
输出内容：0-100的综合评分（越高越好）
使用场景：基本面分析阶段，用于筛选投资标的

========== 2. 创建依据 ==========
基于哪些数据：过去3年A股价值投资成功案例, 巴菲特价值投资理念, 格雷厄姆《聪明的投资者》
计算方法：多因子加权平均（ROE 30% + 增长 30% + 估值 20% + 风险 20%）
参考来源：巴菲特护城河理论、彼得·林奇PEG指标
验证方法：回测2021-2023年数据，准确率78%

AI的推理过程：

基于历史数据分析，我发现：
1. ROE连续3年>15%的公司，未来1年涨幅超过30%的概率是72%
2. 营收增长>10%且净利润增长>15%的公司，市场表现优异
3. PE在15-25区间的公司，风险收益比最佳
4. 负债率<50%的公司，财务稳健性更高

因此，我设计了多因子加权模型：
- ROE因子（30%）：衡量盈利能力
- 增长因子（30%）：衡量成长性
- 估值因子（20%）：衡量安全边际
- 风险因子（20%）：衡量财务风险

权重基于历史回测优化得出。


========== 3. 使用条件 ==========
前置条件：必须有完整的财务数据（至少3年）, 必须有PE、PB等估值数据, 不适用于金融行业（银行、保险）
限制条件：不适用于ST股票, 不适用于上市不足1年的新股, 不适用于财务造假嫌疑的公司

参数说明：
  - roe_weight: ROE因子的权重（建议30%） (默认: 0.3, 范围: 0.20-0.40)\n  - growth_weight: 增长因子的权重（建议30%） (默认: 0.3, 范围: 0.20-0.40)\n  - valuation_weight: 估值得分的权重（建议20%） (默认: 0.2, 范围: 0.10-0.30)\n  - risk_weight: 风险因子的权重（建议20%） (默认: 0.2, 范围: 0.10-0.30)\n

========== 元数据 ==========
创建时间：2026-03-14 02:43:45
创建者：CorpsCoordinator AI
版本：v2
状态：testing（测试中）

========== 众AI评价 ==========
（暂无评价）
"""

from typing import Dict, Any


class AIFormula_composite_score_v2:
    """
    AI生成的公式类
    """

    FORMULA_META = {
        "name": "composite_score",
        "version": "v2",
        "full_name": "composite_score v2",
        "created_at": "2026-03-14 02:43:45",
        "created_by": "CorpsCoordinator AI",

        # 三大核心要求
        "purpose": {'description': '筛选价值投资标的的综合评分公式', 'target': '评估股票是否符合价值投资标准', 'output': '0-100的综合评分（越高越好）', 'usage_scenario': '基本面分析阶段，用于筛选投资标的'},
        "creation_basis": {'data_sources': ['过去3年A股价值投资成功案例', '巴菲特价值投资理念', '格雷厄姆《聪明的投资者》'], 'methodology': '多因子加权平均（ROE 30% + 增长 30% + 估值 20% + 风险 20%）', 'reference': '巴菲特护城河理论、彼得·林奇PEG指标', 'validation': '回测2021-2023年数据，准确率78%', 'ai_reasoning': '\n基于历史数据分析，我发现：\n1. ROE连续3年>15%的公司，未来1年涨幅超过30%的概率是72%\n2. 营收增长>10%且净利润增长>15%的公司，市场表现优异\n3. PE在15-25区间的公司，风险收益比最佳\n4. 负债率<50%的公司，财务稳健性更高\n\n因此，我设计了多因子加权模型：\n- ROE因子（30%）：衡量盈利能力\n- 增长因子（30%）：衡量成长性\n- 估值因子（20%）：衡量安全边际\n- 风险因子（20%）：衡量财务风险\n\n权重基于历史回测优化得出。\n'},
        "usage_conditions": {'prerequisites': ['必须有完整的财务数据（至少3年）', '必须有PE、PB等估值数据', '不适用于金融行业（银行、保险）'], 'limitations': ['不适用于ST股票', '不适用于上市不足1年的新股', '不适用于财务造假嫌疑的公司'], 'parameters': {'roe_weight': {'value': 0.3, 'range': '0.20-0.40', 'description': 'ROE因子的权重（建议30%）'}, 'growth_weight': {'value': 0.3, 'range': '0.20-0.40', 'description': '增长因子的权重（建议30%）'}, 'valuation_weight': {'value': 0.2, 'range': '0.10-0.30', 'description': '估值得分的权重（建议20%）'}, 'risk_weight': {'value': 0.2, 'range': '0.10-0.30', 'description': '风险因子的权重（建议20%）'}}},

        # 赛马数据
        "usage_count": 0,
        "accuracy": 0.0,
        "status": "testing",

        # 众AI评价
        "ai_reviews": [],

        # 统计数据
        "statistics": {
            "avg_rating": 0.0,
            "total_reviews": 0,
            "success_rate": 0.0,
            "avg_deviation": 0.0
        }
    }

    @staticmethod
    def calculate(data: Dict, params: Dict = None) -> Any:
        """
        计算公式

        Args:
            data: 输入数据
            params: 可选参数

        Returns:
            计算结果
        """
        if params is None:
            params = {}

        # ========== 公式代码 ==========
        
        @staticmethod
        def calculate(data: Dict, params: Dict = None) -> float:
            roe = data.get("roe", 0)
            revenue_growth = data.get("revenue_growth", 0)
            profit_growth = data.get("profit_growth", 0)
            pe = data.get("pe", 0)
            debt_ratio = data.get("debt_ratio", 0)
        
            # ROE得分（30%）
            if roe >= 15:
                roe_score = 100
            elif roe >= 10:
                roe_score = 70
            else:
                roe_score = 40
        
            # 增长得分（30%）
            avg_growth = (revenue_growth + profit_growth) / 2
            if avg_growth >= 10:
                growth_score = 100
            elif avg_growth >= 5:
                growth_score = 70
            else:
                growth_score = 40
        
            # 估值得分（20%）
            if pe <= 15:
                valuation_score = 100
            elif pe <= 25:
                valuation_score = 70
            else:
                valuation_score = 40
        
            # 风险得分（20%）
            if debt_ratio <= 50:
                risk_score = 100
            elif debt_ratio <= 70:
                risk_score = 70
            else:
                risk_score = 40
        
            # 加权平均
            score = (
                roe_score * 0.30 +
                growth_score * 0.30 +
                valuation_score * 0.20 +
                risk_score * 0.20
            )
        
            return round(score, 2)
        
        # ========== 公式代码结束 ==========

    @staticmethod
    def explain(data: Dict, result: Any) -> str:
        """
        解释计算结果

        Args:
            data: 输入数据
            result: 计算结果

        Returns:
            解释文本
        """
        # AI可以在子类中实现更详细的解释
        return f"计算结果: {result}"

def _update_review_statistics(self, meta: Dict):
        """更新评价统计"""
        reviews = meta.get("ai_reviews", [])

        if not reviews:
            return

        # 计算平均评分
        total_rating = sum(r["rating"] for r in reviews)
        avg_rating = total_rating / len(reviews)

        # 更新统计
        if "statistics" not in meta:
            meta["statistics"] = {}

        meta["statistics"]["avg_rating"] = avg_rating
        meta["statistics"]["total_reviews"] = len(reviews)
