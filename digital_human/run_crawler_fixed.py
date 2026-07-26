# 启动爬虫并生成新闻数据文件
import json
import sys
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保正确添加路径
sys.path.append(os.path.dirname(__file__))

try:
    # 导入爬虫模块
    from crawler.news_scraper import NewsScraper

    logger.info("正在启动新闻爬虫...")

    # 创建爬虫实例
    scraper = NewsScraper()

    # 抓取新闻
    news_data = scraper.fetch_news_from_all_sources()

    # 如果没有获取到真实数据，使用示例数据
    if not news_data:
        logger.warning("没有获取到真实新闻数据，使用示例数据")
        news_data = scraper.create_sample_data()

    # 过滤新闻内容
    filtered_news = scraper.filter_news(news_data, min_length=50)

    # 检测热点新闻
    hot_news = scraper.detect_hot_news(filtered_news, min_sources=1, min_keyword_matches=1)

    # 如果热点新闻为空，使用所有新闻
    if not hot_news:
        logger.info("没有检测到热点新闻，使用所有过滤后的新闻")
        hot_news = filtered_news

    # 保存数据到文件
    output_file = os.path.join(os.path.dirname(__file__), 'news_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(hot_news, f, ensure_ascii=False, indent=2)

    logger.info(f"成功抓取并处理了 {len(hot_news)} 条新闻数据")

    # 显示前几条新闻
    print("\n前3条新闻：")
    for i, news in enumerate(hot_news[:3]):
        print(f"{i+1}. {news['title'][:100]}...")
        print(f"   来源: {news['source_display']}")
        print(f"   热度评分: {news['hot_score']}")
        print(f"   多源交叉数: {news['source_cross_count']}")
        print()

    print("数据已保存到 news_data.json")

except Exception as e:
    logger.error(f"错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)