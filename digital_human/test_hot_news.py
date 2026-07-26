# 测试热点新闻检测器
import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    from crawler.hot_news_detector import HotNewsDetector
    print("HotNewsDetector导入成功")

    detector = HotNewsDetector()
    print("HotNewsDetector实例化成功")

    # 创建测试数据
    test_news = [
        {
            'title': '中国与美国在贸易问题上达成新的协议',
            'summary': '中美两国在贸易谈判中取得了重要进展，双方就关税问题达成了新的共识。',
            'link': 'http://example.com/news1',
            'published': '2026-07-21',
            'source': 'rss',
            'source_name': 'xinhua',
            'source_display': '新华社',
            'scraped_at': '2026-07-21T10:00:00'
        }
    ]

    # 测试热点检测
    hot_news = detector.detect_hot_news(test_news)
    print(f"检测到 {len(hot_news)} 条热点新闻")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()