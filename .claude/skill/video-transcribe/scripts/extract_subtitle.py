#!/usr/bin/env python3
"""
提取视频字幕
支持平台字幕，优先级：简体中文 > 繁体中文（转简体） > 英文
"""

import os
import yt_dlp
import opencc
from pathlib import Path
from cookies_helper import get_ydl_opts_with_cookies


# 繁体转简体转换器
converter = opencc.OpenCC('t2s')


def extract_subtitle(url, output_dir):
    """
    提取视频字幕

    Args:
        url: 视频链接
        output_dir: 输出目录（临时保存字幕文件）

    Returns:
        字幕文本内容，无字幕返回 None
    """
    # 字幕优先级
    subtitle_priority = [
        ('zh-Hans', '简体中文'),
        ('zh-CN', '简体中文'),
        ('zh-Hant', '繁体中文'),
        ('zh-TW', '繁体中文'),
        ('en', '英文'),
    ]

    try:
        # 获取基础配置
        base_opts = get_ydl_opts_with_cookies()

        # 获取可用字幕列表
        ydl_opts = {
            **base_opts,
            'listsubs': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subtitles = info.get('subtitles', {})
            automatic_captions = info.get('automatic_captions', {})

            print(f"可用字幕: {list(subtitles.keys())}")
            print(f"自动字幕: {list(automatic_captions.keys())}")

            # 合并字幕列表
            all_subtitles = {**subtitles, **automatic_captions}

            # 按优先级查找字幕
            selected_lang = None
            for lang_code, lang_name in subtitle_priority:
                if lang_code in all_subtitles:
                    selected_lang = lang_code
                    print(f"选择字幕语言: {lang_name} ({lang_code})")
                    break

            if not selected_lang:
                print("未找到可用的字幕")
                return None

            # 返回字幕信息而不是实际下载（避免文件名编码问题）
            return selected_lang, all_subtitles.get(selected_lang, {}).get('data', None)

    except Exception as e:
        print(f"提取字幕失败: {e}")
        return None


def parse_srt_file(srt_file):
    """
    解析 SRT 字幕文件

    Args:
        srt_file: SRT 文件路径

    Returns:
        纯文本字幕内容（移除时间戳）
    """
    text = []

    with open(srt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        # 跳过序号行（纯数字）
        if line.isdigit():
            continue
        # 跳过时间戳行
        if '-->' in line:
            continue
        # 跳过空行
        if not line:
            continue
        # 跳过 WebVTT 样式标签
        if line.startswith('WEBVTT'):
            continue
        # 移除 HTML 标签
        while '<' in line and '>' in line:
            start = line.find('<')
            end = line.find('>', start) + 1
            line = line[:start] + line[end:]
        # 移除常见的字幕样式
        line = line.replace('&nbsp;', ' ')
        line = line.replace('&lt;', '<')
        line = line.replace('&gt;', '>')
        line = line.replace('&amp;', '&')

        text.append(line)

    return '\n'.join(text)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("用法: python extract_subtitle.py <视频链接> [输出目录]")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './temp'

    result = extract_subtitle(url, output_dir)
    if result:
        print("字幕提取成功:")
        print(result[:500] + "..." if len(str(result)) > 500 else result)
    else:
        print("未找到字幕")
