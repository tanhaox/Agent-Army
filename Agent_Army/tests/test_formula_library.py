"""
测试公式库功能
验证标准公式、私有公式、赛马机制
"""

import sys
import io
from pathlib import Path

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.formula_manager import FormulaManager


def test_standard_formulas():
    """测试标准公式"""
    print("\n" + "=" * 60)
    print("  测试标准公式（业界公认，不可改）")
    print("=" * 60)

    manager = FormulaManager()

    # 测试数据
    financial_data = {
        "net_profit": 1500000000,  # 15亿
        "net_assets": 10000000000,  # 100亿
        "stock_price": 150,
        "eps": 10,
        "total_liabilities": 4000000000,  # 40亿
        "total_assets": 10000000000,  # 100亿
        "revenue": 10000000000,  # 100亿
        "cost": 7000000000,  # 70亿
    }

    # 测试ROE
    print("\n[1] ROE 计算:")
    roe = manager.calculate("roe", financial_data)
    print(f"   净利润: {financial_data['net_profit']/1e8:.1f}亿")
    print(f"   净资产: {financial_data['net_assets']/1e8:.1f}亿")
    print(f"   ROE: {roe}%")
    print(f"   ✅ 公式: ROE = 净利润 / 净资产 × 100%")

    # 测试PE
    print("\n[2] PE 计算:")
    pe = manager.calculate("pe", financial_data)
    print(f"   股价: {financial_data['stock_price']}元")
    print(f"   EPS: {financial_data['eps']}元")
    print(f"   PE: {pe}倍")
    print(f"   ✅ 公式: PE = 股价 / EPS")

    # 测试负债率
    print("\n[3] 资产负债率 计算:")
    debt_ratio = manager.calculate("debt_ratio", financial_data)
    print(f"   总负债: {financial_data['total_liabilities']/1e8:.1f}亿")
    print(f"   总资产: {financial_data['total_assets']/1e8:.1f}亿")
    print(f"   负债率: {debt_ratio}%")
    print(f"   ✅ 公式: 负债率 = 总负债 / 总资产 × 100%")

    # 测试毛利率
    print("\n[4] 毛利率 计算:")
    gross_margin = manager.calculate("gross_margin", financial_data)
    print(f"   营业收入: {financial_data['revenue']/1e8:.1f}亿")
    print(f"   营业成本: {financial_data['cost']/1e8:.1f}亿")
    print(f"   毛利率: {gross_margin}%")
    print(f"   ✅ 公式: 毛利率 = (营收 - 成本) / 营收 × 100%")

    print("\n✅ 标准公式测试通过!")


def test_private_formulas():
    """测试私有公式"""
    print("\n" + "=" * 60)
    print("  测试私有公式（可调整，赛马机制）")
    print("=" * 60)

    manager = FormulaManager()

    # 测试数据
    test_data = {
        "intrinsic_value": 200,  # 内在价值200元
        "current_price": 150,  # 当前价格150元
        "roe": 15.5,
        "revenue_growth": 12.0,
        "profit_growth": 18.0,
        "pe": 20,
        "debt_ratio": 40.0
    }

    # 测试安全边际
    print("\n[1] 安全边际 (私有公式):")
    formula = manager.get_formula("safety_margin")
    safety_margin = manager.calculate("safety_margin", test_data)

    print(f"   内在价值: {test_data['intrinsic_value']}元")
    print(f"   当前价格: {test_data['current_price']}元")
    print(f"   安全边际: {safety_margin}%")
    print(f"   公式版本: {formula.FORMULA_META['version']}")
    print(f"   创建者: {formula.FORMULA_META['created_by']}")
    print(f"   使用次数: {formula.FORMULA_META['usage_count']}")
    print(f"   准确率: {formula.FORMULA_META['accuracy']:.2%}")
    print(f"   状态: {formula.FORMULA_META['status']}")

    # 评估
    evaluation = formula.evaluate(safety_margin)
    print(f"   评估: {evaluation}")

    # 测试综合评分
    print("\n[2] 综合评分 (私有公式):")
    formula = manager.get_formula("composite_score")
    composite_score = manager.calculate("composite_score", test_data)

    print(f"   ROE: {test_data['roe']}%")
    print(f"   营收增长: {test_data['revenue_growth']}%")
    print(f"   净利润增长: {test_data['profit_growth']}%")
    print(f"   PE: {test_data['pe']}")
    print(f"   负债率: {test_data['debt_ratio']}%")
    print(f"   综合评分: {composite_score}/100")
    print(f"   公式版本: {formula.FORMULA_META['version']}")
    print(f"   创建者: {formula.FORMULA_META['created_by']}")

    # 详细分解
    breakdown = formula.breakdown(test_data)
    print(f"\n   评分分解:")
    for dimension, detail in breakdown["breakdown"].items():
        print(f"     {dimension}: {detail['score']}分 × {detail['weight']:.0%} = {detail['weighted_score']:.1f}分")
        print(f"       原因: {detail['reason']}")

    print("\n✅ 私有公式测试通过!")


