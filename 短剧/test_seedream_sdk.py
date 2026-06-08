"""
测试火山引擎豆包 Seedream 图像生成 - 使用官方 SDK。
密钥从环境变量 ARK_API_KEY 读取。
"""

import os
import sys
import time
import requests as http_requests
from volcenginesdkarkruntime import Ark

API_KEY = os.environ.get("ARK_API_KEY", "")
if not API_KEY:
    print("ERROR: 请设置环境变量 ARK_API_KEY")
    sys.exit(1)

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=API_KEY,
)

# 依次尝试的模型列表（含版本号后缀）
models_to_try = [
    "doubao-seedream-4-5-250516",
    "doubao-seedream-5-0-260128",
    "doubao-seedream-5-0-lite-250415",
    "doubao-seedream-4-0-250304",
    "doubao-seedream-3-0-t2i-250328",
]

prompt = "一只橘猫穿着宇航服漂浮在太空中，背景是璀璨的星云和银河，电影级光影，超写实细节，8K"

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output")
os.makedirs(out_dir, exist_ok=True)

for model in models_to_try:
    print("=" * 60)
    print(f"  Testing: {model}")
    print("=" * 60)
    print(f"Prompt: {prompt[:60]}...")
    print()

    start_time = time.time()
    try:
        resp = client.images.generate(
            model=model,
            prompt=prompt,
            sequential_image_generation="disabled",
            response_format="url",
            size="2048x2048",
            watermark=False,
            stream=False,
        )
        elapsed = time.time() - start_time
        print(f"Response Time: {elapsed:.2f}s")
        print(f"Model: {resp.model}")
        print(f"Created: {resp.created}")
        print(f"Images: {len(resp.data)}")

        for i, img in enumerate(resp.data):
            url = img.url
            print(f"\nImage {i+1} size={img.size}")
            print(f"URL: {url[:120]}...")

            suffix = f"_{i+1}" if len(resp.data) > 1 else ""
            out_path = os.path.join(out_dir, f"test_{model.replace('-', '_')}{suffix}.jpg")

            dl_start = time.time()
            img_resp = http_requests.get(url, timeout=60)
            dl_elapsed = time.time() - dl_start

            if img_resp.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(img_resp.content)
                size_kb = len(img_resp.content) / 1024
                print(f"Download: {dl_elapsed:.2f}s, {size_kb:.1f} KB")
                print(f"Saved: {out_path}")
            else:
                print(f"Download failed: HTTP {img_resp.status_code}")

        print()
        print(f"Total: {elapsed + dl_elapsed:.2f}s")
        print("=" * 60)
        print(f"  {model} PASSED")
        print("=" * 60)
        break  # 第一个成功的模型就退出

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"FAILED ({elapsed:.2f}s): {type(e).__name__}: {e}")
        print()
