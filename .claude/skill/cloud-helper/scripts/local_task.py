#!/usr/bin/env python3
"""
本地任务处理模块
使用本地 Ollama 零 Token 处理更多类型任务
"""

import os
import sys
import argparse
from pathlib import Path


class LocalTaskHandler:
    """本地任务处理器"""

    def __init__(self):
        # 初始化本地 AI 配置
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'qwen:1.8b')

    def translate(self, text):
        """本地翻译（零 Token）"""
        import requests

        print(f"[本地] 开始翻译... (模型: {self.ollama_model})")

        payload = {
            "model": self.ollama_model,
            "prompt": f"""请将以下文本翻译成简体中文。

文本内容：
{text}""",
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result['response']
            else:
                print(f"[本地] 翻译失败: {response.status_code}")
                return text

        except Exception as e:
            print(f"[本地] 翻译错误: {str(e)}")
            return text

    def summarize(self, text):
        """本地摘要生成（零 Token）"""
        import requests

        print(f"[本地] 生成摘要...")

        payload = {
            "model": self.ollama_model,
            "prompt": f"""请为以下文本生成摘要，要求简洁清晰。

文本内容：
{text}

请用中文输出摘要。""",
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result['response']
            else:
                print(f"[本地] 摘要失败: {response.status_code}")
                return text

        except Exception as e:
            print(f"[本地] 摘要错误: {str(e)}")
            return text

    def extract_info(self, text):
        """提取关键信息（零 Token）"""
        import requests

        print(f"[本地] 提取关键信息...")

        payload = {
            "model": self.ollama_model,
            "prompt": f"""请从以下文本中提取关键信息（如：标题、要点、关键词）。

文本内容：
{text}

请用结构化的方式输出，例如 JSON 格式。""",
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result['response']
            else:
                print(f"[本地] 信息提取失败: {response.status_code}")
                return text

        except Exception as e:
            print(f"[本地] 信息提取错误: {str(e)}")
            return text

    def fix_format(self, text):
        """格式修复（零 Token）"""
        import requests

        print(f"[本地] 修复格式...")

        payload = {
            "model": self.ollama_model,
            "prompt": f"""请修复以下文本的格式问题，保持原文语义。

文本内容：
{text}""",
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result['response']
            else:
                print(f"[本地] 格式修复失败: {response.status_code}")
                return text

        except Exception as e:
            print(f"[本地] 格式修复错误: {str(e)}")
            return text

    def rewrite(self, text):
        """扩写（零 Token）"""
        import requests

        print(f"[本地] 扩写内容...")

        payload = {
            "model": self.ollama_model,
            "prompt": f"""请将以下文本扩写成更详细的版本。

文本内容：
{text}

请保持原文结构，但增加细节和深度。""",
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result['response']
            else:
                print(f"[本地] 扩写失败: {response.status_code}")
                return text

        except Exception as e:
            print(f"[本地] 扩写错误: {str(e)}")
            return text

    def compress(self, text):
        """压缩（零 Token）"""
        import requests

        print(f"[本地] 压缩内容...")

        payload = {
            "model": self.ollama_model,
            "prompt": f"""请将以下文本压缩至 200 字以内，保持核心信息。

文本内容：
{text}

请用简洁的方式输出压缩后的内容。""",
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result['response']
            else:
                print(f"[本地] 压缩失败: {response.status_code}")
                return text

        except Exception as e:
            print(f"[本地] 压缩错误: {str(e)}")
            return text

    def generate(self, prompt, length='medium'):
        """文本生成（零 Token）"""
        import requests

        print(f"[本地] 生成文本... (主题/长度: {length})")

        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=180
            )

            if response.status_code == 200:
                result = response.json()
                return result['response']
            else:
                print(f"[本地] 文本生成失败: {response.status_code}")
                return text

        except Exception as e:
            print(f"[本地] 文本生成错误: {str(e)}")
            return text

    def chat(self, message):
        """多轮对话（零 Token）"""
        import requests

        print(f"[本地] 对话...")

        payload = {
            "model": self.ollama_model,
            "messages": [
                {"role": "user", "content": message}
            ],
            "stream": False
        }

        try:
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result['message']['content']
            else:
                print(f"[本地] 对话失败: {response.status_code}")
                return None

        except Exception as e:
            print(f"[本地] 对话错误: {str(e)}")
            return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description='本地任务处理器（支持更多能力）')
    subparsers = parser.add_subparsers(dest='task', help='任务类型')

    # 翻译任务
    translate_parser = subparsers.add_parser('translate', help='翻译文本')
    translate_parser.add_argument('text', help='待翻译的文本')

    # 摘要任务
    summarize_parser = subparsers.add_parser('summarize', help='生成摘要')
    summarize_parser.add_argument('text', help='待摘要的文本')

    # 提取信息任务
    extract_parser = subparsers.add_parser('extract', help='提取关键信息')
    extract_parser.add_argument('text', help='待提取的文本')

    # 格式修复任务
    fix_parser = subparsers.add_parser('fix', help='修复格式')
    fix_parser.add_argument('text', help='待修复的文本')

    # 扩展任务（新增）
    rewrite_parser = subparsers.add_parser('rewrite', help='扩写内容')
    rewrite_parser.add_argument('text', help='待扩写的文本')

    compress_parser = subparsers.add_parser('compress', help='压缩内容')
    compress_parser.add_argument('text', help='待压缩的文本')

    # 文本生成任务（新增）
    generate_parser = subparsers.add_parser('generate', help='文本生成')
    generate_parser.add_argument('prompt', help='生成提示')
    generate_parser.add_argument('--length', '-l', choices=['short', 'medium', 'long'], default='medium', help='输出长度')

    # 对话任务（新增）
    chat_parser = subparsers.add_parser('chat', help='多轮对话')
    chat_parser.add_argument('message', help='用户消息')

    args = parser.parse_args()

    handler = LocalTaskHandler()

    if args.task == 'translate':
        result = handler.translate(args.text)
        print(f"\n翻译结果:\n{result}\n")
    elif args.task == 'summarize':
        result = handler.summarize(args.text)
        print(f"\n摘要结果:\n{result}\n")
    elif args.task == 'extract':
        result = handler.extract_info(args.text)
        print(f"\n提取结果:\n{result}\n")
    elif args.task == 'fix':
        result = handler.fix_format(args.text)
        print(f"\n修复结果:\n{result}\n")
    elif args.task == 'rewrite':
        result = handler.rewrite(args.text)
        print(f"\n扩写结果:\n{result}\n")
    elif args.task == 'compress':
        result = handler.compress(args.text)
        print(f"\n压缩结果:\n{result}\n")
    elif args.task == 'generate':
        result = handler.generate(args.prompt, args.length)
        print(f"\n生成结果:\n{result}\n")
    elif args.task == 'chat':
        result = handler.chat(args.message)
        print(f"\n对话回复:\n{result}\n")
    else:
        parser.print_help()


if __name__ == '__main__':
    sys.exit(main())
