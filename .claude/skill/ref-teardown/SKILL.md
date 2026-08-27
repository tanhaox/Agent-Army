---
name: ref-teardown
description: 参考片技术反推 — 给一条抖音/视频链接或本地视频, 产出"每个视觉现象→剪映技术→我们产线现状→升级项"的反推报告。用户说"拆解这条视频/反推/学习这条/这视频怎么做的/复刻"时使用。依赖 tools/vision (本地 llama 视觉) + ffmpeg + faster-whisper, 全本地。
---

# 参考片技术反推 (ref-teardown)

把任意参考片拆解成**可执行的技术规格**, 不是内容摘要。产出四列表:
视觉现象(帧实测) → 剪映技术(pyJianYingDraft 名词) → 我们产线现状 → 升级项。

项目: digital_human (F:\AI-Agent-Local\digital_human)。所有命令在项目根目录跑。

## 流程 (六步, 顺序执行)

### 1. 下载视频 (输入链接时)

```bash
# 首选 yt-dlp (免 cookies 时部分平台可用)
python -c "import yt_dlp; ..."  # outtmpl 到 sandbox/ref_videos/ref_<id>.%(ext)s

# 抖音等需登录态: kimi-webbridge 抓真实播放地址 (curl POST 127.0.0.1:10086,
# Windows 必须文件体传 JSON, 见 kimi-webbridge skill)
#   navigate 短链 → sleep 6 → evaluate: document.querySelector('video').currentSrc
#   → curl -A "<UA>" -e "https://www.douyin.com/" -o ref_<id>.mp4 "<完整URL>"
# 注意: playAddr 是短时效链接, 拿到立刻下; Read 工具读不了图, 视觉一律走 tools/vision
```

### 2. 规格与节奏

```bash
"C:\Programs\ffmpeg\bin\ffprobe.exe" -v error -show_entries format=duration:stream=width,height -of default=noprint_wrappers=1 <视频>
# 切点: -vf "select='gt(scene,0.3)',metadata=print" -f null - 2>&1 | grep -oE "pts_time:[0-9.]+"
# 分析: 30s 窗口密度直方 + 快切间隔分布 (≤1s 间隔数 = 逐词级动画信号)
```

⚠️ 关键认知: **文字动画不动背景 → 不产生场景切点**。切点只反映画面层节奏;
文字层节拍必须靠第 5 步逐帧视觉。切点稀疏 ≠ 节奏慢。

### 3. 口播转写

```bash
python -c "faster_whisper medium (cpu int8, language zh, vad_filter, beam 5)" → json
```
(或复用 video-transcribe skill; 8 分钟视频约 5-8 分钟)

### 4. 总览 (contact sheet)

```bash
ffmpeg -vf "fps=1/40,scale=480:-1,tile=4x3" -frames:v 2 → sheet.png
python -m tools.vision sheet_1.png -p "12帧拼图逐帧: 编号|画面构成|文字及样式|包装痕迹 + 一行账号形态总结"
```

### 5. 分区精拆 (tools/vision 定点连拍)

从切点密度图挑 2-3 个高价值区(快切段/文字卡区/图表区), 每区 4 帧:

```python
from tools.vision import analyze_video_at
analyze_video_at(视频, times=[...], prompt="""相邻时刻连续帧:
1) 哪些文字元素帧间变化(新出现/消失/位移)=逐帧动画
2) 颜色/层级/字号关系  3) 背景层帧间动不动  4) 推测剪辑手法""")
```

llama 上下文约束: 每批 ≤4 帧。tools/vision 首次调用自动拉起 llama-server
(E:/Llama-cpp-12, 8080; 若权限拦截, 请用户授权或用户手动跑 start_qwythos_9b.bat)。

### 6. 合成技术反推报告

落 `sandbox/reports/<视频id>_teardown.md`, 七节结构:
一、账号形态(画布/时长/内容类型/口播密度=字数÷秒)
二、节奏谱(切点密度表 + 三段式判定; 对照 R9 密度规则)
三、文字样式体系表(**核心交付**, 四列: 现象→pyJYD技术→我们现状→升级项🔥)
四、画面构成配比(contact sheet 抽样估算)
五、复刻路径(只列"现有武器能做"的, 标 ✅/工时级)
六、工具记录(tools/vision 调用次数)
七、口播×画面对齐公式(如"案例→B-roll/概念→AI意象/数字→图表" — 见 7662042592342740274_teardown.md 范例)

## 反推时的知识锚点 (映射表来源)

- 动画/音效/字体名词: config/jy_anim_sfx_cooccurrence.json (75动画×音效族),
  config/jy_style_palette.json (颜色语义/字体表/字号阶梯), R1~R20 配方
  (docs/剪映模板套路分析-效果配方库.md)
- 字号体系: pyJYD size = 剪映UI读数; 行宽 = 字号×8px×字数 ≤ 画布宽;
  行高 ≈ 字号×11px (y 单位 = 半屏高)
- 我们产线现状: hf_title/quote/opening J线原生版 (scripts/demo_jy_native_hf.py,
  v10 定稿), 字幕 5 号标准, 划重点金 7.5, 署名条 _CREDIT_BG

## 边界

- 视觉结论全部来自 tools/vision 实测帧, 不凭记忆猜样式
- 反推表只写"帧里看到的"; 推测处标"推测"
- 复刻路径第五节必须是现有武器圈内能做的 (产线三 config + pyJYD 能力),
  圈外的写明缺口, 不开空头支票
