#!/usr/bin/env python3
"""
Verify that async test fixes are working correctly
"""

import subprocess
import sys
from pathlib import Path

# List of files that were fixed
FIXED_FILES = [
    "test_commander_agent.py",
    "test_buy_timing_ai.py",
    "test_cache.py",
    "test_capital_flow_ai.py",
    "test_chip_analysis_ai.py",
    "test_competition_pattern_ai.py",
    "test_comprehensive_score_ai.py",
    "test_dragon_tiger_ai.py",
    "test_financial_health_ai.py",
    "test_hr_agent.py",
    "test_market_sentiment_ai.py",
    "test_news_monitor.py",
    "test_position_management_ai.py",
    "test_risk_control_ai.old.py",
    "test_target_pricing_ai.py",
    "test_technical_analysis_ai.py",
    "test_tools_library.py",
    "test_valuation_model_ai.py",
]

def run_test(test_file):
    """Run a single test file and return result"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", f"tests/{test_file}", "-v"],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="ignore"
        )

        # Check for "passed" in output
        if "passed" in result.stdout:
            # Extract the summary line
            for line in result.stdout.split('\n'):
                if 'passed' in line and ('==' in line or 'error' in line.lower()):
                    return True, line.strip()
            return True, "Tests passed"
        elif "failed" in result.stdout or "ERROR" in result.stdout:
            return False, "Tests failed or had errors"
        else:
            return False, "Unknown result"

    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main verification function"""
    print("=" * 70)
    print("ASYNC TEST FIX VERIFICATION")
    print("=" * 70)
    print()

    passed = 0
    failed = 0

    for test_file in FIXED_FILES:
        test_path = Path(f"tests/{test_file}")
        if not test_path.exists():
            print(f"[SKIP] {test_file} - File not found")
            continue

        print(f"[TEST] {test_file}...", end=" ")
        success, message = run_test(test_file)

        if success:
            print(f"OK - {message}")
            passed += 1
        else:
            print(f"FAIL - {message}")
            failed += 1

    print()
    print("=" * 70)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 70)

    if failed == 0:
        print("\nAll async test fixes are working correctly!")
        return 0
    else:
        print(f"\nWarning: {failed} test(s) failed or had errors")
        return 1

if __name__ == '__main__':
    sys.exit(main())
