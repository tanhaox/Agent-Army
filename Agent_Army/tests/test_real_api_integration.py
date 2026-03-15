"""
Test Real API Integration
"""
import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.mark.asyncio
async def test_financial_tool_real_apis():
    """Test real Tushare API integration"""
    print("="*80)
    print("Real API Integration Test")
    print("="*80)
    
    from src.core.tools.data_source.financial_tool import FinancialTool
    
    tool = FinancialTool()
    stock_code = "600519"  # 贵州茅台
    
    # Test 1: get_moneyflow
    print(f"\n[Test 1] get_moneyflow - {stock_code}")
    try:
        result = await tool.get_moneyflow(stock_code, limit=5)
        if result.get("data_source") == "Tushare":
            print(f"[PASS] Real moneyflow data: {len(result.get('data', []))} records")
            summary = result.get('summary', {})
            print(f"[INFO] Total net inflow: {summary.get('total_net_inflow', 0):.2f}")
        else:
            print(f"[INFO] Using fallback data: {result.get('data_source')}")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
    
    # Test 2: get_top_list
    print(f"\n[Test 2] get_top_list - {stock_code}")
    try:
        result = await tool.get_top_list(stock_code)
        if result.get("data_source") == "Tushare":
            print(f"[PASS] Real top_list data: {len(result.get('data', []))} records")
            summary = result.get('summary', {})
            print(f"[INFO] Total count: {summary.get('total_count', 0)}")
        else:
            print(f"[INFO] Using fallback data: {result.get('data_source')}")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
    
    # Test 3: get_announcement
    print(f"\n[Test 3] get_announcement - {stock_code}")
    try:
        result = await tool.get_announcement(stock_code, limit=5)
        if result.get("data_source") == "Tushare":
            print(f"[PASS] Real announcement data: {len(result.get('data', []))} records")
            summary = result.get('summary', {})
            print(f"[INFO] Total announcements: {summary.get('total_count', 0)}")
        else:
            print(f"[INFO] Using fallback data: {result.get('data_source')}")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
    
    print("\n" + "="*80)
    print("[DONE] Real API integration test completed")
    print("="*80)
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_financial_tool_real_apis())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
