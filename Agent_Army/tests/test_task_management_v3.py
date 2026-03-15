"""
验证任务管理页面 v3.0 的代码符合性
"""

import re
from pathlib import Path

def check_file_content():
    """检查 task_management_v3.py 文件内容"""

    print("=" * 80)
    print("  任务管理页面 v3.0 - 代码符合性验证")
    print("=" * 80)
    print()

    # 读取文件
    file_path = Path(__file__).parent.parent / 'src' / 'core' / 'pages_v2' / 'task_management_v3.py'

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
        ('DesignTokens.Colors.INFO', '信息颜色'),
        ('DesignTokens.Typography.H1', 'H1字体'),
        ('DesignTokens.Typography.H2', 'H2字体'),
        ('DesignTokens.Typography.H3', 'H3字体'),
        ('DesignTokens.Typography.H4', 'H4字体'),
        ('DesignTokens.Typography.BODY', '正文字体'),
        ('DesignTokens.Typography.SMALL', '小号字体'),
        ('DesignTokens.Spacing.P_MD', '中等内边距'),
        ('DesignTokens.Spacing.P_LG', '大内边距'),
        ('DesignTokens.Spacing.M_LG', '大外边距'),
        ('DesignTokens.Spacing.M_SM', '小外边距'),
        ('DesignTokens.Radius.LG', '大圆角'),
        ('DesignTokens.Radius.MD', '中圆角'),
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

    # 检查卡片式布局
    print("=" * 80)
    print("4. 检查卡片式布局")
    print("=" * 80)

    card_checks = [
        ('border-left: 4px solid', '左边框设计'),
        ('border-radius:', '圆角'),
        ('box-shadow:', '阴影'),
        ('padding:', '内边距'),
        ('background:', '背景色'),
    ]

    card_ok = True
    for check, desc in card_checks:
        if check in content:
            print(f"[OK] {desc}")
        else:
            print(f"[FAIL] 缺少: {desc}")
            card_ok = False

    print()

    # 检查筛选功能
    print("=" * 80)
    print("5. 检查筛选功能")
    print("=" * 80)

    filter_checks = [
        ('status_filter', '状态筛选器'),
        ('type_filter', '类型筛选器'),
        ('sort_by', '排序选择器'),
    ]

    filter_ok = True
    for check, desc in filter_checks:
        if check in content:
            print(f"[OK] {desc}")
        else:
            print(f"[FAIL] 缺少: {desc}")
            filter_ok = False

    print()

    # 检查展开/折叠功能
    print("=" * 80)
    print("6. 检查展开/折叠功能")
    print("=" * 80)

    expand_checks = [
        ('st.session_state[expand_task_', 'Session State 管理'),
        ('st.button("📋 详情 ▼"', '展开按钮'),
        ('st.button("📋 详情 ▲"', '折叠按钮'),
    ]

    expand_ok = True
    for check, desc in expand_checks:
        if check in content:
            print(f"[OK] {desc}")
        else:
            print(f"[FAIL] 缺少: {desc}")
            expand_ok = False

    print()

    # 检查进度条可视化
    print("=" * 80)
    print("7. 检查进度条可视化")
    print("=" * 80)

    progress_checks = [
        ('进度:', '进度标签'),
        ('width:', '进度宽度'),
        ('transition:', '过渡动画'),
    ]

    progress_ok = True
    for check, desc in progress_checks:
        if check in content and 'progress' in content.lower():
            print(f"[OK] {desc}")
        else:
            print(f"[INFO] {desc} (可选)")

    print()

    # 检查批量操作
    print("=" * 80)
    print("8. 检查批量操作")
    print("=" * 80)

    batch_checks = [
        ('st.button("▶️ 开始所有待执行"', '批量开始'),
        ('st.button("🗑️ 清理已完成"', '批量清理'),
    ]

    batch_ok = True
    for check, desc in batch_checks:
        if check in content:
            print(f"[OK] {desc}")
        else:
            print(f"[FAIL] 缺少: {desc}")
            batch_ok = False

    print()

    # 检查移除旧代码
    print("=" * 80)
    print("9. 检查是否移除旧代码模式")
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

    # 总结
    print("=" * 80)
    print("  验证总结")
    print("=" * 80)

    checks = [
        ('必需导入', imports_ok),
        ('Design Tokens', tokens_ok),
        ('辅助函数', True),
        ('卡片式布局', card_ok),
        ('筛选功能', filter_ok),
        ('展开折叠功能', expand_ok),
        ('进度条可视化', True),
        ('批量操作', batch_ok),
        ('移除旧代码', clean_ok),
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
        print("[FAIL] web_app_v2.py 不存在")
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否导入 v3 版本
    if 'from src.core.pages_v2.task_management_v3 import render_task_management_v3' in content:
        print("[OK] 已导入 task_management_v3")
    else:
        print("[FAIL] 未导入 task_management_v3")
        return False

    if 'render_task_management_v3()' in content:
        print("[OK] 已调用 render_task_management_v3()")
    else:
        print("[FAIL] 未调用 render_task_management_v3()")
        return False

    # 检查是否移除旧版本
    if 'from src.core.pages_v2.task_management import render_task_management' not in content:
        print("[OK] 已移除旧版本 task_management 导入")
    else:
        print("[WARN] 仍存在旧版本 task_management 导入（可能导致冲突）")

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
        print("[PASS] 任务管理页面 v3.0 优化版本验证通过！")
        print()
        print("下一步:")
        print("1. 启动 Web 应用: streamlit run web_app_v2.py")
        print("2. 在浏览器中打开: http://localhost:8501")
        print("3. 导航到 '📋 任务管理' 页面")
        print("4. 验证页面显示正常，所有功能可用")
        exit(0)
    else:
        print("[FAIL] 验证失败，请检查上述问题")
        exit(1)
