# 测试热点新闻检测器
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crawler'))

try:
    from hot_news_detector import HotNewsDetector
    print("HotNewsDetector导入成功")

    detector = HotNewsDetector()
    print("HotNewsDetector实例化成功")

    # 创建测试数据 - 包含更多关键词
    test_news = [
        {
            'title': 'China and US reach new trade agreement',
            'summary': 'China and US made significant progress in trade negotiations, reaching a new consensus on tariff issues.',
            'link': 'http://example.com/news1',
            'published': '2026-07-21',
            'source': 'rss',
            'source_name': 'xinhua',
            'source_display': 'Xinhua',
            'scraped_at': '2026-07-21T10:00:00'
        },
        {
            'title': 'Technology breakthrough in artificial intelligence',
            'summary': 'Major breakthrough in artificial intelligence technology achieved in multiple fields.',
            'link': 'http://example.com/news2',
            'published': '2026-07-21',
            'source': 'rss',
            'source_name': 'sina',
            'source_display': 'Sina News',
            'scraped_at': '2026-07-21T10:00:00'
        }
    ]

    # 测试热点检测
    hot_news = detector.detect_hot_news(test_news)
    print(f"检测到 {len(hot_news)} 条热点新闻")
    if hot_news:
        for i, news in enumerate(hot_news):
            print(f"\n--- Hot News {i+1} ---")
            print(f"Title: {news['title']}")
            print(f"Hot Score: {news['hot_score']}")
            print(f"Keyword Matches: {news['keyword_matches']}")
            print(f"Source Cross Count: {news['source_cross_count']}")
            print(f"Category: {news['category']}")
    else:
        print("No hot news detected")
        # 显示所有新闻的详细信息
        for i, news in enumerate(test_news):
            print(f"\n--- Test News {i+1} ---")
            print(f"Title: {news['title']}")
            print(f"Summary: {news['summary'][:100]}...")

            # 手动检查关键词匹配
            keyword_matches = detector._count_keyword_matches(news)
            print(f"Manual keyword matches: {keyword_matches}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()