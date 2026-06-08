#!/usr/bin/env python3
"""Patch monitor.py: add strong signal detection inline in run_once()"""

content = open('/root/.openclaw/workspace/scripts/monitor.py').read()

# 1. Add config after STOP_LOSS_CONFIG block
config_code = '''

# 强信号监控配置
STRONG_SIGNAL_CONFIG = {
    'enabled': True,
    'confidence_threshold': 0.6,
    'max_watchlist_stocks': 10,
}
try:
    import json as _json
    _cfg_path = '/root/.openclaw/workspace/config/monitor_config.json'
    if os.path.exists(_cfg_path):
        with open(_cfg_path) as _cf:
            _cfg = _json.load(_cf)
            if 'strong_signal' in _cfg:
                STRONG_SIGNAL_CONFIG.update(_cfg['strong_signal'])
except Exception:
    pass
'''

if 'STRONG_SIGNAL_CONFIG' not in content:
    content = content.replace(
        "class Monitor:",
        config_code + "\nclass Monitor:"
    )

# 2. Add strong signal check inside run_once stock loop
# After price limit check, before saving alerts
old_block = """            # 涨跌停预警
            all_signals.extend(self.check_price_limit(code, name))
            # 保存预警"""

new_block = """            # 涨跌停预警
            all_signals.extend(self.check_price_limit(code, name))

            # ── 强信号检测（ML预测置信度≥阈值） ──
            try:
                from ml_predictor import MLPredictor
                from ml_feature_engineer import MLFeatureEngineer
                _predictor = MLPredictor()
                if _predictor.ready:
                    _threshold = STRONG_SIGNAL_CONFIG.get('confidence_threshold', 0.6)
                    _today_str = datetime.now().strftime('%Y-%m-%d')
                    # 去重：同一股票同一交易日只记录一次
                    _conn_s = self.db.get_conn('system')
                    _dup = _conn_s.execute(f"""
                        SELECT COUNT(*) FROM alerts
                        WHERE category = 'STRONG_SIGNAL'
                          AND stock_code = '{code}'
                          AND CAST(alert_time AS VARCHAR) LIKE '{_today_str}%'
                    """).fetchone()[0]
                    if _dup == 0:
                        _kdf = self.data_fetcher.get_daily_kline(code,
                            (datetime.now() - pd.Timedelta(days=120)).strftime('%Y-%m-%d'),
                            datetime.now().strftime('%Y-%m-%d'))
                        if not _kdf.empty and len(_kdf) >= 60:
                            _eng = MLFeatureEngineer(_kdf, stock_code=code)
                            _feat = _eng.compute_features()
                            _ml = _predictor.predict(_feat)
                            if _ml and _ml.get('direction') != 'unknown':
                                _dir = _ml['direction']
                                _conf = _ml.get('confidence', 0)
                                _er = _ml.get('expected_return', 0)
                                if _dir == 'up' and _conf >= _threshold:
                                    all_signals.append({
                                        'level': 'high',
                                        'type': 'STRONG_SIGNAL',
                                        'msg': (f'{name}({code}) 出现强上涨信号，'
                                                f'置信度{_conf:.0%}，'
                                                f'历史准确率{_predictor.accuracy:.1%}，'
                                                f'预期收益{_er:.2f}%。建议关注。')
                                    })
                                elif _dir == 'down' and _conf >= _threshold:
                                    all_signals.append({
                                        'level': 'medium',
                                        'type': 'STRONG_SIGNAL_BEAR',
                                        'msg': (f'{name}({code}) ML高置信度看空，'
                                                f'置信度{_conf:.0%}，'
                                                f'历史准确率{_predictor.accuracy:.1%}。注意风险。')
                                    })
            except Exception:
                pass

            # 保存预警"""

if 'STRONG_SIGNAL' not in content:
    content = content.replace(old_block, new_block)

with open('/root/.openclaw/workspace/scripts/monitor.py', 'w') as f:
    f.write(content)

print("monitor.py patched OK")
