#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 PKX 航班数据 JSON 文件
移除执行结果包装，提取纯 JSON
"""

import json
import re
import sys
import io

# 设置 UTF-8 输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def clean_json_file(input_file, output_file):
    """清理JSON文件，提取纯数据"""

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 使用 raw_decode 处理可能不完整的JSON
    import json.decoder
    decoder = json.JSONDecoder()

    try:
        # 解析第一个完整的JSON对象
        wrapper, idx = decoder.raw_decode(content)

        # 提取第一个元素的 text 字段
        if isinstance(wrapper, list) and len(wrapper) > 0:
            text_content = wrapper[0].get('text', '')

            # 移除 "Execution result:\n" 前缀
            prefix = 'Execution result:\n'
            if text_content.startswith(prefix):
                text_content = text_content[len(prefix):]

            # 解析内部 JSON
            data = json.loads(text_content)

            # 保存为纯JSON
            with open(output_file, 'w', encoding='utf-8') as out:
                json.dump(data, out, ensure_ascii=False, indent=2)

            flight_count = len(data.get('data', {}).get('flights', []))
            print(f'OK: Extracted {flight_count} flights')
            print(f'OK: Saved to {output_file}')

            return True
        else:
            print('Error: Invalid file structure')
            return False

    except (json.JSONDecodeError, ValueError) as e:
        print(f'Error: Cannot parse JSON - {e}')
        return False

if __name__ == '__main__':
    input_file = 'data/pkx-flights-2026-03-04-full.json'
    output_file = 'data/pkx-flights-2026-03-04-clean.json'

    clean_json_file(input_file, output_file)
