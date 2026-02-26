#!/usr/bin/env python3
"""
Cookies 管理器
处理 YouTube 登录验证问题
"""

import os
from pathlib import Path


def get_ydl_opts_with_cookies():
    """
    获取带有 cookies 配置的 yt-dlp 选项
    按优先级尝试多种方法

    Returns:
        dict: yt-dlp 配置选项
    """
    opts = {
        'quiet': True,
        'no_warnings': True,
        # 添加常用绕过参数
        'nocheckcertificate': True,  # 忽略证书检查
        'ignoreerrors': True,  # 忽略错误继续下载
        'extract_flat': False,
        # 设置 User-Agent
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        },
    }

    # 方案 1: 使用 cookies.txt 文件
    cookies_file = Path(__file__).parent.parent / "cookies.txt"
    if cookies_file.exists():
        print(f"使用 cookies.txt 文件")
        opts['cookiefile'] = str(cookies_file)
        return opts

    # 方案 2: 尝试从多个浏览器获取 cookies
    browsers = ['chrome', 'edge', 'brave', 'firefox', 'opera']
    for browser in browsers:
        opts['cookiesfrombrowser'] = (browser,)

        # 尝试测试是否可用
        import yt_dlp
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                # 尝试获取一个简单的 YouTube 页面
                test_url = "https://www.youtube.com"
                ydl.extract_info(test_url, download=False)
                print(f"成功从 {browser} 获取 cookies")
                return opts
        except Exception as e:
            error_msg = str(e)
            # 如果是常见的 cookies 错误，跳过
            if 'decrypt' in error_msg or 'cookie' in error_msg.lower():
                print(f"从 {browser} 获取 cookies 失败 (需要导出 cookies.txt)")
                continue
            # 其他错误可能是正常的，说明 cookies 工作但需要更多配置
            print(f"从 {browser} 测试出错，尝试使用...")
            return opts

    # 方案 3: 不使用 cookies（某些视频可能不需要）
    print("无法获取 cookies，尝试不使用 cookies 继续（可能仅支持部分视频）")
    if 'cookiesfrombrowser' in opts:
        del opts['cookiesfrombrowser']
    return opts


def create_cookies_guide():
    """
    生成 cookies.txt 导出指南
    """
    guide = """
========================================
YouTube Cookies 快速设置指南
========================================

由于 YouTube 的机器人验证，需要使用 cookies。

【最简单的 3 步方法】
----------------------------------------
步骤 1: 安装浏览器插件
在 Chrome/Edge 中安装:
- 搜索: "Get cookies.txt LOCA"
- 或搜索: "cookies.txt"

步骤 2: 登录 YouTube
打开 https://www.youtube.com 并登录

步骤 3: 导出 cookies
点击插件图标 -> Export -> 保存为 cookies.txt

步骤 4: 放置文件
复制到: C:\\AI-Agent-Local\\.claude\\skill\\video-transcribe\\cookies.txt

========================================
完成后重新运行程序即可！
========================================
"""
    print(guide)


if __name__ == '__main__':
    create_cookies_guide()
