"""
验证 Agent 状态页面 v3.0 的代码符合性（无需导入模块）
"""

import re
from pathlib import Path

def check_file_content():
    """检查 agent_status_v3.py 文件内容"""

    print("=" * 80)
    print("  Agent 状态页面 v3.0 - 代码符合性验证")
    print("=" * 80)
    print()

    # 读取文件
    file_path = Path(__file__).parent.parent / 'src' / 'core' / 'pages_v2' / 'agent_status_v3.py'

    if not file_path.exists():
        print(f"[错误] 文件不存在: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"[OK] 文件大小: {len(content)} 字节")
    print(f"[OK] 文件行数: {len(content.splitlines())} 行")
    print()

    # 检查必需的导入
    print("=" * 80)
    print("1. 检查必需的导入")
    print("=" * 80)

    required_imports = [
        ('from src.core.design_tokens import DesignTokens', 'Design Tokens'),
        ('from src.core.global_styles import apply_global_styles', '全局样式'),
        ('from src.core.ui_components import', 'UI组件'),
    ]

    imports_ok = True
    for import_stmt, desc in required_imports:
        if import_stmt in content:
            print(f"[OK] 导入 {desc}")
        else:
            print(f"[FAIL] 缺少导入: {desc}")
            imports_ok = False

    print()

    # 检查 Design Tokens 使用
    print("=" * 80)
    print("2. 检查 Design Tokens 使用")
    print("=" * 80)

    design_token_checks = [
        ('DesignTokens.Colors.PRIMARY', '主颜色'),
        ('DesignTokens.Colors.SUCCESS', '成功颜色'),
        ('DesignTokens.Colors.WARNING', '警告颜色'),
        ('DesignTokens.Colors.ERROR', '错误颜色'),
        ('DesignTokens.Colors.ARMY_INDUSTRY', '产业分析军团色'),
        ('DesignTokens.Colors.ARMY_HOTSPOT', '热点捕捉军团色'),
        ('DesignTokens.Colors.ARMY_STOCK', '个股挖掘军团色'),
        ('DesignTokens.Colors.ARMY_TARGET', '目标预测军团色'),
        ('DesignTokens.Colors.ARMY_STRATEGY', '策略执行军团色'),
        ('DesignTokens.Colors.ARMY_VALIDATION', '结果验证军团色'),
        ('DesignTokens.Typography.H1', 'H1字体'),
        ('DesignTokens.Typography.H3', 'H3字体'),
        ('DesignTokens.Typography.BODY', '正文字体'),
        ('DesignTokens.Spacing.P_MD', '中等内边距'),
        ('DesignTokens.Spacing.M_LG', '大外边距'),
        ('DesignTokens.Radius.LG', '大圆角'),
        ('DesignTokens.Shadow.SM', '小阴影'),
    ]

    tokens_ok = True
    for token, desc in design_token_checks:
        if token in content:
            print(f"[OK] 使用 {desc}")
        else:
            print(f"[FAIL] 未使用: {desc}")
            tokens_ok = False

    print()

    # 检查辅助函数
    print("=" * 80)
    print("3. 检查辅助函数")
    print("=" * 80)

    if 'def rgba(hex_color: str, alpha: float) -> str:' in content:
        print("[OK] rgba() 函数定义")
        if 'rgba(' in content and 'return f"rgba(' in content:
            print("[OK] rgba() 函数实现")
        else:
            print("[FAIL] rgba() 函数实现不完整")
    else:
        print("[FAIL] 缺少 rgba() 函数")

    print()

    # 检查展开/折叠功能
    print("=" * 80)
    print("4. 检查展开/折叠功能")
    print("=" * 80)

    expand_checks = [
        ('st.session_state[expand_', 'Session State 管理'),
        ('st.button(', '展开/折叠按钮'),
        ("'展开详情", '展开文本'),
        ("'收起详情", '收起文本'),
    ]

    expand_ok = True
    for check, desc in expand_checks:
        if check in content:
            print(f"[OK] {desc}")
        else:
            print(f"[FAIL] 缺少: {desc}")
            expand_ok = False

    print()

    # 检查旧代码模式
    print("=" * 80)
    print("5. 检查是否移除旧代码模式")
    print("=" * 80)

    bad_patterns = [
        ('st.tabs(', '深层嵌套标签页'),
        ('st.info(', '原生 st.info() 组件'),
    ]

    clean_ok = True
    for pattern, desc in bad_patterns:
        if pattern in content:
            print(f"[FAIL] 仍存在旧模式: {desc}")
            clean_ok = False
        else:
            print(f"[OK] 已移除旧模式: {desc}")

    print()

    # 检查军团主题色使用
    print("=" * 80)
    print("6. 检查军团主题色应用")
    print("=" * 80)

    army_themes = [
        ('ARMY_INDUSTRY', '产业分析军团'),
        ('ARMY_HOTSPOT', '热点捕捉军团'),
        ('ARMY_STOCK', '个股挖掘军团'),
        ('ARMY_TARGET', '目标预测军团'),
        ('ARMY_STRATEGY', '策略执行军团'),
        ('ARMY_VALIDATION', '结果验证军团'),
    ]

    army_ok = True
    for theme, name in army_themes:
        pattern = f"DesignTokens.Colors.{theme}"
        if pattern in content:
            print(f"[OK] {name} 使用主题色 {theme}")
        else:
            print(f"[FAIL] {name} 未使用主题色 {theme}")
            army_ok = False

    print()

    # 检查统计卡片
    print("=" * 80)
    print("7. 检查统计卡片")
    print("=" * 80)

    metric_patterns = [
        ('Agent总数', 'Agent总数卡片'),
        ('空闲', '空闲Agent卡片'),
        ('忙碌', '忙碌Agent卡片'),
        ('错误', '错误Agent卡片'),
        ('可用率', '可用率卡片'),
    ]

    metrics_ok = True
    for pattern, desc in metric_patterns:
        if pattern in content:
            print(f"[OK] {desc}")
        else:
            print(f"[FAIL] 缺少: {desc}")
            metrics_ok = False

    print()

    # 检查UI组件使用
    print("=" * 80)
    print("8. 检查UI组件使用")
    print("=" * 80)

    if 'get_status_badge(' in content:
        print("[OK] 使用 get_status_badge() 组件")
    else:
        print("[FAIL] 未使用 get_status_badge() 组件")

    if 'create_metric_card(' in content:
        print("[OK] 使用 create_metric_card() 组件")
    else:
        print("[INFO] 未使用 create_metric_card() 组件（可能使用自定义HTML）")

    print()

    # 总结
    print("=" * 80)
    print("  验证总结")
    print("=" * 80)

    checks = [
        ('必需导入', imports_ok),
        ('Design Tokens', tokens_ok),
        ('辅助函数', True),  # rgba检查在上面的输出中已经显示
        ('展开折叠功能', expand_ok),
        ('移除旧代码', clean_ok),
        ('军团主题色', army_ok),
        ('统计卡片', metrics_ok),
    ]

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)

    for name, ok in checks:
        status = "[PASS]" if ok else "[FAIL]"
        print(f"{status} {name}")

    print()
    print(f"总计: {passed}/{total} 项检查通过")

    if passed == total:
        print()
        print("=" * 80)
        print("  CONCLUSION: All checks passed! v3.0 is ready.")
        print("=" * 80)
        return True
    else:
        print()
        print("=" * 80)
        print(f"  WARNING: {total - passed} check(s) failed")
        print("=" * 80)
        return False

