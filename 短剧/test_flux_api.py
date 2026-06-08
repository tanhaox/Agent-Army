"""
测试硅基流动 FLUX.2 Pro API 连接和图像生成。
密钥从环境变量 SILICONFLOW_API_KEY 读取。
"""

import os
import sys
import time
import requests

API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
if not API_KEY:
    print("ERROR: 请设置环境变量 SILICONFLOW_API_KEY")
    sys.exit(1)

API_URL = "https://api.siliconflow.cn/v1/images/generations"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "model": "Kwai-Kolors/Kolors",
    "prompt": "A close-up portrait of a young Chinese delivery rider, messy black hair, yellow uniform, determined look, cyberpunk city street at night, neon lights, cinematic lighting, 4k",
    "image_size": "1024x1024",
    "num_inference_steps": 20,
}

print("=" * 60)
print("  硅基流动 FLUX.2 Pro API 测试")
print("=" * 60)
print(f"API URL: {API_URL}")
print(f"Model:   {payload['model']}")
print(f"Size:    {payload['image_size']}")
print(f"Key:     {API_KEY[:8]}...{API_KEY[-4:]}")
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
        print(f"Response: {resp.text}")
        sys.exit(1)

    data = resp.json()
    images = data.get("images", [])
    if not images:
        print(f"ERROR: 返回数据无图片")
        print(f"Response: {data}")
        sys.exit(1)

    image_url = images[0].get("url", "")
    print(f"Image URL: {image_url}")

    # 下载图片
    out_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "test_flux_pro.png")

    print(f"Downloading image...")
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
    print("可能原因：网络问题、API 地址错误")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
