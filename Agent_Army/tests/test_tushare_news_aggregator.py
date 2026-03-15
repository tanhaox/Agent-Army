"""
测试 TushareNewsAggregator - Tushare新闻聚合工具
演示10个新闻源的使用
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
sys.path.insert(0, 'C:/AI-Agent-Local/Agent_Army')

from src.core.tools.data_source.tushare_news_aggregator import TushareNewsAggregator


def print_header(text):
    """打印标题"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def test_available_sources():
    """测试1: 显示所有可用新闻源"""

    print_header("测试1: 可用新闻源")

    aggregator = TushareNewsAggregator()
    sources = aggregator.get_available_sources()

    print(f"共 {len(sources)} 个新闻源：\n")

    for i, (code, info) in enumerate(sources.items(), 1):
        print(f"{i}. {info['name']} ({code})")
        print(f"   描述: {info['description']}")
        if info['categories']:
            print(f"   子分类: {', '.join(info['categories'])}")
        print()


def test_fetch_single_source():
    """测试2: 获取单个新闻源"""

    print_header("测试2: 获取单个新闻源（雪球）")

    aggregator = TushareNewsAggregator()

    # 获取雪球新闻
    news = aggregator.fetch_news(source='xq', limit=5)

    print(f"获取到 {len(news)} 条雪球新闻：\n")

    for i, item in enumerate(news, 1):
        print(f"{i}. {item['title']}")
        print(f"   时间: {item['publish_time']}")
        print(f"   内容: {item['content'][:100]}...")
        print()


def test_fetch_with_category():
    """测试3: 获取指定分类新闻"""

    print_header("测试3: 获取新浪财经-央行分类")

    aggregator = TushareNewsAggregator()

    # 获取新浪财经-央行分类
    news = aggregator.fetch_news(source='sina', category='央行', limit=5)

    print(f"获取到 {len(news)} 条央行新闻：\n")

    for i, item in enumerate(news, 1):
        print(f"{i}. {item['title']}")
        print(f"   来源: {item['source']} - {item['category']}")
        print(f"   时间: {item['publish_time']}")
        print()


def test_search_news():
    """测试4: 搜索新闻"""

    print_header("测试4: 搜索新闻（关键词：降息）")

    aggregator = TushareNewsAggregator()

    # 先保存一些测试数据
    test_news = aggregator.fetch_news(source='xq', limit=10)
    aggregator.save_to_db(test_news)

    # 搜索
    results = aggregator.search_news('降息', limit=5)

    print(f"找到 {len(results)} 条关于'降息'的新闻：\n")

    for i, item in enumerate(results, 1):
        print(f"{i}. 【{item['source']}】{item['title']}")
        if item['category']:
            print(f"   分类: {item['category']}")
        print(f"   时间: {item['publish_time']}")
        print()


def test_wallstreetcn_categories():
    """测试5: 华尔街见闻多个分类"""

    print_header("测试5: 华尔街见闻-多个分类")

    aggregator = TushareNewsAggregator()

    categories = ['A股', '美股', '黄金', '外汇']

    for cat in categories:
        news = aggregator.fetch_news(source='wallstreetcn', category=cat, limit=3)
        print(f"【{cat}】获取到 {len(news)} 条")
        if news:
            print(f"  最新: {news[0]['title']}")
        print()


def test_cls_categories():
    """测试6: 财联社多个分类"""

    print_header("测试6: 财联社-多个分类")

    aggregator = TushareNewsAggregator()

    categories = ['基金', '港美股', '公司']

    for cat in categories:
        news = aggregator.fetch_news(source='cls', category=cat, limit=3)
        print(f"【{cat}】获取到 {len(news)} 条")
        if news:
            print(f"  最新: {news[0]['title']}")
        print()


def test_get_stats():
    """测试7: 获取统计信息"""

    print_header("测试7: 数据库统计")

    aggregator = TushareNewsAggregator()

    # 先获取一些数据
    test_news = aggregator.fetch_news(source='xq', limit=20)
    aggregator.save_to_db(test_news)

    stats = aggregator.get_stats()

    print(f"总记录数: {stats['total']}")
    print(f"最新时间: {stats['latest_time']}")

    if stats['by_source']:
        print(f"\n按来源统计:")
        for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count}")

    if stats['by_category']:
        print(f"\n按分类统计:")
        for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {category}: {count}")


def test_ai_agent_usage():
    """测试8: AI Agent 使用场景"""

    print_header("测试8: AI Agent 使用场景")

    print("场景: AI 需要获取多源财经新闻并进行综合分析\n")

    aggregator = TushareNewsAggregator()

    # 1. 获取多个源的新闻
    print("[步骤1] 获取多个新闻源...")
    sources_to_fetch = ['xq', 'yicai', 'cls']

    all_news = []
    for source in sources_to_fetch:
        news = aggregator.fetch_news(source=source, limit=5)
        all_news.extend(news)
        print(f"  ✓ {source}: {len(news)} 条")

    # 保存
    saved = aggregator.save_to_db(all_news)
    print(f"\n  保存了 {saved} 条新数据\n")

    # 2. 搜索特定主题
    print("[步骤2] 搜索特定主题...")
    results = aggregator.search_news('央行', limit=5)
    print(f"  找到 {len(results)} 条关于'央行'的新闻\n")

    # 3. 获取统计
    print("[步骤3] 获取统计信息...")
    stats = aggregator.get_stats()
    print(f"  总记录: {stats['total']} 条")
    print(f"  来源数: {len(stats['by_source'])} 个")

    print("\n✓ AI 分析完成")


def test_all_sources_summary():
    """测试9: 所有新闻源概览"""

    print_header("测试9: 所有新闻源概览")

    aggregator = TushareNewsAggregator()
    sources = aggregator.get_available_sources()

    print("Tushare Pro 新闻聚合平台包含：\n")

    print("【7×24小时直播】")
    for code, info in sources.items():
        if '24' in info['description'] or '直播' in info['description']:
            print(f"  • {info['name']}: {info['description']}")

    print("\n【支持子分类的源】")
    for code, info in sources.items():
        if info['categories']:
            print(f"  • {info['name']}: {len(info['categories'])}个分类")
            print(f"    {', '.join(info['categories'][:5])}")
            if len(info['categories']) > 5:
                print(f"    ... 还有 {len(info['categories']) - 5} 个")
            print()

    print("\n【总计】")
    print(f"  • 新闻源: {len(sources)} 个")
    print(f"  • 子分类: {sum(len(info.get('categories', [])) for info in sources.values())} 个")


def main():
    """主函数"""

    print("""
╔══════════════════════════════════════════════════════════╗
║     TushareNewsAggregator - 新闻聚合工具测试              ║
║     支持10个新闻源 + 多个子分类                           ║
╚══════════════════════════════════════════════════════════╝
""")

    try:
        # 运行所有测试
        test_available_sources()
        test_all_sources_summary()
        test_fetch_single_source()
        test_fetch_with_category()
        test_search_news()
        test_wallstreetcn_categories()
        test_cls_categories()
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
