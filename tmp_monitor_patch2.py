#!/usr/bin/env python3
"""Patch monitor.py - add strong signal detection"""
import sys

with open('/root/.openclaw/workspace/scripts/monitor.py') as f:
    lines = f.readlines()

# Find insertion points
config_insert = None
signal_insert = None

for i, line in enumerate(lines):
    if 'class Monitor:' in line and config_insert is None:
        config_insert = i
    if 'all_signals.extend(self.check_price_limit' in line:
        signal_insert = i + 1  # After this line

print(f"Config insert at line {config_insert}")
print(f"Signal insert at line {signal_insert}")

# 1. Insert config before class Monitor
config_lines = [
    "\n# 强信号监控配置\n",
    "STRONG_SIGNAL_CONFIG = {'enabled': True, 'confidence_threshold': 0.6, 'max_watchlist_stocks': 10}\n",
    "try:\n",
    "    import json as _json\n",
    "    _cfg_path = '/root/.openclaw/workspace/config/monitor_config.json'\n",
    "    if os.path.exists(_cfg_path):\n",
    "        with open(_cfg_path) as _cf:\n",
    "            _cfg = _json.load(_cf)\n",
    "            STRONG_SIGNAL_CONFIG.update(_cfg.get('strong_signal', {}))\n",
    "except Exception:\n",
    "    pass\n",
    "\n",
]

# 2. Insert strong signal check block after price limit check
signal_lines = [
    "\n",
    "            # -- 强信号检测（ML预测置信度>=阈值） --\n",
    "            try:\n",
    "                from ml_predictor import MLPredictor\n",
    "                from ml_feature_engineer import MLFeatureEngineer\n",
    "                _predictor = MLPredictor()\n",
    "                if _predictor.ready:\n",
    "                    _threshold = STRONG_SIGNAL_CONFIG.get('confidence_threshold', 0.6)\n",
    "                    _today_str = datetime.now().strftime('%Y-%m-%d')\n",
    "                    _conn_s = self.db.get_conn('system')\n",
    "                    _dup = _conn_s.execute(\n",
    '                        f"SELECT COUNT(*) FROM alerts WHERE category=\'STRONG_SIGNAL\' '\n",
    '                        f"AND stock_code=\\'{code}\\' AND CAST(alert_time AS VARCHAR) LIKE \'{_today_str}%\'"\n',
    "                    ).fetchone()[0]\n",
    "                    if _dup == 0:\n",
    "                        _kdf = self.data_fetcher.get_daily_kline(code,\n",
    "                            (datetime.now() - pd.Timedelta(days=120)).strftime('%Y-%m-%d'),\n",
    "                            datetime.now().strftime('%Y-%m-%d'))\n",
    "                        if not _kdf.empty and len(_kdf) >= 60:\n",
    "                            _eng = MLFeatureEngineer(_kdf, stock_code=code)\n",
    "                            _feat = _eng.compute_features()\n",
    "                            _ml = _predictor.predict(_feat)\n",
    "                            if _ml and _ml.get('direction') != 'unknown':\n",
    "                                _dir = _ml['direction']\n",
    "                                _conf = _ml.get('confidence', 0)\n",
    "                                _er = _ml.get('expected_return', 0)\n",
    "                                if _dir == 'up' and _conf >= _threshold:\n",
    "                                    all_signals.append({'level': 'high', 'type': 'STRONG_SIGNAL',\n",
    "                                        'msg': (f'{name}({code}) 出现强上涨信号，'\n",
    "                                                f'置信度{_conf:.0%}，'\n",
    "                                                f'历史准确率{_predictor.accuracy:.1%}，'\n",
    "                                                f'预期收益{_er:.2f}%。建议关注。')})\n",
    "                                elif _dir == 'down' and _conf >= _threshold:\n",
    "                                    all_signals.append({'level': 'medium', 'type': 'STRONG_SIGNAL_BEAR',\n",
    "                                        'msg': (f'{name}({code}) ML高置信度看空，'\n",
    "                                                f'置信度{_conf:.0%}，'\n",
    "                                                f'历史准确率{_predictor.accuracy:.1%}。注意风险。')})\n",
    "            except Exception:\n",
    "                pass\n",
]

# Apply patches
if 'STRONG_SIGNAL_CONFIG' not in ''.join(lines):
    lines[config_insert:config_insert] = config_lines
    # Adjust signal_insert after config insertion
    signal_insert += len(config_lines)
    lines[signal_insert:signal_insert] = signal_lines

with open('/root/.openclaw/workspace/scripts/monitor.py', 'w') as f:
    f.writelines(lines)

print("Done: monitor.py patched")
