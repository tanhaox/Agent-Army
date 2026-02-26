#!/usr/bin/env python3
"""
本地 AI 翻译模块
使用 Ollama 调用本地模型（如 Qwen、DeepSeek）
"""

import requests
import re


class OllamaTranslator:
    """Ollama 翻译器 - 调用本地 Ollama API"""

    def __init__(self, api_url='http://localhost:11434', model='qwen:1.8b'):
        """
        Args:
            api_url: Ollama API 地址
            model: 模型名称
        """
        self.api_url = api_url
        self.model = model

    def translate(self, text, source_lang='en', target_lang='zh'):
        """
        使用 Ollama 进行翻译

        Args:
            text: 待翻译的文本

        Returns:
            翻译后的文本
        """
        if not text or not text.strip():
            return text

        print(f"调用本地 AI 翻译... (模型: {self.model})")

        payload = {
            "model": self.model,
            "prompt": f"""请将以下文本翻译成简体中文。如果是中文内容则保持不变。
要求：
1. 保持段落结构
2. 保留原有的说话人标签（如"人物A:"）
3. 对于英文内容，先保留英文原文，然后换行提供中文翻译

文本内容：
{text}""",
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 256,
            "top_k": 40,
                "top_p": 0.9
            }
        }

        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result['response']
            elif response.status_code == 400:
                print(f"错误: {response.text[:200]}")
                return text
            else:
                print(f"翻译失败，状态码: {response.status_code}")
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


def translate_text(text, service='ollama', api_url='http://localhost:11434', model='qwen:1.8b'):
    """
    翻译文本

    Args:
        text: 待翻译的文本
        service: 翻译服务 ('ollama' 调用本地)
        api_url: Ollama API 地址
        model: 模型名称

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

    # 创建本地 AI 翻译器
    translator = OllamaTranslator(api_url=api_url, model=model)

    # 翻译
    result = translator.translate(text)

    return result


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python ollama_translate.py <文本文件> [API地址] [模型名称]")
        print("示例:")
        print("  python ollama_translate.py test.txt http://localhost:11434 qwen:1.8b")
        print("  python ollama_translate.py test.txt http://localhost:11434 huihui_ai/deepseek-r1:8b")
        sys.exit(1)

    text_file = sys.argv[1]
    api_url = sys.argv[2] if len(sys.argv) > 2 else 'http://localhost:11434'
    model_name = sys.argv[3] if len(sys.argv) > 3 else 'qwen:1.8b'

    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()

    result = translate_text(text, service='ollama', api_url=api_url, model=model_name)

    print("\n翻译结果:")
    print("=" * 50)
    print(result)
    print("=" * 50)

    # 保存结果
    output_file = text_file.replace('.txt', '_ollama_translated.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"\n翻译结果已保存到: {output_file}")
