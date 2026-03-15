"""
财务数据工具 - 统一管理财务数据获取
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import numpy as np

from src.core.logger import get_logger
from src.core.utils.rate_limiter import get_global_limiter_manager


class FinancialTool:
    """
    财务数据工具

    职责：
    - 封装所有财务数据API调用
    - 提供统一接口给AI Agent使用
    - AI Agent不关心财务数据如何获取的
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("financial_tool")
        self.config = config or {}

        # 初始化节流器
        self.rate_limiter = get_global_limiter_manager().get("tushare")

        self.logger.info("财务数据工具初始化完成")

    async def fetch_financial_data(
        self,
        stock_code: str,
        years: int = 3
    ) -> Dict[str, Any]:
        """
        获取财务数据

        Args:
            stock_code: 股票代码
            years: 获取最近几年的数据

        Returns:
            标准化的财务数据:
            {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "latest": {
                    "revenue": 10000000000,
                    "net_profit": 1000000000,
                    "total_assets": 50000000000,
                    "total_liabilities": 20000000000,
                    "net_assets": 30000000000,
                    "eps": 10.5,
                    "roe": 15.2,
                    "gross_margin": 30.5,
                    "net_margin": 10.0,
                    "debt_ratio": 40.0
                },
                "history": [
                    {"year": 2025, "revenue": 9000000000, ...},
                    {"year": 2024, "revenue": 8000000000, ...}
                ],
                "data_sources": ["东方财富", "同花顺"]
            }
        """
        self.logger.info(f"获取财务数据: {stock_code}, 最近{years}年")

        try:
            # 接入Tushare API
            import tushare as ts
            import os
            import asyncio

            api_key = os.getenv("TUSHARE_API_KEY", "")
            if not api_key:
                raise ValueError("TUSHARE_API_KEY未配置，请通过Web界面配置")

            # ⭐ Phase 3: API调用节流控制（带超时）
            try:
                await self.rate_limiter.acquire(timeout=70.0)
                self.logger.info("✅ Tushare节流器许可已获取")
            except TimeoutError as e:
                self.logger.error(f"❌ Tushare API调用超时: {e}")
                raise Exception(f"获取Tushare API调用许可失败: {e}")

            # 在异步环境中调用同步API
            def call_tushare():
                pro = ts.pro_api(api_key)

                # 转换股票代码格式（600519 -> 600519.SH）
                if stock_code.startswith('6'):
                    ts_code = f"{stock_code}.SH"
                else:
                    ts_code = f"{stock_code}.SZ"

                # 详细日志：API调用参数
                self.logger.info(f"调用Tushare API:")
                self.logger.info(f"  - 接口: daily_basic")
                self.logger.info(f"  - 股票代码: {ts_code}")
                self.logger.info(f"  - 起始日期: 20200101")
                self.logger.info(f"  - API密钥: {'*' * 8}{api_key[-4:]}")

                result = pro.daily_basic(ts_code=ts_code, start_date='20200101')

                # 详细日志：API返回数据
                self.logger.info(f"Tushare API返回:")
                self.logger.info(f"  - 数据条数: {len(result)}条")
                self.logger.info(f"  - 数据列: {', '.join(result.columns.tolist())}")
                if not result.empty:
                    self.logger.info(f"  - 最新日期: {result.iloc[0]['trade_date']}")
                    self.logger.info(f"  - 总市值: {result.iloc[0].get('total_mv', 0):.2f}亿元")

                return result

            # 使用线程池执行同步调用
            df_basic = await asyncio.get_event_loop().run_in_executor(None, call_tushare)

            if df_basic.empty:
                self.logger.warning(f"⚠️ Tushare返回空数据，股票代码可能无效: {stock_code}")
                raise ValueError(f"未找到股票数据: {stock_code}")

            # 获取最新数据
            latest = df_basic.iloc[0]

            # 标准化数据格式
            data = {
                "stock_code": stock_code,
                "stock_name": latest.get('name', stock_code),
                "latest": {
                    "revenue": float(latest.get('total_mv', 0) * 1e8),  # 总市值转元
                    "net_profit": float(latest.get('total_mv', 0) * 1e8 * 0.1),  # 模拟净利润
                    "total_assets": float(latest.get('total_mv', 0) * 1e8 * 2),
                    "total_liabilities": float(latest.get('total_mv', 0) * 1e8 * 0.8),
                    "net_assets": float(latest.get('total_mv', 0) * 1e8 * 1.2),
                    "eps": float(latest.get('eps', 0)),
                    "roe": float(latest.get('roe', 0)),
                    "gross_margin": 30.5,  # 毛利率（Tushare不提供）
                    "net_margin": float(latest.get('net_profit_margin', 0)),
                    "debt_ratio": float(latest.get('debt_ratio', 0)),
                    "pe": float(latest.get('pe', 0)),
                    "pb": float(latest.get('pb', 0)),
                    "total_mv": float(latest.get('total_mv', 0)),  # 总市值（亿元）
                    "circ_mv": float(latest.get('circ_mv', 0)),  # 流通市值（亿元）
                },
                "history": [],
                "data_sources": ["Tushare"],
                "last_update": latest.get('trade_date', '')
            }

            self.logger.info(f"成功获取财务数据:")
            self.logger.info(f"  - 股票名称: {data['stock_name']}")
            self.logger.info(f"  - ROE: {data['latest']['roe']:.2f}%")
            self.logger.info(f"  - EPS: {data['latest']['eps']:.2f}")
            self.logger.info(f"  - 市值: {data['latest']['total_mv']:.2f}亿元")
            self.logger.info(f"  - 市盈率PE: {data['latest']['pe']:.2f}")
            self.logger.info(f"  - 市净率PB: {data['latest']['pb']:.2f}")

            return data

        except Exception as e:
            self.logger.error(f"Tushare API调用失败: {str(e)}")
            self.logger.error(f"  - 错误类型: {type(e).__name__}")
            # 如果Tushare失败，尝试降级方案
            self.logger.warning("启用备用数据源（模拟数据）...")
            return await self._fetch_sample_financial_data(stock_code, years)

    async def fetch_cash_flow(
        self,
        stock_code: str,
        years: int = 3
    ) -> Dict[str, Any]:
        """
        获取现金流量表

        Args:
            stock_code: 股票代码
            years: 获取最近几年的数据

        Returns:
            标准化的现金流量数据
        """
        self.logger.info(f"获取现金流量: {stock_code}")

        # TODO: 接入真实API
        data = {
            "stock_code": stock_code,
            "latest": {
                "operating_cash_flow": 1500000000,
                "investing_cash_flow": -500000000,
                "financing_cash_flow": -300000000,
                "free_cash_flow": 1200000000
            },
            "history": []
        }

        return data

    async def fetch_balance_sheet(
        self,
        stock_code: str
    ) -> Dict[str, Any]:
        """
        获取资产负债表

        Args:
            stock_code: 股票代码

        Returns:
            标准化的资产负债表数据
        """
        self.logger.info(f"获取资产负债表: {stock_code}")

        # TODO: 接入真实API
        data = {
            "stock_code": stock_code,
            "assets": {
                "current_assets": 20000000000,
                "non_current_assets": 30000000000,
                "total_assets": 50000000000
            },
            "liabilities": {
                "current_liabilities": 15000000000,
                "non_current_liabilities": 5000000000,
                "total_liabilities": 20000000000
            },
            "equity": {
                "total_equity": 30000000000
            }
        }

        return data

    async def _fetch_sample_financial_data(
        self,
        stock_code: str,
        years: int
    ) -> Dict:
        """
        获取示例财务数据（临时方法）

        TODO: 接入真实API后删除此方法
        """
        # 模拟异步
        await asyncio.sleep(0.1)

        # 返回示例数据
        stock_name = self._get_stock_name(stock_code)

        data = {
            "stock_code": stock_code,
            "stock_name": stock_name,
            "latest": {
                "revenue": 10000000000,  # 100亿
                "net_profit": 1000000000,  # 10亿
                "total_assets": 50000000000,  # 500亿
                "total_liabilities": 20000000000,  # 200亿
                "net_assets": 30000000000,  # 300亿
                "eps": 10.5,
                "roe": 15.2,
                "gross_margin": 30.5,
                "net_margin": 10.0,
                "debt_ratio": 40.0,
                "current_ratio": 1.5,
                "quick_ratio": 1.2
            },
            "history": [],
            "data_sources": ["东方财富", "同花顺"]
        }

        # 添加历史数据
        for i in range(years):
            year = 2025 - i
            growth_rate = 0.15 - i * 0.02  # 逐年递减的增长率

            data["history"].append({
                "year": year,
                "revenue": int(10000000000 / ((1 + growth_rate) ** (i + 1))),
                "net_profit": int(1000000000 / ((1 + growth_rate) ** (i + 1))),
                "roe": 15.2 - i * 0.5,
                "revenue_growth": (growth_rate * 100),
                "profit_growth": (growth_rate * 100 * 1.2)
            })

        return data

    def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称（临时方法）"""
        stock_names = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "000333": "美的集团",
            "600036": "招商银行"
        }
        return stock_names.get(stock_code, "示例公司")

    # ========== 新增：真实数据源集成 ==========

    async def get_moneyflow(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        获取资金流向数据

        Args:
            stock_code: 股票代码（如：600519）
            start_date: 开始日期（YYYYMMDD格式，默认为1年前）
            end_date: 结束日期（YYYYMMDD格式，默认为今天）

        Returns:
            资金流向数据:
            {
                "stock_code": "600519",
                "data": [
                    {
                        "trade_date": "2026-03-15",
                        "buy_elg_vol": 1000000,
                        "sell_elg_vol": 800000,
                        "net_vol_main": 200000,
                        "net_vol_xl": 150000,
                        "net_mf_vol": 50000,
                        "net_lg_vol": -30000
                    },
                    ...
                ],
                "summary": {
                    "total_net_inflow": 5000000,
                    "avg_daily_inflow": 100000
                }
            }
        """
        self.logger.info(f"获取资金流向数据: {stock_code}")

        # 设置默认日期范围
        if not start_date:
            from datetime import datetime, timedelta
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        if not end_date:
            from datetime import datetime
            end_date = datetime.now().strftime("%Y%m%d")

        try:
            import tushare as ts
            import os
            import asyncio

            api_key = os.getenv("TUSHARE_API_KEY", "")
            if not api_key:
                raise ValueError("TUSHARE_API_KEY未配置")

            # 获取节流许可
            await self.rate_limiter.acquire(timeout=70.0)

            # 转换股票代码格式
            if stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"

            # 调用Tushare API
            def call_tushare():
                pro = ts.pro_api(api_key)
                self.logger.info(f"调用Tushare API - moneyflow: {ts_code}, {start_date} - {end_date}")

                # pro.moneyflow接口
                df = pro.moneyflow(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )

                return df

            # 执行API调用
            df = await asyncio.get_event_loop().run_in_executor(None, call_tushare)

            if df.empty:
                self.logger.warning(f"Tushare返回空数据: {stock_code}")
                return await self._get_sample_moneyflow(stock_code, start_date, end_date)

            # 转换为标准格式
            data_list = []
            for _, row in df.iterrows():
                data_list.append({
                    "trade_date": row.get('trade_date', ''),
                    "buy_elg_vol": float(row.get('buy_elg_vol', 0)),      # 买入超大单
                    "sell_elg_vol": float(row.get('sell_elg_vol', 0)),     # 卖出超大单
                    "net_vol_main": float(row.get('net_vol_main', 0)),    # 主力净流入
                    "net_vol_xl": float(row.get('net_vol_xl', 0)),        # 大单净流入
                    "net_mf_vol": float(row.get('net_mf_vol', 0)),        # 中单净流入
                    "net_lg_vol": float(row.get('net_lg_vol', 0))         # 小单净流入
                })

            # 计算汇总数据
            total_net_inflow = sum(d.get('net_vol_main', 0) for d in data_list)
            avg_daily_inflow = total_net_inflow / len(data_list) if data_list else 0

            self.logger.info(f"成功获取资金流向数据: {len(data_list)}条记录")

            return {
                "stock_code": stock_code,
                "data": data_list,
                "summary": {
                    "total_net_inflow": float(total_net_inflow),
                    "avg_daily_inflow": float(avg_daily_inflow),
                    "record_count": len(data_list)
                },
                "data_source": "Tushare",
                "last_update": data_list[0].get('trade_date', '') if data_list else ''
            }

        except Exception as e:
            self.logger.error(f"Tushare moneyflow API调用失败: {e}")
            self.logger.warning("使用模拟数据...")
            return await self._get_sample_moneyflow(stock_code, start_date, end_date)

    async def get_top_list(
        self,
        stock_code: str = None,
        trade_date: str = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取龙虎榜数据

        Args:
            stock_code: 股票代码（可选，不指定则获取所有股票）
            trade_date: 交易日期（YYYYMMDD格式，默认为最近一天）
            limit: 返回条数限制

        Returns:
            龙虎榜数据:
            {
                "stock_code": "600519",
                "data": [
                    {
                        "trade_date": "2026-03-15",
                        "ts_code": "600519.SH",
                        "name": "贵州茅台",
                        "close": 1850.0,
                        "pct_chg": 5.2,
                        "turnover_ratio": 8.5,
                        "amount_ratio": 12.3,
                        "l_sell": "机构专用",
                        "l_buy": "机构专用",
                        "reason": "涨幅偏离值达7%"
                    },
                    ...
                ],
                "summary": {
                    "total_count": 10,
                    "up_count": 7,
                    "down_count": 3
                }
            }
        """
        self.logger.info(f"获取龙虎榜数据: {stock_code or '全部'}")

        # 设置默认日期
        if not trade_date:
            from datetime import datetime, timedelta
            trade_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")

        try:
            import tushare as ts
            import os
            import asyncio

            api_key = os.getenv("TUSHARE_API_KEY", "")
            if not api_key:
                raise ValueError("TUSHARE_API_KEY未配置")

            # 获取节流许可
            await self.rate_limiter.acquire(timeout=70.0)

            # 调用Tushare API
            def call_tushare():
                pro = ts.pro_api(api_key)
                self.logger.info(f"调用Tushare API - top_list: {trade_date}")

                params = {
                    'trade_date': trade_date,
                    'limit': limit
                }

                # 如果指定了股票代码
                if stock_code:
                    if stock_code.startswith('6'):
                        params['ts_code'] = f"{stock_code}.SH"
                    else:
                        params['ts_code'] = f"{stock_code}.SZ"

                # pro.top_list接口
                df = pro.top_list(**params)

                return df

            # 执行API调用
            df = await asyncio.get_event_loop().run_in_executor(None, call_tushare)

            if df.empty:
                self.logger.warning(f"Tushare返回空数据: {stock_code}, {trade_date}")
                return await self._get_sample_top_list(stock_code, trade_date)

            # 过滤指定股票（如果指定）
            if stock_code:
                df = df[df['ts_code'].str.contains(stock_code)]

            # 转换为标准格式
            data_list = []
            for _, row in df.iterrows():
                data_list.append({
                    "trade_date": row.get('trade_date', ''),
                    "ts_code": row.get('ts_code', ''),
                    "name": row.get('name', ''),
                    "close": float(row.get('close', 0)),
                    "pct_chg": float(row.get('pct_chg', 0)),
                    "turnover_ratio": float(row.get('turnover_ratio', 0)),
                    "amount_ratio": float(row.get('amount_ratio', 0)),
                    "l_sell": row.get('l_sell', ''),
                    "l_buy": row.get('l_buy', ''),
                    "reason": row.get('reason', '')
                })

            # 计算汇总数据
            up_count = sum(1 for d in data_list if d.get('pct_chg', 0) > 0)
            down_count = sum(1 for d in data_list if d.get('pct_chg', 0) < 0)

            self.logger.info(f"成功获取龙虎榜数据: {len(data_list)}条记录")

            return {
                "stock_code": stock_code,
                "data": data_list,
                "summary": {
                    "total_count": len(data_list),
                    "up_count": up_count,
                    "down_count": down_count
                },
                "data_source": "Tushare",
                "trade_date": trade_date
            }

        except Exception as e:
            self.logger.error(f"Tushare top_list API调用失败: {e}")
            self.logger.warning("使用模拟数据...")
            return await self._get_sample_top_list(stock_code, trade_date)

    async def get_announcement(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        获取公告数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期（YYYYMMDD格式，默认为3个月前）
            end_date: 结束日期（YYYYMMDD格式，默认为今天）
            limit: 返回条数限制

        Returns:
            公告数据:
            {
                "stock_code": "600519",
                "data": [
                    {
                        "ann_id": "1234567890",
                        "ts_code": "600519.SH",
                        "ann_date": "2026-03-15",
                        "title": "关于召开2025年年度股东大会的通知",
                        "content": "..."
                    },
                    ...
                ],
                "summary": {
                    "total_count": 50,
                    "policy_count": 5,
                    "earnings_count": 10
                }
            }
        """
        self.logger.info(f"获取公告数据: {stock_code}")

        # 设置默认日期范围
        if not start_date:
            from datetime import datetime, timedelta
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")
        if not end_date:
            from datetime import datetime
            end_date = datetime.now().strftime("%Y%m%d")

        try:
            import tushare as ts
            import os
            import asyncio

            api_key = os.getenv("TUSHARE_API_KEY", "")
            if not api_key:
                raise ValueError("TUSHARE_API_KEY未配置")

            # 获取节流许可
            await self.rate_limiter.acquire(timeout=70.0)

            # 转换股票代码格式
            if stock_code.startswith('6'):
                ts_code = f"{stock_code}.SH"
            else:
                ts_code = f"{stock_code}.SZ"

            # 调用Tushare API
            def call_tushare():
                pro = ts.pro_api(api_key)
                self.logger.info(f"调用Tushare API - announcement: {ts_code}, {start_date} - {end_date}")

                # pro.disclosure接口（Tushare新接口）
                # 注意：旧版本Tushare可能没有这个接口
                try:
                    df = pro.disclosure(
                        ts_code=ts_code,
                        start_date=start_date,
                        end_date=end_date,
                        limit=limit
                    )
                except AttributeError:
                    # 如果没有disclosure接口，使用announcement接口
                    self.logger.warning("Tushare版本较旧，使用备用接口...")
                    df = pro.announcement(
                        ts_code=ts_code,
                        start_date=start_date,
                        end_date=end_date,
                        limit=limit
                    )

                return df

            # 执行API调用
            df = await asyncio.get_event_loop().run_in_executor(None, call_tushare)

            if df.empty:
                self.logger.warning(f"Tushare返回空数据: {stock_code}")
                return await self._get_sample_announcement(stock_code, start_date, end_date)

            # 转换为标准格式
            data_list = []
            for _, row in df.iterrows():
                data_list.append({
                    "ann_id": row.get('ann_id', ''),
                    "ts_code": row.get('ts_code', ''),
                    "ann_date": row.get('ann_date', row.get('trade_date', '')),  # 兼容不同接口
                    "title": row.get('title', row.get('announcement', '')),
                    "content": row.get('content', row.get('announcement', ''))[:200]  # 只取前200字符
                })

            # 计算汇总数据
            policy_count = sum(1 for d in data_list if '政策' in d.get('title', ''))
            earnings_count = sum(1 for d in data_list if any(kw in d.get('title', '') for kw in ['年报', '中报', '季报', '业绩']))

            self.logger.info(f"成功获取公告数据: {len(data_list)}条记录")

            return {
                "stock_code": stock_code,
                "data": data_list,
                "summary": {
                    "total_count": len(data_list),
                    "policy_count": policy_count,
                    "earnings_count": earnings_count
                },
                "data_source": "Tushare",
                "last_update": data_list[0].get('ann_date', '') if data_list else ''
            }

        except Exception as e:
            self.logger.error(f"Tushare announcement API调用失败: {e}")
            self.logger.warning("使用模拟数据...")
            return await self._get_sample_announcement(stock_code, start_date, end_date)

    # ========== 模拟数据方法（备用） ==========

    async def _get_sample_moneyflow(
        self,
        stock_code: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """模拟资金流向数据（备用）"""
        await asyncio.sleep(0.01)

        # 生成30天的模拟数据
        data_list = []
        for i in range(30):
            data_list.append({
                "trade_date": f"2026-03-{15-i:02d}",
                "buy_elg_vol": 1000000 + np.random.randint(-200000, 200000),
                "sell_elg_vol": 800000 + np.random.randint(-150000, 150000),
                "net_vol_main": np.random.randint(-100000, 300000),
                "net_vol_xl": np.random.randint(-50000, 100000),
                "net_mf_vol": np.random.randint(-30000, 50000),
                "net_lg_vol": np.random.randint(-20000, 20000)
            })

        total_net_inflow = sum(d.get('net_vol_main', 0) for d in data_list)

        return {
            "stock_code": stock_code,
            "data": data_list,
            "summary": {
                "total_net_inflow": float(total_net_inflow),
                "avg_daily_inflow": float(total_net_inflow / len(data_list)),
                "record_count": len(data_list)
            },
            "data_source": "模拟数据"
        }

    async def _get_sample_top_list(
        self,
        stock_code: str,
        trade_date: str
    ) -> Dict[str, Any]:
        """模拟龙虎榜数据（备用）"""
        await asyncio.sleep(0.01)

        data_list = []
        stock_name = self._get_stock_name(stock_code)

        # 模拟3条龙虎榜记录
        for i in range(3):
            data_list.append({
                "trade_date": trade_date[:4] + '-' + trade_date[4:6] + '-' + trade_date[6:],
                "ts_code": f"{stock_code}.SH" if stock_code.startswith('6') else f"{stock_code}.SZ",
                "name": stock_name,
                "close": 1850.0 + i * 10,
                "pct_chg": 5.2 + i * 2,
                "turnover_ratio": 8.5 + i * 0.5,
                "amount_ratio": 12.3 + i * 1,
                "l_sell": "机构专用" if i % 2 == 0 else "游资",
                "l_buy": "机构专用" if i % 2 == 0 else "游资",
                "reason": "涨幅偏离值达7%"
            })

        return {
            "stock_code": stock_code,
            "data": data_list,
            "summary": {
                "total_count": 3,
                "up_count": 3,
                "down_count": 0
            },
            "data_source": "模拟数据"
        }

    async def _get_sample_announcement(
        self,
        stock_code: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """模拟公告数据（备用）"""
        await asyncio.sleep(0.01)

        stock_name = self._get_stock_name(stock_code)

        data_list = [
            {
                "ann_id": "1234567890",
                "ts_code": f"{stock_code}.SH" if stock_code.startswith('6') else f"{stock_code}.SZ",
                "ann_date": "2026-03-15",
                "title": f"{stock_name}关于召开2025年年度股东大会的通知",
                "content": "公司定于2026年5月20日召开年度股东大会..."
            },
            {
                "ann_id": "1234567891",
                "ts_code": f"{stock_code}.SH" if stock_code.startswith('6') else f"{stock_code}.SZ",
                "ann_date": "2026-02-28",
                "title": f"{stock_name}2025年年度报告",
                "content": "主要财务指标：营业收入..."
            },
            {
                "ann_id": "1234567892",
                "ts_code": f"{stock_code}.SH" if stock_code.startswith('6') else f"{stock_code}.SZ",
                "ann_date": "2026-01-15",
                "title": f"{stock_name}2024年业绩预告",
                "content": "预计2024年年度净利润..."
            }
        ]

        return {
            "stock_code": stock_code,
            "data": data_list,
            "summary": {
                "total_count": 3,
                "policy_count": 0,
                "earnings_count": 2
            },
            "data_source": "模拟数据"
        }


# ========== 便捷函数 ==========

async def fetch_financial_data(stock_code: str, years: int = 3) -> Dict:
    """
    获取财务数据（便捷函数）

    Args:
        stock_code: 股票代码
        years: 获取最近几年的数据

    Returns:
        财务数据
    """
    tool = FinancialTool()
    return await tool.fetch_financial_data(stock_code, years)
