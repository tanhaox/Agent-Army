"""Quick Test - Verify pages_v2 Module Import"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("  Testing pages_v2 Module Import")
print("=" * 60)

try:
    print("\n[1/2] Importing src.core.pages_v2...")
    from src.core.pages_v2 import (
        render_dashboard,
        render_agent_status,
        render_task_management,
        render_analysis_reports,
        render_portfolio,
        render_market_monitor,
        render_system_config
    )
    print("[OK] Import successful!")

    print("\n[2/2] Checking available render functions...")
    print(f"  - render_dashboard: {render_dashboard is not None}")
    print(f"  - render_agent_status: {render_agent_status is not None}")
    print(f"  - render_task_management: {render_task_management is not None}")
    print(f"  - render_analysis_reports: {render_analysis_reports is not None}")
    print(f"  - render_portfolio: {render_portfolio is not None}")
    print(f"  - render_market_monitor: {render_market_monitor is not None}")
    print(f"  - render_system_config: {render_system_config is not None}")

    print("\n" + "=" * 60)
    print("  [SUCCESS] All tests passed! Ready to start app")
    print("=" * 60)
    print("\nStart command:")
    print("  streamlit run web_app_v2.py")
    print("  or")
    print("  start_ps1.bat")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
