"""
快速验证脚本 - 验证所有模块是否可以导入
"""

import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("  Agent Army Web v2.0 - Module Import Test")
print("=" * 60)
print()

# 测试导入
modules_to_test = [
    ("Performance Tools", "src.core.utils.performance"),
    ("Visualization Tools", "src.core.utils.visualization"),
    ("Export Tools", "src.core.utils.exporters"),
    ("Responsive Tools", "src.core.utils.responsive"),
    ("Agent Manager", "src.core.agents.agent_manager"),
    ("Dashboard Page", "src.core.pages_v2.dashboard_full"),
    ("Agent Status Page", "src.core.pages_v2.agent_status_optimized"),
    ("Task Management Page", "src.core.pages_v2.task_management_optimized"),
    ("Data Center Page", "src.core.pages_v2.data_center_v2"),
    ("Analysis Reports Page", "src.core.pages_v2.analysis_reports_v2"),
]

success_count = 0
fail_count = 0

for module_name, module_path in modules_to_test:
    try:
        __import__(module_path)
        print(f"[OK] {module_name}")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] {module_name}: {e}")
        fail_count += 1

print()
print("=" * 60)
print(f"  Results: {success_count} passed, {fail_count} failed")
print("=" * 60)

if fail_count == 0:
    print("\nAll modules imported successfully!")
else:
    print(f"\n{fail_count} module(s) failed to import.")
