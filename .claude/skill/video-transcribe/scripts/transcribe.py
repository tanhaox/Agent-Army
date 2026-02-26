#!/usr/bin/env python3
"""
语音识别模块
使用 Whisper 进行语音识别
"""

import os
import whisper
import torch


def transcribe_audio(audio_path, model_size='base'):
    """
    使用 Whisper 进行语音识别

    Args:
        audio_path: 音频文件路径
        model_size: Whisper 模型大小 (tiny/base/small/medium/large)

    Returns:
        识别后的文本
    """
    # 设置 FFmpeg 路径环境变量
    ffmpeg_path = r"C:\Users\tanha\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"
    if os.path.exists(ffmpeg_path):
        os.environ['PATH'] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ.get('PATH', '')
    elif os.path.exists("C:/ffmpeg/bin/ffmpeg.exe"):
        os.environ['PATH'] = "C:/ffmpeg/bin" + os.pathsep + os.environ.get('PATH', '')

    print(f"加载 Whisper 模型 ({model_size})...")

    # 检查是否有可用的 GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"使用设备: {device}")

    try:
        # 加载模型
        model = whisper.load_model(model_size, device=device)

        print("正在识别音频...")
        result = model.transcribe(
            audio_path,
            language=None,  # 自动检测语言
            task='transcribe',
            word_timestamps=False,
            verbose=False
        )

        text = result['text']
        detected_lang = result.get('language', 'unknown')

        print(f"识别完成！检测到的语言: {detected_lang}")
        print(f"文本长度: {len(text)} 字符")

        return text.strip()

    except Exception as e:
        print(f"语音识别失败: {e}")
        return None


def detect_language(audio_path):
    """
    检测音频语言

    Args:
        audio_path: 音频文件路径

    Returns:
        检测到的语言代码
    """
    print("检测音频语言...")

    try:
        model = whisper.load_model('tiny')
        audio = whisper.load_audio(audio_path)
        audio = whisper.pad_or_trim(audio)

        # 计算对数梅尔频谱图
        mel = whisper.log_mel_spectrogram(audio).to(model.device)

        # 检测语言
        _, probs = model.detect_language(mel)
        detected_lang = max(probs, key=probs.get)

        print(f"检测到的语言: {detected_lang}")
        return detected_lang

    except Exception as e:
        print(f"语言检测失败: {e}")
        return None


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("用法: python transcribe.py <音频文件路径> [模型大小]")
        print("模型大小选项: tiny, base, small, medium, large")
        sys.exit(1)

    audio_path = sys.argv[1]
    model_size = sys.argv[2] if len(sys.argv) > 2 else 'base'

    if not os.path.exists(audio_path):
        print(f"错误: 音频文件不存在: {audio_path}")
        sys.exit(1)

    result = transcribe_audio(audio_path, model_size)

    if result:
        print("\n识别结果:")
        print("=" * 50)
        print(result)
        print("=" * 50)
    else:
        print("识别失败")
