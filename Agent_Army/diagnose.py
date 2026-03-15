"""
Agent Army v2.0 - 启动诊断脚本
检查所有必需的依赖和配置
"""

import sys
import subprocess
from pathlib import Path

# 设置控制台编码为 UTF-8（Windows）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"检查: {description}")
    print(f"命令: {cmd}")
    print('-'*60)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"[OK] 成功")
            if result.stdout.strip():
                print(f"输出: {result.stdout.strip()[:200]}")
            return True
        else:
            print(f"[FAIL] 失败 (错误代码: {result.returncode})")
            if result.stderr.strip():
                print(f"错误: {result.stderr.strip()[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] 超时")
        return False
    except Exception as e:
        print(f"[ERROR] 异常: {e}")
        return False

def main():
    print("="*60)
    print("  Agent Army v2.0 - 启动诊断")
    print("="*60)

    checks = [
        ("python --version", "Python 版本"),
        ("python -m pip --version", "pip 版本"),
        ("python -m streamlit --version", "Streamlit 版本"),
    ]

    results = []
    for cmd, desc in checks:
        result = run_command(cmd, desc)
        results.append((desc, result))

    # 检查关键文件
    print(f"\n{'='*60}")
    print("检查: 关键文件")
    print('-'*60)

    required_files = [
        ("web_app_v2.py", "主应用文件"),
        ("src/core/design_tokens.py", "Design Tokens"),
        ("src/core/pages_v2/agent_status_v3.py", "Agent状态页面v3"),
        ("src/core/pages_v2/dashboard_v2.py", "Dashboard页面"),
    ]

    for file_path, desc in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"[OK] {desc}: {file_path} ({size} bytes)")
        else:
            print(f"[FAIL] {desc}: {file_path} (文件不存在)")

    # 检查导入
    print(f"\n{'='*60}")
    print("检查: Python 模块导入")
    print('-'*60)

    try:
        sys.path.insert(0, str(Path.cwd()))
        from src.core.design_tokens import DesignTokens
        print("[OK] DesignTokens 导入成功")
    except Exception as e:
        print(f"[FAIL] DesignTokens 导入失败: {e}")

    try:
        from src.core.pages_v2.agent_status_v3 import render_agent_status_v3
        print("[OK] agent_status_v3 导入成功")
    except Exception as e:
        print(f"[FAIL] agent_status_v3 导入失败: {e}")

    try:
        from src.core.pages_v2.dashboard_v2 import render_dashboard
        print("[OK] dashboard_v2 导入成功")
    except Exception as e:
        print(f"[FAIL] dashboard_v2 导入失败: {e}")

    # 总结
    print(f"\n{'='*60}")
    print("  诊断总结")
    print('='*60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for desc, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {desc}")

    print(f"\n通过率: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] 所有基础检查通过！")
        print("\n下一步:")
        print("  运行启动脚本: start_web.bat")
        print("  或手动启动: python -m streamlit run web_app_v2.py")
        return 0
    else:
        print("\n[WARNING] 发现问题，请安装缺失的依赖:")
        print("  pip install streamlit pandas plotly")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        input("\n按回车键退出...")
        exit(exit_code)
    except Exception as e:
        print(f"\n[ERROR] 诊断脚本异常: {e}")
        input("\n按回车键退出...")
        exit(1)
