#!/usr/bin/env python3
"""
说话人分离模块
使用 pyannote.audio 区分对话人物
"""

import os
import torch
from pathlib import Path


def diarize_speakers(text, audio_path=None):
    """
    对文本进行说话人分离

    Args:
        text: 待处理的文本
        audio_path: 音频文件路径（可选，如果有音频可以进行更精确的分离）

    Returns:
        带说话人标签的文本
    """
    # 如果没有音频文件，使用简单规则进行分离
    if not audio_path or not os.path.exists(audio_path):
        print("无音频文件，使用规则进行说话人分离")
        return rule_based_diarization(text)

    # 尝试使用 pyannote.audio 进行精确分离
    try:
        print("使用 AI 进行说话人分离...")
        return ai_diarization(text, audio_path)
    except Exception as e:
        print(f"AI 说话人分离失败，使用规则分离: {e}")
        return rule_based_diarization(text)


def ai_diarization(text, audio_path):
    """
    使用 pyannote.audio 进行 AI 说话人分离

    注意：需要先在 Hugging Face 接受相关模型的用户协议
    """
    try:
        from pyannote.audio import Pipeline

        # 加载预训练模型
        # 注意：需要先接受用户协议并获取访问权限
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=True  # 需要 HF token
        )

        # 检测设备
        device = "cuda" if torch.cuda.is_available() else "cpu"
        pipeline.to(device)

        print("正在进行说话人分离（这可能需要一些时间）...")

        # 进行分离
        diarization = pipeline(audio_path)

        # 将分离结果应用到文本上
        result = apply_diarization_to_text(text, diarization)

        return result

    except ImportError:
        print("pyannote.audio 未安装或未配置")
        return rule_based_diarization(text)
    except Exception as e:
        print(f"AI 分离出错: {e}")
        return rule_based_diarization(text)


def apply_diarization_to_text(text, diarization):
    """
    将说话人分离结果应用到文本上

    这是一个简化版本，实际实现需要更复杂的对齐算法
    """
    # 计算说话人数量
    speakers = {segment.speaker for _, _, segment in diarization.itertracks(yield_label=True)}
    speaker_count = len(speakers)

    print(f"检测到 {speaker_count} 位说话人")

    # 这里需要将时间戳与文本对齐
    # 简化实现：按段落分配说话人
    paragraphs = text.split('\n\n')
    speaker_labels = ['人物A', '人物B', '人物C', '人物D', '人物E']

    result = []
    for i, para in enumerate(paragraphs):
        speaker = speaker_labels[i % len(speaker_labels)]
        result.append(f"{speaker}: {para.strip()}")

    return '\n\n'.join(result)


def rule_based_diarization(text):
    """
    基于规则的说话人分离

    使用简单的启发式规则区分不同说话人
    """
    print("使用规则进行说话人分离...")

    # 按段落分割文本
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    if len(paragraphs) <= 1:
        # 只有一段内容，不需要分离
        return text

    # 分析对话模式
    result = []
    speaker_labels = ['人物A', '人物B', '人物C', '人物D', '人物E']
    current_speaker = 0

    # 检测对话切换的指标
    def detect_speaker_change(prev_para, current_para):
        """检测是否应该切换说话人"""
        # 如果段落太短，可能是同一个人的连续话语
        if len(current_para) < 30:
            return False

        # 如果有明显的对话标记（如问号、引号等），可能需要切换
        if current_para.strip().endswith(('？', '?', '。', '.')):
            return True

        # 简单的启发式：长段落后可能切换
        if len(prev_para) > 100:
            return True

        return False

    # 为第一段分配说话人
    if paragraphs:
        result.append(f"{speaker_labels[0]}: {paragraphs[0]}")

    # 处理后续段落
    for i in range(1, len(paragraphs)):
        prev_para = paragraphs[i-1]
        current_para = paragraphs[i]

        # 检测是否需要切换说话人
        if detect_speaker_change(prev_para, current_para):
            current_speaker = (current_speaker + 1) % len(speaker_labels)

        result.append(f"{speaker_labels[current_speaker]}: {current_para}")

    return '\n\n'.join(result)


def is_dialogue(text):
    """
    检测文本是否是对话

    Args:
        text: 待检测的文本

    Returns:
        True 如果是对话，False 如果是独白
    """
    # 简单检测指标
    indicators = [
        # 检测问答模式
        ('？' in text or '?' in text) and len(text) > 200,
        # 检测引号使用
        text.count('"') >= 4 or text.count('"') >= 4 or text.count('"') >= 4,
        # 检测段落切换频率
        len([p for p in text.split('\n') if p.strip()]) > 3,
    ]

    # 如果有至少 2 个指标为 True，判定为对话
    return sum(indicators) >= 2


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python diarization.py <文本文件> [音频文件路径]")
        sys.exit(1)

    text_file = sys.argv[1]
    audio_path = sys.argv[2] if len(sys.argv) > 2 else None

    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()

    result = diarize_speakers(text, audio_path)

    print("\n说话人分离结果:")
    print("=" * 50)
    print(result)
    print("=" * 50)
