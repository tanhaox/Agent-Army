#!/usr/bin/env python3
"""
unified_analyzer.py - 统一分析器（v1.0）

解决问题：
- analyze_stock.py（用户分析）与 silicon_evolution_cycle.py（自主训练）使用不同调用路径
- 无统一入口导致分析结果不可比、进化闭环断裂

设计原则：
- 包装现有 analyze_stock.py 的分析管线，而非重写
- 所有分析场景（用户查询、自主训练、批量回测）走同一入口
- 统一输出格式，供 UnifiedRouter 和训练脚本共用
- 支持上下文参数区分调用场景

调用链路：
  UnifiedAnalyzer.analyze(code, context)
      ↓
  get_stock_data() → 6维度Agent分析 → CoordinatorAgent综合 → 结果
      ↓
  统一 JSON 输出

作者：AI Agent
日期：2026-04-16
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any

sys.path.insert(0, '/root/.openclaw/workspace')

logger = logging.getLogger('UnifiedAnalyzer')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(handler)

WORKSPACE = '/root/.openclaw/workspace'
SCRIPTS_DIR = os.path.join(WORKSPACE, 'scripts')


class UnifiedAnalyzer:
    """统一分析器 - 所有分析场景的单一入口

    包装 analyze_stock.py 的分析管线，提供：
    - 统一入口 analyze(code, context)
    - 上下文感知（user/auto_train/backtest）
    - 可选预测记录
    - 标准化输出格式
    """

    def __init__(self, mode: str = 'standard'):
        """
        Args:
            mode: 分析模式
                - 'standard': 标准模式（用户分析）
                - 'auto_train': 自主训练模式
                - 'backtest': 回测模式（不写DB）
        """
        self.mode = mode
        self._weights = None

    def analyze(self, code: str, context: dict = None) -> dict:
        """统一分析入口

        Args:
            code: 股票代码（如 '600887.SH'）
            context: 上下文参数
                - source: 'user' | 'auto_train' | 'backtest'
                - record_prediction: bool (是否记录预测到DB)
                - date: str (分析日期，用于回测)
                - force: bool (跳过清仓检查)

        Returns:
            统一格式分析结果字典
        """
        context = context or {}
        source = context.get('source', 'user')
        analysis_date = context.get('date')
        record = context.get('record_prediction', False)
        force = context.get('force', True)  # 统一入口默认跳过清仓交互

        logger.info(f"分析 [{source}]: {code}" +
                    (f" date={analysis_date}" if analysis_date else ""))

        # 1. 转换代码格式（.SH → .SS 用于 yfinance/data_fetcher）
        yf_code = self._convert_code(code)

        # 2. 获取K线数据
        stock_df = self._get_stock_data(yf_code, end_date=analysis_date)
        if stock_df is None or stock_df.empty:
            return self._error_result(code, '无法获取K线数据')

        # 3. 获取市场环境和动态权重
        market_state = self._get_market_state()
        weights = market_state.get('weights', self._default_weights())

        # 4. 执行各维度分析（每个都有超时降级）
        try:
            tech_result = self._analyze_technical(stock_df)
        except Exception as e:
            logger.warning(f"技术分析失败: {e}")
            tech_result = {'total_score': 5.0, 'recommendation': 'neutral'}

        # 基本面和资金面容易阻塞，使用线程超时
        fund_result = self._run_with_timeout(
            lambda: self._analyze_fundamental(yf_code),
            timeout=20, fallback={'total_score': 5.0, 'recommendation': 'neutral'},
            name='基本面'
        )

        cap_result = self._run_with_timeout(
            lambda: self._analyze_capital(yf_code),
            timeout=10, fallback={'total_score': 5.0, 'recommendation': 'neutral'},
            name='资金面'
        )

        try:
            news_result = self._analyze_news(yf_code)
        except Exception as e:
            logger.warning(f"新闻面分析失败: {e}")
            news_result = {'total_score': 5.0, 'recommendation': 'neutral'}

        try:
            kline_result = self._analyze_kline_game(stock_df)
        except Exception as e:
            logger.warning(f"K线博弈分析失败: {e}")
            kline_result = {'total_score': 5.0}

        # 可选维度
        rs_result = None
        try:
            rs_result = self._analyze_rs(yf_code, stock_df)
        except Exception:
            pass

        ml_result = None
        try:
            ml_result = self._analyze_ml(yf_code)
        except Exception:
            pass

        # 5. 多周期分析（可选）
        multi_period = None
        try:
            multi_period = self._analyze_multi_period(yf_code, stock_df)
        except Exception:
            pass

        # 宏观分析（可选）
        macro_result = None
        try:
            macro_result = self._analyze_macro()
        except Exception:
            pass

        # 6. 调用 CoordinatorAgent 综合评分
        try:
            from agent_army.coordinator_agent import CoordinatorAgent
            coordinator = CoordinatorAgent(weights=weights)
            final = coordinator.coordinate(
                technical_result=tech_result,
                fundamental_result=fund_result,
                capital_result=cap_result,
                news_result=news_result,
                kline_result=kline_result,
                rs_result=rs_result,
                ml_result=ml_result,
                macro_result=macro_result,
                multi_period=multi_period,
            )
        except Exception as e:
            logger.warning(f"协调器失败，使用简单加权: {e}")
            final = self._simple_weighted_score(
                tech_result, fund_result, cap_result, news_result,
                kline_result, rs_result, ml_result, weights
            )

        # 6.5 持仓纪律因子分析（需要持仓上下文）
        discipline = None
        cost_price = context.get('cost_price')
        buy_date = context.get('buy_date')
        if cost_price and buy_date:
            try:
                current_price = None
                if stock_df is not None and not stock_df.empty:
                    # 取最后一个非NaN的close
                    valid_close = stock_df['close'].dropna()
                    if not valid_close.empty:
                        current_price = float(valid_close.iloc[-1])
                if current_price:
                    from agent_army.discipline_analyzer import DisciplineAnalyzer
                    da = DisciplineAnalyzer()
                    discipline = da.analyze_health(
                        stock_code=code,
                        current_price=current_price,
                        cost_price=float(cost_price),
                        buy_date=buy_date,
                    )
                    logger.info(f"纪律因子: {code} 健康度={discipline['score']} 建议={discipline['suggestion']}")
            except Exception as e:
                logger.warning(f"纪律因子分析失败: {e}")

        # 7. 构建统一输出
        result = {
            'code': code,
            'yf_code': yf_code,
            'source': source,
            'total_score': final.get('total_score', 5.0),
            'recommendation': final.get('recommendation', '中性'),
            'position_advice': final.get('position_advice', ''),
            'reasoning': final.get('reasoning', ''),
            'details': {
                'scores': {
                    'technical': tech_result.get('total_score', 5.0),
                    'fundamental': fund_result.get('total_score', 5.0),
                    'capital': cap_result.get('total_score', 5.0),
                    'news': news_result.get('total_score', 5.0),
                    'kline_game': kline_result.get('total_score', 5.0),
                    'rs': rs_result.get('total_score', 5.0) if rs_result else None,
                    'ml': ml_result,
                },
                'weights': weights,
                'market_state': market_state.get('current_state', 'unknown'),
            },
            'technical_analysis': tech_result,
            'fundamental_analysis': fund_result,
            'capital_analysis': cap_result,
            'news_analysis': news_result,
            'kline_game': kline_result,
            'rs_analysis': rs_result,
            'ml_prediction': ml_result,
            'multi_period': multi_period,
            'macro_analysis': macro_result,
            'discipline': discipline,
            'analysis_date': analysis_date or datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat(),
        }

        # 7.5 纪律因子覆盖建议
        if discipline:
            result = self._apply_discipline_override(result, discipline)
            # 提取周线分位到顶层
            tech_detail = discipline.get('factors', {}).get('technical_position', {}).get('detail', {})
            if tech_detail.get('source') == 'weekly_kline':
                result['weekly_percentile'] = {
                    'position_pct': tech_detail.get('position_pct'),
                    'range_low': tech_detail.get('range_120w_low'),
                    'range_high': tech_detail.get('range_120w_high'),
                    'weekly_bars': tech_detail.get('weekly_bars'),
                }

        # 8. 记录预测（可选）
        if record and source != 'backtest':
            try:
                self._save_prediction(result, context)
            except Exception as e:
                logger.warning(f"保存预测失败: {e}")

        # 9. 记录操作日志
        if source == 'auto_train':
            logger.info(f"自主训练分析完成: {code} score={result['total_score']}")

        return result

    # ==================== 超时控制 ====================

    def _run_with_timeout(self, func, timeout: int = 15, fallback: dict = None, name: str = '') -> dict:
        """带超时的函数执行"""
        import threading
        fallback = fallback or {'total_score': 5.0, 'recommendation': 'neutral'}
        result = [fallback]
        exception = [None]

        def target():
            try:
                result[0] = func()
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            logger.warning(f"{name}分析超时 ({timeout}s)，使用默认值")
            return fallback

        if exception[0]:
            logger.warning(f"{name}分析失败: {exception[0]}")
            return fallback

        return result[0]

    # ==================== 数据获取 ====================

    def _convert_code(self, code: str) -> str:
        """转换代码格式：.SH → .SS（yfinance格式）"""
        if '.' in code:
            return code.replace('.SH', '.SS').replace('.BJ', '.BJ')
        # 纯数字，补后缀
        if code.startswith('6') or code.startswith('5'):
            return code + '.SS'
        elif code.startswith('0') or code.startswith('2') or code.startswith('3'):
            return code + '.SZ'
        return code + '.SS'

    def _get_stock_data(self, stock_code: str, end_date: str = None):
        """获取K线数据（复用 data_fetcher_duckdb）"""
        try:
            from agent_army.data_fetcher_duckdb import get_data_fetcher
            fetcher = get_data_fetcher()
            # 默认获取最近180天数据
            from datetime import timedelta
            start = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
            end = end_date or datetime.now().strftime('%Y-%m-%d')
            df = fetcher.get_daily_kline(
                stock_code=stock_code,
                start_date=start,
                end_date=end,
                adj=True
            )
            return df
        except Exception as e:
            logger.warning(f"获取K线失败 [{stock_code}]: {e}")
            return None

    # ==================== 各维度分析 ====================

    def _get_market_state(self) -> dict:
        """获取市场状态和动态权重"""
        try:
            # 导入 analyze_stock.py 的函数
            sys.path.insert(0, SCRIPTS_DIR)
            import importlib
            import analyze_stock
            importlib.reload(analyze_stock)
            return analyze_stock.get_market_state()
        except Exception:
            return {'current_state': 'normal', 'state_name': '正常', 'weights': self._default_weights()}

    def _analyze_technical(self, stock_df) -> dict:
        """技术分析"""
        from agent_army.technical_analysis_agent import TechnicalAnalysisAgent
        agent = TechnicalAnalysisAgent()
        return agent.analyze({'df': stock_df})

    def _analyze_fundamental(self, stock_code: str) -> dict:
        """基本面分析"""
        from agent_army.fundamental_analysis_agent import FundamentalAnalysisAgent
        agent = FundamentalAnalysisAgent(stock_code=stock_code)
        return agent.analyze()

    def _analyze_capital(self, stock_code: str) -> dict:
        """资金面分析"""
        try:
            from capital_flow_analyzer import CapitalFlowAnalyzer
            analyzer = CapitalFlowAnalyzer()
            return analyzer.analyze(stock_code, timeout=3)
        except Exception as e:
            logger.debug(f"资金面分析异常: {e}")
            return {'total_score': 5.0, 'recommendation': 'neutral'}

    def _analyze_news(self, stock_code: str) -> dict:
        """新闻面分析（从DuckDB读取预计算结果）"""
        try:
            import duckdb
            db_path = os.path.join(WORKSPACE, 'data/predictions.db')
            conn = duckdb.connect(db_path, read_only=True)
            short_code = stock_code.split('.')[0]

            # 查询最近的新闻情绪
            row = conn.execute("""
                SELECT AVG(sentiment_score) as avg_score
                FROM news_sentiment
                WHERE stock_code LIKE ? AND date >= CURRENT_DATE - INTERVAL '7 days'
            """, [f'%{short_code}%']).fetchone()
            conn.close()

            if row and row[0] is not None:
                score = max(1, min(10, row[0] * 10))
                return {'total_score': round(score, 1), 'recommendation': 'neutral'}
        except Exception:
            pass
        return {'total_score': 5.0, 'recommendation': 'neutral'}

    def _analyze_kline_game(self, stock_df) -> dict:
        """K线博弈分析"""
        try:
            from kline_game_analyzer import KlineGameAnalyzer
            analyzer = KlineGameAnalyzer(stock_df)
            return analyzer.game_conclusion()
        except Exception:
            return {'total_score': 5.0}

    def _analyze_rs(self, stock_code: str, stock_df) -> dict:
        """相对强度分析"""
        try:
            from relative_strength_agent import RelativeStrengthAgent
            agent = RelativeStrengthAgent(stock_code=stock_code, stock_df=stock_df)
            return agent.analyze()
        except Exception:
            return None

    def _analyze_ml(self, stock_code: str) -> dict:
        """ML预测"""
        try:
            from agent_army.ml_predictor import MLPredictor
            predictor = MLPredictor()
            short_code = stock_code.split('.')[0]
            # 转换为灵启格式
            if short_code.startswith('6'):
                lq_code = short_code + '.SH'
            else:
                lq_code = short_code + '.SZ'
            return predictor.predict({'stock_code': lq_code})
        except Exception:
            return None

    def _analyze_multi_period(self, stock_code: str, stock_df) -> dict:
        """多周期分析"""
        try:
            from multi_period_analyzer import MultiPeriodAnalyzer
            analyzer = MultiPeriodAnalyzer(stock_code=stock_code, stock_df=stock_df)
            return analyzer.analyze()
        except Exception:
            return None

    def _analyze_macro(self) -> dict:
        """宏观分析"""
        try:
            from macro_analyzer import MacroAnalyzer
            analyzer = MacroAnalyzer()
            return analyzer.get_latest_macro_score()
        except Exception:
            return None

    # ==================== 权重和评分 ====================

    def _default_weights(self) -> dict:
        """默认权重"""
        # 从配置文件加载
        config_path = os.path.join(WORKSPACE, 'config/weights.json')
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {
                "technical": 0.30, "fundamental": 0.22, "capital": 0.16,
                "news": 0.05, "game": 0.05, "rs": 0.04, "ml": 0.03,
                "macro": 0.05, "weekly": 0.10
            }

    def _simple_weighted_score(self, tech, fund, cap, news,
                                kline, rs, ml, weights) -> dict:
        """简单加权评分（CoordinatorAgent 不可用时的降级方案）"""
        scores = {
            'technical': tech.get('total_score', 5.0),
            'fundamental': fund.get('total_score', 5.0),
            'capital': cap.get('total_score', 5.0),
            'news': news.get('total_score', 5.0),
        }

        # 可选维度
        if kline and kline.get('total_score'):
            scores['kline_game'] = kline['total_score']
        if rs and rs.get('total_score'):
            scores['rs'] = rs['total_score']
        if ml and ml.get('confidence'):
            # ML 转换为 0-10 分
            ml_score = 7.0 if ml.get('direction') == 'up' else 3.0
            scores['ml'] = ml_score

        total = 0.0
        weight_sum = 0.0
        weight_map = {
            'technical': 'technical', 'fundamental': 'fundamental',
            'capital': 'capital', 'news': 'news',
            'kline_game': 'game', 'rs': 'rs', 'ml': 'ml',
        }
        for key, score in scores.items():
            w_key = weight_map.get(key, key)
            w = weights.get(w_key, 0)
            total += score * w
            weight_sum += w

        total_score = round(total / weight_sum, 1) if weight_sum > 0 else 5.0
        return {
            'total_score': total_score,
            'recommendation': '买入' if total_score >= 7 else '持有' if total_score >= 5 else '卖出',
            'reasoning': f'简单加权: {scores}',
        }

    # ==================== 预测记录 ====================

    def _save_prediction(self, result: dict, context: dict):
        """保存预测到 predictions 表"""
        try:
            import duckdb
            from datetime import date

            db_path = os.path.join(WORKSPACE, 'data/predictions.db')
            conn = duckdb.connect(db_path)

            code = result['code']
            source = context.get('source', 'user')
            pred_id = f"{source}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{code}"

            # 检查是否已存在（同一天同一股票不重复记录）
            existing = conn.execute(
                "SELECT prediction_id FROM predictions WHERE stock_code = ? AND analysis_date = CURRENT_DATE AND source = ?",
                [code, source]
            ).fetchall()
            if existing:
                conn.close()
                return

            conn.execute("""
                INSERT INTO predictions (
                    prediction_id, stock_code, analysis_date, total_score,
                    recommendation, position_advice, confidence_level,
                    reasoning, source, is_strong_signal, is_backtest,
                    verified, created_at
                ) VALUES (?, ?, CURRENT_DATE, ?, ?, ?, ?, ?, ?, ?, ?, false, now())
            """, [
                pred_id,
                code,
                round(result['total_score'], 2),
                result['recommendation'],
                result.get('position_advice', ''),
                'medium',
                result.get('reasoning', '')[:500],
                source,
                result['total_score'] >= 7.5,
                source == 'backtest',
            ])
            conn.close()
            logger.debug(f"预测已保存: {pred_id}")
        except Exception as e:
            logger.warning(f"保存预测失败: {e}")

    # ==================== 辅助方法 ====================

    def _error_result(self, code: str, msg: str) -> dict:
        """错误结果"""
        return {
            'code': code,
            'total_score': 0,
            'recommendation': '数据不足',
            'reasoning': msg,
            'details': {'scores': {}, 'weights': {}},
            'error': msg,
            'timestamp': datetime.now().isoformat(),
        }

    def _apply_discipline_override(self, result: dict, discipline: dict) -> dict:
        """根据纪律因子健康度覆盖建议

        规则：
        - 健康度 < 40：强制"减仓"或"止损"
        - 40-70：根据原有综合评分
        - > 70：可输出"持有"或"加仓"
        - 止损触发时：强制"止损"
        """
        health_score = discipline.get('score', 50)
        suggestion = discipline.get('suggestion', '持有')
        stop_triggered = discipline.get('stop_loss_triggered', False)
        original_rec = result.get('recommendation', '中性')

        if stop_triggered:
            result['recommendation'] = '止损'
            result['position_advice'] = '0%'
            result['reasoning'] = (
                f"[纪律因子-止损触发] 当前价 ≤ 动态止损价({discipline.get('stop_loss_price', 'N/A')})\n"
                f"健康度: {health_score}/100 | 原始建议: {original_rec}\n"
                + result.get('reasoning', '')
            )
        elif health_score < 40:
            # 强制减仓或止损
            if health_score < 30:
                result['recommendation'] = '止损'
                result['position_advice'] = '0%-10%'
            else:
                result['recommendation'] = '减仓'
                result['position_advice'] = '10%-30%'
            result['reasoning'] = (
                f"[纪律因子-低健康度] 评分{health_score}/100\n"
                f"建议: {suggestion} | 原始建议: {original_rec}\n"
                + result.get('reasoning', '')
            )
        elif health_score >= 70:
            # 健康度高，维持或加仓
            if original_rec in ('买入', '增持', '加仓'):
                result['recommendation'] = '加仓'
            elif health_score >= 80:
                result['recommendation'] = '持有'
            # 否则保持原始建议
        # 40-70 之间保持原始建议

        # 记录覆盖信息
        result['discipline_override'] = {
            'health_score': health_score,
            'discipline_suggestion': suggestion,
            'original_recommendation': original_rec,
            'final_recommendation': result['recommendation'],
            'overridden': (original_rec != result['recommendation']),
        }

        return result


# ==================== 单例 ====================

_analyzer = None


def get_unified_analyzer(mode: str = 'standard') -> UnifiedAnalyzer:
    """获取统一分析器单例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = UnifiedAnalyzer(mode=mode)
    return _analyzer


