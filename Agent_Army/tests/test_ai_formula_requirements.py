"""
测试AI创建公式的三大要求
1. 公式用途、创建依据、使用条件
2. 标准化命名
3. 众AI评价机制
"""

import sys
import io
from pathlib import Path
from datetime import datetime

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.formula_manager import FormulaManager


def test_ai_formula_creation_with_requirements():
    """测试AI创建公式（三大要求）"""

    print("\n" + "=" * 60)
    print("  测试AI创建公式的三大要求")
    print("=" * 60)

    manager = FormulaManager()

    # ========== 要求1：三大核心信息 ==========

    print("\n[要求1] 三大核心信息（用途、依据、条件）")
    print("-" * 60)

    # 1.1 公式用途
    purpose = {
        "description": "筛选价值投资标的的综合评分公式",
        "target": "评估股票是否符合价值投资标准",
        "output": "0-100的综合评分（越高越好）",
        "usage_scenario": "基本面分析阶段，用于筛选投资标的"
    }

    print("✅ 公式用途:")
    print(f"   说明: {purpose['description']}")
    print(f"   目标: {purpose['target']}")
    print(f"   输出: {purpose['output']}")
    print(f"   场景: {purpose['usage_scenario']}")

    # 1.2 创建依据
    creation_basis = {
        "data_sources": [
            "过去3年A股价值投资成功案例",
            "巴菲特价值投资理念",
            "格雷厄姆《聪明的投资者》"
        ],
        "methodology": "多因子加权平均（ROE 30% + 增长 30% + 估值 20% + 风险 20%）",
        "reference": "巴菲特护城河理论、彼得·林奇PEG指标",
        "validation": "回测2021-2023年数据，准确率78%",
        "ai_reasoning": """
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
"""
    }

    print("\n✅ 创建依据:")
    print(f"   数据源: {', '.join(creation_basis['data_sources'])}")
    print(f"   方法: {creation_basis['methodology']}")
    print(f"   参考: {creation_basis['reference']}")
    print(f"   验证: {creation_basis['validation']}")
    print(f"   AI推理: {creation_basis['ai_reasoning'][:50]}...")

    # 1.3 使用条件
    usage_conditions = {
        "prerequisites": [
            "必须有完整的财务数据（至少3年）",
            "必须有PE、PB等估值数据",
            "不适用于金融行业（银行、保险）"
        ],
        "limitations": [
            "不适用于ST股票",
            "不适用于上市不足1年的新股",
            "不适用于财务造假嫌疑的公司"
        ],
        "parameters": {
            "roe_weight": {
                "value": 0.30,
                "range": "0.20-0.40",
                "description": "ROE因子的权重（建议30%）"
            },
            "growth_weight": {
                "value": 0.30,
                "range": "0.20-0.40",
                "description": "增长因子的权重（建议30%）"
            },
            "valuation_weight": {
                "value": 0.20,
                "range": "0.10-0.30",
                "description": "估值得分的权重（建议20%）"
            },
            "risk_weight": {
                "value": 0.20,
                "range": "0.10-0.30",
                "description": "风险因子的权重（建议20%）"
            }
        }
    }

    print("\n✅ 使用条件:")
    print(f"   前置条件: {usage_conditions['prerequisites'][0]}")
    print(f"   限制条件: {usage_conditions['limitations'][0]}")
    print(f"   参数数量: {len(usage_conditions['parameters'])}个")

    # ========== 要求2：标准化命名 ==========

    print("\n[要求2] 标准化命名（文件名清晰，不乱）")
    print("-" * 60)

    # 公式代码（简化示例）
    formula_code = """
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
"""

    # 创建公式
    filename = manager.create_ai_formula(
        formula_type="composite_score",
        purpose=purpose,
        creation_basis=creation_basis,
        usage_conditions=usage_conditions,
        formula_code=formula_code,
        created_by="CorpsCoordinator AI"
    )

    print(f"✅ 文件名: {filename}")
    print(f"   命名规则: {{formula_type}}_{{purpose}}_{{version}}_{{timestamp}}.py")
    print(f"   含义:")
    print(f"     - composite_score: 公式类型")
    print(f"     - value_investing: 用途关键词")
    print(f"     - v1: 版本号")
    print(f"     - 20260314_xxxxxx: 创建时间")

    # ========== 要求3：众AI评价机制 ==========

    print("\n[要求3] 众AI评价机制（使用效果打分）")
    print("-" * 60)

    # 3.1 FundamentalAnalyzer AI 使用并评价
    manager.add_ai_review(
        formula_name="composite_score",
        formula_version="v1",
        reviewer="FundamentalAnalyzer AI",
        rating=4.5,
        comment="公式设计合理，多因子权重科学，ROE和增长因子确实是核心指标",
        usage_context="用于筛选贵州茅台、五粮液等白酒股",
        suggestions=[
            "建议增加行业对比因子",
            "PE阈值可以根据行业动态调整"
        ]
    )

    print(f"✅ 评价1:")
    print(f"   评价者: FundamentalAnalyzer AI")
    print(f"   评分: 4.5/5 ⭐")
    print(f"   评价: 公式设计合理，多因子权重科学，ROE和增长因子确实是核心指标")
    print(f"   使用场景: 用于筛选贵州茅台、五粮液等白酒股")
    print(f"   建议: 建议增加行业对比因子")

    # 3.2 IndustryAnalyzer AI 使用并评价
    manager.add_ai_review(
        formula_name="composite_score",
        formula_version="v1",
        reviewer="IndustryAnalyzer AI",
        rating=4.0,
        comment="公式整体不错，但对周期性行业适用性一般，建议增加行业周期调整因子",
        usage_context="用于筛选周期性行业股票（钢铁、煤炭）",
        suggestions=[
            "建议区分周期性和非周期性行业",
            "增加行业景气度因子"
        ]
    )

    print(f"\n✅ 评价2:")
    print(f"   评价者: IndustryAnalyzer AI")
    print(f"   评分: 4.0/5 ⭐")
    print(f"   评价: 公式整体不错，但对周期性行业适用性一般")

    # 3.3 查看所有评价
    reviews = manager.get_ai_reviews("composite_score", "v1")

    print(f"\n✅ 查看所有评价:")
    print(f"   总评价数: {len(reviews)}条")

    if reviews:
        avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
        print(f"   平均评分: {avg_rating:.1f}/5 ⭐")

        print(f"\n   评价详情:")
        for i, review in enumerate(reviews, 1):
            print(f"   [{i}] {review['reviewer']}: {review['rating']}/5")
            print(f"       {review['comment']}")

    # 3.4 基于评价选择最优公式
    best_formula = manager.get_best_formula_by_reviews("composite_score")

    print(f"\n✅ 基于评价选择最优公式:")
    print(f"   最优版本: {best_formula.FORMULA_META['version']}")
    print(f"   平均评分: {best_formula.FORMULA_META['statistics']['avg_rating']:.1f}/5")
    print(f"   总评价数: {best_formula.FORMULA_META['statistics']['total_reviews']}条")

    # 3.5 改进建议（用于下次创建公式）
    print(f"\n✅ 改进建议汇总（用于创建v2版本）:")
    all_suggestions = []
    for review in reviews:
        all_suggestions.extend(review.get("suggestions", []))

    for i, suggestion in enumerate(set(all_suggestions), 1):
        print(f"   [{i}] {suggestion}")

    print("\n" + "=" * 60)
    print("  ✅ 三大要求测试完成!")
    print("=" * 60)

    print("\n总结:")
    print("1. ✅ 三大核心信息：用途明确、依据充分、条件清晰")
    print("2. ✅ 标准化命名：文件名长但不乱，一眼看出用途")
    print("3. ✅ 众AI评价：形成评价体系，助力持续改进")


if __name__ == "__main__":
    test_ai_formula_creation_with_requirements()
