# -*- coding: utf-8 -*-
"""
AKShare A股数据同步脚本
功能：获取历史K线 + 个股信息
测试日期：2026-03-12
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import sys
import time

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def retry_on_failure(max_retries=3, delay=2):
    """重试装饰器"""
    import functools
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"  ⚠️  第{attempt+1}次尝试失败，{delay}秒后重试... 错误: {e}")
                    time.sleep(delay * (attempt + 1))
        return wrapper
    return decorator


@retry_on_failure(max_retries=3, delay=2)
def get_stock_hist(symbol, start_date, end_date):
    """
    获取股票历史K线数据

    Args:
        symbol: 股票代码（如 "601669"）
        start_date: 开始日期（格式：YYYYMMDD）
        end_date: 结束日期（格式：YYYYMMDD）

    Returns:
        DataFrame: K线数据
    """
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"  # 前复权
    )
    return df


@retry_on_failure(max_retries=3, delay=2)
def get_stock_info(symbol):
    """
    获取个股详细信息

    Args:
        symbol: 股票代码（如 "601669"）

    Returns:
        DataFrame: 个股信息
    """
    df = ak.stock_individual_info_em(symbol=symbol)
    return df


def sync_stock_data(stock_code, stock_name, days=30):
    """
    同步单只股票的完整数据

    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        days: 获取最近N天的数据

    Returns:
        dict: 包含K线数据和个股信息
    """
    print(f"\n📊 正在同步: {stock_name} ({stock_code})")
    print("-" * 100)

    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')

    result = {
        'code': stock_code,
        'name': stock_name,
        'success': False,
        'kline': None,
        'info': None,
        'error': None
    }

    # 1. 获取K线数据
    print(f"  📈 获取K线数据 ({start_date_str} ~ {end_date_str})...")
    try:
        kline_df = get_stock_hist(stock_code, start_date_str, end_date_str)

        if kline_df is not None and len(kline_df) > 0:
            print(f"  ✅ K线数据获取成功: {len(kline_df)} 条记录")
            print(f"     字段: {list(kline_df.columns)}")

            # 显示最新5条数据
            print(f"\n  最新5个交易日数据:")
            print(f"  {'日期':<12} {'开盘':<8} {'收盘':<8} {'最高':<8} {'最低':<8} {'成交量':<12} {'涨跌幅':<8}")
            print("  " + "-" * 90)
            for _, row in kline_df.tail(5).iterrows():
                volume_str = f"{row['成交量']/10000:.1f}万手" if row['成交量'] > 0 else "0"
                print(f"  {row['日期']:<12} {row['开盘']:<8.2f} {row['收盘']:<8.2f} {row['最高']:<8.2f} "
                      f"{row['最低']:<8.2f} {volume_str:<12} {row['涨跌幅']:<8.2f}%")

            result['kline'] = kline_df
        else:
            print(f"  ❌ K线数据为空")
            result['error'] = "K线数据为空"
    except Exception as e:
        print(f"  ❌ K线数据获取失败: {e}")
        result['error'] = str(e)

    # 添加间隔，避免请求过快
    time.sleep(0.5)

    # 2. 获取个股信息
    print(f"\n  📋 获取个股信息...")
    try:
        info_df = get_stock_info(stock_code)

        if info_df is not None and len(info_df) > 0:
            print(f"  ✅ 个股信息获取成功: {len(info_df)} 项")

            # 转换为字典显示
            info_dict = dict(zip(info_df['item'], info_df['value']))

            # 显示关键信息
            print(f"\n  关键信息:")
            for key in ['股票代码', '股票名称', '总市值', '流通市值', '行业', '上市时间']:
                if key in info_dict:
                    print(f"    {key}: {info_dict[key]}")

            result['info'] = info_df
        else:
            print(f"  ❌ 个股信息为空")
    except Exception as e:
        print(f"  ❌ 个股信息获取失败: {e}")

    result['success'] = (result['kline'] is not None) or (result['info'] is not None)

    return result


def test_multiple_stocks():
    """测试多只股票的数据同步"""

    print_section("AKShare A股数据同步测试")

    # 测试股票列表
    test_stocks = [
        {'code': '601669', 'name': '中国电建', 'industry': '建筑装饰'},
        {'code': '600519', 'name': '贵州茅台', 'industry': '食品饮料'},
        {'code': '000001', 'name': '平安银行', 'industry': '银行'},
        {'code': '002594', 'name': '比亚迪', 'industry': '汽车'},
        {'code': '300750', 'name': '宁德时代', 'industry': '电池'},
    ]

    print(f"\n📋 测试股票列表: {len(test_stocks)} 只")
    for stock in test_stocks:
        print(f"   - {stock['name']} ({stock['code']}) - {stock['industry']}")

    # 同步数据
    results = []
    for i, stock in enumerate(test_stocks, 1):
        print(f"\n{'='*100}")
        print(f"进度: [{i}/{len(test_stocks)}]")
        result = sync_stock_data(stock['code'], stock['name'], days=30)
        results.append(result)

        # 股票之间添加间隔
        if i < len(test_stocks):
            print(f"\n⏳ 等待1秒后处理下一只股票...")
            time.sleep(1)

    # 汇总结果
    print_section("同步结果汇总")

    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count

    print(f"\n总计: {len(results)} 只股票")
    print(f"✅ 成功: {success_count} 只")
    print(f"❌ 失败: {fail_count} 只")
    print(f"成功率: {success_count/len(results)*100:.1f}%")

    print(f"\n{'='*100}")
    print(f"{'股票名称':<12} {'代码':<8} {'K线数据':<10} {'个股信息':<10} {'状态':<8}")
    print('-' * 100)

    for r in results:
        kline_status = f"{len(r['kline'])}条" if r['kline'] is not None else "无"
        info_status = f"{len(r['info'])}项" if r['info'] is not None else "无"
        status = "✅成功" if r['success'] else "❌失败"

        print(f"{r['name']:<12} {r['code']:<8} {kline_status:<10} {info_status:<10} {status:<8}")

        if r['error']:
            print(f"  ⚠️  错误: {r['error']}")

    print(f"\n{'='*100}")

    # 数据质量检查
    print_section("数据质量检查")

    for r in results:
        if r['kline'] is not None:
            df = r['kline']

            print(f"\n📊 {r['name']} ({r['code']})")

            # 检查数据完整性
            required_fields = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅']
            missing_fields = [f for f in required_fields if f not in df.columns]

            if missing_fields:
                print(f"  ❌ 缺失字段: {missing_fields}")
            else:
                print(f"  ✅ 字段完整: {len(df.columns)} 个字段")

            # 检查数据连续性
            df_sorted = df.sort_values('日期')
            date_range = (df_sorted['日期'].max() - df_sorted['日期'].min()).days
            print(f"  📅 数据跨度: {date_range} 天")

            # 检查最新数据日期
            latest_date = df_sorted['日期'].max()
            today = datetime.now().date()
            days_diff = (today - latest_date).days
            print(f"  🕐 最新数据: {latest_date} (距今天{days_diff}天)")

    return results


def test_data_export(results):
    """测试数据导出功能"""
    print_section("数据导出测试")

    # 合并所有K线数据
    all_kline_data = []

    for r in results:
        if r['kline'] is not None:
            df = r['kline'].copy()
            df['股票代码'] = r['code']
            df['股票名称'] = r['name']
            all_kline_data.append(df)

    if all_kline_data:
        combined_df = pd.concat(all_kline_data, ignore_index=True)

        print(f"\n📊 合并数据统计:")
        print(f"  总记录数: {len(combined_df)} 条")
        print(f"  股票数量: {combined_df['股票代码'].nunique()} 只")
        print(f"  日期范围: {combined_df['日期'].min()} ~ {combined_df['日期'].max()}")

        # 保存为CSV
        output_file = 'stock_data_test.csv'
        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 数据已导出: {output_file}")
        print(f"   文件大小: {len(open(output_file, 'rb').read()) / 1024:.2f} KB")

        # 显示数据结构
        print(f"\n📋 数据字段:")
        for i, col in enumerate(combined_df.columns, 1):
            print(f"   {i:2d}. {col}")

        # 显示前5条记录
        print(f"\n📄 数据预览（前5条）:")
        print(combined_df[['股票代码', '股票名称', '日期', '收盘', '成交量', '涨跌幅']].head().to_string(index=False))

    else:
        print(f"\n❌ 没有数据可导出")


if __name__ == '__main__':
    print("\n" + "🚀" * 50)
    print("  AKShare A股数据同步脚本 - 本地测试")
    print("  测试时间:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("🚀" * 50)

    # 显示AKShare版本
    print(f"\n📦 环境信息:")
    print(f"   AKShare版本: {ak.__version__}")
    print(f"   Pandas版本: {pd.__version__}")
    print(f"   Python版本: {sys.version.split()[0]}")

    try:
        # 测试多只股票
        results = test_multiple_stocks()

        # 测试数据导出
        test_data_export(results)

        print("\n" + "=" * 100)
        print("  ✅ 测试完成！")
        print("=" * 100)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
