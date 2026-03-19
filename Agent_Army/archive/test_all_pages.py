"""Quick Test - Verify All Page Modules Can Import"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("  Testing All Page Modules Import")
print("=" * 70)

passed = 0
failed = 0

# Test imports
tests = [
    ("Dashboard v2", "from src.core.pages_v2.dashboard_v2 import render_dashboard"),
    ("Agent Status v3", "from src.core.pages_v2.agent_status_v3 import render_agent_status_v3"),
    ("Task Management v3", "from src.core.pages_v2.task_management_v3 import render_task_management_v3"),
    ("Analysis Reports v3", "from src.core.pages_v2.analysis_reports_v3 import render_analysis_reports_v3"),
    ("Portfolio", "from src.core.pages_v2.portfolio import render_portfolio"),
    ("Market Monitor", "from src.core.pages_v2.market_monitor import render_market_monitor"),
    ("System Config v3", "from src.core.pages_v2.system_config_v3 import render_system_config_v3"),
    ("Navigation Guide v3", "from src.core.pages_v2.navigation_guide_v3 import render_navigation_guide_v3"),
]

for idx, (name, import_cmd) in enumerate(tests, 1):
    try:
        print(f"[{idx}/{len(tests)}] Testing {name}...", end=" ")
        exec(import_cmd)
        print("[OK]")
        passed += 1
    except Exception as e:
        print(f"[FAILED]")
        print(f"  Error: {e}")
        failed += 1

print("\n" + "=" * 70)
print(f"  Results: {passed} passed, {failed} failed")
print("=" * 70)

if failed == 0:
    print("\n[SUCCESS] All page modules imported successfully!")
    print("\nYou can now start the application:")
    print("  streamlit run web_app_v2.py")
    print("  or")
    print("  start_ps1.bat")
else:
    print(f"\n[WARNING] {failed} module(s) failed to import")
    sys.exit(1)