# ==================== CLI 入口 ====================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='统一分析器')
    parser.add_argument('code', help='股票代码')
    parser.add_argument('--date', help='分析日期', default=None)
    parser.add_argument('--source', default='user', choices=['user', 'auto_train', 'backtest'])
    parser.add_argument('--record', action='store_true', help='记录预测到DB')
    parser.add_argument('--json', action='store_true', help='JSON输出')

    args = parser.parse_args()

    analyzer = UnifiedAnalyzer()
    result = analyzer.analyze(args.code, {
        'source': args.source,
        'date': args.date,
        'record_prediction': args.record,
    })

    if args.json:
        # 清理 NaN/None 以便 JSON 序列化
        def clean(obj):
            if isinstance(obj, dict):
                return {k: clean(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean(i) for i in obj]
            elif isinstance(obj, float) and (obj != obj):  # NaN
                return None
            return obj

        print(json.dumps(clean(result), ensure_ascii=False, indent=2, default=str))
    else:
        print(f"代码: {result['code']}")
        print(f"评分: {result['total_score']}/10")
        print(f"建议: {result['recommendation']}")
        print(f"理由: {result.get('reasoning', '')[:200]}")
        scores = result.get('details', {}).get('scores', {})
        if scores:
            print(f"\n各维度评分:")
            for k, v in scores.items():
                if v is not None:
                    print(f"  {k}: {v}")
