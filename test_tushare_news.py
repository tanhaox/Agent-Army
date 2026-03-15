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
        print("TUSHARE_API_KEY未配置")
        print("\n请先在系统配置中设置Tushare API Key")
        return

    print("="*60)
    print("Tushare Pro 新闻接口测试")
    print("="*60)
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print()

    import tushare as ts

    try:
        # 初始化API
        pro = ts.pro_api(api_key)

        # 测试新闻接口
        print("测试1: 获取最新新闻...")
        print("-"*60)

        # 获取新闻（最新的20条）
        df = pro.news(
            src='sina',  # 新浪新闻
            date='20260315',  # 日期
            limit=20  # 数量
        )

        print(f"✅ 成功！获取 {len(df)} 条新闻\n")

        # 显示前5条
        print("【最新5条新闻】")
        print("-"*60)
        for i, row in df.head(5).iterrows():
            print(f"\n{i+1}. {row['title']}")
            print(f"   时间: {row.get('datetime', 'N/A')}")
            print(f"   来源: {row.get('source', 'N/A')}")
            print(f"   链接: {row.get('url', 'N/A')}")

        print("\n" + "="*60)
        print("【数据统计】")
        print("-"*60)
        print(f"总数: {len(df)} 条")
        print(f"列名: {list(df.columns)}")

        return True

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        print("\n可能的原因:")
        print("1. API Key无效或已过期")
        print("2. 账户没有新闻接口权限")
        print("3. 网络连接问题")
        return False


if __name__ == '__main__':
    test_tushare_news()
