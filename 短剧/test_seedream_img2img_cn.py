"""
火山引擎 Seedream 5.0 图生图测试（中文提示词）
使用 closeup_face.jpg 作为参考图，验证角色一致性
"""

import os
import sys
import time
import base64
import requests as http_requests
from volcenginesdkarkruntime import Ark

API_KEY = os.environ.get("ARK_API_KEY", "")
if not API_KEY:
    print("ERROR: 请设置环境变量 ARK_API_KEY")
    sys.exit(1)

# 读取参考图并转 Base64（带 data URI 前缀）
REF_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "test_output", "seedream_test", "closeup_face.jpg"
)
if not os.path.exists(REF_PATH):
    print(f"ERROR: 参考图不存在: {REF_PATH}")
    sys.exit(1)

with open(REF_PATH, "rb") as f:
    img_bytes = f.read()
img_b64 = "data:image/jpeg;base64," + base64.b64encode(img_bytes).decode("utf-8")
print(f"参考图: {REF_PATH}")
print(f"参考图大小: {len(img_bytes)/1024:.1f} KB")
print(f"Base64长度: {len(img_b64)} 字符")
print()

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=API_KEY,
)

MODEL = "doubao-seedream-5-0-260128"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output", "seedream_img2img_cn")
os.makedirs(OUT_DIR, exist_ok=True)

ANGLES = [
    {
        "name": "left_side_cn",
        "label": "左侧面半身（图生图+中文）",
        "prompt": (
            "参考这张图片的人物和服装，生成同一个人的左侧面半身照。要求：\n"
            "- 脸部特征、发型、肤色必须与参考图完全相同。\n"
            "- 黄色外卖冲锋衣的样式、颜色、细节（领口、拉链、口袋）必须与参考图一致。\n"
            "- 背景：赛博朋克风格街道，雨夜，霓虹灯。\n"
            "- 光影：冷色调，高对比，电影级布光。\n"
            "- 画质：4K，高细节。\n"
            "- 不要添加任何纹身、伤痕或面部标记。"
        ),
    },
    {
        "name": "right_side_cn",
        "label": "右侧面半身（图生图+中文）",
        "prompt": (
            "参考这张图片的人物和服装，生成同一个人的右侧面半身照。要求：\n"
            "- 脸部特征、发型、肤色必须与参考图完全相同。\n"
            "- 黄色外卖冲锋衣的样式、颜色、细节必须与参考图一致。\n"
            "- 背景：赛博朋克风格街道，雨夜，霓虹灯。\n"
            "- 光影：冷色调，高对比，电影级布光。\n"
            "- 画质：4K，高细节。\n"
            "- 不要添加任何纹身、伤痕或面部标记。"
        ),
    },
    {
        "name": "front_full_cn",
        "label": "正面全身（图生图+中文）",
        "prompt": (
            "参考这张图片的人物和服装，生成同一个人的正面全身照。要求：\n"
            "- 脸部特征、发型、肤色必须与参考图完全相同。\n"
            "- 全身服装：黄色外卖冲锋衣、黑色工装裤、运动鞋，样式细节必须与参考图一致。\n"
            "- 站姿：自然站立，双手自然下垂或插兜。\n"
            "- 背景：赛博朋克风格街道，霓虹灯，雨夜。\n"
            "- 光影：冷色调，高对比，电影级布光。\n"
            "- 画质：4K，高细节。\n"
            "- 不要添加任何纹身、伤痕或面部标记。"
        ),
    },
]

print("=" * 70)
print("  Seedream 5.0 图生图测试（中文提示词）")
print(f"  模型: {MODEL}")
print(f"  参考图: closeup_face.jpg")
print(f"  测试角度: {len(ANGLES)}")
print("=" * 70)
print()

results = []

for i, angle in enumerate(ANGLES):
    print(f"[{i+1}/{len(ANGLES)}] {angle['label']}")
    prompt_preview = angle["prompt"][:60].replace("\n", " ")
    print(f"  提示词: {prompt_preview}...")
    print()

    start = time.time()
    try:
        resp = client.images.generate(
            model=MODEL,
            prompt=angle["prompt"],
            image=img_b64,
            sequential_image_generation="disabled",
            response_format="url",
            size="2048x2048",
            watermark=False,
            stream=False,
        )
        gen_time = time.time() - start

        if not resp.data:
            print(f"  ERROR: 无图片返回")
            results.append({"angle": angle["name"], "status": "FAIL", "error": "no data"})
            continue

        img = resp.data[0]
        url = img.url
        print(f"  生成耗时: {gen_time:.2f}s")
        print(f"  图片尺寸: {img.size}")

        # 下载
        out_path = os.path.join(OUT_DIR, f"{angle['name']}.jpg")
        dl_start = time.time()
        img_resp = http_requests.get(url, timeout=60)
        dl_time = time.time() - dl_start

        if img_resp.status_code == 200:
            with open(out_path, "wb") as f:
                f.write(img_resp.content)
            size_kb = len(img_resp.content) / 1024
            print(f"  下载耗时: {dl_time:.2f}s, 大小: {size_kb:.1f} KB")
            print(f"  保存路径: {out_path}")
            results.append({
                "angle": angle["name"],
                "label": angle["label"],
                "status": "OK",
                "gen_time": gen_time,
                "dl_time": dl_time,
                "size_kb": size_kb,
                "path": out_path,
            })
        else:
            print(f"  下载失败: HTTP {img_resp.status_code}")
            results.append({"angle": angle["name"], "status": "FAIL", "error": f"download {img_resp.status_code}"})

    except Exception as e:
        gen_time = time.time() - start
        print(f"  FAILED ({gen_time:.2f}s): {type(e).__name__}: {e}")
        results.append({"angle": angle["name"], "status": "FAIL", "error": str(e)})

    print()
    if i < len(ANGLES) - 1:
        print("  等待 2s...")
        time.sleep(2)
        print()

# 汇总
print()
print("=" * 70)
print("  图生图测试报告汇总")
print("=" * 70)
ok_count = sum(1 for r in results if r["status"] == "OK")
print(f"成功: {ok_count}/{len(results)}")
print()

for r in results:
    if r["status"] == "OK":
        print(f"  {r['label']:25s} | {r['gen_time']:.1f}s | {r['size_kb']:.0f}KB | {r['path']}")
    else:
        print(f"  {r.get('label', r['angle']):25s} | FAILED: {r.get('error', 'unknown')}")

if ok_count > 0:
    avg_gen = sum(r["gen_time"] for r in results if r["status"] == "OK") / ok_count
    total = sum(r["gen_time"] + r["dl_time"] for r in results if r["status"] == "OK")
    print(f"\n平均生成耗时: {avg_gen:.1f}s")
    print(f"总耗时: {total:.1f}s")

print()
print("=" * 70)
print("  测试完成，请查看 test_output/seedream_img2img_cn/ 目录")
print("=" * 70)
