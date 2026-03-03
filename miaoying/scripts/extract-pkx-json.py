#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取 PKX JSON 数据的简单版本
"""

import json
import sys
import io

# 设置 UTF-8 输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def extract_json():
    with open('data/pkx-flights-2026-03-04-full.json', 'r', encoding='utf-8') as f:
        content = f.read()

    # 手动解析数组
    if content.strip().startswith('['):
        depth = 0
        in_string = False
        escape = False

        for i, char in enumerate(content):
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if char == '"' and not escape:
                in_string = not in_string
            if not in_string:
                if char == '[':
                    depth += 1
                elif char == ']':
                    depth -= 1
                    if depth == 0:
                        # 找到完整的数组
                        array_str = content[:i+1]
                        wrapper = json.loads(array_str)

                        if len(wrapper) > 0:
                            # 获取第一个元素的 text 字段
                            text = wrapper[0].get('text', '')

                            # 移除前缀
                            prefix = 'Execution result:\n'
                            if text.startswith(prefix):
                                text = text[len(prefix):]

                            # 使用 raw_decode 提取第一个完整的JSON对象
                            decoder = json.JSONDecoder()
                            data, _ = decoder.raw_decode(text)

                            # 保存
                            with open('data/pkx-flights-2026-03-04-clean.json', 'w', encoding='utf-8') as out:
                                json.dump(data, out, ensure_ascii=False, indent=2)

                            flights = len(data.get('data', {}).get('flights', []))
                            print(f'OK: 提取 {flights} 条航班')
                            print(f'OK: 保存到 data/pkx-flights-2026-03-04-clean.json')
                            return

                        print('Error: 空数组')
                        return

        print('Error: 未找到数组结束')
    else:
        print('Error: 文件不是数组格式')

if __name__ == '__main__':
    extract_json()
