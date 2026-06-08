"""
测试火山引擎豆包 Seedream 4.5 图像生成 API。
密钥从环境变量 ARK_API_KEY 读取。

文档参考：https://www.volcengine.com/docs/82379/1399008
"""

import os
import sys
import time
import requests

API_KEY = os.environ.get("ARK_API_KEY", "")
if not API_KEY:
    print("ERROR: 请设置环境变量 ARK_API_KEY")
    sys.exit(1)

API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "model": "doubao-seedream-4.5",
    "prompt": "一只橘猫穿着宇航服漂浮在太空中，背景是璀璨的星云和银河，电影级光影，超写实细节，8K",
    "size": "3072x3072",
    "watermark": False,
    "response_format": "url",
    "optimize_prompt_options": {"mode": "standard"},
}

print("=" * 60)
print("  火山引擎豆包 Seedream 4.5 API 测试")
print("=" * 60)
print(f"API URL: {API_URL}")
print(f"Model:   {payload['model']}")
print(f"Size:    {payload['size']}")
print(f"Key:     {API_KEY[:8]}...{API_KEY[-4:]}")
print(f"Prompt:  {payload['prompt'][:50]}...")
print()

start_time = time.time()
try:
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    elapsed = time.time() - start_time
    print(f"HTTP Status: {resp.status_code}")
    print(f"Response Time: {elapsed:.2f}s")
    print()

    if resp.status_code != 200:
        print(f"ERROR: API 调用失败")
        print(f"Response: {resp.text[:500]}")
        if resp.status_code == 401:
            print("可能原因：API Key 无效或过期")
        elif resp.status_code == 403:
            print("可能原因：账户欠费或模型未开通")
        elif resp.status_code == 404:
            print("可能原因：模型服务未开通，请访问火山方舟控制台开通 Seedream 4.5")
        elif resp.status_code == 400:
            print("可能原因：请求参数格式错误")
        sys.exit(1)

    data = resp.json()
    print(f"Response keys: {list(data.keys())}")
    print(f"Model: {data.get('model', 'N/A')}")
    print(f"Created: {data.get('created', 'N/A')}")

    # 用量信息
    usage = data.get("usage", {})
    if usage:
        print(f"Generated images: {usage.get('generated_images', 'N/A')}")
        print(f"Output tokens: {usage.get('output_tokens', 'N/A')}")

    # 提取图片
    images = data.get("data", [])
    if not images:
        print(f"ERROR: 返回数据无图片")
        print(f"Full response: {data}")
        sys.exit(1)

    for i, img_data in enumerate(images):
        # 检查是否有错误
        if "error" in img_data:
            print(f"Image {i+1} error: {img_data['error']}")
            continue

        image_url = img_data.get("url", "")
        img_size = img_data.get("size", "N/A")
        print(f"\nImage {i+1}: size={img_size}")
        print(f"URL: {image_url[:120]}...")

        # 下载图片
        out_dir = os.path.join(os.path.dirname(__file__), "test_output")
        os.makedirs(out_dir, exist_ok=True)
        suffix = f"_{i+1}" if len(images) > 1 else ""
        out_path = os.path.join(out_dir, f"test_seedream_45{suffix}.jpg")

        print(f"Downloading...")
        dl_start = time.time()
        img_resp = requests.get(image_url, timeout=60)
        dl_elapsed = time.time() - dl_start

        if img_resp.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(img_resp.content)
            size_kb = len(img_resp.content) / 1024
            print(f"Download: {dl_elapsed:.2f}s, {size_kb:.1f} KB")
            print(f"Saved to: {out_path}")
        else:
            print(f"ERROR: 下载失败 HTTP {img_resp.status_code}")

    print()
    print(f"Total Time: {elapsed + dl_elapsed:.2f}s")
    print("=" * 60)
    print("  TEST PASSED")
    print("=" * 60)

except requests.exceptions.Timeout:
    print("ERROR: 请求超时（120s）")
except requests.exceptions.ConnectionError:
    print("ERROR: 无法连接到 API 服务器")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
