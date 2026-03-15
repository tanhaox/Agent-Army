#!/usr/bin/env python3
"""
查看当前浏览器的设备 ID
使用说明：在 OpenClaw 网页中打开浏览器控制台（F12），运行以下代码查看设备 ID
"""

# 在浏览器控制台（Console）中运行这段代码：
BROWSER_CONSOLE_CODE = """
// 查看 OpenClaw 设备 ID
console.log('OpenClaw Device ID:', localStorage.getItem('openclaw_device_id'));
console.log('All OpenClaw data:', localStorage);

// 如果没有设备 ID，会生成一个新的
if (!localStorage.getItem('openclaw_device_id')) {
    const deviceId = crypto.randomUUID();
    localStorage.setItem('openclaw_device_id', deviceId);
    console.log('Generated new Device ID:', deviceId);
}
"""

print("=" * 60)
print("  如何查看你的浏览器设备 ID")
print("=" * 60)

print("\n【步骤1】访问 OpenClaw：")
print("  https://112.126.61.223/#token=01d133a62e424e9ade0b59ac39db176fc8a2def6fd873f26")

print("\n【步骤2】打开浏览器开发者工具：")
print("  Windows/Linux: 按 F12 或 Ctrl+Shift+I")
print("  Mac: 按 Cmd+Option+I")

print("\n【步骤3】切换到 Console（控制台）标签")

print("\n【步骤4】复制粘贴以下代码并回车：")
print("-" * 60)
print(BROWSER_CONSOLE_CODE)
print("-" * 60)

print("\n【步骤5】查看输出的 Device ID")
print("  这就是你当前浏览器的唯一标识符")

print("\n" + "=" * 60)
print("  提示")
print("=" * 60)
print("""
• 清除浏览器数据后，Device ID 会重新生成
• 每个浏览器（Chrome/Safari/Edge）都有不同的 Device ID
• 同一浏览器的无痕模式也有独立的 Device ID
""")
