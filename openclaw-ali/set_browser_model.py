#!/usr/bin/env python3
"""
在浏览器控制台中设置 OpenClaw 默认模型

使用方法：
1. 访问 https://112.126.61.223/#token=01d133a62e424e9ade0b59ac39db176fc8a2def6fd873f26
2. 按 F12 打开开发者工具
3. 切换到 Console（控制台）标签
4. 复制下面的代码并运行
"""

BROWSER_CONSOLE_CODE = """
// OpenClaw 浏览器端设置默认模型
console.log('设置 OpenClaw 默认模型为 zai/glm-4.7...');

// 尝试从 localStorage 读取设置
const settings = localStorage.getItem('openclaw_settings');
if (settings) {
    console.log('当前设置:', settings);
    const parsed = JSON.parse(settings);
    parsed.model = 'zai/glm-4.7';
    localStorage.setItem('openclaw_settings', JSON.stringify(parsed));
    console.log('✓ 已更新默认模型为 zai/glm-4.7');
    console.log('新设置:', JSON.stringify(parsed, null, 2));
} else {
    console.log('创建新的默认设置...');
    const newSettings = {
        model: 'zai/glm-4.7',
        reasoning: true
    };
    localStorage.setItem('openclaw_settings', JSON.stringify(newSettings));
    console.log('✓ 已创建默认设置，模型: zai/glm-4.7');
}

// 刷新页面
console.log('请刷新页面（F5 或 Ctrl+R）使设置生效');
"""

print("=" * 60)
print("  在浏览器中设置 OpenClaw 默认模型")
print("=" * 60)

print("\n【方法1：通过 UI 设置】")
print("1. 访问: https://112.126.61.223/#token=01d133a62e424e9ade0b59ac39db176fc8a2def6fd873f26")
print("2. 点击右上角设置按钮（齿轮图标）")
print("3. 在 Model/模型 下拉菜单中选择: zai/glm-4.7")
print("4. 保存设置")

print("\n【方法2：通过浏览器控制台】")
print("1. 访问 OpenClaw")
print("2. 按 F12 打开开发者工具")
print("3. 切换到 Console（控制台）标签")
print("4. 复制粘贴以下代码并回车:")
print("-" * 60)
print(BROWSER_CONSOLE_CODE)
print("-" * 60)
print("5. 刷新页面（F5）")

print("\n【方法3：清除浏览器缓存】")
print("如果以上方法都不行，尝试：")
print("1. 在浏览器中按 F12")
print("2. 右键点击刷新按钮")
print("3. 选择'清空缓存并硬性重新加载'")
print("4. 然后重新在设置中选择模型")

print("\n" + "=" * 60)
print("  原因说明")
print("=" * 60)
print("""
错误 "No API key found for provider 'anthropic'" 的原因：

• 服务器端配置正确：agent.json 使用 zai/glm-4.7
• 但浏览器端可能缓存了旧的默认模型（anthropic）
• 需要在浏览器中手动切换到 zai/glm-4.7

一旦设置成功，之后访问都会使用 zai/glm-4.7，无需重复设置。
""")