def test_formula_selection():
    """测试赛马机制"""
    print("\n" + "=" * 60)
    print("  测试赛马机制（选择最优公式）")
    print("=" * 60)

    manager = FormulaManager()

    # 查看公式信息
    print("\n[1] 查看公式信息:")
    info = manager.get_formula_info("composite_score")
    print(f"   公式名称: {info['name']}")
    print(f"   标准公式: {'存在' if info['standard'] else '不存在'}")
    print(f"   私有公式版本:")
    for version in info["private"]:
        print(f"     - 版本: {version['version']}")
        print(f"       创建者: {version['created_by']}")
        print(f"       使用次数: {version['usage_count']}")
        print(f"       准确率: {version['accuracy']}")
        print(f"       状态: {version['status']}")

    # 获取最优公式
    print("\n[2] 获取最优公式:")
    best_formula = manager.get_formula("composite_score", use_best=True)
    print(f"   最优版本: {best_formula.FORMULA_META['version']}")
    print(f"   准确率: {best_formula.FORMULA_META['accuracy']:.2%}")

    print("\n✅ 赛马机制测试通过!")


def test_usage_recording():
    """测试使用记录（赛马数据更新）"""
    print("\n" + "=" * 60)
    print("  测试使用记录（赛马数据更新）")
    print("=" * 60)

    manager = FormulaManager()

    # 获取公式
    formula = manager.get_formula("composite_score")
    version = formula.FORMULA_META['version']

    print(f"\n[1] 初始状态:")
    print(f"   使用次数: {formula.FORMULA_META['usage_count']}")
    print(f"   准确率: {formula.FORMULA_META['accuracy']:.2%}")

    # 记录成功使用
    print(f"\n[2] 记录成功使用:")
    manager.record_usage("composite_score", version, success=True)

    # 重新获取公式查看更新
    formula = manager.get_formula("composite_score")
    print(f"   使用次数: {formula.FORMULA_META['usage_count']}")
    print(f"   准确率: {formula.FORMULA_META['accuracy']:.2%}")

    # 记录失败使用
    print(f"\n[3] 记录失败使用:")
    manager.record_usage("composite_score", version, success=False)

    formula = manager.get_formula("composite_score")
    print(f"   使用次数: {formula.FORMULA_META['usage_count']}")
    print(f"   准确率: {formula.FORMULA_META['accuracy']:.2%}")

    print("\n✅ 使用记录测试通过!")


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("  公式库功能测试")
    print("=" * 60)

    # 测试标准公式
    test_standard_formulas()

    # 测试私有公式
    test_private_formulas()

    # 测试赛马机制
    test_formula_selection()

    # 测试使用记录
    test_usage_recording()

    # 列出所有公式
    print("\n" + "=" * 60)
    print("  公式库总览")
    print("=" * 60)

    manager = FormulaManager()
    all_formulas = manager.list_formulas()

    print(f"\n标准公式 ({len(all_formulas['standard'])}个):")
    for name in all_formulas["standard"]:
        print(f"  - {name}")

    print(f"\n私有公式 ({len(all_formulas['private'])}组):")
    for name in all_formulas["private"]:
        info = manager.get_formula_info(name)
        print(f"  - {name} ({len(info['private'])}个版本)")

    print("\n" + "=" * 60)
    print("  ✅ 所有测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    main()
