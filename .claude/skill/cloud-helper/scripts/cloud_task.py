#!/usr/bin/env python3
"""
云端任务处理模块
使用小号 AI Token 处理复杂任务
"""

import os
import requests
from pathlib import Path


class CloudTaskHandler:
    """云端任务处理器"""

    def __init__(self):
        self.api_key = os.getenv('CLOUD_API_KEY')

        # 默认使用 DeepSeek
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.model = "deepseek-chat"

        # 可选：豆包、Kimi、Claude
        alt_models = {
            'doubao': ('https://ark.cn-beijing.volces.com/api/v3/chat/completions', 'ep-20250201135848-5r4g2'),
            'kimi': ('https://api.moonshot.cn/v1/chat/completions', 'moonshot-v1-8k'),
            'claude': ('https://api.anthropic.com/v1/messages', 'claude-sonnet-4-20250629', None),  # Claude 需要不同的 API
        }

    def translate(self, text):
        """
        云端翻译（消耗 Token）

        Args:
            text: 待翻译文本

        Returns:
            翻译后的文本
        """
        print(f"[云端] 开始翻译... (服务: {self.model})")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        prompt = f"""请将以下文本翻译成简体中文。

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
                print(f"[云端] Token 余额不足")
                return text  # 返回原文
            else:
                print(f"[云端] 翻译失败: {response.status_code}")
                return text

        except Exception as e:
            print(f"[云端] 翻译错误: {str(e)[:100]}")
            return text

    def analyze(self, text):
        """
        智能分析（消耗 Token）

        Args:
            text: 待分析的文本

        Returns:
            分析结果
        """
        print(f"[云端] 开始智能分析...")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        prompt = f"""请对以下文本进行智能分析。

分析要求：
1. 识别文本类型（叙事、说明、对话等）
2. 提取关键信息
3. 总结主要观点
4. 评估文本质量

文本内容：
{text}

请用结构化的方式输出分析结果。"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 402:
                print(f"[云端] Token 余额不足")
                return text
            else:
                print(f"[云端] 分析失败: {response.status_code}")
                return text

        except Exception as e:
            print(f"[云端] 分析错误: {str(e)[:100]}")
            return text

    def creative_writing(self, topic, length='medium'):
        """
        创意写作（消耗 Token）

        Args:
            topic: 写作主题
            length: 长度（short/medium/long）

        Returns:
            写作内容
        """
        print(f"[云端] 开始创意写作... (主题: {topic}, 长度: {length})")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        length_guide = {
            'short': '约 100-300 字',
            'medium': '约 500-1000 字',
            'long': '约 1500-3000 字'
        }

        prompt = f"""请为我写一篇文章。

主题：{topic}
长度：{length_guide[length]}

要求：
1. 开头引人入胜
2. 内容连贯有逻辑
3. 结尾总结升华
4. 使用生动的语言和例子

请用中文输出。"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=180)

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 402:
                print(f"[云端] Token 余额不足")
                return text
            else:
                print(f"[云端] 创意写作失败: {response.status_code}")
                return text

        except Exception as e:
            print(f"[云端] 创意写作错误: {str(e)[:100]}")
            return text

    def chat(self, message):
        """
        多轮对话（消耗 Token）

        Args:
            message: 用户消息

        Returns:
            AI 回复
        """
        print(f"[云端] 处理对话...")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": message}
            ],
            "temperature": 0.7
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 402:
                print(f"[云端] Token 余额不足")
                return None
            else:
                print(f"[云端] 对话失败: {response.status_code}")
                return None

        except Exception as e:
            print(f"[云端] 对话错误: {str(e)[:100]}")
            return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description='云端任务处理器')
    subparsers = parser.add_subparsers(dest='task', help='任务类型')

    # 翻译任务
    translate_parser = subparsers.add_parser('translate', help='翻译文本')
    translate_parser.add_argument('text', help='待翻译文本')

    # 分析任务
    analyze_parser = subparsers.add_parser('analyze', help='智能分析')
    analyze_parser.add_argument('text', help='待分析文本')

    # 创意写作任务
    write_parser = subparsers.add_parser('write', help='创意写作')
    write_parser.add_argument('topic', help='写作主题')
    write_parser.add_argument('--length', '-l', choices=['short', 'medium', 'long'], default='medium')

    # 对话任务
    chat_parser = subparsers.add_parser('chat', help='多轮对话')
    chat_parser.add_argument('message', help='用户消息')

    args = parser.parse_args()

    handler = CloudTaskHandler()

    if args.task == 'translate':
        result = handler.translate(args.text)
        print(f"\n翻译结果:\n{result}\n")
    elif args.task == 'analyze':
        result = handler.analyze(args.text)
        print(f"\n分析结果:\n{result}\n")
    elif args.task == 'write':
        result = handler.creative_writing(args.topic, args.length)
        print(f"\n写作结果:\n{result}\n")
    elif args.task == 'chat':
        result = handler.chat(args.message)
        print(f"\n对话回复:\n{result}\n")
    else:
        parser.print_help()


if __name__ == '__main__':
    sys.exit(main())
