"""
测试Tushare Pro新闻接口
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, 'C:/AI-Agent-Local/Agent_Army')

def test_tushare_news():
    """测试Tushare新闻接口"""

    # 加载.env文件
    env_path = 'C:/AI-Agent-Local/Agent_Army/.env'
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('TUSHARE_API_KEY='):
                    api_key = line.split('=', 1)[1]
                    os.environ['TUSHARE_API_KEY'] = api_key
                    break

    # 获取API Key
    api_key = os.getenv("TUSHARE_API_KEY")

    if not api_key:
        print("TUSHARE_API_KEY not configured")
        return

    print("="*60)
    print("Tushare Pro News API Test")
    print("="*60)
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print()

    import tushare as ts

    try:
        # 初始化API
        pro = ts.pro_api(api_key)

        # 测试新闻接口
        print("Test 1: Get latest news...")
        print("-"*60)

        # 获取新闻（最新的20条）
        df = pro.news(
            src='sina',  # 新浪新闻
            date='20260315',  # 日期
            limit=20  # 数量
        )

        print(f"SUCCESS! Got {len(df)} news\n")

        # 显示前5条
        print("[Latest 5 News]")
        print("-"*60)
        for i, row in df.head(5).iterrows():
            print(f"\n{i+1}. {row['title']}")
            print(f"   Time: {row.get('datetime', 'N/A')}")
            print(f"   Source: {row.get('source', 'N/A')}")
            print(f"   URL: {row.get('url', 'N/A')}")

        print("\n" + "="*60)
        print("[Data Statistics]")
        print("-"*60)
        print(f"Total: {len(df)} news")
        print(f"Columns: {list(df.columns)}")

        return True

    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("\nPossible reasons:")
        print("1. Invalid API Key")
        print("2. No permission for news API")
        print("3. Network connection issue")
        return False


if __name__ == '__main__':
    test_tushare_news()
