#!/usr/bin/env python3
"""
unified_router.py - 统一流程路由器（v1.0）

解决问题：
- 用户自然语言问法无统一路由
- 操作分散在不同脚本，没有标准化API
- OpenClaw 工具调用直接执行散落脚本

设计原则：
- 规则关键词匹配的意图识别（暂不引入NLP库）
- 统一 JSON 响应格式
- 所有操作通过 route() 单入口
- 向后兼容：保留原有脚本，路由器调用它们

意图映射：
  analyze      - 分析个股（调用 analyze_stock.py --json）
  holdings     - 查询持仓（调用 UnifiedDataManager）
  assets       - 总资产概览（调用 UnifiedDataManager）
  opportunities- 机会扫描（调用 scanner.py，从DB读结果）
  clear        - 清仓操作（调用 UnifiedDataManager + record_clear.py）
  watchlist    - 关注池管理（调用 UnifiedDataManager）
  history      - 历史持仓/操作记录
  predict      - 预测查询
  help         - 帮助信息

作者：AI Agent
日期：2026-04-16
"""

import sys
import os
import re
import json
import logging
import subprocess
from datetime import datetime
from typing import Dict, Optional, Tuple, Any

sys.path.insert(0, '/root/.openclaw/workspace')

logger = logging.getLogger('UnifiedRouter')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(handler)

SCRIPTS_DIR = '/root/.openclaw/workspace/scripts'


