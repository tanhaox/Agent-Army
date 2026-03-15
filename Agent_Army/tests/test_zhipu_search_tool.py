"""
测试 ZhipuSearchTool - AI Agent 调用示例
演示 AI Agent 如何使用智谱搜索工具
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
sys.path.insert(0, 'C:/AI-Agent-Local/Agent_Army')

from src.core.tools.data_source.zhipu_search_tool import ZhipuSearchTool


def test_basic_search():
    """测试基本搜索"""

    print("\n" + "="*70)
    print("  测试1: 基本搜索")
    print("="*70 + "\n")

    tool = ZhipuSearchTool()

    # 执行搜索
    result = tool.search('人工智能最新进展', top_k=5)

    print(f"搜索引擎: {result['engine']}")
    print(f"选择原因: {result['reason']}")
    print(f"剩余余额: {result['remaining_balance']}")
    print(f"\n搜索结果:\n")

    for i, item in enumerate(result.get('results', []), 1):
        print(f"{i}. {item['title']}")
        print(f"   链接: {item['url']}")
        print(f"   摘要: {item['snippet'][:100]}...")
        print()


def test_high_importance_search():
    """测试高优先级搜索"""

    print("\n" + "="*70)
    print("  测试2: 高优先级搜索")
    print("="*70 + "\n")

    tool = ZhipuSearchTool()

    # 重要查询
    result = tool.search('股票市场分析报告', importance='high', top_k=5)

    print(f"搜索引擎: {result['engine']}")
    print(f"选择原因: {result['reason']}")
    print(f"剩余余额: {result['remaining_balance']}")
    print(f"\n搜索结果:\n")

    for i, item in enumerate(result.get('results', []), 1):
        print(f"{i}. {item['title']}")
        print()


def test_professional_search():
    """测试专业领域搜索"""

    print("\n" + "="*70)
    print("  测试3: 专业领域搜索（医疗）")
    print("="*70 + "\n")

    tool = ZhipuSearchTool()

    # 医疗健康查询
    result = tool.search('高血压治疗药物最新研究', top_k=5)

    print(f"搜索引擎: {result['engine']}")
    print(f"选择原因: {result['reason']}")
    print(f"剩余余额: {result['remaining_balance']}")
    print(f"\n搜索结果:\n")

    for i, item in enumerate(result.get('results', []), 1):
        print(f"{i}. {item['title']}")
        print()


def test_balance_stats():
    """测试余额统计"""

    print("\n" + "="*70)
    print("  测试4: 资源包余额统计")
    print("="*70 + "\n")

    tool = ZhipuSearchTool()

    stats = tool.get_balance_stats()

    print(f"总余额: {stats['total_balance']} 次")
    print(f"到期时间: {stats['expires_at']}")
    print(f"剩余天数: {stats['days_remaining']} 天")
    print(f"每日配额: {stats['daily_quota']} 次")

    print(f"\n各引擎余额:")
    for engine, info in stats['engines'].items():
        print(f"  {engine}:")
        print(f"    余额: {info['balance']} 次")
        print(f"    价格: ¥{info['price']}/次")
        print(f"    占比: {info['percentage']}%")


def test_usage_recommendation():
    """测试使用建议"""

    print("\n" + "="*70)
    print("  测试5: 使用策略建议")
    print("="*70 + "\n")

    tool = ZhipuSearchTool()

    recommendations = tool.get_usage_recommendation()

    print("搜索引擎使用建议:\n")

    for engine, info in recommendations.items():
        print(f"{engine}:")
        print(f"  分配比例: {info['percentage']}%")
        print(f"  每日配额: {info['daily_quota']} 次")
        print(f"  使用场景: {info['usage']}")
        print()


def test_ai_agent_usage():
    """演示 AI Agent 使用场景"""

    print("\n" + "="*70)
    print("  测试6: AI Agent 使用场景")
    print("="*70 + "\n")

    print("场景: AI 需要搜索最新的政策信息\n")

    tool = ZhipuSearchTool()

    # 1. 搜索政策信息
    print("[步骤1] 搜索政策信息...")
    result = tool.search('2024年中国房地产政策最新动态', importance='high', top_k=5)

    print(f"✓ 使用引擎: {result['engine']}")
    print(f"✓ 原因: {result['reason']}")
    print(f"✓ 找到 {len(result.get('results', []))} 条结果")

    # 2. 搜索行业报告
    print("\n[步骤2] 搜索行业报告...")
    result = tool.search('人工智能行业研究报告2024', top_k=5)

    print(f"✓ 使用引擎: {result['engine']}")
    print(f"✓ 原因: {result['reason']}")

    # 3. 查看余额
    print("\n[步骤3] 查看剩余余额...")
    stats = tool.get_balance_stats()
    print(f"✓ 总余额: {stats['total_balance']} 次")

    print("\n✓ AI 搜索任务完成")


def main():
    """主函数"""

    print("""
╔══════════════════════════════════════════════════════════╗
║       ZhipuSearchTool - AI Agent 调用测试                 ║
╚══════════════════════════════════════════════════════════╝
""")

    try:
        # 运行所有测试
        test_basic_search()
        test_high_importance_search()
        test_professional_search()
        test_balance_stats()
        test_usage_recommendation()
        test_ai_agent_usage()

        print("\n" + "="*70)
        print("  ✓ 所有测试通过")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
