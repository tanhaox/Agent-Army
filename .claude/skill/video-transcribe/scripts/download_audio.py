#!/usr/bin/env python3
"""
下载视频音频文件
使用 yt-dlp 下载最低质量的音频
"""

import os
import yt_dlp
from pathlib import Path
from cookies_helper import get_ydl_opts_with_cookies


def download_audio(url, output_dir):
    """
    下载视频的音频部分

    Args:
        url: 视频链接
        output_dir: 输出目录

    Returns:
        音频文件路径，失败返回 None
    """
    output_path = os.path.join(output_dir, '%(id)s.%(ext)s')  # 使用视频 ID

    # 获取基础配置
    base_opts = get_ydl_opts_with_cookies()

    # 添加音频下载配置
    ydl_opts = {
        **base_opts,
        'format': 'worstaudio/bestaudio',  # 最低质量的音频
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 获取视频信息
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'unknown')

            print(f"正在下载: {title}")

            # 下载音频
            ydl.download([url])

            # 查找生成的音频文件
            audio_extensions = ['*.m4a', '*.mp4', '*.webm', '*.wav']
            audio_files = []
            for ext in audio_extensions:
                audio_files.extend(list(Path(output_dir).glob(ext)))

            if audio_files:
                # 返回最新的音频文件
                audio_file = max(audio_files, key=os.path.getctime)
                # 等待文件完全写入
                import time
                time.sleep(1)
                return str(audio_file)
            else:
                print("未找到下载的音频文件")
                return None

    except Exception as e:
        print(f"下载音频失败: {e}")
        return None


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("用法: python download_audio.py <视频链接> [输出目录]")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './temp'

    result = download_audio(url, output_dir)
    if result:
        print(f"音频已保存到: {result}")
    else:
        print("下载失败")
