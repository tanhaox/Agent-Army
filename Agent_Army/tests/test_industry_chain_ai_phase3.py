"""
产业链分析AI测试 - Phase 3实现验证
"""

import asyncio
import sys
from pathlib import Path

# Windows UTF-8 编码设置
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_industry_chain_analyzer():
    """测试产业链分析AI"""
    from src.agents.business.industry_analyzers import IndustryChainAnalyzer

    print("=" * 60)
    print("  产业链分析AI测试 - Phase 3实现")
    print("=" * 60)
    print()

    # 初始化分析器
    analyzer = IndustryChainAnalyzer()

    # 测试用例
    test_cases = [
        ("600519", "贵州茅台 - 白酒行业"),
        ("000858", "五粮液 - 白酒行业"),
        ("300750", "宁德时代 - 新能源"),
    ]

    for stock_code, description in test_cases:
        print(f"\n{'=' * 60}")
        print(f"测试: {description}")
        print(f"股票代码: {stock_code}")
        print(f"{'=' * 60}\n")

        try:
            # 执行分析
            result = await analyzer.analyze(stock_code)

            # 显示结果
            print(f"✅ 分析成功")
            print(f"  股票名称: {result.stock_name}")
            print(f"  行业名称: {result.industry_name}")
            print(f"  综合评分: {result.score:.1f}/100")
            print(f"  置信度: {result.confidence:.1%}")
            print(f"  行业规模: {result.industry_size:.1f}亿元")
            print(f"  行业增长: {result.industry_growth:.1f}%")
            print(f"  市场份额: {result.market_share:.1f}%")
            print(f"  行业排名: {result.industry_rank}")
            print(f"  行业周期: {result.industry_cycle}")
            print(f"  成长驱动: {', '.join(result.growth_driver)}")
            print(f"  风险因素: {', '.join(result.risk_factors)}")
            print(f"\n  分析摘要: {result.summary}")

        except Exception as e:
            print(f"❌ 分析失败: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)


async def test_east_money_scraper():
    """测试东方财富爬虫"""
    from src.core.tools.data_source.east_money_scraper import EastMoneyScraper

    print("\n" + "=" * 60)
    print("  东方财富爬虫测试")
    print("=" * 60)
    print()

    scraper = EastMoneyScraper()

    # 测试股票
    test_code = "600519"
    print(f"测试股票: {test_code} (贵州茅台)\n")

    try:
        result = await scraper.get_industry_info(test_code)

        print("✅ 数据获取成功")
        print(f"  股票名称: {result['stock_name']}")
        print(f"  行业名称: {result['industry_name']}")
        print(f"  行业代码: {result['industry_code']}")
        print(f"  行业规模: {result['industry_size']:.1f}亿元")
        print(f"  行业增长: {result['industry_growth']:.1f}%")
        print(f"  市场份额: {result['market_share']:.1f}%")
        print(f"  行业排名: {result['industry_rank']}")
        print(f"  行业周期: {result['industry_cycle']}")
        print(f"  数据来源: {', '.join(result['data_sources'])}")
        print(f"  更新时间: {result['last_update']}")

        # 显示产业链信息
        chain = result.get('industry_chain', {})
        if chain:
            print(f"\n  产业链信息:")
            if chain.get('upstream'):
                print(f"    上游: {', '.join(chain['upstream'])}")
            if chain.get('midstream'):
                print(f"    中游: {', '.join(chain['midstream'])}")
            if chain.get('downstream'):
                print(f"    下游: {', '.join(chain['downstream'])}")

    except Exception as e:
        print(f"❌ 数据获取失败: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)


async def test_scoring_logic():
    """测试评分逻辑"""
    from src.agents.business.industry_analyzers import IndustryChainAnalyzer

    print("\n" + "=" * 60)
    print("  评分逻辑测试")
    print("=" * 60)
    print()

    analyzer = IndustryChainAnalyzer()

    # 测试用例1: 高增长行业
    test_data_1 = {
        "industry_size": 5000.0,
        "industry_growth": 25.0,
        "market_share": 8.0,
        "industry_rank": 5
    }

    score_1 = analyzer._calculate_industry_score(test_data_1)
    print(f"测试1 - 高增长行业:")
    print(f"  行业规模: {test_data_1['industry_size']}亿")
    print(f"  行业增长: {test_data_1['industry_growth']}%")
    print(f"  市场份额: {test_data_1['market_share']}%")
    print(f"  行业排名: {test_data_1['industry_rank']}")
    print(f"  评分: {score_1:.1f}/100 ⭐")

    # 测试用例2: 低增长行业
    test_data_2 = {
        "industry_size": 1000.0,
        "industry_growth": 3.0,
        "market_share": 2.0,
        "industry_rank": 50
    }

    score_2 = analyzer._calculate_industry_score(test_data_2)
    print(f"\n测试2 - 低增长行业:")
    print(f"  行业规模: {test_data_2['industry_size']}亿")
    print(f"  行业增长: {test_data_2['industry_growth']}%")
    print(f"  市场份额: {test_data_2['market_share']}%")
    print(f"  行业排名: {test_data_2['industry_rank']}")
    print(f"  评分: {score_2:.1f}/100")

    # 测试用例3: 负增长行业
    test_data_3 = {
        "industry_size": 500.0,
        "industry_growth": -5.0,
        "market_share": 1.0,
        "industry_rank": 150
    }

    score_3 = analyzer._calculate_industry_score(test_data_3)
    print(f"\n测试3 - 负增长行业:")
    print(f"  行业规模: {test_data_3['industry_size']}亿")
    print(f"  行业增长: {test_data_3['industry_growth']}%")
    print(f"  市场份额: {test_data_3['market_share']}%")
    print(f"  行业排名: {test_data_3['industry_rank']}")
    print(f"  评分: {score_3:.1f}/100 ⚠️")

    print("\n" + "=" * 60)


async def main():
    """主测试函数"""
    print("\n🧪 产业链分析AI - Phase 3实现测试")
    print("=" * 60)

    # 测试1: 评分逻辑
    await test_scoring_logic()

    # 测试2: 东方财富爬虫
    await test_east_money_scraper()

    # 测试3: 产业链分析器
    await test_industry_chain_analyzer()

    print("\n✅ 所有测试完成")


if __name__ == "__main__":
    asyncio.run(main())
