"""
政策新闻搜索工具
支持命令行快速查询政策新闻数据库
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import argparse
from datetime import datetime
from policy_tool import PolicyTool


def print_header(text):
    """打印标题"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def print_result(item, index):
    """打印单条结果"""
    print(f"{index}. 【{item['source']}】{item['title']}")
    print(f"   日期: {item['publish_date']}")
    if item.get('url'):
        print(f"   链接: {item['url']}")
    if item.get('content') and len(item['content']) < 100:
        print(f"   内容: {item['content']}")
    print()


def search_by_keyword(tool, keyword, limit=20):
    """按关键词搜索"""

    print_header(f"🔍 搜索关键词: {keyword}")

    results = tool.search(keyword, limit=limit)

    if not results:
        print(f"❌ 未找到包含 '{keyword}' 的政策新闻\n")
        return 0

    print(f"✓ 找到 {len(results)} 条结果\n")

    for i, item in enumerate(results, 1):
        print_result(item, i)

    return len(results)


def search_by_source(tool, source, limit=20):
    """按来源搜索"""

    print_header(f"📂 数据来源: {source}")

    import sqlite3
    conn = sqlite3.connect(tool.db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT title, content, source, category, url, publish_date
        FROM policies
        WHERE source LIKE ?
        ORDER BY publish_date DESC
        LIMIT ?
    ''', (f'%{source}%', limit))

    results = cursor.fetchall()
    conn.close()

    if not results:
        print(f"❌ 未找到来自 '{source}' 的数据\n")
        return 0

    policies = []
    for row in results:
        policies.append({
            'title': row[0],
            'content': row[1],
            'source': row[2],
            'category': row[3],
            'url': row[4],
            'publish_date': row[5]
        })

    print(f"✓ 找到 {len(policies)} 条结果\n")

    for i, item in enumerate(policies, 1):
        print_result(item, i)

    return len(policies)


def search_by_date(tool, date_str, limit=20):
    """按日期搜索"""

    print_header(f"📅 发布日期: {date_str}")

    import sqlite3
    conn = sqlite3.connect(tool.db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT title, content, source, category, url, publish_date
        FROM policies
        WHERE publish_date = ?
        ORDER BY id DESC
        LIMIT ?
    ''', (date_str, limit))

    results = cursor.fetchall()
    conn.close()

    if not results:
        print(f"❌ 未找到日期为 '{date_str}' 的数据\n")
        return 0

    policies = []
    for row in results:
        policies.append({
            'title': row[0],
            'content': row[1],
            'source': row[2],
            'category': row[3],
            'url': row[4],
            'publish_date': row[5]
        })

    print(f"✓ 找到 {len(policies)} 条结果\n")

    for i, item in enumerate(policies, 1):
        print_result(item, i)

    return len(policies)


def show_latest(tool, limit=20):
    """显示最新数据"""

    print_header(f"📰 最新政策新闻 (Top {limit})")

    import sqlite3
    conn = sqlite3.connect(tool.db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT title, content, source, category, url, publish_date
        FROM policies
        ORDER BY publish_date DESC, id DESC
        LIMIT ?
    ''', (limit,))

    results = cursor.fetchall()
    conn.close()

    if not results:
        print("❌ 数据库中没有数据\n")
        return 0

    policies = []
    for row in results:
        policies.append({
            'title': row[0],
            'content': row[1],
            'source': row[2],
            'category': row[3],
            'url': row[4],
            'publish_date': row[5]
        })

    for i, item in enumerate(policies, 1):
        print_result(item, i)

    return len(policies)


def show_stats(tool):
    """显示统计信息"""

    print_header("📊 数据库统计")

    stats = tool.get_stats()

    print(f"总记录数: {stats['total']}")
    print(f"最新日期: {stats['latest_date']}")

    print(f"\n按来源统计:")
    for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")

    print(f"\n按分类统计:")
    for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")

    print()


def interactive_search(tool):
    """交互式搜索模式"""

    print_header("🔍 交互式搜索模式")

    print("可用命令:")
    print("  /关键词          - 搜索关键词")
    print("  @来源            - 按来源搜索")
    print("  @Tushare         - 搜索Tushare数据")
    print("  @中国政府网      - 搜索政府网数据")
    print("  @发改委          - 搜索发改委数据")
    print("  最新             - 显示最新20条")
    print("  统计             - 显示统计信息")
    print("  quit / exit      - 退出")
    print()

    while True:
        try:
            query = input("🔍 搜索> ").strip()

            if not query:
                continue

            if query in ['quit', 'exit', 'q']:
                print("\n✓ 退出搜索\n")
                break

            elif query == '最新':
                show_latest(tool, 20)

            elif query == '统计':
                show_stats(tool)

            elif query.startswith('@'):
                # 按来源搜索
                source = query[1:].strip()
                search_by_source(tool, source, 20)

            else:
                # 关键词搜索
                search_by_keyword(tool, query, 20)

        except KeyboardInterrupt:
            print("\n\n✓ 退出搜索\n")
            break
        except Exception as e:
            print(f"❌ 错误: {str(e)}\n")


def main():
    """主函数"""

    parser = argparse.ArgumentParser(
        description='政策新闻搜索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python search_policy_news.py 央行                    # 搜索关键词
  python search_policy_news.py @Tushare                # 按来源搜索
  python search_policy_news.py --date 2026-03-15       # 按日期搜索
  python search_policy_news.py --latest                # 显示最新20条
  python search_policy_news.py --stats                 # 显示统计
  python search_policy_news.py --interactive           # 交互模式
        """
    )

    parser.add_argument('keyword', nargs='?', help='搜索关键词')
    parser.add_argument('-s', '--source', help='按来源搜索')
    parser.add_argument('-d', '--date', help='按日期搜索 (YYYY-MM-DD)')
    parser.add_argument('-l', '--latest', action='store_true', help='显示最新数据')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('-i', '--interactive', action='store_true', help='交互式搜索')
    parser.add_argument('--limit', type=int, default=20, help='结果数量限制 (默认20)')
    parser.add_argument('--db', help='数据库文件路径')

    args = parser.parse_args()

    # 初始化工具
    tool = PolicyTool(db_path=args.db)

    # 根据参数执行不同操作
    if args.interactive:
        interactive_search(tool)

    elif args.stats:
        show_stats(tool)

    elif args.latest:
        show_latest(tool, args.limit)

    elif args.date:
        search_by_date(tool, args.date, args.limit)

    elif args.source:
        search_by_source(tool, args.source, args.limit)

    elif args.keyword:
        search_by_keyword(tool, args.keyword, args.limit)

    else:
        # 没有参数，显示帮助并进入交互模式
        parser.print_help()
        print("\n进入交互模式...\n")
        interactive_search(tool)


if __name__ == '__main__':
    main()
