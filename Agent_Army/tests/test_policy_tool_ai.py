"""
测试 PolicyTool - AI Agent 调用示例
演示 AI Agent 如何使用政策工具搜索政策新闻
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
sys.path.insert(0, 'C:/AI-Agent-Local/Agent_Army')

from src.core.tools.data_source.policy_tool import PolicyTool


def test_search_by_keyword():
    """测试关键词搜索"""

    print("\n" + "="*70)
    print("  测试1: 关键词搜索")
    print("="*70 + "\n")

    # 初始化工具
    tool = PolicyTool()

    # 搜索央行相关政策
    results = tool.search_policies('央行', limit=5)

    print(f"找到 {len(results)} 条关于'央行'的政策：\n")

    for i, item in enumerate(results, 1):
        print(f"{i}. 【{item['source']}】{item['title']}")
        print(f"   日期: {item['publish_date']}")
        if item.get('url'):
            print(f"   链接: {item['url']}")
        print()


def test_search_by_source():
    """测试按来源搜索"""

    print("\n" + "="*70)
    print("  测试2: 按来源搜索")
    print("="*70 + "\n")

    tool = PolicyTool()

    # 搜索政府网政策
    results = tool.search_policies('', source='中国政府网', limit=5)

    print(f"找到 {len(results)} 条政府网政策：\n")

    for i, item in enumerate(results, 1):
        print(f"{i}. {item['title']}")
        print(f"   日期: {item['publish_date']}")
        print()


def test_get_latest():
    """测试获取最新政策"""

    print("\n" + "="*70)
    print("  测试3: 获取最新政策")
    print("="*70 + "\n")

    tool = PolicyTool()

    # 获取最新10条
    results = tool.get_latest_policies(limit=10)

    print(f"最新 {len(results)} 条政策：\n")

    for i, item in enumerate(results, 1):
        print(f"{i}. 【{item['source']}】{item['title']}")
        print(f"   日期: {item['publish_date']}")
        print()


def test_get_stats():
    """测试统计信息"""

    print("\n" + "="*70)
    print("  测试4: 数据库统计")
    print("="*70 + "\n")

    tool = PolicyTool()

    stats = tool.get_stats()

    print(f"总记录数: {stats['total']}")
    print(f"最新日期: {stats['latest_date']}")

    print(f"\n按来源统计:")
    for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")

    print(f"\n按分类统计:")
    for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")


def test_ai_agent_usage():
    """演示 AI Agent 使用场景"""

    print("\n" + "="*70)
    print("  测试5: AI Agent 使用场景")
    print("="*70 + "\n")

    print("场景: AI 需要分析最新的货币政策对股市的影响\n")

    tool = PolicyTool()

    # 1. 搜索货币政策相关
    print("[步骤1] 搜索货币政策相关政策...")
    results = tool.search_policies('央行 货币政策', limit=5)

    print(f"找到 {len(results)} 条相关政策：\n")
    for item in results[:3]:
        print(f"- {item['title']}")
        print(f"  来源: {item['source']}")
        print(f"  日期: {item['publish_date']}")
        print()

    # 2. 获取最新财经新闻
    print("\n[步骤2] 获取最新财经新闻...")
    latest = tool.get_latest_policies(limit=5, source='Tushare Pro')

    print(f"最新 {len(latest)} 条财经新闻：\n")
    for item in latest[:3]:
        print(f"- {item['title']}")
        print(f"  日期: {item['publish_date']}")
        print()

    # 3. 分析数据
    print("\n[步骤3] AI 分析完成，生成投资建议...")
    print("✓ 基于当前政策环境，建议关注...")
    print()


def main():
    """主函数"""

    print("""
╔══════════════════════════════════════════════════════════╗
║       PolicyTool - AI Agent 调用测试                       ║
╚══════════════════════════════════════════════════════════╝
""")

    try:
        # 运行所有测试
        test_search_by_keyword()
        test_search_by_source()
        test_get_latest()
        test_get_stats()
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
