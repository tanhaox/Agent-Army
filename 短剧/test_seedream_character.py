"""
火山引擎 Seedream 角色多角度参考图测试
模型: doubao-seedream-5-0-260128
角色: 林野（混沌外卖员主角）
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

MODEL = "doubao-seedream-5-0-260128"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output", "seedream_test")
os.makedirs(OUT_DIR, exist_ok=True)

# 角色基础描述（中英文混合，Seedream 支持中文）
CHAR_BASE_CN = "20岁东亚中国男性，黑色碎发，眼神锐利，穿着黄色外卖冲锋衣，黑色工装裤，运动鞋"
CHAR_SPECIAL = "瞳孔内有混沌纹路，额头中央有古篆封印印记"
ENV_STYLE = "赛博朋克雨夜街道，霓虹灯闪烁，全息广告牌，冷色调高对比光影，紫青黑色调，4K，虚幻引擎5电影级渲染"

# 四个角度的 Prompt
ANGLES = [
    {
        "name": "front_full",
        "label": "正面全身",
        "prompt": (
            f"Full body shot, facing camera directly, {CHAR_BASE_CN}. "
            f"{CHAR_SPECIAL}. Standing in a cyberpunk rain-soaked street, "
            f"neon lights reflecting on wet ground, holographic billboards, "
            f"cool-toned high contrast lighting, purple cyan black color palette, "
            f"cyberpunk art style, cinematic, 4K, Unreal Engine 5 render, "
            f"highly detailed, sharp focus, professional photography"
        ),
    },
    {
        "name": "left_side",
        "label": "左侧面半身",
        "prompt": (
            f"Left side profile, medium shot, waist up, {CHAR_BASE_CN}. "
            f"{CHAR_SPECIAL}. Cyberpunk street at night with rain, "
            f"neon signs casting colored shadows, cool-toned dramatic lighting, "
            f"purple cyan black palette, cyberpunk art style, cinematic, "
            f"4K, Unreal Engine 5, highly detailed, sharp focus"
        ),
    },
    {
        "name": "right_side",
        "label": "右侧面半身",
        "prompt": (
            f"Right side profile, medium shot, waist up, {CHAR_BASE_CN}. "
            f"{CHAR_SPECIAL}. Cyberpunk rain-soaked alley, "
            f"neon lights and holographic ads, high contrast cool-toned lighting, "
            f"purple cyan black palette, cyberpunk art style, cinematic, "
            f"4K, Unreal Engine 5, highly detailed, sharp focus"
        ),
    },
    {
        "name": "closeup_face",
        "label": "正面特写（强调瞳孔和封印）",
        "prompt": (
            f"Extreme close-up on face, front view, {CHAR_BASE_CN}. "
            f"Focus on eyes showing {CHAR_SPECIAL}. Rain drops on face, "
            f"cyberpunk neon lights reflecting in eyes, dramatic side lighting, "
            f"purple cyan glow on skin, ultra detailed skin texture, "
            f"pores visible, cinematic lighting, 4K, Unreal Engine 5, "
            f"macro photography, shallow depth of field"
        ),
    },
]

print("=" * 70)
print("  火山引擎 Seedream 5.0 角色多角度参考图测试")
print(f"  模型: {MODEL}")
print(f"  角色: 林野（混沌外卖员）")
print(f"  角度数: {len(ANGLES)}")
print("=" * 70)
print()

results = []

for i, angle in enumerate(ANGLES):
    print(f"[{i+1}/{len(ANGLES)}] {angle['label']} ({angle['name']})")
    print(f"  Prompt: {angle['prompt'][:80]}...")
    print()

    start = time.time()
    try:
        resp = client.images.generate(
            model=MODEL,
            prompt=angle["prompt"],
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
    # 间隔 2 秒避免限流
    if i < len(ANGLES) - 1:
        print("  等待 2s...")
        time.sleep(2)
        print()

# 汇总报告
print()
print("=" * 70)
print("  测试报告汇总")
print("=" * 70)
ok_count = sum(1 for r in results if r["status"] == "OK")
print(f"成功: {ok_count}/{len(results)}")
print()

for r in results:
    if r["status"] == "OK":
        print(f"  {r['label']:12s} | {r['gen_time']:.1f}s 生成 | {r['size_kb']:.0f}KB | {r['path']}")
    else:
        print(f"  {r.get('label', r['angle']):12s} | FAILED: {r.get('error', 'unknown')}")

if ok_count > 0:
    avg_gen = sum(r["gen_time"] for r in results if r["status"] == "OK") / ok_count
    avg_dl = sum(r["dl_time"] for r in results if r["status"] == "OK") / ok_count
    print(f"\n平均生成耗时: {avg_gen:.1f}s")
    print(f"平均下载耗时: {avg_dl:.1f}s")
    print(f"总耗时: {sum(r['gen_time']+r['dl_time'] for r in results if r['status']=='OK'):.1f}s")

print()
print("=" * 70)
print("  测试完成，请查看 test_output/seedream_test/ 目录中的图片")
print("=" * 70)
