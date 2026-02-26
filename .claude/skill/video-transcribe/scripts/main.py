#!/usr/bin/env python3
"""
Video Transcribe - 从视频链接提取完整文稿
支持 YouTube、B站、今日头条、抖音
支持本地 AI 翻译（Ollama）
"""

import os
import sys
import argparse
from pathlib import Path

# 添加 scripts 目录到 Python 路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from cookies_helper import get_ydl_opts_with_cookies
from download_audio import download_audio
from extract_subtitle import extract_subtitle, converter
from transcribe import transcribe_audio
from diarization import diarize_speakers
from translate import translate_text

# 输出目录
OUTPUT_DIR = Path(r"C:\AI-Agent-Local\.claude\docs")
# 临时文件目录
TEMP_DIR = SCRIPT_DIR / "temp"


def setup_directories():
    """创建必要的目录"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_filename(title):
    """清理文件名，移除非法字符"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '_')
    # 限制文件名长度
    return title[:200]


def get_video_info(url):
    """获取视频信息"""
    import yt_dlp

    # 简单检查是否是 URL
    if not url or not url.startswith(('http://', 'https://')):
        return None

    # 获取带有 cookies 的配置
    base_opts = get_ydl_opts_with_cookies()

    with yt_dlp.YoutubeDL(base_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info
        except Exception as e:
            print(f"获取视频信息失败: {e}")
            return None


def process_video(url, translate_service='deepseek', use_local_ai=False):
    """
    处理视频，提取文稿

    Args:
        url: 视频链接
        translate_service: 翻译服务 (deepseek/doubao/kimi/ollama)
        use_local_ai: 是否使用本地 AI (Ollama)
    """
    setup_directories()

    print(f"正在处理视频: {url}")

    # 1. 获取视频信息
    print("获取视频信息...")
    info = get_video_info(url)
    if not info:
        print("无法获取视频信息")
        return None

    title = info.get('title', 'unknown_title')
    video_id = info.get('id', 'video')
    safe_title = sanitize_filename(title)
    print(f"视频标题: {title}")
    print(f"视频ID: {video_id}")

    # 2. 尝试提取字幕
    print("\n检查是否有字幕...")
    subtitle_result = extract_subtitle(url, TEMP_DIR)

    subtitle_text = None

    if subtitle_result:
        # extract_subtitle 返回 (selected_lang, subtitle_data)
        selected_lang, subtitle_data = subtitle_result

        if subtitle_data:
            # 解析字幕数据
            subtitle_text = parse_subtitle_data(subtitle_data)

            # 如果是繁体中文，转换为简体
            if selected_lang in ['zh-Hant', 'zh-TW']:
                subtitle_text = converter.convert(subtitle_text)
                print("繁体中文已转换为简体中文")

    # 3. 如果没有字幕，下载音频并进行语音识别
    if not subtitle_text:
        print("未找到字幕，开始下载音频...")
        audio_path = download_audio(url, TEMP_DIR)

        if audio_path and os.path.exists(audio_path):
            print("音频下载完成，开始语音识别...")
            subtitle_text = transcribe_audio(audio_path)

            # 删除临时音频文件
            try:
                os.remove(audio_path)
                print("临时音频文件已清理")
            except Exception as e:
                print(f"清理音频文件失败: {e}")
        else:
            print("音频下载失败")
            return None

    if not subtitle_text:
        print("无法获取字幕或进行语音识别")
        return None

    # 4. 说话人分离
    print("\n进行说话人分离...")
    text_with_speakers = diarize_speakers(subtitle_text, audio_path)

    # 5. 翻译（如果需要）
    if use_local_ai:
        print("\n使用本地 AI (Ollama) 翻译...")
        # 导入本地 AI 翻译
        from ollama_translate import translate_text as ollama_translate_text

        translated_text = ollama_translate_text(text_with_speakers, service='ollama', api_url='http://localhost:11434', model='qwen:1.8b')
    else:
        print("\n检查是否需要翻译...")
        translated_text = translate_text(text_with_speakers, translate_service)

    # 6. 保存输出文件
    output_path = OUTPUT_DIR / f"{safe_title}.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(translated_text)

    print(f"\n文稿已保存到: {output_path}")
    return output_path


def parse_subtitle_data(data):
    """解析字幕数据"""
    if isinstance(data, str):
        # 如果是字符串，直接返回
        lines = data.split('\n')
        result = []
        for line in lines:
            line = line.strip()
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
            if line:
                result.append(line)
        return '\n'.join(result)
    elif isinstance(data, list):
        # 如果是列表（SRT 格式）
        result = []
        for item in data:
            if isinstance(item, dict):
                line = item.get('text', '')
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
                if line.strip():
                    result.append(line.strip())
            elif isinstance(item, str) and item.strip():
                result.append(item.strip())
        return '\n'.join(result)
    else:
        return str(data) if data else ''


def main():
    parser = argparse.ArgumentParser(description='从视频链接提取完整文稿')
    parser.add_argument('url', help='视频链接')
    parser.add_argument('--translate', '-t',
                       choices=['deepseek', 'doubao', 'kimi', 'ollama'],
                       default='deepseek',
                       help='翻译服务 (默认: deepseek，ollama 为本地 AI)')
    parser.add_argument('--no-translate', action='store_true',
                       help='禁用翻译')

    args = parser.parse_args()

    translate_service = None if args.no_translate else args.translate
    use_local_ai = (args.translate == 'ollama')

    result = process_video(args.url, translate_service, use_local_ai)

    if result:
        print(f"\n[OK] 处理完成！")
        print(f"文件位置: {result}")
        return 0
    else:
        print("\n[FAIL] 处理失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
