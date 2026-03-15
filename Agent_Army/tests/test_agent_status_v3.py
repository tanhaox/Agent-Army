"""
测试 Agent 状态页面 v3.0 扁平化版本
验证设计一致性和功能完整性
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试1: 验证所有必要的导入"""
    print("=" * 60)
    print("测试1: 验证所有必要的导入")
    print("=" * 60)

    try:
        from src.core.design_tokens import DesignTokens
        print("✅ DesignTokens 导入成功")
    except ImportError as e:
        print(f"❌ DesignTokens 导入失败: {e}")
        return False

    try:
        from src.core.global_styles import apply_global_styles
        print("✅ apply_global_styles 导入成功")
    except ImportError as e:
        print(f"❌ apply_global_styles 导入失败: {e}")
        return False

    try:
        from src.core.ui_components import create_metric_card, get_status_badge
        print("✅ ui_components 导入成功")
    except ImportError as e:
        print(f"❌ ui_components 导入失败: {e}")
        return False

    try:
        from src.core.pages_v2.agent_status_v3 import render_agent_status_v3, rgba
        print("✅ agent_status_v3 导入成功")
    except ImportError as e:
        print(f"❌ agent_status_v3 导入失败: {e}")
        return False

    print("\n✅ 所有导入测试通过！\n")
    return True

def test_design_tokens():
    """测试2: 验证 Design Tokens 配置"""
    print("=" * 60)
    print("测试2: 验证 Design Tokens 配置")
    print("=" * 60)

    from src.core.design_tokens import DesignTokens

    # 测试颜色
    colors_to_check = [
        ('PRIMARY', '#1E88E5'),
        ('SUCCESS', '#4CAF50'),
        ('WARNING', '#FF9800'),
        ('ERROR', '#F44336'),
        ('INFO', '#2196F3'),
        ('ARMY_INDUSTRY', '#2196F3'),
        ('ARMY_HOTSPOT', '#FF5722'),
        ('ARMY_STOCK', '#4CAF50'),
        ('ARMY_TARGET', '#FF9800'),
        ('ARMY_STRATEGY', '#9C27B0'),
        ('ARMY_VALIDATION', '#00BCD4'),
    ]

    print("检查颜色配置:")
    for color_name, expected_value in colors_to_check:
        actual_value = getattr(DesignTokens.Colors, color_name, None)
        if actual_value == expected_value:
            print(f"  ✅ Colors.{color_name} = {actual_value}")
        else:
            print(f"  ❌ Colors.{color_name} = {actual_value} (期望: {expected_value})")
            return False

    # 测试字体
    typography_to_check = [
        ('H1', '2.5rem'),
        ('H2', '2.0rem'),
        ('H3', '1.75rem'),
        ('H4', '1.5rem'),
        ('BODY', '1.0rem'),
        ('SMALL', '0.875rem'),
    ]

    print("\n检查字体配置:")
    for font_name, expected_value in typography_to_check:
        actual_value = getattr(DesignTokens.Typography, font_name, None)
        if actual_value == expected_value:
            print(f"  ✅ Typography.{font_name} = {actual_value}")
        else:
            print(f"  ❌ Typography.{font_name} = {actual_value} (期望: {expected_value})")
            return False

    # 测试间距
    spacing_to_check = [
        ('P_MD', '16px'),
        ('P_LG', '24px'),
        ('M_SM', '8px'),
    ]

    print("\n检查间距配置:")
    for spacing_name, expected_value in spacing_to_check:
        actual_value = getattr(DesignTokens.Spacing, spacing_name, None)
        if actual_value == expected_value:
            print(f"  ✅ Spacing.{spacing_name} = {actual_value}")
        else:
            print(f"  ❌ Spacing.{spacing_name} = {actual_value} (期望: {expected_value})")
            return False

    print("\n✅ 所有 Design Tokens 测试通过！\n")
    return True

def test_rgba_function():
    """测试3: 验证 rgba() 辅助函数"""
    print("=" * 60)
    print("测试3: 验证 rgba() 辅助函数")
    print("=" * 60)

    from src.core.pages_v2.agent_status_v3 import rgba

    # 测试用例
    test_cases = [
        ('#1E88E5', 0.1, 'rgba(30, 136, 229, 0.1)'),
        ('#4CAF50', 0.5, 'rgba(76, 175, 80, 0.5)'),
        ('#FF5722', 1.0, 'rgba(255, 87, 34, 1.0)'),
    ]

    print("检查 rgba() 函数:")
    for hex_color, alpha, expected in test_cases:
        result = rgba(hex_color, alpha)
        if result == expected:
            print(f"  ✅ rgba('{hex_color}', {alpha}) = {result}")
        else:
            print(f"  ❌ rgba('{hex_color}', {alpha}) = {result} (期望: {expected})")
            return False

    print("\n✅ rgba() 函数测试通过！\n")
    return True