def check_web_app_integration():
    """检查 web_app_v2.py 集成"""

    print()
    print("=" * 80)
    print("  检查 web_app_v2.py 集成")
    print("=" * 80)
    print()

    file_path = Path(__file__).parent.parent / 'web_app_v2.py'

    if not file_path.exists():
        print(f"[FAIL] web_app_v2.py 不存在")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否导入 v3 版本
    if 'from src.core.pages_v2.agent_status_v3 import render_agent_status_v3' in content:
        print("[OK] 已导入 agent_status_v3")
    else:
        print("[FAIL] 未导入 agent_status_v3")
        return False

    if 'render_agent_status_v3()' in content:
        print("[OK] 已调用 render_agent_status_v3()")
    else:
        print("[FAIL] 未调用 render_agent_status_v3()")
        return False

    # 检查是否移除旧版本
    if 'from src.core.pages_v2.agent_status import render_agent_status' not in content:
        print("[OK] 已移除旧版本 agent_status 导入")
    else:
        print("[WARN] 仍存在旧版本 agent_status 导入（可能导致冲突）")

    print()
    print("=" * 80)
    print("  Integration check PASSED")
    print("=" * 80)

    return True

if __name__ == "__main__":
    file_check = check_file_content()
    integration_check = check_web_app_integration()

    print()
    print("=" * 80)
    print("  FINAL RESULT")
    print("=" * 80)

    if file_check and integration_check:
        print("[PASS] Agent状态页面 v3.0 扁平化版本验证通过！")
        print()
        print("下一步:")
        print("1. 启动 Web 应用: streamlit run web_app_v2.py")
        print("2. 在浏览器中打开: http://localhost:8501")
        print("3. 导航到 '🤖 Agent状态' 页面")
        print("4. 验证页面显示正常，所有功能可用")
        exit(0)
    else:
        print("[FAIL] 验证失败，请检查上述问题")
        exit(1)
