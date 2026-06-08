#!/usr/bin/env python3
"""Patch monitor.py - add strong signal detection"""
import textwrap

with open('/root/.openclaw/workspace/scripts/monitor.py') as f:
    content = f.read()

if 'STRONG_SIGNAL' in content:
    print("Already patched")
    exit(0)

# 1. Config block before class Monitor
config_block = textwrap.dedent("""
    # 强信号监控配置
    STRONG_SIGNAL_CONFIG = {'enabled': True, 'confidence_threshold': 0.6, 'max_watchlist_stocks': 10}
    try:
        import json as _json
        _cfg_path = '/root/.openclaw/workspace/config/monitor_config.json'
        if os.path.exists(_cfg_path):
            with open(_cfg_path) as _cf:
                STRONG_SIGNAL_CONFIG.update(_json.load(_cf).get('strong_signal', {}))
    except Exception:
        pass

""")

content = content.replace('class Monitor:', config_block + 'class Monitor:')

# 2. Signal check block - use a helper function to avoid quoting issues
signal_code = '''
            # -- 强信号检测（ML预测置信度>=阈值） --
            try:
                from ml_predictor import MLPredictor
                from ml_feature_engineer import MLFeatureEngineer
                _predictor = MLPredictor()
                if _predictor.ready:
                    _threshold = STRONG_SIGNAL_CONFIG.get('confidence_threshold', 0.6)
                    _today_str = datetime.now().strftime('%Y-%m-%d')
                    _conn_s = self.db.get_conn('system')
                    _sql = "SELECT COUNT(*) FROM alerts WHERE category='STRONG_SIGNAL' AND stock_code=? AND CAST(alert_time AS VARCHAR) LIKE ?"
                    _dup = _conn_s.execute(_sql, [code, _today_str + '%']).fetchone()[0]
                    if _dup == 0:
                        _kdf = self.data_fetcher.get_daily_kline(code,
                            (datetime.now() - pd.Timedelta(days=120)).strftime('%Y-%m-%d'),
                            datetime.now().strftime('%Y-%m-%d'))
                        if not _kdf.empty and len(_kdf) >= 60:
                            _eng = MLFeatureEngineer(_kdf, stock_code=code)
                            _feat = _eng.compute_features()
                            _ml = _predictor.predict(_feat)
                            if _ml and _ml.get('direction') != 'unknown':
                                _d = _ml['direction']
                                _c = _ml.get('confidence', 0)
                                _er = _ml.get('expected_return', 0)
                                _acc = _predictor.accuracy
                                if _d == 'up' and _c >= _threshold:
                                    all_signals.append({'level': 'high', 'type': 'STRONG_SIGNAL',
                                        'msg': f'{name}({code}) 出现强上涨信号，置信度{_c:.0%}，历史准确率{_acc:.1%}，预期收益{_er:.2f}%。建议关注。'})
                                elif _d == 'down' and _c >= _threshold:
                                    all_signals.append({'level': 'medium', 'type': 'STRONG_SIGNAL_BEAR',
                                        'msg': f'{name}({code}) ML高置信度看空，置信度{_c:.0%}，历史准确率{_acc:.1%}。注意风险。'})
            except Exception:
                pass
'''

old = "            # 保存预警\n            for sig in all_signals:"
new = signal_code + "\n            # 保存预警\n            for sig in all_signals:"
content = content.replace(old, new)

with open('/root/.openclaw/workspace/scripts/monitor.py', 'w') as f:
    f.write(content)

print("Done: monitor.py patched")
