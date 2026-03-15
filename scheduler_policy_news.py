"""
政策新闻定时采集脚本
每天上午9点和下午3点各执行一次
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import time
from datetime import datetime, timedelta
from policy_tool import PolicyTool
import schedule


def fetch_policy_news():
    """执行政策新闻采集任务"""

    print("\n" + "="*60)
    print(f"政策新闻采集任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    try:
        # 初始化工具
        tool = PolicyTool()

        # 获取所有数据
        all_policies = []

        # 1. Tushare Pro
        print("[1/3] Fetching Tushare Pro news...")
        tushare_news = tool.fetch_tushare_news()
        all_policies.extend(tushare_news)
        print(f"✓ Fetched {len(tushare_news)} items from Tushare Pro\n")

        # 2. 中国政府网
        print("[2/3] Fetching Gov.cn policies...")
        gov_policies = tool.fetch_gov_policies()
        all_policies.extend(gov_policies)
        print(f"✓ Fetched {len(gov_policies)} items from Gov.cn\n")

        # 3. 发改委
        print("[3/3] Fetching NDRC policies...")
        ndrc_policies = tool.fetch_ndrc_policies()
        all_policies.extend(ndrc_policies)
        print(f"✓ Fetched {len(ndrc_policies)} items from NDRC\n")

        # 保存到数据库
        print("-" * 60)
        print(f"Total fetched: {len(all_policies)} items")
        print("Saving to database...")

        saved = tool.save_to_db(all_policies)
        print(f"✓ Saved {saved} new items (duplicates filtered)")

        # 显示统计
        stats = tool.get_stats()

        print(f"\n[Database Statistics]")
        print(f"Total items: {stats['total']}")
        print(f"Latest date: {stats['latest_date']}")

        print(f"\nBy source:")
        for source, count in stats['by_source'].items():
            print(f"  {source}: {count}")

        print("-" * 60)
        print(f"✓ Task completed at {datetime.now().strftime('%H:%M:%S')}")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""

    print("""
╔══════════════════════════════════════════════════════════╗
║       政策新闻定时采集系统                                 ║
║       每天 09:00 和 15:00 自动执行                         ║
╚══════════════════════════════════════════════════════════╝
""")

    # 设置定时任务
    schedule.every().day.at("09:00").do(fetch_policy_news)
    schedule.every().day.at("15:00").do(fetch_policy_news)

    # 显示下次执行时间
    next_run = schedule.next_run()
    print(f"✓ Scheduler started")
    print(f"✓ Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"✓ Schedule: 09:00 and 15:00 daily")
    print("\nPress Ctrl+C to exit\n")

    # 立即执行一次（可选）
    print("Running initial fetch...")
    fetch_policy_news()

    # 持续运行
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次

    except KeyboardInterrupt:
        print("\n\n[INFO] Scheduler stopped by user")


if __name__ == '__main__':
    main()
