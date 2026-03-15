"""
Coverage Analysis Script for Agent Army
Runs all 16 agent tests and generates coverage report
"""
import subprocess
import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Change to Agent Army directory
os.chdir(r"C:\AI-Agent-Local\Agent_Army")

# Test files for 16 core agents
TEST_FILES = [
    "tests/test_market_sentiment_ai.py",
    "tests/test_capital_flow_ai.py",
    "tests/test_dragon_tiger_ai.py",
    "tests/test_competition_pattern_ai.py",
    "tests/test_policy_impact_ai.py",
    "tests/test_valuation_model_ai.py",
    "tests/test_profit_forecast_ai.py",
    "tests/test_position_management_ai.py",
    "tests/test_stop_loss_ai.py",
    "tests/test_risk_control_ai.py",
    "tests/test_backtest_analysis_ai.py",
    "tests/test_realtime_tracking_ai.py",
    "tests/test_strategy_optimization_ai.py",
    "tests/test_asset_allocation_ai.py",
    "tests/test_buy_timing_ai.py",
    "tests/test_target_pricing_ai.py",
]

def run_tests():
    """Run tests and collect results"""
    results = {}

    print("=" * 80)
    print("Running Coverage Analysis for 16 Core Agents")
    print("=" * 80)
    print()

    for test_file in TEST_FILES:
        agent_name = test_file.replace("tests/test_", "").replace("_ai.py", "").replace("test_", "").replace(".py", "")

        print(f"\n{'=' * 80}")
        print(f"Testing: {agent_name}")
        print(f"File: {test_file}")
        print(f"{'=' * 80}")

        try:
            # Run pytest without coverage first to see if tests exist
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=line", "-q"],
                capture_output=True,
                text=True,
                timeout=60
            )

            output = result.stdout + result.stderr

            # Count tests
            if "collected" in output:
                lines = output.split('\n')
                for line in lines:
                    if "collected" in line or "item" in line.lower():
                        print(f"  {line.strip()}")

            # Check if tests passed
            if result.returncode == 0:
                print(f"  ✓ Status: PASSED")
                status = "PASSED"
            else:
                if "collected 0 items" in output or "no tests ran" in output.lower():
                    print(f"  ⚠ Status: NO TESTS")
                    status = "NO TESTS"
                else:
                    print(f"  ✗ Status: FAILED")
                    status = "FAILED"
        except subprocess.TimeoutExpired:
            print(f"  ✗ Status: TIMEOUT")
            status = "TIMEOUT"
        except Exception as e:
            print(f"  ✗ Status: ERROR - {str(e)}")
            status = "ERROR"

        results[agent_name] = {
            "file": test_file,
            "status": status
        }

    return results

def generate_coverage_report(results):
    """Generate final coverage report"""
    print("\n" + "=" * 80)
    print("COVERAGE ANALYSIS SUMMARY")
    print("=" * 80)
    print()

    # Count statistics
    total = len(results)
    passed = sum(1 for r in results.values() if r["status"] == "PASSED")
    failed = sum(1 for r in results.values() if r["status"] == "FAILED")
    no_tests = sum(1 for r in results.values() if r["status"] == "NO TESTS")
    errors = sum(1 for r in results.values() if r["status"] in ["ERROR", "TIMEOUT"])

    print(f"Total Agents: {total}")
    print(f"✓ Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"✗ Failed: {failed} ({failed/total*100:.1f}%)")
    print(f"⚠ No Tests: {no_tests} ({no_tests/total*100:.1f}%)")
    print(f"? Errors: {errors} ({errors/total*100:.1f}%)")
    print()

    # Detailed table
    print("-" * 80)
    print(f"{'Agent Name':<35} {'Status':<15} {'File'}")
    print("-" * 80)

    status_order = ["PASSED", "NO TESTS", "FAILED", "ERROR", "TIMEOUT"]
    sorted_results = sorted(results.items(), key=lambda x: (
        status_order.index(x[1]["status"]) if x[1]["status"] in status_order else 999,
        x[0]
    ))

    for agent_name, info in sorted_results:
        status = info["status"]
        file = info["file"]

        # Add icon
        if status == "PASSED":
            icon = "✓"
        elif status == "FAILED":
            icon = "✗"
        elif status == "NO TESTS":
            icon = "⚠"
        else:
            icon = "?"

        print(f"{icon} {agent_name:<33} {status:<15} {file}")

    print("-" * 80)
    print()

    # Coverage estimation (based on test existence)
    coverage_rate = (passed + failed) / total * 100 if total > 0 else 0
    print(f"Test Coverage Rate: {coverage_rate:.1f}%")
    print(f"(Agents with test files: {passed + failed}/{total})")
    print()

    # Recommendations
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()

    if no_tests > 0:
        print(f"⚠ {no_tests} agents have no tests implemented yet.")
        print("  Priority: HIGH - Implement basic test cases")
        print()

    if failed > 0:
        print(f"✗ {failed} agents have failing tests.")
        print("  Priority: MEDIUM - Fix failing tests")
        print()

    if errors > 0:
        print(f"? {errors} agents have test errors.")
        print("  Priority: HIGH - Investigate and fix errors")
        print()

    if passed == total:
        print("✓ All agents have passing tests!")
        print("  Next Step: Measure actual code coverage with pytest-cov")
        print()

if __name__ == "__main__":
    results = run_tests()
    generate_coverage_report(results)

    print("=" * 80)
    print("Analysis Complete!")
    print("=" * 80)
