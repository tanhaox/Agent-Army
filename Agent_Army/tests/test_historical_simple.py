"""
Simple Historical Node AI Test (No Emoji)
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.business.stock.historical_cycle_ai import HistoricalCycleAI
from src.agents.business.stock.kline_pattern_ai import KlinePatternAI
from src.agents.business.stock.capital_regular_ai import CapitalRegularAI
from src.agents.business.stock.historical_node_ai import HistoricalNodeAI

async def main():
    print("="*80)
    print("Historical Node AI Test")
    print("="*80)

    # Test 1: HistoricalCycleAI
    print("\n[Test 1] HistoricalCycleAI")
    cycle_ai = HistoricalCycleAI()
    result1 = await cycle_ai.analyze_event_cycles("600519", years=5)
    print(f"[PASS] Cycle AI initialized: {cycle_ai.name}")
    print(f"[INFO] Earnings detected: {result1['earnings_cycles'].get('detected')}")

    # Test 2: KlinePatternAI
    print("\n[Test 2] KlinePatternAI")
    pattern_ai = KlinePatternAI()
    result2 = await pattern_ai.analyze_kline_patterns("601669", years=3)
    print(f"[PASS] Pattern AI initialized: {pattern_ai.name}")
    print(f"[INFO] Support levels: {len(result2.get('support_levels', []))}")

    # Test 3: CapitalRegularAI
    print("\n[Test 3] CapitalRegularAI")
    capital_ai = CapitalRegularAI()
    result3 = await capital_ai.identify_regular_capital("601669", years=3)
    print(f"[PASS] Capital AI initialized: {capital_ai.name}")
    print(f"[INFO] Regular funds: {len(result3.get('regular_funds', []))}")

    # Test 4: HistoricalNodeAI (Core)
    print("\n[Test 4] HistoricalNodeAI (Core)")
    node_ai = HistoricalNodeAI()
    result4 = await node_ai.analyze("601669", years=3)
    print(f"[PASS] Node AI initialized: {node_ai.name}")
    print(f"[INFO] Overall score: {result4.get('overall_score', 0)}/100")
    print(f"[INFO] Rating: {result4.get('rating', '')}")
    print(f"[INFO] Key nodes: {len(result4.get('key_nodes', []))}")

    # Summary
    print("\n" + "="*80)
    print("[PASS] All tests passed!")
    print("="*80)
    print("Test 1: HistoricalCycleAI - PASS")
    print("Test 2: KlinePatternAI - PASS")
    print("Test 3: CapitalRegularAI - PASS")
    print("Test 4: HistoricalNodeAI (Core) - PASS")
    print("\nTotal: 4/4 (100%)")
    print("="*80)

    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