def test_code_compliance():
    """测试4: 验证代码符合设计规范"""
    print("=" * 60)
    print("测试4: 验证代码符合设计规范")
    print("=" * 60)

    # 读取 agent_status_v3.py 文件
    v3_file = project_root / 'src' / 'core' / 'pages_v2' / 'agent_status_v3.py'
    with open(v3_file, 'r', encoding='utf-8') as f:
        code = f.read()

    # 检查关键函数和导入
    checks = [
        ('apply_global_styles', '应用全局样式'),
        ('DesignTokens.Colors', '使用颜色 Tokens'),
        ('DesignTokens.Typography', '使用字体 Tokens'),
        ('DesignTokens.Spacing', '使用间距 Tokens'),
        ('DesignTokens.Radius', '使用圆角 Tokens'),
        ('DesignTokens.Shadow', '使用阴影 Tokens'),
        ('ARMY_INDUSTRY', '军团主题色 - 产业分析'),
        ('ARMY_HOTSPOT', '军团主题色 - 热点捕捉'),
        ('ARMY_STOCK', '军团主题色 - 个股挖掘'),
        ('ARMY_TARGET', '军团主题色 - 目标预测'),
        ('ARMY_STRATEGY', '军团主题色 - 策略执行'),
        ('ARMY_VALIDATION', '军团主题色 - 结果验证'),
        ('rgba(', 'rgba() 辅助函数'),
        ('st.session_state[expand_', '展开/折叠状态管理'),
    ]

    print("检查代码符合性:")
    all_passed = True
    for check_str, description in checks:
        if check_str in code:
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ 缺少: {description}")
            all_passed = False

    # 检查不应该出现的旧代码
    bad_patterns = [
        ('st.info(', '原生 st.info() 组件'),
        ('🟢 🟡 🔴', '硬编码表情符号状态'),
        ('st.tabs(', '深层嵌套的标签页结构'),
    ]

    print("\n检查不应存在的旧模式:")
    for pattern, description in bad_patterns:
        if pattern in code:
            print(f"  ❌ 发现旧模式: {description}")
            all_passed = False
        else:
            print(f"  ✅ 无旧模式: {description}")

    if all_passed:
        print("\n✅ 代码符合性测试通过！\n")
    else:
        print("\n❌ 代码符合性测试失败！\n")

    return all_passed

def test_file_structure():
    """测试5: 验证文件结构"""
    print("=" * 60)
    print("测试5: 验证文件结构")
    print("=" * 60)

    files_to_check = [
        ('src/core/pages_v2/agent_status_v3.py', 'Agent状态页面v3'),
        ('src/core/design_tokens.py', 'Design Tokens'),
        ('src/core/global_styles.py', '全局样式'),
        ('src/core/ui_components.py', 'UI组件'),
        ('web_app_v2.py', '主应用文件'),
    ]

    print("检查文件存在性:")
    all_exist = True
    for file_path, description in files_to_check:
        full_path = project_root / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✅ {description}: {file_path} ({size} bytes)")
        else:
            print(f"  ❌ 文件不存在: {file_path}")
            all_exist = False

    if all_exist:
        print("\n✅ 文件结构测试通过！\n")
    else:
        print("\n❌ 文件结构测试失败！\n")

    return all_exist

def test_web_app_integration():
    """测试6: 验证 web_app_v2.py 集成"""
    print("=" * 60)
    print("测试6: 验证 web_app_v2.py 集成")
    print("=" * 60)

    # 读取 web_app_v2.py 文件
    web_app_file = project_root / 'web_app_v2.py'
    with open(web_app_file, 'r', encoding='utf-8') as f:
        code = f.read()

    # 检查是否使用新的 v3 版本
    checks = [
        ('from src.core.pages_v2.agent_status_v3 import render_agent_status_v3',
         '导入 agent_status_v3'),
        ('render_agent_status_v3()',
         '调用 render_agent_status_v3()'),
    ]

    print("检查 web_app_v2.py 集成:")
    all_passed = True
    for check_str, description in checks:
        if check_str in code:
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ 缺少: {description}")
            all_passed = False

    # 检查不应该使用的旧版本
    if 'from src.core.pages_v2.agent_status import render_agent_status' in code:
        print(f"  ❌ 仍在使用旧版本 agent_status.py")
        all_passed = False
    else:
        print(f"  ✅ 未使用旧版本 agent_status.py")

    if all_passed:
        print("\n✅ web_app_v2.py 集成测试通过！\n")
    else:
        print("\n❌ web_app_v2.py 集成测试失败！\n")

    return all_passed

def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("  Agent 状态页面 v3.0 - 扁平化版本测试")
    print("=" * 60)
    print("\n")

    tests = [
        ("导入测试", test_imports),
        ("Design Tokens 配置", test_design_tokens),
        ("rgba() 函数", test_rgba_function),
        ("代码符合性", test_code_compliance),
        ("文件结构", test_file_structure),
        ("web_app_v2.py 集成", test_web_app_integration),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行失败: {e}\n")
            results.append((test_name, False))

    # 输出总结
    print("=" * 60)
    print("  测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")

    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有测试通过！Agent状态页面v3.0已准备就绪！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查上述问题。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