class UnifiedRouter:
    """统一流程路由器 - 所有用户操作的单一入口"""

    def __init__(self):
        from agent_army.unified_data_manager import get_unified_data_manager
        self.data_manager = get_unified_data_manager()
        self._scanner_cache = None
        self._scanner_cache_time = None

    # ==================== 主入口 ====================

    def route(self, user_input: str) -> dict:
        """主入口：接收用户自然语言，返回统一响应

        Args:
            user_input: 用户输入的自然语言文本

        Returns:
            统一格式响应:
            {
                "status": "ok" | "error",
                "intent": "analyze" | "holdings" | ...,
                "data": { ... },
                "message": "人类可读的摘要",
                "suggestions": ["建议1", "建议2"],
                "timestamp": "2026-04-16T12:00:00"
            }
        """
        if not user_input or not user_input.strip():
            return self._help_response()

        intent, params = self._parse_intent(user_input)
        logger.info(f"意图识别: '{user_input[:50]}' -> {intent} {params}")

        handler = getattr(self, f'_handle_{intent}', None)
        if not handler:
            return self._error_response(
                f"无法识别意图: {user_input[:30]}",
                intent='unknown',
                suggestions=['输入"帮助"查看可用命令']
            )

        try:
            result = handler(params)
            return self._format_response(intent, result)
        except Exception as e:
            logger.error(f"处理 [{intent}] 失败: {e}")
            return self._error_response(str(e), intent=intent)

    # ==================== 意图识别 ====================

    def _parse_intent(self, text: str) -> Tuple[str, dict]:
        """规则 + 关键词匹配的意图识别

        优先级：分析 > 清仓 > 关注 > 持仓 > 机会 > 预测 > 历史 > 帮助

        Returns:
            (intent, params) 元组
        """
        text_lower = text.lower().strip()
        params = {}

        # --- 分析个股（优先级最高，避免被"持仓"等关键词截断） ---
        analyze_kw = ['分析', '怎么样', '如何', '走势', '诊断', '看看', '评估']
        if any(kw in text_lower for kw in analyze_kw):
            code = self._extract_code(text)
            if code:
                return ('analyze', {'code': code})
            # 有关键词但没提取到代码，尝试提取股票名
            name = self._extract_stock_name(text)
            if name:
                code = self._resolve_name_to_code(name)
                if code:
                    return ('analyze', {'code': code})

        # --- 清仓/卖出 ---
        clear_kw = ['清仓', '卖出全部', '全部卖出', '止损清仓']
        if any(kw in text_lower for kw in clear_kw):
            code = self._extract_code(text)
            if not code:
                name = self._extract_stock_name(text)
                if name:
                    code = self._resolve_name_to_code(name)
            reason = 'stop_loss' if '止损' in text_lower else 'manual'
            return ('clear', {'code': code, 'reason': reason, 'text': text})

        # --- 减仓/部分卖出 ---
        reduce_kw = ['减仓', '卖出一部分', '部分卖出']
        if any(kw in text_lower for kw in reduce_kw):
            code = self._extract_code(text)
            if not code:
                name = self._extract_stock_name(text)
                if name:
                    code = self._resolve_name_to_code(name)
            return ('reduce', {'code': code, 'text': text})

        # --- 关注池查看（必须在"关注"添加/移除之前检查） ---
        watch_view_kw = ['关注池', '关注列表', '我的关注', '关注股']
        if any(kw in text_lower for kw in watch_view_kw):
            return ('watchlist', {})

        # --- 关注池管理 ---
        watch_add_kw = ['加入关注', '添加关注', '加关注', '关注']
        watch_rm_kw = ['移除关注', '取消关注', '删除关注', '移出关注']
        if any(kw in text_lower for kw in watch_rm_kw):
            code = self._extract_code(text)
            return ('remove_watch', {'code': code})
        if any(kw in text_lower for kw in watch_add_kw):
            code = self._extract_code(text)
            if not code:
                name = self._extract_stock_name(text)
                if name:
                    code = self._resolve_name_to_code(name)
            return ('add_watch', {'code': code, 'text': text})

        # --- 总资产 ---
        asset_kw = ['总资产', '资金', '账户', '账户概览', '盈亏总览']
        if any(kw in text_lower for kw in asset_kw):
            return ('assets', {})

        # --- 持仓查询 ---
        holdings_kw = ['我的持仓', '持仓情况', '持有股票', '当前持仓', '持仓', '持仓明细']
        if any(kw in text_lower for kw in holdings_kw):
            return ('holdings', {})

        # --- 机会扫描 ---
        opp_kw = ['机会', '推荐', '扫描', '选股', '今日机会', '好股', '潜力股']
        if any(kw in text_lower for kw in opp_kw):
            top = 10
            m = re.search(r'top\s*(\d+)', text_lower)
            if m:
                top = int(m.group(1))
            return ('opportunities', {'top': top})

        # --- 预测查询 ---
        predict_kw = ['预测', '准确率', '预测结果']
        if any(kw in text_lower for kw in predict_kw):
            code = self._extract_code(text)
            return ('predict', {'code': code})

        # --- 历史记录 ---
        history_kw = ['历史', '操作记录', '交易记录', '清仓记录']
        if any(kw in text_lower for kw in history_kw):
            return ('history', {'days': 30})

        # --- 更新持仓 ---
        update_kw = ['更新持仓', '同步持仓', '提交持仓']
        if any(kw in text_lower for kw in update_kw):
            return ('update_holdings', {'text': text})

        # --- 帮助 ---
        help_kw = ['帮助', 'help', '命令', '功能', '能做什么', '怎么用']
        if any(kw in text_lower for kw in help_kw):
            return ('help', {})

        # --- 兜底：有股票代码默认分析 ---
        code = self._extract_code(text)
        if code:
            return ('analyze', {'code': code})

        return ('unknown', {'text': text})

    # ==================== 辅助方法 ====================

    def _extract_code(self, text: str) -> Optional[str]:
        """从文本中提取6位数字股票代码并补全后缀"""
        # 不用 \b，直接匹配连续6位数字
        match = re.search(r'(\d{6})', text)
        if match:
            code_num = match.group(1)
            if code_num.startswith('6') or code_num.startswith('5'):
                return f"{code_num}.SH"
            elif code_num.startswith('0') or code_num.startswith('2') or code_num.startswith('3'):
                return f"{code_num}.SZ"
            elif code_num.startswith('8') or code_num.startswith('4'):
                return f"{code_num}.BJ"
            return code_num
        return None

    def _extract_stock_name(self, text: str) -> Optional[str]:
        """从文本中提取股票名称（常见的几个）"""
        # 优先从已知持仓/关注池中匹配
        known = {
            '伊利': '600887.SH', '伊利股份': '600887.SH',
            '格力': '000651.SZ', '格力电器': '000651.SZ',
            '正泰': '601877.SH', '正泰电器': '601877.SH',
            '佳都': '600728.SH', '佳都科技': '600728.SH',
            '京东方': '000725.SZ', '京东方A': '000725.SZ',
            '美的': '000333.SZ', '美的集团': '000333.SZ',
            '平安': '601318.SH', '中国平安': '601318.SH',
            '中国电建': '601669.SH', '电建': '601669.SH',
        }
        for name, code in known.items():
            if name in text:
                return name
        return None

    def _resolve_name_to_code(self, name: str) -> Optional[str]:
        """将股票名转换为代码"""
        known = {
            '伊利': '600887.SH', '伊利股份': '600887.SH',
            '格力': '000651.SZ', '格力电器': '000651.SZ',
            '正泰': '601877.SH', '正泰电器': '601877.SH',
            '佳都': '600728.SH', '佳都科技': '600728.SH',
            '京东方': '000725.SZ', '京东方A': '000725.SZ',
            '美的': '000333.SZ', '美的集团': '000333.SZ',
            '平安': '601318.SH', '中国平安': '601318.SH',
            '中国电建': '601669.SH', '电建': '601669.SH',
        }
        return known.get(name)

    def _run_script(self, script_name: str, args: list, timeout: int = 60) -> Tuple[int, str, str]:
        """运行脚本并捕获输出

        Returns:
            (return_code, stdout, stderr)
        """
        script_path = os.path.join(SCRIPTS_DIR, script_name)
        if not os.path.exists(script_path):
            return (-1, '', f'脚本不存在: {script_path}')

        cmd = ['python3', script_path] + args
        logger.debug(f"执行: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                cwd='/root/.openclaw/workspace'
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return (-1, '', f'脚本超时 ({timeout}s)')
        except Exception as e:
            return (-1, '', str(e))

    # ==================== 意图处理器 ====================

    def _handle_analyze(self, params: dict) -> dict:
        """分析个股（通过 UnifiedAnalyzer 直接调用，不再用 subprocess）"""
        code = params.get('code')
        if not code:
            return {'error': '请提供股票代码，如"分析 600887"'}

        try:
            from agent_army.unified_analyzer import get_unified_analyzer
            analyzer = get_unified_analyzer()
            result = analyzer.analyze(code, {
                'source': 'user',
                'record_prediction': True,
            })

            # 生成人类可读摘要
            score = result.get('total_score', 0)
            rec = result.get('recommendation', '未知')
            result['_message'] = f"{code} 分析完成：评分 {score}/10，建议 {rec}"
            result['_code'] = code
            return result
        except Exception as e:
            logger.error(f"分析失败 [{code}]: {e}")
            # 降级到 subprocess 方式
            return self._handle_analyze_fallback(code)

    def _handle_analyze_fallback(self, code: str) -> dict:
        """分析降级方案：subprocess 调用 analyze_stock.py"""
        yf_code = code.replace('.SH', '.SS').replace('.BJ', '.BJ')
        rc, stdout, stderr = self._run_script(
            'analyze_stock.py', [yf_code, '--json'], timeout=30
        )
        if rc != 0:
            return {'error': f'分析失败: {stderr[:200]}'}
        try:
            json_str = stdout
            start = json_str.find('{\n  "total_score"')
            if start < 0:
                start = json_str.find('{\n  "stock_code"')
            if start < 0:
                start = json_str.find('{')
            end = json_str.rfind('}') + 1
            if start >= 0 and end > start:
                data = json.loads(json_str[start:end])
                data['_message'] = f"{code} 分析完成（fallback模式）"
                data['_code'] = code
                return data
        except Exception:
            pass
        return {'raw_output': stdout[:2000], '_message': '分析完成（文本格式）'}

    def _handle_holdings(self, params: dict) -> dict:
        """查询持仓（含纪律因子健康度评分）"""
        data = self.data_manager.get_holdings(as_of='latest')
        holdings = data.get('holdings', {})
        assets = data.get('assets', {})

        # 逐股运行纪律因子分析
        discipline_results = {}
        try:
            from agent_army.discipline_analyzer import DisciplineAnalyzer
            da = DisciplineAnalyzer()
            for code, info in holdings.items():
                cost_price = info.get('cost_price')
                current_price = info.get('current_price')
                holding_days = info.get('holding_days', 0)

                if cost_price and current_price and holding_days > 0:
                    try:
                        # 从 holding_days 反推买入日期
                        buy_dt = datetime.now() - __import__('datetime').timedelta(days=holding_days)
                        buy_date = buy_dt.strftime('%Y-%m-%d')

                        disc = da.analyze_health(
                            stock_code=code,
                            current_price=float(current_price),
                            cost_price=float(cost_price),
                            buy_date=buy_date,
                        )
                        discipline_results[code] = {
                            'score': disc['score'],
                            'suggestion': disc['suggestion'],
                            'stop_loss_price': disc.get('stop_loss_price'),
                            'stop_triggered': disc.get('stop_loss_triggered', False),
                            'factors': {k: v['score'] for k, v in disc.get('factors', {}).items()},
                        }
                    except Exception as e:
                        logger.debug(f"纪律因子分析失败 [{code}]: {e}")
            da._close_conn()
        except ImportError:
            logger.debug("DisciplineAnalyzer 不可用，跳过健康度分析")

        # 生成摘要
        lines = []
        for code, info in holdings.items():
            pl = info.get('profit_loss', 0)
            pl_str = f"+{pl:.0f}" if pl >= 0 else f"{pl:.0f}"
            line = f"{info.get('name', code)}({code}): {info['shares']}股, 盈亏{pl_str}"
            # 追加健康度评分
            disc = discipline_results.get(code)
            if disc:
                line += f" | 健康度:{disc['score']} 建议:{disc['suggestion']}"
            lines.append(line)

        message = f"当前持有 {len(holdings)} 只股票"
        if assets:
            message += f"，总资产 {assets.get('total_assets', 0):,.0f}元"

        # 检查是否有需要预警的持仓
        alerts = []
        for code, disc in discipline_results.items():
            name = holdings.get(code, {}).get('name', code)
            if disc['suggestion'] in ('止损', '减仓'):
                alerts.append(f"⚠ {name}({code}): {disc['suggestion']} (健康度{disc['score']})")

        return {
            'holdings': holdings,
            'assets': assets,
            'discipline': discipline_results,
            '_message': message,
            '_detail': '\n'.join(lines),
            'alerts': alerts,
        }

    def _handle_assets(self, params: dict) -> dict:
        """总资产概览"""
        assets = self.data_manager.get_total_assets()

        message = (
            f"总资产: {assets.get('total_assets', 0):,.2f}元 "
            f"(盈亏 {assets.get('total_pnl', 0):+,.2f}元, "
            f"{assets.get('total_pnl_pct', 0):+.2f}%)"
        )

        return {
            'assets': assets,
            '_message': message
        }

    def _handle_opportunities(self, params: dict) -> dict:
        """机会扫描

        策略：
        1. 如果有最近的 scanner 结果（30分钟内），直接从DB读取
        2. 否则运行 scanner.py（不传 --json，从DB读结果）
        """
        top = params.get('top', 10)

        # 尝试从DB读取最近的扫描结果
        try:
            import duckdb
            db_path = '/root/.openclaw/workspace/data/predictions.db'
            conn = duckdb.connect(db_path, read_only=True)

            rows = conn.execute("""
                SELECT stock_code, stock_name, total_score, close_price,
                       sector, triggers, scan_date
                FROM opportunities
                ORDER BY scan_date DESC, total_score DESC
                LIMIT ?
            """, [top]).fetchall()

            conn.close()

            if rows:
                results = []
                for r in rows:
                    results.append({
                        'code': r[0], 'name': r[1], 'score': float(r[2]) if r[2] else 0,
                        'price': float(r[3]) if r[3] else 0, 'sector': r[4],
                        'triggers': r[5], 'date': str(r[6])
                    })

                # 生成摘要
                top3 = results[:3]
                names = ', '.join(f"{r['name']}({r['score']}分)" for r in top3)
                message = f"Top {len(results)} 机会: {names}"

                return {
                    'opportunities': results,
                    'count': len(results),
                    '_message': message
                }
        except Exception as e:
            logger.debug(f"从DB读取扫描结果失败: {e}")

        # DB没有结果，运行 scanner
        rc, stdout, stderr = self._run_script(
            'scanner.py', ['--top', str(top)], timeout=120
        )

        if rc != 0:
            return {'error': f'扫描失败: {stderr[:200]}'}

        return {
            'raw_output': stdout[:3000],
            '_message': f'扫描完成（Top {top}），详见原始输出'
        }

    def _handle_clear(self, params: dict) -> dict:
        """清仓操作"""
        code = params.get('code')
        reason = params.get('reason', 'manual')

        if not code:
            return {'error': '请提供股票代码，如"清仓 600887"'}

        # 1. 先通过 UnifiedDataManager 清仓
        result = self.data_manager.update_holdings('manual', {
            'action': 'clear', 'code': code
        })

        # 2. 同时记录清仓到 record_clear.py（用于深度分析）
        rc, stdout, stderr = self._run_script(
            'record_clear.py', ['--code', code, '--reason', reason], timeout=15
        )

        clear_msg = f"已清仓 {code}"
        if result.get('status') == 'updated':
            clear_msg += "（数据库已更新）"
        elif result.get('status') == 'rejected':
            clear_msg += f"（被拒绝: {result.get('reason')}）"

        return {
            'clear_result': result,
            'record_result': {'status': 'ok' if rc == 0 else 'failed', 'output': stdout[:200]},
            '_message': clear_msg
        }

    def _handle_reduce(self, params: dict) -> dict:
        """减仓操作（仅记录意图，实际需用户确认数量）"""
        code = params.get('code')
        if not code:
            return {'error': '请提供股票代码'}
        return {
            'action': 'reduce',
            'code': code,
            '_message': f"请确认 {code} 的减仓数量和价格",
            'suggestions': ['提供具体减仓数量后可更新持仓']
        }

    def _handle_add_watch(self, params: dict) -> dict:
        """添加到关注池"""
        code = params.get('code')
        if not code:
            return {'error': '请提供股票代码'}

        # 获取股票名
        name = ''
        try:
            holdings = self.data_manager.get_holdings()
            for c, info in holdings.get('holdings', {}).items():
                if c == code:
                    name = info.get('name', '')
        except Exception:
            pass

        result = self.data_manager.update_holdings('manual', {
            'action': 'add_watch', 'code': code, 'name': name,
            'reason': params.get('text', '用户添加')
        })

        return {
            'result': result,
            '_message': f"已将 {code} {name} 添加到关注池"
        }

    def _handle_remove_watch(self, params: dict) -> dict:
        """从关注池移除"""
        code = params.get('code')
        if not code:
            return {'error': '请提供股票代码'}

        result = self.data_manager.update_holdings('manual', {
            'action': 'remove_watch', 'code': code
        })

        return {
            'result': result,
            '_message': f"已将 {code} 从关注池移除"
        }

    def _handle_watchlist(self, params: dict) -> dict:
        """查看关注池"""
        watchlist = self.data_manager.get_watchlist()
        names = ', '.join(f"{w['name']}({w['code']})" for w in watchlist[:10])
        return {
            'watchlist': watchlist,
            'count': len(watchlist),
            '_message': f"关注池共 {len(watchlist)} 只: {names}"
        }

    def _handle_predict(self, params: dict) -> dict:
        """预测准确率查询"""
        code = params.get('code')

        try:
            import duckdb
            db_path = '/root/.openclaw/workspace/data/predictions.db'
            conn = duckdb.connect(db_path, read_only=True)

            if code:
                short_code = code.split('.')[0] if '.' in code else code
                rows = conn.execute("""
                    SELECT prediction_id, stock_code, analysis_date, recommendation,
                           confidence_level, verified, is_correct, actual_result, actual_return_5d
                    FROM predictions
                    WHERE stock_code LIKE ?
                    ORDER BY analysis_date DESC LIMIT 20
                """, [f'%{short_code}%']).fetchall()

                results = []
                for r in rows:
                    results.append({
                        'id': r[0], 'code': r[1], 'date': str(r[2]),
                        'rec': r[3], 'confidence': r[4], 'verified': r[5],
                        'correct': r[6], 'result': r[7],
                        'return_5d': round(float(r[8]), 2) if r[8] else None
                    })

                verified = [r for r in results if r['verified']]
                correct = [r for r in verified if r['correct']]
                acc = round(len(correct) / len(verified) * 100, 1) if verified else 0

                conn.close()
                return {
                    'predictions': results,
                    'total': len(results),
                    'verified': len(verified),
                    'correct': len(correct),
                    'accuracy': acc,
                    '_message': f"{code} 共 {len(results)} 条预测，已验证 {len(verified)} 条，准确率 {acc}%"
                }
            else:
                # 总体预测准确率
                row = conn.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN verified THEN 1 ELSE 0 END) as verified,
                           SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
                    FROM predictions
                """).fetchone()

                total, verified, correct = row[0], row[1], row[2]
                acc = round(correct / verified * 100, 1) if verified and verified > 0 else 0

                # 最近预测
                recent = conn.execute("""
                    SELECT stock_code, analysis_date, recommendation, confidence_level, verified
                    FROM predictions ORDER BY analysis_date DESC LIMIT 5
                """).fetchall()

                conn.close()

                recent_list = [
                    {'code': r[0], 'date': str(r[1]), 'rec': r[2], 'conf': r[3], 'verified': r[4]}
                    for r in recent
                ]

                return {
                    'total': total, 'verified': verified,
                    'correct': correct, 'accuracy': acc,
                    'recent': recent_list,
                    '_message': f"预测系统：共 {total} 条，已验证 {verified} 条，准确率 {acc}%"
                }
        except Exception as e:
            return {'error': f'查询预测失败: {e}'}

    def _handle_history(self, params: dict) -> dict:
        """历史记录"""
        days = params.get('days', 30)

        operations = self.data_manager.get_operations(days=days)
        cleared = self.data_manager.get_cleared_stocks(days=days)

        return {
            'operations': operations.to_dict('records') if hasattr(operations, 'to_dict') else [],
            'cleared_stocks': cleared,
            '_message': f"近 {days} 天: {len(operations) if hasattr(operations, '__len__') else 0} 条操作记录"
        }

    def _handle_update_holdings(self, params: dict) -> dict:
        """更新持仓（从用户输入中提取表格数据）"""
        text = params.get('text', '')
        # 检查文本中是否包含表格数据（包含制表符分隔的多行）
        if '\t' in text:
            result = self.data_manager.update_holdings('user_table', text)
            return {'result': result, '_message': f"持仓已更新: {result.get('status')}"}
        else:
            return {
                'error': '需要表格数据',
                '_message': '请粘贴持仓表格（制表符分隔）来更新持仓',
                'suggestions': ['从券商App复制持仓表格后粘贴']
            }

    def _handle_help(self, params: dict) -> dict:
        """帮助信息"""
        commands = [
            ('分析 600887 / 伊利怎么样', '分析个股'),
            ('我的持仓', '查看当前持仓'),
            ('总资产', '查看账户概览'),
            ('今日机会 / 扫描', '扫描市场机会'),
            ('清仓 600887', '清仓指定股票'),
            ('减仓 600887', '减仓指定股票'),
            ('关注 600887', '添加到关注池'),
            ('关注池', '查看关注列表'),
            ('预测 / 准确率', '查看预测系统状态'),
            ('历史 / 操作记录', '查看交易历史'),
            ('更新持仓 [表格数据]', '更新持仓数据'),
        ]
        return {
            'commands': commands,
            '_message': '可用命令：\n' + '\n'.join(f"  {c[0]:30s} - {c[1]}" for c in commands)
        }

    # ==================== 响应格式化 ====================

    def _format_response(self, intent: str, result: dict) -> dict:
        """统一输出格式"""
        has_error = 'error' in result
        message = result.pop('_message', '')
        detail = result.pop('_detail', None)
        suggestions = result.pop('suggestions', None)

        response = {
            'status': 'error' if has_error else 'ok',
            'intent': intent,
            'data': result,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

        if detail:
            response['detail'] = detail
        if suggestions:
            response['suggestions'] = suggestions

        return response

    def _error_response(self, msg: str, intent: str = 'unknown',
                        suggestions: list = None) -> dict:
        return {
            'status': 'error',
            'intent': intent,
            'data': {'error': msg},
            'message': msg,
            'suggestions': suggestions or [],
            'timestamp': datetime.now().isoformat()
        }

    def _help_response(self) -> dict:
        return self._format_response('help', self._handle_help({})['data'])


# ==================== 单例 ====================

_router = None


def get_unified_router() -> UnifiedRouter:
    """获取路由器单例"""
    global _router
    if _router is None:
        _router = UnifiedRouter()
    return _router


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='统一流程路由器')
    parser.add_argument('query', nargs='*', help='自然语言查询')
    parser.add_argument('--json', action='store_true', help='强制JSON输出')
    parser.add_argument('--intent-only', action='store_true', help='只显示识别的意图')

    args = parser.parse_args()

    if args.query:
        user_input = ' '.join(args.query)
    else:
        user_input = sys.stdin.read().strip()

    if not user_input:
        user_input = '帮助'

    router = get_unified_router()

    if args.intent_only:
        intent, params = router._parse_intent(user_input)
        print(json.dumps({'intent': intent, 'params': params}, ensure_ascii=False))
    else:
        response = router.route(user_input)
        if args.json:
            print(json.dumps(response, ensure_ascii=False, indent=2, default=str))
        else:
            # 人类可读格式
            print(f"[{response['status'].upper()}] {response.get('intent', '')}")
            if response.get('message'):
                print(response['message'])
            if response.get('detail'):
                print(response['detail'])
            if response.get('suggestions'):
                for s in response['suggestions']:
                    print(f"  → {s}")
