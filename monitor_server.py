#!/usr/bin/env python3
"""
monitor.py - 盘中监控脚本
扫描持仓股和关注池，检测异常/机会信号，生成预警
"""

import sys
import time
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List

# 添加项目路径
sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/agent_army')

from db_manager import get_db_manager
from data_fetcher_duckdb import get_data_fetcher
from agent_army.technical_analysis_agent import TechnicalAnalysisAgent

# 可选导入
try:
    from scripts.news_sentiment_analyzer import NewsSentimentAnalyzer
    HAS_NEWS_ANALYZER = True
except ImportError:
    HAS_NEWS_ANALYZER = False
    print("⚠️ NewsSentimentAnalyzer 未找到，将跳过新闻分析")

try:
    from scripts.capital_flow_analyzer import CapitalFlowAnalyzer
    HAS_CAPITAL_ANALYZER = True
except ImportError:
    try:
        from agent_army.capital_flow_analyzer import CapitalFlowAnalyzer
        HAS_CAPITAL_ANALYZER = True
    except ImportError:
        HAS_CAPITAL_ANALYZER = False
        print("⚠️ CapitalFlowAnalyzer 未找到，将跳过资金面分析")

try:
    from event_impact_analyzer import EventImpactAnalyzer
    HAS_EVENT_ANALYZER = True
except ImportError:
    HAS_EVENT_ANALYZER = False
    print("⚠️ EventImpactAnalyzer 未找到，将跳过事件分析")

try:
    from market_sentiment_analyzer import MarketSentimentAnalyzer
    HAS_MARKET_SENTIMENT = True
except ImportError:
    HAS_MARKET_SENTIMENT = False
    print("⚠️ MarketSentimentAnalyzer 未找到，将跳过市场情绪监控")

try:
    from market_technical_analyzer import MarketTechnicalAnalyzer
    HAS_MARKET_TECHNICAL = True
except ImportError:
    HAS_MARKET_TECHNICAL = False
    print("⚠️ MarketTechnicalAnalyzer 未找到，将跳过大盘技术监控")

try:
    from capital_flow_v2_analyzer import CapitalFlowV2Analyzer
    HAS_CAPITAL_FLOW_V2 = True
except ImportError:
    HAS_CAPITAL_FLOW_V2 = False
    print("⚠️ CapitalFlowV2Analyzer 未找到，将跳过资金面监控")

# ========== 配置 ==========
ALERT_LEVELS = {
    'high': 3,    # 严重预警（如放量破位）
    'medium': 2,  # 中等信号（如MACD金叉）
    'low': 1      # 一般提示（如RSI超卖）
}

# 止损预警配置（基于回测验证: 5%止损 Sharpe最优）
STOP_LOSS_CONFIG = {
    'enabled': True,
    'threshold': 0.95,     # 跌破成本价95%触发预警
    'apply_to_holdings': True,
    'apply_to_watchlist': True,  # 关注池中也提示参考止损
}

