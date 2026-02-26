#!/usr/bin/env python3
"""
AI 翻译模块
使用免费 AI 服务进行翻译 (DeepSeek/豆包/Kimi)
"""

import re
import json
import requests
from pathlib import Path


class AITranslator:
    """AI 翻译器基类"""

    def translate(self, text, source_lang='en', target_lang='zh'):
        """翻译文本"""
        raise NotImplementedError


class DeepSeekTranslator(AITranslator):
    """DeepSeek 翻译器"""

    def __init__(self):
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.model = "deepseek-chat"
        self.api_key = None

    def translate(self, text, source_lang='en', target_lang='zh'):
        """使用 DeepSeek API 进行翻译"""
        if not self.api_key:
            import os
            self.api_key = os.getenv('DEEPSEEK_API_KEY')

        if not self.api_key:
            print("警告: 未设置 DEEPSEEK_API_KEY，跳过翻译")
            return text

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        prompt = f"""请将以下文本翻译成简体中文。如果是中文内容则保持不变。
要求：
1. 保持段落结构
2. 保留原有的说话人标签（如"人物A:"）
3. 对于英文内容，先保留英文原文，然后换行提供中文翻译

文本内容：
{text}"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 402:
                print("警告: DeepSeek API 余额不足或密钥无效，跳过翻译")
                return text  # 返回原文
            else:
                print(f"翻译失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text[:200]}")
                return text  # 失败时返回原文

        except Exception as e:
            print(f"翻译错误: {str(e)[:100]}")
            return text  # 错误时返回原文


class DoubaoTranslator(AITranslator):
    """豆包翻译器"""

    def __init__(self):
        self.api_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        self.model = "ep-20250201135848-5r4g2"
        self.api_key = None

    def translate(self, text, source_lang='en', target_lang='zh'):
        """使用豆包 API 进行翻译"""
        if not self.api_key:
            import os
            self.api_key = os.getenv('DOUBAO_API_KEY')

        if not self.api_key:
            print("警告: 未设置 DOUBAO_API_KEY，跳过翻译")
            return text

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        prompt = f"""请将以下文本翻译成简体中文。如果是中文内容则保持不变。
要求：
1. 保持段落结构
2. 保留原有的说话人标签（如"人物A:"）
3. 对于英文内容，先保留英文原文，然后换行提供中文翻译

文本内容：
{text}"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 402:
                print("警告: 豆包 API 余额不足或密钥无效，跳过翻译")
                return text
            else:
                print(f"翻译失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text[:200]}")
                return text

        except Exception as e:
            print(f"翻译错误: {str(e)[:100]}")
            return text


class KimiTranslator(AITranslator):
    """Kimi 翻译器"""

    def __init__(self):
        self.api_url = "https://api.moonshot.cn/v1/chat/completions"
        self.model = "moonshot-v1-8k"
        self.api_key = None

    def translate(self, text, source_lang='en', target_lang='zh'):
        """使用 Kimi API 进行翻译"""
        if not self.api_key:
            import os
            self.api_key = os.getenv('KIMI_API_KEY')

        if not self.api_key:
            print("警告: 未设置 KIMI_API_KEY，跳过翻译")
            return text

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        prompt = f"""请将以下文本翻译成简体中文。如果是中文内容则保持不变。
要求：
1. 保持段落结构
2. 保留原有的说话人标签（如"人物A:"）
3. 对于英文内容，先保留英文原文，然后换行提供中文翻译

文本内容：
{text}"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 402:
                print("警告: Kimi API 余额不足或密钥无效，跳过翻译")
                return text
            else:
                print(f"翻译失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text[:200]}")
                return text

        except Exception as e:
            print(f"翻译错误: {str(e)[:100]}")
            return text


def detect_language(text):
    """
    检测文本语言

    Args:
        text: 待检测的文本

    Returns:
        'en' 如果是英文，'zh' 如果是中文
    """
    # 简单检测：统计英文字符和中文字符的比例
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    total = chinese_chars + english_chars

    if total == 0:
        return 'unknown'

    # 如果中文字符占比超过 30%，认为是中文
    if chinese_chars / total > 0.3:
        return 'zh'
    else:
        return 'en'


def translate_text(text, service='deepseek'):
    """
    翻译文本

    Args:
        text: 待翻译的文本
        service: 翻译服务 (deepseek/doubao/kimi)

    Returns:
        翻译后的文本
    """
    if not text or not text.strip():
        return text

    # 检测语言
    lang = detect_language(text)

    print(f"检测到文本语言: {lang} {'中文' if lang == 'zh' else '英文'}")

    # 如果是中文，不需要翻译
    if lang == 'zh':
        print("文本为中文，跳过翻译")
        return text

    # 选择翻译器
    translator = None
    if service == 'deepseek':
        translator = DeepSeekTranslator()
    elif service == 'doubao':
        translator = DoubaoTranslator()
    elif service == 'kimi':
        translator = KimiTranslator()
    else:
        print(f"未知的翻译服务: {service}")
        return text

    # 翻译
    result = translator.translate(text)

    return result


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("用法: python translate.py <文本文件> [服务名称]")
        print("服务名称选项: deepseek, doubao, kimi")
        sys.exit(1)

    text_file = sys.argv[1]
    service_name = sys.argv[2] if len(sys.argv) > 2 else 'deepseek'

    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()

    result = translate_text(text, service_name)

    print("\n翻译结果:")
    print("=" * 50)
    print(result)
    print("=" * 50)

    # 保存结果
    output_file = text_file.replace('.txt', f'_{service_name}_translated.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"\n翻译结果已保存到: {output_file}")
