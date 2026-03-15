"""
AI


1. HistoricalCycleAI - 
2. KlinePatternAI - K
3. CapitalRegularAI - 
4. HistoricalNodeAI - 


    python tests/test_historical_node_ai.py
"""
import pytest

import asyncio
import sys
import os

# 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.business.stock.historical_cycle_ai import HistoricalCycleAI
from src.agents.business.stock.kline_pattern_ai import KlinePatternAI
from src.agents.business.stock.capital_regular_ai import CapitalRegularAI
from src.agents.business.stock.historical_node_ai import HistoricalNodeAI


@pytest.mark.asyncio
async def test_historical_cycle_ai():
    """1AI"""
    print("\n" + "="*60)
    print("1AI")
    print("="*60)

    ai = HistoricalCycleAI()

    # 
    stock_code = "600519"
    print(f"\n[TEST] {stock_code}")

    result = await ai.analyze_event_cycles(stock_code, years=5)

    # 
    assert "stock_code" in result
    assert result["stock_code"] == stock_code
    assert "earnings_cycles" in result
    assert "policy_cycles" in result

    # 
    print(f"\n[PASS] ")
    print(f"   - AI: {ai.name}")
    print(f"   - AI: {ai.role}")

    # 
    earnings = result["earnings_cycles"]
    print(f"\n[REPORT] :")
    if earnings.get("detected"):
        print(f"   [PASS] ")
        print(f"   - : {earnings.get('cycle_length')} ")
        print(f"   - : {earnings.get('confidence', 0):.2f}")
        print(f"   - : {earnings.get('next_event')}")
    else:
        print(f"   [FAIL] : {earnings.get('reason')}")

    # 
    policy = result["policy_cycles"]
    print(f"\n[REPORT] :")
    if policy.get("detected"):
        print(f"   [PASS] ")
        print(f"   - : {policy.get('cycle_length')} ")
        print(f"   - : {policy.get('confidence', 0):.2f}")
        print(f"   - : {policy.get('next_event')}")
    else:
        print(f"   [FAIL] : {policy.get('reason')}")

    # 
    key_windows = result.get("key_time_windows", [])
    print(f"\n[REPORT] :")
    for window in key_windows[:3]:
        print(f"   - {window['window']}: {window['type']} ({window['importance']})")

    print(f"\n[PASS] 1AI")

    return True


@pytest.mark.asyncio
async def test_kline_pattern_ai():
    """2KAI"""
    print("\n" + "="*60)
    print("2KAI")
    print("="*60)

    ai = KlinePatternAI()

    # 
    stock_code = "601669"
    print(f"\n[TEST] {stock_code}")

    result = await ai.analyze_kline_patterns(stock_code, years=3)

    # 
    assert "stock_code" in result
    assert result["stock_code"] == stock_code
    assert "support_levels" in result
    assert "resistance_levels" in result
    assert "seasonal_patterns" in result

    # 
    print(f"\n[PASS] ")
    print(f"   - AI: {ai.name}")

    # 
    support_levels = result.get("support_levels", [])
    print(f"\n[DATA] :")
    for level in support_levels[:3]:
        print(f"   - {level:.2f} ")

    # 
    resistance_levels = result.get("resistance_levels", [])
    print(f"\n[REPORT] :")
    for level in resistance_levels[:3]:
        print(f"   - {level:.2f} ")

    # 
    seasonal = result.get("seasonal_patterns", {})
    print(f"\n :")
    print(f"   - Q1: {seasonal.get('q1_trend')}")
    print(f"   - Q2: {seasonal.get('q2_trend')}")
    print(f"   - Q3: {seasonal.get('q3_trend')}")
    print(f"   - Q4: {seasonal.get('q4_trend')}")
    print(f"   - : {seasonal.get('best_quarter')}")
    print(f"   - : {seasonal.get('worst_quarter')}")

    # 
    key_findings = result.get("key_findings", [])
    print(f"\n[INSIGHT] :")
    for finding in key_findings[:3]:
        print(f"   - {finding}")

    print(f"\n[PASS] 2KAI")

    return True


