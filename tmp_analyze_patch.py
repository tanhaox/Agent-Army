#!/usr/bin/env python3
"""Patch analyze_stock.py - add valuation details output"""

with open('/root/.openclaw/workspace/scripts/analyze_stock.py') as f:
    content = f.read()

if 'valuation_details' in content:
    print("Already patched")
    exit(0)

# 1. After fundamental analysis (line ~609-610), add valuation details call and output
# Find the section after "基本面评分" print
old_fund = '''    print(f"  基本面评分: {fund_result.get('total_score', 'N/A')}")'''
new_fund = '''    print(f"  基本面评分: {fund_result.get('total_score', 'N/A')}")

    # 估值详情（基本面深度解读）
    valuation_details = None
    try:
        from fundamental_analysis_agent import FundamentalAnalysisAgent as _FAA
        _fa_agent = _FAA(stock_code=stock_code)
        valuation_details = _fa_agent.get_valuation_details()
        if valuation_details and valuation_details.get('pe_current') is not None:
            print(f"  --- 估值分析（基本面深度解读）---")
            pe_pct = valuation_details.get('pe_3y_percentile')
            pb_pct = valuation_details.get('pb_3y_percentile')
            pe_str = f"{valuation_details['pe_current']} (历史分位 {pe_pct}%)" if pe_pct else f"{valuation_details['pe_current']}"
            pb_str = f"{valuation_details['pb_current']} (历史分位 {pb_pct}%)" if pb_pct else f"{valuation_details['pb_current']}"
            print(f"  PE: {pe_str}")
            print(f"  PB: {pb_str}")
            print(f"  ROE趋势: {valuation_details['roe_3y_trend']}")
            ind = valuation_details.get('industry_name', '')
            ind_pe = valuation_details.get('industry_pe_median')
            if ind_pe and ind != '未知':
                print(f"  行业对比: {ind}行业中位PE {ind_pe}，公司PE {valuation_details['pe_current']}")
            print(f"  综合: {valuation_details['valuation_suggestion']}")
            # 添加到fund_result
            fund_result['valuation_details'] = valuation_details
    except Exception as e:
        print(f"  估值详情获取失败: {e}")'''

content = content.replace(old_fund, new_fund)

# 2. Add valuation_details to JSON output
# Find the JSON output section where we add ml_prediction
old_json = "        if ml_prediction:\n            json_output['ml_prediction'] = ml_prediction"
new_json = """        if ml_prediction:
            json_output['ml_prediction'] = ml_prediction
        # 估值详情
        if valuation_details:
            json_output['valuation_details'] = valuation_details"""

content = content.replace(old_json, new_json)

with open('/root/.openclaw/workspace/scripts/analyze_stock.py', 'w') as f:
    f.write(content)

print("Done: analyze_stock.py patched")