class Monitor:
    def __init__(self):
        self.db = get_db_manager()
        self.data_fetcher = get_data_fetcher()
        self.news_analyzer = NewsSentimentAnalyzer() if HAS_NEWS_ANALYZER else None
        self.capital_analyzer = CapitalFlowAnalyzer() if HAS_CAPITAL_ANALYZER else None
        self.event_analyzer = EventImpactAnalyzer() if HAS_EVENT_ANALYZER else None

    def get_watch_symbols(self) -> List[Dict]:
        """获取需要监控的股票列表（持仓 + 关注池，含成本价）"""
        conn = self.db.get_conn('holdings')
        # 当前持仓（含成本价）
        holdings = conn.execute("""
            SELECT code, name, shares, cost_price
            FROM current_holdings
        """).fetchdf()
        # 关注池
        watchlist = conn.execute("""
            SELECT stock_code as code, stock_name as name FROM watchlist
        """).fetchdf()
        # 合并去重
        if holdings.empty and watchlist.empty:
            return []
        if holdings.empty:
            all_stocks = watchlist[['code', 'name']].copy()
            all_stocks['cost_price'] = None
        elif watchlist.empty:
            all_stocks = holdings[['code', 'name', 'cost_price']].copy()
        else:
            h = holdings[['code', 'name', 'cost_price']].copy()
            w = watchlist[['code', 'name']].copy()
            w['cost_price'] = None
            all_stocks = pd.concat([h, w], ignore_index=True)
        all_stocks = all_stocks.drop_duplicates(subset='code')
        return all_stocks.to_dict('records')

    def check_technical(self, stock_code: str, stock_name: str) -> List[Dict]:
        """技术面检查，返回信号列表"""
        signals = []
        try:
            # 获取最近3个月日K线
            df = self.data_fetcher.get_daily_kline(stock_code,
                (datetime.now() - pd.Timedelta(days=90)).strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d'))
            if df.empty:
                return signals

            # 调用技术分析Agent
            agent = TechnicalAnalysisAgent(stock_data={'df': df})
            result = agent.analyze()

            # 提取关键指标
            rsi = result.get('indicators', {}).get('RSI', 50)
            macd = result.get('indicators', {}).get('MACD', 0)
            trend = result.get('trend', 'sideways')

            # RSI 超买超卖
            if rsi > 70:
                signals.append({'level': 'medium', 'type': '技术超买',
                    'msg': f'{stock_name}({stock_code}) RSI={rsi:.1f}，进入超买区'})
            elif rsi < 30:
                signals.append({'level': 'medium', 'type': '技术超卖',
                    'msg': f'{stock_name}({stock_code}) RSI={rsi:.1f}，进入超卖区'})

            # MACD 金叉死叉（简单判断：当日MACD>0且前日<=0）
            if len(df) >= 2:
                macd_prev = result.get('indicators_prev', {}).get('MACD', 0)
                if macd > 0 and macd_prev <= 0:
                    signals.append({'level': 'medium', 'type': 'MACD金叉',
                        'msg': f'{stock_name}({stock_code}) MACD金叉，短期看涨'})
                elif macd < 0 and macd_prev >= 0:
                    signals.append({'level': 'medium', 'type': 'MACD死叉',
                        'msg': f'{stock_name}({stock_code}) MACD死叉，短期看跌'})

            # 趋势
            if trend == 'up':
                signals.append({'level': 'low', 'type': '上升趋势',
                    'msg': f'{stock_name}({stock_code}) 处于上升趋势'})
            elif trend == 'down':
                signals.append({'level': 'high', 'type': '下降趋势',
                    'msg': f'{stock_name}({stock_code}) 处于下降趋势，注意风险'})

            # 换手率异动检测
            if 'Turnover' in df.columns and df['Turnover'].notna().any():
                turnover = df['Turnover'].dropna()
                if len(turnover) >= 20:
                    turnover_last = float(turnover.iloc[-1])
                    turnover_ma20 = float(turnover.tail(20).mean())
                    if turnover_ma20 > 0:
                        turnover_ratio = turnover_last / turnover_ma20
                        if turnover_ratio > 2:
                            signals.append({
                                'level': 'high',
                                'type': '换手率异常放大',
                                'msg': f'{stock_name}({stock_code}) 换手率异常放大(当前{turnover_last:.2f}%, '
                                       f'20日均{turnover_ma20:.2f}%, 放大{turnover_ratio:.1f}倍), 注意主力动向'
                            })
                        elif turnover_ratio > 1.5:
                            signals.append({
                                'level': 'medium',
                                'type': '换手率放大',
                                'msg': f'{stock_name}({stock_code}) 换手率放大(当前{turnover_last:.2f}%, '
                                       f'20日均{turnover_ma20:.2f}%, 放大{turnover_ratio:.1f}倍)'
                            })
                        elif turnover_ratio < 0.3:
                            signals.append({
                                'level': 'low',
                                'type': '换手率极低',
                                'msg': f'{stock_name}({stock_code}) 换手率极低(当前{turnover_last:.2f}%, '
                                       f'20日均{turnover_ma20:.2f}%, 仅{turnover_ratio:.1f}倍), 交易冷清'
                            })

        except Exception as e:
            print(f"技术分析失败 {stock_code}: {e}")
        return signals

    def check_capital(self, stock_code: str, stock_name: str) -> List[Dict]:
        """资金面检查（主力资金 + 龙虎榜 + 北向资金）"""
        signals = []
        if not self.capital_analyzer:
            return signals
        try:
            # 调用资金面分析器
            capital_result = self.capital_analyzer.analyze(stock_code)
            if capital_result:
                # 主力净流入
                inflow = capital_result.get('main_net_inflow', 0)
                if inflow > 2e7:  # 大于2000万
                    signals.append({'level': 'medium', 'type': '主力大幅流入',
                        'msg': f'{stock_name}({stock_code}) 主力净流入{inflow/1e4:.0f}万'})
                elif inflow < -2e7:
                    signals.append({'level': 'high', 'type': '主力大幅流出',
                        'msg': f'{stock_name}({stock_code}) 主力净流出{-inflow/1e4:.0f}万'})

                # 龙虎榜机构净买入预警
                lhb_score = capital_result.get('lhb_score', 0)
                if lhb_score > 0:
                    lhb_details = [d for d in capital_result.get('details', []) if '龙虎榜' in d]
                    detail_msg = lhb_details[0] if lhb_details else '龙虎榜机构净买入'
                    signals.append({
                        'level': 'medium',
                        'type': '龙虎榜机构买入',
                        'msg': f'{stock_name}({stock_code}) {detail_msg}，关注短期异动'
                    })

                # 北向资金评分
                north_score = capital_result.get('north_score', 0)
                if north_score < -0.5:
                    north_details = [d for d in capital_result.get('details', []) if '北向' in d and '流出' in d]
                    if north_details:
                        signals.append({
                            'level': 'high',
                            'type': '北向资金流出',
                            'msg': f'{stock_name}({stock_code}) {north_details[0]}，注意外资减仓风险'
                        })
        except Exception as e:
            print(f"资金面分析失败 {stock_code}: {e}")

        # 独立的北向连续流出检测
        try:
            code = self.data_fetcher.normalize_stock_code(stock_code)
            end = datetime.now().strftime('%Y-%m-%d')
            start = (datetime.now() - pd.Timedelta(days=10)).strftime('%Y-%m-%d')
            north_df = self.data_fetcher.get_north_flow(code, start, end)
            if north_df is not None and not north_df.empty and len(north_df) >= 3:
                north_df = north_df.sort_values('trade_date', ascending=False).head(3)
                negative_days = sum(1 for v in north_df['net_buy_amount'].values if v < 0)
                if negative_days >= 3:
                    total_out = abs(north_df['net_buy_amount'].sum())
                    signals.append({
                        'level': 'high',
                        'type': '北向连续流出',
                        'msg': f'{stock_name}({stock_code}) 北向资金连续3日净流出，注意外资减仓风险'
                    })
        except Exception:
            pass  # 北向数据不可用时静默跳过

        return signals

    def check_news(self, stock_code: str, stock_name: str) -> List[Dict]:
        """新闻情感检查（从 market_data.db 读取近1天预存新闻）"""
        signals = []
        try:
            df = self.data_fetcher.get_stock_news(stock_code, days=1)
            if df is None or df.empty:
                return signals

            avg = df['sentiment_score'].mean()
            news_count = len(df)

            if avg < -0.4:
                signals.append({'level': 'medium', 'type': '新闻利空',
                    'msg': f'{stock_name}({stock_code}) 近期新闻偏负面(avg={avg:.2f}, {news_count}条)'})
            elif avg > 0.4:
                signals.append({'level': 'low', 'type': '新闻利多',
                    'msg': f'{stock_name}({stock_code}) 近期新闻偏正面(avg={avg:.2f}, {news_count}条)'})
        except Exception as e:
            print(f"新闻分析失败 {stock_code}: {e}")
        return signals

    def check_events(self, stock_code: str, stock_name: str) -> List[Dict]:
        """事件驱动检查（近期重大事件 + 预期差信号）"""
        signals = []
        if not self.event_analyzer:
            return signals
        try:
            result = self.event_analyzer.analyze(stock_code)
            score = result.get('total_score', 5.0)

            # 预期差信号
            for sig in result.get('surprise_signals', []):
                direction = '超预期' if sig['direction'] == 'beat' else '不及预期'
                level = 'medium' if sig['direction'] == 'beat' else 'high'
                signals.append({
                    'level': level,
                    'type': f'业绩{direction}',
                    'msg': f'{stock_name}({stock_code}) {sig["metric"]}{direction}{sig["surprise_pct"]:+.1f}%'
                })

            # 近期重大事件
            for evt in result.get('recent_events', []):
                evt_type = evt.get('event_type', '')
                if evt_type in ('lockup_expire', 'insider_sell'):
                    signals.append({
                        'level': 'high',
                        'type': evt['event_title'],
                        'msg': f'{stock_name}({stock_code}) 近期{evt["event_title"]}: {evt.get("event_detail", "")}'
                    })
                elif evt_type in ('dividend', 'share_buyback', 'insider_buy'):
                    signals.append({
                        'level': 'low',
                        'type': evt['event_title'],
                        'msg': f'{stock_name}({stock_code}) 近期{evt["event_title"]}: {evt.get("event_detail", "")}'
                    })

            # 未来事件预警
            for evt in result.get('upcoming_events', []):
                evt_type = evt.get('event_type', '')
                if evt_type in ('lockup_expire',):
                    signals.append({
                        'level': 'medium',
                        'type': '解禁预告',
                        'msg': f'{stock_name}({stock_code}) 即将{evt["event_title"]}({evt["event_date"]})'
                    })
                elif evt_type == 'earnings_release':
                    signals.append({
                        'level': 'low',
                        'type': '财报预告',
                        'msg': f'{stock_name}({stock_code}) 将于{evt["event_date"]}披露财报'
                    })
        except Exception as e:
            print(f"事件分析失败 {stock_code}: {e}")
        return signals

    def check_stop_loss(self, stock_code: str, stock_name: str,
                        cost_price: float = None) -> List[Dict]:
        """止损预警：检测是否跌破成本价95%（基于回测验证的5%止损阈值）"""
        signals = []
        if not STOP_LOSS_CONFIG['enabled']:
            return signals
        if cost_price is None or cost_price <= 0:
            return signals
        try:
            df = self.data_fetcher.get_daily_kline(stock_code,
                (datetime.now() - pd.Timedelta(days=5)).strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d'))
            if df.empty:
                return signals
            current_price = float(df['close'].iloc[-1] if 'close' in df.columns else df['Close'].iloc[-1])
            loss_pct = (current_price / cost_price - 1) * 100
            if current_price < cost_price * STOP_LOSS_CONFIG['threshold']:
                signals.append({
                    'level': 'high',
                    'type': '建议止损',
                    'msg': f'{stock_name}({stock_code}) 当前价{current_price:.2f}, '
                           f'成本价{cost_price:.2f}, 跌幅{loss_pct:.1f}%, '
                           f'已跌破{STOP_LOSS_CONFIG["threshold"]:.0%}止损线，建议止损'
                })
            elif current_price < cost_price * 0.97:
                signals.append({
                    'level': 'medium',
                    'type': '接近止损线',
                    'msg': f'{stock_name}({stock_code}) 当前价{current_price:.2f}, '
                           f'成本价{cost_price:.2f}, 跌幅{loss_pct:.1f}%, 接近止损线'
                })
        except Exception as e:
            print(f"止损检查失败 {stock_code}: {e}")
        return signals

    def check_price_limit(self, stock_code: str, stock_name: str) -> List[Dict]:
        """涨跌停预警：检测是否接近涨停/跌停价格"""
        signals = []
        try:
            # 获取涨跌停价格
            conn_md = self.db.get_conn('market_data')
            limit_df = conn_md.execute(f"""
                SELECT up_limit, down_limit FROM stk_limit
                WHERE ts_code = '{stock_code}'
                ORDER BY trade_date DESC LIMIT 1
            """).fetchdf()
            if limit_df.empty:
                return signals

            up_limit = float(limit_df.iloc[0]['up_limit']) if pd.notna(limit_df.iloc[0]['up_limit']) else None
            down_limit = float(limit_df.iloc[0]['down_limit']) if pd.notna(limit_df.iloc[0]['down_limit']) else None

            if up_limit is None and down_limit is None:
                return signals

            # 获取当前价格
            df = self.data_fetcher.get_daily_kline(stock_code,
                (datetime.now() - pd.Timedelta(days=5)).strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d'))
            if df.empty:
                return signals

            current_price = float(df['close'].iloc[-1])

            # 接近涨停（>95%）
            if up_limit and up_limit > 0:
                ratio_up = current_price / up_limit
                if ratio_up >= 0.95:
                    signals.append({
                        'level': 'medium',
                        'type': '接近涨停',
                        'msg': f'{stock_name}({stock_code}) 当前价{current_price:.2f}, '
                               f'涨停价{up_limit:.2f}, 接近度{ratio_up:.1%}'
                    })

            # 接近跌停（<105%）
            if down_limit and down_limit > 0:
                ratio_down = current_price / down_limit
                if ratio_down <= 1.05:
                    signals.append({
                        'level': 'high',
                        'type': '接近跌停',
                        'msg': f'{stock_name}({stock_code}) 当前价{current_price:.2f}, '
                               f'跌停价{down_limit:.2f}, 接近度{ratio_down:.1%}'
                    })
        except Exception as e:
            print(f"涨跌停检查失败 {stock_code}: {e}")
        return signals

    def save_alert(self, stock_code: str, alert_type: str, level: str, message: str):
        """将预警写入数据库"""
        conn = self.db.get_conn('system')
        # 获取下一个id
        max_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM alerts").fetchone()[0]
        next_id = max_id + 1
        conn.execute("""
            INSERT INTO alerts (id, alert_time, stock_code, category, level, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [next_id, datetime.now(), stock_code, alert_type, level, message, datetime.now()])

    def run_once(self):
        """执行一次完整监控"""
        stocks = self.get_watch_symbols()
        if not stocks:
            print(f"{datetime.now()} 无监控股票")
            return

        print(f"{datetime.now()} 开始监控 {len(stocks)} 只股票")
        for stock in stocks:
            code = stock['code']
            name = stock['name']
            cost_price = stock.get('cost_price')
            # 综合各维度信号
            all_signals = []
            all_signals.extend(self.check_technical(code, name))
            all_signals.extend(self.check_capital(code, name))
            all_signals.extend(self.check_news(code, name))
            all_signals.extend(self.check_events(code, name))
            # 止损预警（持仓股或有成本价的关注股）
            if cost_price:
                all_signals.extend(self.check_stop_loss(code, name, cost_price))
            # 涨跌停预警
            all_signals.extend(self.check_price_limit(code, name))
            # 保存预警
            for sig in all_signals:
                self.save_alert(code, sig['type'], sig['level'], sig['msg'])
                # 同时输出到控制台
                print(f"[{sig['level'].upper()}] {sig['msg']}")

        # 市场情绪极端预警
        if HAS_MARKET_SENTIMENT:
            try:
                sentiment = MarketSentimentAnalyzer().get_latest_sentiment()
                if sentiment:
                    composite = float(sentiment.get('composite_index', 50))
                    if composite < 20 or composite > 80:
                        level_str = '极度恐慌' if composite < 20 else '极度乐观'
                        self.save_alert('MARKET', '市场情绪极端', 'medium',
                            f"综合情绪指数 {composite:.1f}，处于{level_str}区间，注意风险")
                        print(f"[MEDIUM] 市场情绪极端: 综合指数 {composite:.1f}（{level_str}），注意风险")
            except Exception as e:
                print(f"市场情绪检查失败: {e}")

        # 大盘破位预警
        if HAS_MARKET_TECHNICAL:
            try:
                mt = MarketTechnicalAnalyzer()
                sr = mt.support_resistance()
                if sr:
                    current = sr.get('current_price', 0)
                    strong_support = sr.get('strong_support', 0)
                    strong_resistance = sr.get('strong_resistance', 0)
                    if strong_support > 0 and current < strong_support:
                        self.save_alert('MARKET', '大盘破位', 'high',
                            f"上证指数当前{current:.1f}跌破长期支撑位{strong_support:.1f}，注意系统性风险")
                        print(f"[HIGH] 大盘跌破长期支撑位: 当前{current:.1f} < 支撑{strong_support:.1f}")
                    elif strong_resistance > 0 and current > strong_resistance:
                        self.save_alert('MARKET', '大盘突破', 'medium',
                            f"上证指数当前{current:.1f}突破长期阻力位{strong_resistance:.1f}，可能开启上涨趋势")
                        print(f"[MEDIUM] 大盘突破长期阻力位: 当前{current:.1f} > 阻力{strong_resistance:.1f}")
            except Exception as e:
                print(f"大盘技术监控失败: {e}")

        # 资金面极端预警
        if HAS_CAPITAL_FLOW_V2:
            try:
                cf = CapitalFlowV2Analyzer()
                score = cf.calculate_score()
                etf_5d = score.get('etf_flow_5d', 0) / 1e4  # 亿元
                corp_5d = score.get('corp_net_5d', 0) / 1e4  # 亿元
                if etf_5d > 800:
                    self.save_alert('CAPITAL', 'ETF资金大幅流入', 'medium',
                        f"ETF近5日净流入{etf_5d:.0f}亿元，市场情绪亢奋，注意短期过热风险")
                    print(f"[MEDIUM] ETF资金大幅流入: 近5日净流入{etf_5d:.0f}亿元")
                if corp_5d < -100:
                    self.save_alert('CAPITAL', '产业资本大幅减持', 'medium',
                        f"产业资本近5日净减持{abs(corp_5d):.0f}亿元，警惕股东套现")
                    print(f"[MEDIUM] 产业资本大幅减持: 近5日净减持{abs(corp_5d):.0f}亿元")
            except Exception as e:
                print(f"资金面监控失败: {e}")

        # 宏观环境预警
        try:
            from macro_analyzer import MacroAnalyzer
            _macro = MacroAnalyzer()
            _macro_result = _macro.get_latest_macro_score()
            _macro_score = _macro_result.get('total_score', 5.0)
            if _macro_score < 3.0:
                self.save_alert('MACRO', '宏观环境恶化', 'high',
                    f"宏观经济评分{_macro_score}/10，{_macro_result['comment']}")
                print(f"[HIGH] 宏观环境恶化: 评分{_macro_score}/10，{_macro_result['comment']}")
            elif _macro_score > 8.0:
                self.save_alert('MACRO', '宏观环境偏暖', 'medium',
                    f"宏观经济评分{_macro_score}/10，市场风险偏好可能提升")
                print(f"[MEDIUM] 宏观环境偏暖: 评分{_macro_score}/10")
        except Exception as e:
            print(f"宏观监控失败: {e}")

        print("监控完成")

if __name__ == "__main__":
    from agent_army.data_fetcher_duckdb import get_data_fetcher as _gdf
    from datetime import datetime as _dt
    _today = _dt.now().strftime('%Y-%m-%d')
    if not _gdf().is_trading_day(_today):
        print(f"今日 {_today} 非交易日，监控脚本退出")
        sys.exit(0)
    monitor = Monitor()
    monitor.run_once()
