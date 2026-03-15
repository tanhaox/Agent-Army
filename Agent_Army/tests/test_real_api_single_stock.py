"""
真实API数据质量测试
只测试中国电建（601669）一只股票，避免过度消耗API配额
"""
import pytest

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载.env文件
from dotenv import load_dotenv
env_path = project_root / '.env'
load_dotenv(env_path)

from src.core.logger import get_logger
from src.core.tools.data_source.financial_tool import FinancialTool


class RealApiTester:
    """真实API测试器"""

    def __init__(self):
        self.logger = get_logger("real_api_tester")
        self.tool = FinancialTool()
        self.test_stock = "601669"  # 中国电建

    @pytest.mark.asyncio
    async def test_api_connection(self):
        """测试API连接"""
        self.logger.info("=" * 60)
        self.logger.info("测试1: API连接测试")
        self.logger.info("=" * 60)

        api_key = os.getenv("TUSHARE_API_KEY", "")
        if not api_key:
            self.logger.error("TUSHARE_API_KEY未配置！")
            return False

        self.logger.info(f"API密钥: {'*' * 8}{api_key[-4:]}")

        try:
            import tushare as ts
            pro = ts.pro_api(api_key)

            # 测试简单查询
            def test_call():
                # 查询股票基本信息
                df = pro.stock_basic(ts_code='601669.SH', fields='ts_code,name,area,industry,list_date')
                return df

            import asyncio
            df = await asyncio.get_event_loop().run_in_executor(None, test_call)

            if not df.empty:
                self.logger.info("[OK] API连接成功")
                self.logger.info(f"   股票名称: {df.iloc[0]['name']}")
                self.logger.info(f"   所属行业: {df.iloc[0]['industry']}")
                self.logger.info(f"   上市日期: {df.iloc[0]['list_date']}")
                return True
            else:
                self.logger.error("[ERROR] API返回空数据")
                return False

        except Exception as e:
            self.logger.error(f"[ERROR] API连接失败: {e}")
            return False

    @pytest.mark.asyncio
    async def test_moneyflow_data(self):
        """测试资金流向数据"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("测试2: 资金流向数据（moneyflow）")
        self.logger.info("=" * 60)

        # 测试最近30天
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")

        self.logger.info(f"测试股票: {self.test_stock}（中国电建）")
        self.logger.info(f"时间范围: {start_date} - {end_date}")

        try:
            data = await self.tool.get_moneyflow(
                stock_code=self.test_stock,
                start_date=start_date,
                end_date=end_date
            )

            # 分析数据质量
            self.logger.info("\n数据质量分析:")
            self.logger.info(f"  - 数据条数: {data['summary']['record_count']}条")
            self.logger.info(f"  - 数据来源: {data.get('data_source', '未知')}")

            if data['data']:
                latest = data['data'][0]
                self.logger.info(f"  - 最新日期: {latest['trade_date']}")
                self.logger.info(f"  - 主力净流入: {latest['net_vol_main']:.0f}手")
                self.logger.info(f"  - 超大单净买入: {latest['buy_elg_vol'] - latest['sell_elg_vol']:.0f}手")

                # 检查数据完整性
                has_null = any(v is None or v == '' for d in data['data'] for v in d.values())
                if has_null:
                    self.logger.warning("  [!] 数据包含空值")
                else:
                    self.logger.info("  [OK] 数据完整，无空值")

                return True
            else:
                self.logger.warning("  [!] 未获取到数据")
                return False

        except Exception as e:
            self.logger.error(f"[ERROR] 测试失败: {e}")
            return False

    @pytest.mark.asyncio
    async def test_top_list_data(self):
        """测试龙虎榜数据"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("测试3: 龙虎榜数据（top_list）")
        self.logger.info("=" * 60)

        # 测试最近一天
        trade_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        self.logger.info(f"测试股票: {self.test_stock}（中国电建）")
        self.logger.info(f"交易日期: {trade_date}")

        try:
            data = await self.tool.get_top_list(
                stock_code=self.test_stock,
                trade_date=trade_date,
                limit=10
            )

            # 分析数据质量
            self.logger.info("\n数据质量分析:")
            self.logger.info(f"  - 数据条数: {data['summary']['total_count']}条")
            self.logger.info(f"  - 数据来源: {data.get('data_source', '未知')}")

            if data['data']:
                for i, item in enumerate(data['data'][:3], 1):
                    self.logger.info(f"\n  记录{i}:")
                    self.logger.info(f"    - 日期: {item['trade_date']}")
                    self.logger.info(f"    - 收盘价: {item['close']:.2f}元")
                    self.logger.info(f"    - 涨跌幅: {item['pct_chg']:.2f}%")
                    self.logger.info(f"    - 上榜原因: {item['reason']}")

                return True
            else:
                self.logger.info("  [INFO] 该股票当日未上龙虎榜（正常情况）")
                return True  # 不算失败，只是没上榜

        except Exception as e:
            self.logger.error(f"[ERROR] 测试失败: {e}")
            return False

    @pytest.mark.asyncio
    async def test_announcement_data(self):
        """测试公告数据"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("测试4: 公告数据（announcement/disclosure）")
        self.logger.info("=" * 60)

        # 测试最近3个月
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")

        self.logger.info(f"测试股票: {self.test_stock}（中国电建）")
        self.logger.info(f"时间范围: {start_date} - {end_date}")

        try:
            data = await self.tool.get_announcement(
                stock_code=self.test_stock,
                start_date=start_date,
                end_date=end_date,
                limit=10
            )

            # 分析数据质量
            self.logger.info("\n数据质量分析:")
            self.logger.info(f"  - 数据条数: {data['summary']['total_count']}条")
            self.logger.info(f"  - 数据来源: {data.get('data_source', '未知')}")

            if data['data']:
                self.logger.info(f"\n  最近{min(3, len(data['data']))}条公告:")

                for i, item in enumerate(data['data'][:3], 1):
                    self.logger.info(f"\n  公告{i}:")
                    self.logger.info(f"    - 日期: {item['ann_date']}")
                    self.logger.info(f"    - 标题: {item['title']}")

                # 检查公告类型
                if data['summary']['earnings_count'] > 0:
                    self.logger.info(f"\n[INFO] 包含{data['summary']['earnings_count']}条业绩相关公告")

                return True
            else:
                self.logger.warning("  ⚠️ 未获取到公告数据")
                return False

        except Exception as e:
            self.logger.error(f"[ERROR] 测试失败: {e}")
            return False

    @pytest.mark.asyncio
    async def test_daily_basic_data(self):
        """测试日线基础数据"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("测试5: 日线基础数据（daily_basic）")
        self.logger.info("=" * 60)

        self.logger.info(f"测试股票: {self.test_stock}（中国电建）")

        try:
            data = await self.tool.fetch_financial_data(
                stock_code=self.test_stock,
                years=1
            )

            # 分析数据质量
            self.logger.info("\n数据质量分析:")
            self.logger.info(f"  - 数据来源: {data.get('data_sources', ['未知'])[0]}")

            latest = data.get('latest', {})
            if latest:
                self.logger.info(f"\n  最新指标:")
                self.logger.info(f"    - 股票名称: {data.get('stock_name', '未知')}")
                self.logger.info(f"    - 总市值: {latest.get('total_mv', 0):.2f}亿元")
                self.logger.info(f"    - 流通市值: {latest.get('circ_mv', 0):.2f}亿元")
                self.logger.info(f"    - 市盈率PE: {latest.get('pe', 0):.2f}")
                self.logger.info(f"    - 市净率PB: {latest.get('pb', 0):.2f}")
                self.logger.info(f"    - ROE: {latest.get('roe', 0):.2f}%")
                self.logger.info(f"    - EPS: {latest.get('eps', 0):.2f}元")

                # 检查数据合理性
                if latest.get('total_mv', 0) > 0:
                    self.logger.info("\n  [OK] 数据质量良好")
                    return True
                else:
                    self.logger.warning("\n  ⚠️ 市值数据异常")
                    return False
            else:
                self.logger.warning("\n  ⚠️ 未获取到数据")
                return False

        except Exception as e:
            self.logger.error(f"[ERROR] 测试失败: {e}")
            return False

    async def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("[TEST] 真实API数据质量测试 - 中国电建（601669）")
        self.logger.info("=" * 60)

        results = {}

        # 测试1: API连接
        results['connection'] = await self.test_api_connection()

        # 测试2-5: 各类数据
        results['moneyflow'] = await self.test_moneyflow_data()
        results['top_list'] = await self.test_top_list_data()
        results['announcement'] = await self.test_announcement_data()
        results['daily_basic'] = await self.test_daily_basic_data()

        # 总结报告
        self.logger.info("\n" + "=" * 60)
        self.logger.info("测试总结报告")
        self.logger.info("=" * 60)

        total_tests = len(results)
        passed_tests = sum(results.values())

        self.logger.info(f"\n总测试数: {total_tests}")
        self.logger.info(f"通过数: {passed_tests}")
        self.logger.info(f"失败数: {total_tests - passed_tests}")
        self.logger.info(f"通过率: {passed_tests/total_tests*100:.1f}%")

        self.logger.info("\n详细结果:")
        for test_name, result in results.items():
            status = "[OK]" if result else "[FAIL]"
            self.logger.info(f"  - {test_name}: {status}")

        # 建议
        self.logger.info("\n" + "=" * 60)
        self.logger.info("优化建议")
        self.logger.info("=" * 60)

        if not results.get('connection'):
            self.logger.info("1. [HIGH] 优先级最高：修复API连接问题")
            self.logger.info("   - 检查TUSHARE_API_KEY是否正确")
            self.logger.info("   - 检查网络连接")
        elif results.get('daily_basic') and not results.get('moneyflow'):
            self.logger.info("1. [MED] 优先级高：集成资金流向数据")
            self.logger.info("   - 历史节点分析AI的关键数据")
        elif results.get('daily_basic') and not results.get('announcement'):
            self.logger.info("1. [MED] 优先级中：完善公告数据获取")
            self.logger.info("   - 用于事件驱动分析")
        else:
            self.logger.info("[OK] 所有核心数据源工作正常")
            self.logger.info("   可以开始集成到历史节点分析AI")

        return results


async def main():
    """主函数"""
    tester = RealApiTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
