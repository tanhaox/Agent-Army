#!/usr/bin/env python3
"""Patch fundamental_analysis_agent.py - add get_valuation_details method"""

with open('/root/.openclaw/workspace/agent_army/fundamental_analysis_agent.py') as f:
    content = f.read()

if 'get_valuation_details' in content:
    print("Already patched")
    exit(0)

# Add the new method before the analyze() method
new_method = '''
    def get_valuation_details(self, stock_code: str = None) -> Dict[str, Any]:
        """获取估值详情：PE/PB历史分位数、ROE趋势、行业对比

        从 finance 表获取过去3年数据，计算估值分位数。
        无未来函数（查询时使用当前日期）。

        Args:
            stock_code: 股票代码（如 '600887.SH'），默认使用 self.stock_code

        Returns:
            dict: 估值详情字典
        """
        code = stock_code or self.stock_code
        if not code:
            return self._empty_valuation()

        try:
            import duckdb
            db_path = '/root/.openclaw/workspace/data/market_data.db'
            if not os.path.exists(db_path):
                return self._empty_valuation()
            conn = duckdb.connect(db_path, read_only=True)

            from datetime import datetime, timedelta
            three_years_ago = (datetime.now() - timedelta(days=1095)).strftime('%Y-%m-%d')

            # 1. PE/PB 分位数（过去3年）
            pe_pb = conn.execute(f"""
                SELECT pe, pb, date FROM finance
                WHERE stock_code = '{code}'
                  AND date >= '{three_years_ago}'
                  AND pe IS NOT NULL AND pe > 0
                ORDER BY date
            """).fetchall()
            conn.close()

            pe_values = [float(r[0]) for r in pe_pb if r[0] is not None and float(r[0]) > 0]
            pb_values = [float(r[1]) for r in pe_pb if r[1] is not None and float(r[1]) > 0]

            # 最新值
            pe_current = pe_values[-1] if pe_values else None
            pb_current = pb_values[-1] if pb_values else None

            # 分位数（当前值在历史中的位置）
            pe_percentile = None
            if pe_current and len(pe_values) >= 10:
                pe_percentile = round(
                    sum(1 for v in pe_values if v <= pe_current) / len(pe_values) * 100, 1)

            pb_percentile = None
            if pb_current and len(pb_values) >= 10:
                pb_percentile = round(
                    sum(1 for v in pb_values if v <= pb_current) / len(pb_values) * 100, 1)

            # 2. ROE 趋势（从 finance 表获取最近几期 ROE）
            roe_trend = '数据不足'
            try:
                conn2 = duckdb.connect(db_path, read_only=True)
                roe_rows = conn2.execute(f"""
                    SELECT roe, date FROM finance
                    WHERE stock_code = '{code}'
                      AND roe IS NOT NULL AND roe != 0
                    ORDER BY date DESC LIMIT 12
                """).fetchall()
                conn2.close()

                if len(roe_rows) >= 4:
                    roes = [float(r[0]) for r in reversed(roe_rows)]
                    # 简单线性回归斜率
                    n = len(roes)
                    x_mean = (n - 1) / 2
                    y_mean = sum(roes) / n
                    numerator = sum((i - x_mean) * (roes[i] - y_mean) for i in range(n))
                    denominator = sum((i - x_mean) ** 2 for i in range(n))
                    if denominator > 0:
                        slope = numerator / denominator
                        if slope > 0.5:
                            roe_trend = '上升'
                        elif slope < -0.5:
                            roe_trend = '下降'
                        else:
                            roe_trend = '平稳'
            except Exception:
                pass

            # 3. 行业对比
            industry_pe_median = None
            industry_name = '未知'
            try:
                import json
                cfg_path = '/root/.openclaw/workspace/config/industry_mapping.json'
                if os.path.exists(cfg_path):
                    with open(cfg_path) as jf:
                        mapping = json.load(jf)
                    stock_info = mapping.get(code, mapping.get('default', {}))
                    industry_name = stock_info.get('industry', '未知')

                # 查询同行业股票的 PE
                if os.path.exists(cfg_path):
                    industry_stocks = [k for k, v in mapping.items()
                                      if k != 'default' and v.get('industry') == industry_name]
                    if len(industry_stocks) >= 2:
                        conn3 = duckdb.connect(db_path, read_only=True)
                        placeholders = ','.join([f"'{s}'" for s in industry_stocks])
                        ind_pe = conn3.execute(f"""
                            SELECT pe FROM finance
                            WHERE stock_code IN ({placeholders})
                              AND pe IS NOT NULL AND pe > 0
                              AND date >= '{three_years_ago}'
                        """).fetchall()
                        conn3.close()
                        if ind_pe:
                            ind_pe_vals = [float(r[0]) for r in ind_pe]
                            industry_pe_median = round(sorted(ind_pe_vals)[len(ind_pe_vals)//2], 1)
            except Exception:
                pass

            # 4. 估值建议
            suggestion = '数据不足，无法判断估值水平'
            if pe_percentile is not None:
                if pe_percentile <= 20:
                    suggestion = f'PE低于历史{100-pe_percentile:.0f}%时间，显著低估'
                elif pe_percentile <= 40:
                    suggestion = f'PE低于历史{100-pe_percentile:.0f}%时间，偏低估'
                elif pe_percentile <= 60:
                    suggestion = f'PE处于历史中位（{pe_percentile:.0f}%分位），估值合理'
                elif pe_percentile <= 80:
                    suggestion = f'PE高于历史{pe_percentile:.0f}%时间，偏高估'
                else:
                    suggestion = f'PE高于历史{pe_percentile:.0f}%时间，显著高估'

                if industry_pe_median and pe_current:
                    if pe_current < industry_pe_median * 0.8:
                        suggestion += f'；行业平均PE {industry_pe_median}，相对低估'
                    elif pe_current > industry_pe_median * 1.2:
                        suggestion += f'；行业平均PE {industry_pe_median}，相对高估'

            return {
                'pe_current': round(pe_current, 1) if pe_current else None,
                'pe_3y_percentile': pe_percentile,
                'pb_current': round(pb_current, 2) if pb_current else None,
                'pb_3y_percentile': pb_percentile,
                'roe_3y_trend': roe_trend,
                'industry_name': industry_name,
                'industry_pe_median': industry_pe_median,
                'valuation_suggestion': suggestion,
                'pe_sample_count': len(pe_values),
                'pb_sample_count': len(pb_values),
            }

        except Exception as e:
            return self._empty_valuation(str(e))

    @staticmethod
    def _empty_valuation(error='') -> Dict[str, Any]:
        return {
            'pe_current': None,
            'pe_3y_percentile': None,
            'pb_current': None,
            'pb_3y_percentile': None,
            'roe_3y_trend': '数据不足',
            'industry_name': '未知',
            'industry_pe_median': None,
            'valuation_suggestion': f'估值数据不可用{": " + error if error else ""}',
            'pe_sample_count': 0,
            'pb_sample_count': 0,
        }

'''

# Insert before analyze() method
content = content.replace(
    "    def analyze(self) -> Dict[str, Any]:",
    new_method + "    def analyze(self) -> Dict[str, Any]:"
)

with open('/root/.openclaw/workspace/agent_army/fundamental_analysis_agent.py', 'w') as f:
    f.write(content)

print("Done: fundamental_analysis_agent.py patched")