@pytest.mark.asyncio
async def test_capital_regular_ai():
    """3AI"""
    print("\n" + "="*60)
    print("3AI")
    print("="*60)

    ai = CapitalRegularAI()

    # 
    stock_code = "601669"
    print(f"\n[TEST] {stock_code}")

    result = await ai.identify_regular_capital(stock_code, years=3)

    # 
    assert "stock_code" in result
    assert result["stock_code"] == stock_code
    assert "regular_funds" in result
    assert "guest_funds" in result

    # 
    print(f"\n[PASS] ")
    print(f"   - AI: {ai.name}")

    # 
    regular_funds = result.get("regular_funds", [])
    print(f"\n[TOP] :")
    for fund in regular_funds:
        print(f"   - {fund['name']}:")
        print(f"     : {fund['type']}")
        print(f"     : {fund['frequency']:.2%}")
        print(f"     : {fund['correlation_with_rise']:.2f}")
        print(f"     : {fund['pattern']}")

    # 
    guest_funds = result.get("guest_funds", [])
    print(f"\n[GUEST] :")
    for fund in guest_funds:
        print(f"   - {fund['name']}:")
        print(f"     : {fund['frequency']:.2%}")
        print(f"     : {fund['correlation_with_rise']:.2f}")

    # 
    prediction = result.get("prediction", "")
    print(f"\n[PREDICT] : {prediction}")

    # 
    key_insights = result.get("key_insights", [])
    print(f"\n[INSIGHT] :")
    for insight in key_insights[:3]:
        print(f"   - {insight}")

    print(f"\n[PASS] 3AI")

    return True


@pytest.mark.asyncio
async def test_historical_node_ai():
    """4AI"""
    print("\n" + "="*60)
    print("4AI")
    print("="*60)

    ai = HistoricalNodeAI()

    # 
    stock_code = "601669"
    print(f"\n[TEST] {stock_code}")

    result = await ai.analyze(stock_code, years=3)

    # 
    assert "stock_code" in result
    assert result["stock_code"] == stock_code
    assert "event_cycles" in result
    assert "kline_patterns" in result
    assert "regular_capital" in result
    assert "key_nodes" in result
    assert "overall_score" in result
    assert "rating" in result
    assert "investment_advice" in result

    # 
    print(f"\n[PASS] ")
    print(f"   - AI: {ai.name}")
    print(f"   - AI: {ai.role}")

    # 
    key_nodes = result.get("key_nodes", [])
    print(f"\n[REPORT] :")
    for node in key_nodes:
        print(f"   - {node['time_window']}: {node['event_type']}")
        print(f"     : {node['confidence']:.2f}")
        print(f"     : {node['importance']}")
        print(f"     : {node['action']}")

    # 
    overall_score = result.get("overall_score", 0)
    rating = result.get("rating", "")
    print(f"\n[TEST] :")
    print(f"   - : {overall_score}/100")
    print(f"   - : {rating}")

    # 
    investment_advice = result.get("investment_advice", "")
    print(f"\n :")
    print(f"   - {investment_advice}")

    # 
    risk_alerts = result.get("risk_alerts", [])
    print(f"\n[WARNING] :")
    for alert in risk_alerts[:3]:
        print(f"   - {alert}")

    # 
    summary = result.get("summary", "")
    print(f"\n :")
    print(f"   - {summary}")

    print(f"\n[PASS] 4AI")

    return True


@pytest.mark.asyncio
async def test_all():
    """"""
    print("\n" + "="*80)
    print("AI - ")
    print("="*80)

    try:
        # 1
        await test_historical_cycle_ai()

        # 2K
        await test_kline_pattern_ai()

        # 3
        await test_capital_regular_ai()

        # 4
        await test_historical_node_ai()

        # 
        print("\n" + "="*80)
        print("[PASS] ")
        print("="*80)
        print("\n")
        print("   - 1 [PASS]")
        print("   - 2K [PASS]")
        print("   - 3 [PASS]")
        print("   - 4 [PASS]")
        print("\n: 4/4  (100%)")
        print("="*80)

        return True

    except Exception as e:
        print(f"\n[FAIL] : {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 
    success = asyncio.run(test_all())

    # 
    sys.exit(0 if success else 1)
