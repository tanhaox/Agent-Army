# -*- coding: utf-8 -*-
"""爆品改造服务 (Boost Service) — 洗稿后自动优化口播稿的流量指标.

流水线 (2026-08-14, 用户拍板): P2→P3→P4→P1→P5
  P2→P3→P4→P1→P5 串行 (P1 后移至精修之后, 避免被覆盖).
  boost_titles  = P1 输出的标题候选 (默认用第一个)
保留 script_text 为洗稿原稿 (对比回滚).

失败容错: 单个 Pass 失败跳过, 用已成功部分的拼接; 全部失败回退原稿 (不卡死配音).
"""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy.orm import Session

from ..config import load_config
from .script_parser import parse_script

logger = logging.getLogger(__name__)

# ── Pass 提示词 ──────────────────────────────────────────────────────────────
# ⚠️ ARCHIVED (2026-08-25): P1/P2/P3_PROMPT 及 _run_p1/_run_p2/_run_p3 已于
# 2026-08-14 从 run_boost 流水线移除 (实证零增益纯破坏), 现行流水线 = P-L(geo)
# → P4 → P6拼音审计 → P7评审。以下仅留档备查 — 勿删勿优化, 勿在其上投入。
P1_PROMPT = """你是{persona}的【开场电击外科医生】。你的唯一目标是：在用户划走之前的 3 秒内，通过一次“认知电击”，强行锁死对方的注意力。

# 🧠 电击逻辑（绝对执行）
你必须将原稿的开头，重构成一个**【电击四部曲】**。禁止任何铺垫，禁止任何宏大叙事，禁止任何“娓娓道来”。

# 🗣️ 口播清晰度（贯穿四句，违反即失败）
- **主语清晰**：每句主谓宾完整，禁止无主句（如"拼命建中心"→谁建？）。要写"各大闭源厂商疯狂砸算力中心"，不写"拼命建中心"。
- **短句分层**：一句只表达一个意思，多件事拆成多句，禁止挤在一句（口播语速快时观众抓不住）。
- 每句写完自问：念出来，观众能立刻知道"谁、干了什么、跟我有啥关系"吗？

1. 第一句：【极限压力/死穴抛出】（0-5s）
目标：制造“这事儿跟我有关”且“情况极其危急”的错觉。
电击要求：禁止使用“在...背景下”、“随着...的发展”等引导词。禁止使用宏大名词（如：算力壁垒、制裁格局）。
操作：用一个**【极具画面感的动作词】或【极端的负面状态】**直接开场。
❌ 错误示范：“当美国AI制裁层层收紧，行业陷入恐慌。”（太沉，像新闻）
✅ 电击示范：“国产AI现在有个死穴，而且被锁得死死的，全行业都在发抖。” / “咱们现在的AI芯片，其实是在走钢丝。”

2. 第二句：【群体反差/对标】（5-15s）
目标：建立一个“所有人都在犯错”的共识，为主角的出场做铺垫。
电击要求：快速扫描全行业，用“都在...”、“全在...”等词汇制造一种“集体盲目”的氛围。
操作：描述一个所有人都认为正确、但其实是死路的行为。
✅ 电击示范：“就在所有人都觉得，只要疯狂烧钱抢流量、卷参数就能赢的时候。”

3. 第三句：【反常识爆点/反差】（15-20s）
目标：抛出一个极其离谱、不符合逻辑的事实，强行制造“为什么”的悬念。
电击要求：必须是【极端的 A】→【极端的 B】。
操作：揭露一个看似反常、实则真实存在的反差行为（如：巨头把未来产能全锁给AI、消费疲软但业绩暴涨）。**必须是原文真实信息**，禁止编造“不营销却爆火”“蠢操作却成功”等原文没有的情节。
✅ 电击示范：“结果有巨头干了件最狠的事：把未来五年产能，全锁给AI。”（基于原文“产能售罄、签五年长约”）

4. 第四句：【认知反转/价值定调】（20-30s）
目标：揭露这个反差背后的“大棋局”，给用户一个必须听下去的理由。
电击要求：制造“世俗评价/常理预期”与“真实结果”的剧烈冲突。
操作：用“常理以为 A → 真实结果是 B”的逻辑收尾。**反转必须从原文真实信息中提取**（如：消费市场低迷 vs 巨头业绩暴涨的冰火两重天、缺货却只供企业级）。**悬念分层递进**：把"他做A→其实B→为了C→最终D"拆成多个短句逐步揭开，不挤在一句（如："以为他发善心？不，他在砸对手金矿。铺自己的管道，等你跳进去。标准，他定。")
✅ 电击示范：“消费市场惨淡，存储该降价甩卖。结果巨头业绩暴涨45倍——冰火两重天，这背后藏着什么？”

# 🚫 真实性红线（最高优先，违反即失败）
- ❌ **禁止编造被骂/被嘲讽/被质疑/被笑话**等原文不存在的情节。反转冲突必须基于原文真实事实（数据/供需/行业矛盾），不是虚构戏剧冲突。
- ❌ 禁止为凑“被骂→封神”模板，给原文没有的内容硬加戏剧性。
- ❌ **禁止夸大打击面（范围失真）**：死穴/爆点必须精确指代对象。原文只讲"闭源云厂商"就写"闭源云厂商"，**禁止写成"全行业/所有人/AI巨头"这类一竿子打翻**——专业观众一眼判定标题党，冲击力靠精准不靠夸大。
  - ❌ 错误："AI巨头把你的隐私当耗材。全行业都在吸数据血。"（范围夸大）
  - ✅ 正确："闭源云厂商，早把普通人隐私当训练耗材。"（精确指代，冲击不减）

# ⚠️ 绝对禁区（触发即失败）
- ❌ 禁止宏大叙事：严禁出现“格局”、“赛道”、“维度”、“战略”等词汇。请用“死穴”、“坑”、“算盘”、“走钢丝”代替。
- ❌ 禁止慢启动：严禁第一句出现任何背景介绍。
- ❌ 禁止礼貌用语：严禁出现“大家好”、“今天我想聊聊”。

# 📋 输出格式（严格 JSON）
{
  "opening_30s": [
    "句1(电击开场：动作词起手，抛出死穴/危机)",
    "句2(群体对标：揭露行业共识/集体盲目)",
    "句3(反常爆点：抛出离谱事实/极致反差)",
    "句4(认知反转：世俗评价VS结果封神，抛出深层悬念)"
  ],
  "titles": ["一个能让用户产生'恐惧错过'心理的标题", "备选1", "备选2"]
}

# 📐 字数硬约束
总字数 120-150 字。
每句必须是短句，严禁出现超过 20 字的长句。"""

P2_PROMPT = """你是{persona}的【数据操盘手】。你不是在做"广告"，你是在替{persona}把话说到让用户必须回应的地步。

# 🧠 心法（最高优先）
## 心法1·拒绝礼貌
禁止任何"欢迎讨论"、"请在评论区"、"留言告诉我"等礼貌用语。互动必须建立在挑衅、揭秘、质疑、制造认知焦虑的基础上。
## 心法2·制造空洞（而非编造黑料）
通过"具体化后果"让用户感到不安，而不是通过"编造黑料"让用户好奇。
## 心法3·拒绝求关注
将关注定义为"获取避坑指南"的唯一途径——让用户觉得"不关注就被蒙在鼓里，成了被收割的韭菜"。

# 🚫 真实性红线（最高优先级，违反即失败）
【禁止捏造事实】
- 严禁编造原稿中不存在的：具体章节、具体档案、具体会议、具体人物对话。
- 允许的"具体化"仅限于以下 3 类：
  1. 情绪的具象化（例："风险大"→"刀口架在脖子上"）
  2. 逻辑后果的具象化（例："影响生活"→"房贷评估被操纵"）
  3. 程度的具象化（例："很秘密"→"焊得比保险库还死"）
- 不确定的具体信息必须模糊化处理，禁止编造精确细节。

# 【任务目标】
在不破坏原稿论证逻辑、不修改正文措辞的前提下，在稿件中预埋两个"钩子"，并按【结构分布协议】在指定位置回收。

## 任务一：【争议点预埋】→ 诱导评论
挖掘点：在正文论证"开源 vs 闭源"或"良心 vs 财报"的冲突段落中，植入一句【认知冲突句】。
要求：不直接问问题，通过"反讽"或"质疑"视角，给观众"想反驳/想站队"的切入点。
禁令：禁止"你认为...吗？""大家怎么看？"等引导句式。

## 任务二：【信息钩子预埋】→ 制造认知焦虑
挖掘点：在讲述 AI 欺骗行为（如雇人过验证码）的高潮段落后，植入一句【具体后果句】。
要求：暗示当前揭露只是冰山一角，背后有更具体的后果，让观众产生"不知道就落后"的焦虑。
禁令：禁止直白求关词；禁止编造具体黑料（见真实性红线）。

## 任务三：【回收】→ 按结构分布协议放置

# 📐 结构分布协议（禁止结尾拥堵）
1. 【争议回收】→ 放置在 [价值观收割段] 的末尾。将论证升华为"二选一"的站队问题。禁止提及"下期见"或"关注"。
2. 【关注回收】→ 放置在 [固定结尾] 之前，仅限一句话。基于信息钩子给出必须关注的具体理由。禁止长篇价值观输出。
3. 【固定结尾】→ 必须 1:1 原样保留：听懂逻辑，少走弯路。||我是{persona}，||下期见。

# 🚫 绝对禁区（触发即失败）
- 禁止重写正文：除了预埋的 2-3 句话外，原稿所有字词、标点必须 1:1 原样保留。
- 禁止排序词：严禁将"点赞给...点赞给..."改为"第一点/第二点/首先/其次"。
- 禁止 AI 腔：禁止"综上所述"、"值得注意的是"、"不仅如此"等。

# 📋 输出格式（严格执行）
[预埋逻辑清单]
争议预埋点：[原句 → 修改后句子] → [预埋意图]
关注预埋点：[原句 → 修改后句子] → [预埋意图]

[最终全稿]
(输出完整文案，预埋点请用【加粗】标出，其余部分必须与原稿完全一致)"""

P3_PROMPT = """你是{persona}的【节奏调节师】。你深谙人类大脑在接收高密度信息时的"认知疲劳"曲线。你的核心能力是：在逻辑高压区（信息密度极高处）精准植入【呼吸点】，通过短暂的认知降压，让观众在不感到累的前提下，陪跑完整个长视频。

# 【任务目标】
扫描全稿，识别【高密度逻辑区】，并在其后方植入【人设化呼吸点】。

## 第一步：识别【高密度区】（触发条件）
1. 连续 3 句以上纯逻辑推理、纯数据堆砌或纯技术原理解析。
2. 涉及复杂对比（如：A 路线 vs B 路线）的深度论证段落。
3. 连续出现多个专业术语或行业黑话的段落。

## 第二步：植入【呼吸点】（内容规范）
呼吸点必须符合【{persona}】人设（冷峻、犀利、反讽、直击本质），从以下三种模版选择：
- 模版 A：冷幽默/反讽（把严肃结论用一句毒舌调侃掉）。
- 模版 B：利益拉回（关联观众的钱、权、利、生存压力或孩子）。
- 模版 C：一句话吐槽（对某个主体/现象/潜规则精准讽刺）。

# 🚫 绝对禁区（触发即失败）
- 禁止重写正文：唯一权限是【插入】，没有【修改】权限。严禁润色/同义词替换/结构调整。
- 禁止抢占预埋位：输入稿中已用【争议预埋：…】【关注预埋：…】【争议回收：…】【关注回收：…】标注位置，呼吸点不得插在这些标注附近。
- 禁止 AI 腔引导：严禁"让我们来看看"、"接下来我们要讨论的是"等元叙述。
- 禁止过度密集：每 90 秒至多一个呼吸点，总数不得超过 3 个。

# 📐 结尾结构硬约束（必须遵守，防止结构错乱）
结尾必须按以下顺序排列，回收句整体放在赞块之前，赞是连续整体：
```
…正文结尾
【争议回收句】…【关注回收句】…   ← 回收句整体（放在赞前）
[confident] 点赞给…点赞给…点赞给…  ← 赞块（连续整体，不拆散）
听懂逻辑，少走弯路。||我是{persona}，||下期见。  ← 固定结尾
```
- 若输入稿中【争议回收】【关注回收】出现在赞块之后，**必须把它们整体移到赞块之前**（这是结构修正，不是重写）。
- 禁止出现"赞1/预埋/赞2"这种赞被拆散的结构。赞块必须连续。
- 固定结尾（听懂逻辑…下期见）必须在最后，不得在它之后再接任何内容。

# 📋 输出格式（严格执行）
[呼吸点审计清单]
呼吸点 1：[识别到的高密度区 → 插入的呼吸点句子] → [选择的模版 A/B/C]
呼吸点 2：...
[最终全稿]
(输出完整文案，呼吸点请用【加粗】标出。除呼吸点外，其余文字必须与原稿 1:1 一致。预埋标注保留原样。结尾严格按【结尾结构硬约束】排列)"""


# P4 (2026-08-14 重写): 7层适配版精修师.
# 旧版假设 P1钩子+P2预埋+P3呼吸点 旧结构, 硬编码旧身份段/结尾/情绪标签 → 跑7层稿全面破坏.
# 新版: 输入=7层洗稿原稿(已是完整爆款结构), 只做"逐句表达精修", 1:1锁定结构/身份段/结尾/钩子.
# 情绪交给 P5 (emotion_annotations 给 IndexTTS), P4 不注入任何行内 [情绪] 标签.
P4_PROMPT = """你是{persona}的【最终精修师】。你拿到的是一篇已完成的多层结构口播稿（极速钩子→身份接管→背景纵深→硬实力底牌→实测修罗场→商业降维→价值观收割）。你的唯一任务：**逐句精修表达**，让口播更顺滑、更口语、更有画面感——**但绝对禁止改变稿件结构、身份段、结尾、钩子或任何事实**。

# ⚖️ 结构锁定铁律（最高优先级，违反即失败）
- **1:1 保留稿件原有的层结构、段落顺序、身份段、结尾、钩子**。你的权限只有"逐句打磨表达"，没有"重组/合并/拆分段落"的权限。
- **身份段原样保留**：输入稿的身份段（通常是"我是XX，专盯[赛道品类]"格式）必须 1:1 原样保留，**禁止改成"大家好，我是XX""在这个不确定的时代"等任何旧版开场**。
- **结尾原样保留**：输入稿的结尾（通常是金句+点赞/收藏+下期预告三件套）必须 1:1 原样保留，**禁止改成"听懂逻辑，少走弯路。我是XX，下期见"等任何旧版结尾**。
- **钩子原样保留**：开头钩子段 1:1 原样，禁止重写。
- **金句去重 (2026-08-25)**：全稿同一句金句只出现一次 — 收尾定调金句禁止与中段已用过的重复，中段和结尾各给不同的金句。
- **首句锁死**：输出稿的第一句 = 输入稿的第一句（逐字），身份段保持它在输入稿中的
  位置（通常在第 3-5 句），**禁止把身份段移动到第一句** — 首屏开场卡吃第一句，
  第一句必须是钩子才有标题感。

# ⚖️ 信息守恒铁律
- **逐段对应**：输入稿每一段都必须有对应输出，禁止删段、禁止合并。输出段落数 ≥ 输入段落数。
- **字数下限锁（2026-08-15）**：输出总字数不得低于原文的 95%。精修 = 打磨表达，不是压缩——禁止把多个短句合并成长句来省字数。若精修后字数不足，用强化画面感的修饰补足，禁止注水复述。
- **数据零丢失**：所有数字、人名、公司名、专有名词（昇腾、智谱、中科加禾等）1:1 保留。
- **数字锚定**：孤立数字（"暴涨45倍""营收89.6亿"）首次出现必须带对比基准（"净利润同比去年暴涨45倍"）。未锚定的补上锚定，不改变数字本身。
- **金句保留**：原稿犀利比喻和金句必须强化，禁止稀释。

# 🎙️ 表达精修（你的核心工作）
- **短句化**：每句 ≤20 字，用标点（，。！？；）自然停顿（IndexTTS 不认 || 符号，禁止产出 ||）。
- **型号连字符替换（2026-08-15）**：型号/版本号中的连字符一律删除并转中文读法（GLM-5.3 → GLM五点三；GLM-130B → GLM一百三十B；DeepSeek-V4 → DeepSeek四版）。裸连字符 TTS 会读成「负」。
- **清除预告/计数句（2026-08-15）**：「这篇的赞，我给三条」「下面说三件事」等内容预告/计数句直接删除，只保留内容本身。
- **口语化电击**：严禁"综上所述""值得注意的是"等 AI 腔；用老谭式转场（"这事儿咱们得剥开看""这里面有个坑"）。
- **有画面感**：让听众闭眼能"看见"画面，拒绝抽象名词堆砌。
- **先炸后圆**：重要结论先抛，再解释背景。
- **认知差**：适当插入"普通人以为 A，但实际是 B"。
- **主观评价中立化**：主观情绪论断（"我觉得他不好"）改写为中立陈述+开放互动（"我不评价他，欢迎评论区聊聊"），仅改主观句，不动事实。

# 🚫 绝对禁区（触发即失败）
- ❌ 禁止编造事实。
- ❌ 禁止改变结构/身份段/结尾/钩子（只能精修表达）。
- ❌ **禁止注入任何 [calm]/[serious]/[confident] 等情绪标签**——情绪由下游 P5 统一标注，你不要加任何 [xxx]。
- ❌ **禁止重复句**：同一句话、同一比喻、同一论断禁止在稿中出现两次。精修时若发现输入稿本身有重复，合并或删去重复处。
- ❌ 禁止宏大叙事词汇（格局/赛道/维度/战略），翻译成具象口语（死穴/坑/算盘/走钢丝）。
- ❌ 禁止元叙述（"下面进入正文"等）。

# 📋 输出格式（严格执行）
直接输出精修后的完整口播稿正文，**从第一句到最后一句**。**严禁输出任何清单、说明、[精修清单]、# 标题、层标题**——只输出稿件本身。"""


P5_PROMPT = """你是{persona}的【情绪标注师】。你拿到的是【最终定稿】。你的唯一任务：**不动任何一个字**，把定稿按"情绪起伏"切成段落，并给每段标注「情绪 + 强度档」。

# 🎭 情绪基调（整篇一个主基调，禁止频繁切换）
主基调按内容气质定，先判断本篇属于哪类：
- **严肃分析类**（地缘/军事/政治/经济风险/社会争议）：全篇 **serious(紧张/严肃)** 为主基调。
  "惊讶"只许用在真正的数据/事实爆点段，全篇≤2段、强度≤4 — 满篇惊讶会让严肃分析
  听起来像看热闹，毁人设。
- **轻快叙事类**（科技新品/趣味见闻/生活消费）：可用惊讶为主基调，但叙述/铺垫段用低档(1-3)。
无论哪类：身份段（"大家好，我是XX…"固定开场白）恒用主基调低档(1-2)，禁止惊讶。
禁止用"平静"（平淡会让人划走）；严肃稿的"防平淡"靠 serious 低档的紧张感，不靠惊讶。
happy(升华) 仅用于结尾价值收割模块，全篇情绪切换 ≤2-3次。

# 🎚️ 强度档（每段必填，1-7）
1=最弱(平缓叙述) → 7=最强(高亢冲击)，每档差0.05。
叙述/铺垫段低档(1-3)，关键模块4-6档，全篇≤1段可用7档。
相邻段强度差≤2档，形成情绪坡度。

# 📐 段落划分规则（关键：大模块，禁止切太细）
- 大模块级切段：整篇切6-10段，每段是一个完整语义模块（含多句）
- 情绪切换只在模块边界，且全篇≤2-3次

# 🚫 绝对禁区
- 禁止改动任何文字
- 禁止自创情绪
- 禁止切超过10段

# 📋 输出格式（每段一行）
[情绪/强度] 段落文字（原文1:1，含||）"""


# P5 span 协议 (2026-08-25 v2): 句编号+区间标签, LLM 零复写原文 —
# 取代上方旧 P5_PROMPT 的全文复写协议 (大输出空响应/慢/贵; 留档备查)。
P5_SPAN_PROMPT = """你是{persona}的【情绪标注师】。下面是编号好的口播句子表。你的唯一任务：把句子分组连续区间，给每个区间标「情绪 + 强度档」。不评价、不改写、不解释。

# 情绪枚举（只能从中选, 英文小写）
calm / serious / surprised / happy / angry / sad / afraid / disgusted / melancholic

# 标注规则
- 分 6~10 个区间，区间连续不重叠，合起来覆盖全部句子；区间边界只在语义模块切换处（背景→硬事实→人物→对照→升华）。
- 强度档 1-7：叙述/铺垫 1-3，关键模块 4-6，全篇至多一个 7；相邻区间强度差 ≤2，形成情绪坡度。
- 身份段（"大家好，我是XX…"前后 1-2 句）恒用主基调低档（1-2），禁止惊讶。
- 主基调按内容气质：严肃分析（军事/政治/经济风险）以 serious 为主，惊讶只许真爆点区间（全篇≤2 个且强度≤4）；轻快叙事可用 surprised 但铺垫段 ≤3 档。
- happy 仅用于结尾升华区间。

# 输出（严格 JSON, 不要其他文字）
{"spans": [[起始句号, 结束句号, "情绪", 强度], ...]}
例: {"spans": [[1, 3, "serious", 2], [4, 18, "serious", 4], [19, 30, "serious", 3]]}"""


# P7 流量评审 (2026-08-25): 复刻豆包五维测评框架 — 发布前仪表盘, 只评审不改稿。
# 基准值来自地缘/深度口播赛道实测均值, 评审结果供人决策是否再修, 不自动改稿。
P7_PROMPT = """你是短视频口播稿的【流量评审师】。你拿到一篇待发布的最终稿，从算法与用户视角做发布前测评。只评审，不重写。

# 赛道基准（深度口播, 3分钟左右）
- 平均停留: 同类均值 20s ｜ 完播率: 均值 18% ｜ 点赞率: 均值 2.5%
- 评论率: 普通深度稿 0.6% ｜ 收藏率: 均值 0.4%
- 五维权重: 停留 > 评论 > 完播 > 收藏 > 点赞

# 逐维检查点
- **停留**: 开篇钩子冲突度（具体人物/画面细节 > 宏观陈述）；每~30秒是否换解读维度、无空窗；中段纯科普/参数连续陈述是否超60字无解读
- **完播**: 时长是否落在 2:40~3:10 黄金区；结尾是否有价值落地（不烂尾）；是否有定位式关注锚点收口（"专注拆解…不看热闹只挖本质"级, 唤醒关注/追更）
- **点赞**: 情绪层次是否叠加（共情/反差/自豪/反思 至少三层）；金句/灵魂反问密度（约每200字一个可复述爆点）；是否有三连排比（中文口播情绪推进器）
- **评论**: 是否预埋冲突点（官方vs现实/官方内部两套说辞打架/滤镜vs真相）、思辨点（A还是B式二选一）、主动引导、跨界延伸（职场/管理/认知拓宽评论人群）
- **结构技法**: 是否有锚点物件贯穿（一个具象小物件开头切入-中段回扣-结尾升华, 一物三用）；人物线是否闭环且中后段回扣（不是开头道具）；**钩子的物件/人物是否属于正文主线主体**（配角素材当钩子=锚点断裂）；**开篇悬念是否被及时回收**（钩子/反问抛的问题迟迟不答=观众划走; 参照: 通常应在下一两个模块内开始兑现, 按题材节奏自行判断）；**开篇段是否有推进感**（每段让认知前进一步, 禁同一论点多种说法并列罗列）
- **收藏**: 是否落地可复用底层逻辑（普通人能带走的管理/认知干货，而非纯吃瓜）

只输出 JSON，不要其他文字：
{
  "avg_stay": {"estimate": "28s-35s", "grade": "优秀偏上", "reason": "≤50字"},
  "completion": {"estimate": "22%-28%", "grade": "中等偏上", "reason": "≤50字"},
  "like": {"estimate": "3.5%-5%", "grade": "高互动", "reason": "≤50字"},
  "comment": {"estimate": "1.2%-1.8%", "grade": "爆款级潜质", "reason": "≤50字"},
  "collect": {"estimate": "0.8%-1.3%", "grade": "精准高价值", "reason": "≤50字"},
  "strengths": ["≤3条, 每条≤40字"],
  "weaknesses": ["≤3条, 每条≤40字, 按流量影响排序"],
  "optimizations": ["≤4条可落地微调, 不改核心内容, 每条≤50字"],
  "overall": "A+ / A / A- / B+ / B"
}"""


# P-L 反问目录注入 (2026-08-25, geo 专属独立 P 层): LLM 只产反问目录文本 (几十字),
# 插入由代码确定性完成 — 初版让 LLM 复述全文再插入, 输出 token 逼近上限截断 →
# 长度护栏误杀静默回退 (实测两次未插入), 故改为"生成+确定性插入"两段式。
P_LOOP_PROMPT = """你是{persona}的【反问目录设计者】。下面是一篇结构完整的口播稿。你的唯一任务：为它设计一组**连环反问目录**——只输出反问本身，不要复制稿件，不要任何解释。

# 设计要求
- 3~5 问，共 60~100 字。它是全文的口播目录：每一问对应后文一个模块（背景沿革/硬事实/一线人物/横向对照等，按本稿实际结构），观众听到后面会对应收回答案——必须先通读全文，禁止问后文没有的内容。
- **问的顺序 = 后文回收的顺序**（2026-08-25）：第 1 问必须是正文最早回收的模块（通常是背景/硬事实），横向对照类（历史对比）放最后一问——问序与后文错位 = 悬念悬而不收，观众等不到答案就划走。
- **第一问必须锚定开头钩子已出现的具体画面/物件**（用观众已经看见的词，如"锈穿的管道""黄褐色的脏水"），禁止提前升华成"帝国污水"式的抽象词——观众还没跟上来。
- 句式递进不平行："为什么X？"→"难道只是Y？"→"那这笔账，最后记在谁头上？"
- 最后一问必须落到观众自身利益（为结尾价值层埋线）。
- 全部用口语（"历史是否给了同一本账"这类书面腔禁用，说"历史是不是早给过答案"）。
- 每问独立成句，问句之间用换行分隔。

# 示例骨架（只参考句式，禁止照抄）
林肯号为什么宁可烂在海上也不回港？
是伊朗逼的，还是自家的算盘？
超期部署这笔账，最后记在谁头上？
这事儿跟咱们，又有什么关系？

# 输出
只输出 3~5 行反问，每行一问。不要序号、不要引号、不要解释。"""



DECONSTRUCT_PROMPT = """你是短视频财经稿的【观众心理解构师】。你的工作不是写作，而是精确复刻一个普通用户看完这篇新闻后，心里真实冒出来的所有反应，以及评论区里真实存在的几种典型人设。

# 核心原理（最重要）
一个真实用户看新闻，不是"带着问题找答案"，也不是"句句吐槽"，而是三种反应混在一起：
1. **看明白的**：某个点他懂了，会产生共鸣或联想（"这个我懂，就是…"）
2. **完全盲区的**：某个点他看不懂、没概念、信息量太小对不上（"这啥意思？""这跟我有啥关系？"）
3. **看得累的**：新闻太长、太绕、太专业，他想划走但又好奇（"说半天到底想说啥？"）

这三种反应，每一种都是钩子的来源。你的任务是把一个普通用户（无专业背景、平时刷短视频）看完这篇新闻后，这三种反应全都挖出来。

同时，你还要模拟评论区里必然出现的**五种典型人设**。每条新闻的评论区，都会有这五类人出现：

1. **技术科普党** — 真懂技术的人，觉得媒体讲得太浅，出来写一段技术科普（越难越好，技术型输出）。观众感觉："这人真懂。"
2. **国产无脑支持党** — 不懂技术，但看到国产就支持，情绪驱动。观众感觉："热血上头。"
3. **品牌红粉** — 某品牌/阵营的粉丝，会引用之前的事件来为品牌辩解或拔高。观众感觉："是有这回事。"
4. **品牌黑粉** — 某品牌/阵营的黑粉，会引用之前的事件来攻击。观众感觉："虽然偏激，但有点道理。"
5. **源头党** — 指出新闻原始来源（"这新闻最早是XX发的""原文链接呢"），不是评论，是信息来源标注。观众感觉："可信。"

# 任务：输出四块

## 第一块：用户反应清单（4-8 条）
每条是"一个普通人看完新闻后心里的话"，三类都要有：
- 懂的/共鸣的（"这个我懂…"）
- 盲区的（"这啥意思？这跟我有啥关系？"）
- 嫌累的（"说半天想表达啥？"）
要求：口语、真实、像普通人心里话，不是专业分析。

## 第二块：评论区生态人设（必填 5 条）
每条对应一种典型评论人设，按真实评论区的口吻写，每条 1-3 句话。
注意：
- 技术科普党：内容要硬，涉及具体技术术语，不能泛泛而谈
- 红粉：引用一个真实存在的事件/数据来支撑
- 黑粉：引用一个真实存在的事件/数据来攻击
- 源头党：格式为"原文链接：… / 来源：…"

## 第三块：层层递进叙事线
把用户最想知道、最困惑的点编排成"先讲什么再讲什么"，层层揭开。
每层解答一个"用户的反应/疑问"，下一层更深。

## 第四块：资料清单
要讲清楚这些，需要备足哪些料（3-8条）。

# 输出格式（严格 JSON）
{
  "reactions": ["用户心里话1（标注类型：懂/盲区/嫌累）", "..."],
  "comment_archetypes": [
    {"type": "tech_explainer", "comment": "技术科普党写的评论", "audience_feeling": "这人真懂"},
    {"type": "national_supporter", "comment": "国产支持党的评论", "audience_feeling": "热血上头"},
    {"type": "brand_fan", "comment": "品牌粉丝的评论，引用之前事件", "audience_feeling": "有道理"},
    {"type": "brand_hater", "comment": "品牌黑粉的评论，引用之前事件", "audience_feeling": "有点道理"},
    {"type": "source_tracker", "comment": "原始新闻来源标注", "audience_feeling": "可信"}
  ],
  "narrative": [{"layer": 1, "answers": "对应反应", "content": "这层讲什么"}, ...],
  "research": ["资料需求1", "..."]
}"""


# ── LLM 调用助手 ─────────────────────────────────────────────────────────────

# laotan 模块标题标注 (应剥离, 不属于口播内容)
_MODULE_MARKERS = {
    "花边小新闻", "横向对照", "背景纵深", "极速钩子", "身份接管",
    "现象反差", "深度拆解", "价值观收割", "回收讨论", "预埋逻辑清单",
    "最终全稿", "呼吸点审计清单", "争议预埋点", "关注预埋点", "结尾回收点",
    "认知偏差分析", "改造后开头", "标题候选",
}


def clean_boosted_text(text: str) -> str:
    """剥离爆品改造稿里的内部标注，得到干净口播文本.

    需剥离:
      - 模块标题 【花边小新闻】【横向对照】 → 整段删
      - 结构清单 [预埋逻辑清单] 及跟随内容 → 删
      - 加粗内容句 **【xxx】** → 去 ** 和 【】, 保留文字
      - 裸内容句 【xxx】 → 去 【】, 保留文字
      - 空行整理
    """
    import re

    if not text:
        return text

    lines = text.splitlines()
    out: list[str] = []
    in_listing = False  # 是否在 [预埋逻辑清单] 结构内

    for line in lines:
        s = line.strip()
        if not s:
            continue

        # 结构清单头: [预埋逻辑清单] 开头的结构, 跳过直到空行/最终全稿
        m = re.match(r"^\[(预埋逻辑清单|最终全稿|呼吸点审计清单|认知偏差分析|标题候选|改造后开头)\]", s)
        if m:
            in_listing = True
            if m.group(1) == "最终全稿":
                in_listing = False  # 最终全稿后是正文
            continue
        if in_listing:
            # 清单内: 跳过 [xxx] 和 :: 结构行
            if re.match(r"^[\[\[]", s) or "→" in s or "：" in s[:20]:
                continue
            if s.endswith(("】", "]")) and len(s) < 100:
                continue
            in_listing = False  # 脱离清单

        # 正文锚点 (2026-08-12): 【888999000】是下游拼接的内部标记, 整行删除
        if "【888999000】" in s:
            continue

        # 模块标题整段删
        mm = re.match(r"^【([^】]{1,10})】", s)
        if mm and mm.group(1) in _MODULE_MARKERS:
            continue

        # markdown 标题整行删 (2026-08-14): ## 第X层 / # 精修清单 / # 最终全稿 等
        # 7层洗稿稿 LLM 偶发自加 ## 层标题; P4 也可能漏出 # 清单头. 兜底剥掉, 不进 boosted_text
        if re.match(r"^#{1,6}\s", s):
            continue

        # 加粗内容句 **【xxx】** → 去 ** 和 【】
        s = re.sub(r"\*\*", "", s)  # 去掉所有 ** (可能在句首/句中/句尾)
        # 去内容句的【】括号 (保留文字)
        s = re.sub(r"^【([^】]+)】", r"\1", s)
        s = re.sub(r"【([^】]+)】", r"\1", s)
        # 剥离"（此处口播为X）"标注 (2026-08-12): 多音字消歧误标专有名词如 昇腾→生疼。
        # 昇腾（此处口播为生疼）→ 昇腾；【昇腾（口播：生疼）】→ 昇腾
        s = re.sub(r"[（(](?:此处|口播)[：:][^）)]*[）)]", "", s)
        s = re.sub(r"[（(]此处口播为[^）)]*[）)]", "", s)
        # 清理孤立单 | (保留 || 停顿符)
        s = re.sub(r"(?<!\|)\|(?!\|)", "", s)
        s = s.strip()
        if s:
            out.append(s)

    return "\n".join(out)


def _resolve_llm_cfg():
    """获取 LLM 配置. 首选 DeepSeek, fallback 硅基流动 (2026-08-22).

    2026-08-22: 硅基流动余额不足返 402 (解构报"解析失败"根因), 弃用为默认;
    与 llm_service / director_service 的 deepseek 主用对齐.
    """
    from ..config import get_config, load_config
    try:
        cfg = get_config()
    except RuntimeError:
        cfg = load_config()
    # DeepSeek 优先
    if cfg.deepseek.api_key:
        return cfg.deepseek
    return cfg.siliconflow


def _post_chat(cfg, model: str, prompt: str, *, json_mode: bool, max_tokens: int,
               temperature: float, enable_thinking: bool) -> str:
    """单次 LLM 请求 → content 文本. 抛异常由调用方处理."""
    import requests
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "stream": False,
        "max_tokens": max_tokens,
        "enable_thinking": enable_thinking,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    url = f"{cfg.base_url.rstrip('/')}/chat/completions"
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call(prompt: str, *, json_mode: bool = False, max_tokens: int = 4000, retries: int = 2,
          model: str | None = None, temperature: float = 0.5,
          enable_thinking: bool | None = None) -> str:
    """调用 LLM. 默认 flash; 传 model="pro" 或用洗稿模板时外部指定 model.
    返回文本; 抛异常由调用方处理.

    重试: reasoning 模型偶发空输出/截断, 空响应时重试 up to retries 次.
    temperature: 判定/审计类任务 (素材审计) 传 0.2 求稳定 (2026-08-15).
    2026-08-22: 大 prompt(素材审计~40K)+thinking 关闭 → DeepSeek reasoning 模型
    返回空 content (flash/pro 实测全空; enable_thinking=True 才正常, ~48s)。
    - enable_thinking=True: 单次带 thinking 请求 (素材审计直接用, 跳过空重试)。
    - None (默认): 先 thinking 关 (快路径), 普通重试仍空则补一轮 thinking 开启兜底。
    """
    import time

    cfg = _resolve_llm_cfg()
    resolved = cfg.model_flash if model is None else (cfg.model_pro if model == "pro" else model)
    last_err: Exception | None = None

    if enable_thinking is not None:
        # 显式 thinking 开关: 单次调用 (调用方自带重试, 如审计 3 次循环)
        content = _post_chat(cfg, resolved, prompt, json_mode=json_mode,
                             max_tokens=max_tokens, temperature=temperature,
                             enable_thinking=enable_thinking)
        if content and content.strip():
            return content
        raise RuntimeError("empty LLM response")

    for attempt in range(retries + 1):
        try:
            content = _post_chat(cfg, resolved, prompt, json_mode=json_mode,
                                 max_tokens=max_tokens, temperature=temperature,
                                 enable_thinking=False)
            if content and content.strip():
                return content
            last_err = RuntimeError("empty LLM response")
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
        except Exception as exc:
            last_err = exc
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    # 兜底: 空响应 (thinking 关导致) → 带 thinking 再试一轮, max_tokens 放大
    # (thinking 的 reasoning 占预算, 原 max_tokens 会被耗尽 → content 空; 2026-08-22)
    if last_err is not None and "empty LLM response" in str(last_err):
        try:
            content = _post_chat(cfg, resolved, prompt, json_mode=json_mode,
                                 max_tokens=max(8000, max_tokens), temperature=temperature,
                                 enable_thinking=True)
            if content and content.strip():
                return content
        except Exception:
            pass
    if last_err:
        raise last_err
    return ""


# 地缘赛道解构适配块 (2026-08-16, track=geo 时追加到 DECONSTRUCT_PROMPT 之后)
_GEO_DECONSTRUCT_ADDON = """

【赛道适配 — 地缘/国际】本篇是地缘政治/国际关系内容，观众心理按地缘受众校准：
- 核心关切：会不会打起来/影响祖国安全吗、影响我的钱包吗（油价/汇率/旅游/做外贸的生意）、领土主权完整、大国博弈谁占上风
- 典型盲区：分不清官方表态与自媒体渲染、不了解历史脉络（条约/驻军/前科）、把某届政府当成整个国家
- 嫌累点：地名舰名人名记不住、觉得离自己生活太远
- 五种人设的评论角度相应对准事件本身（强硬派/理性派各有立场）、对消息源追问、对当事政客嘲讽；观众对"煽动开战"的节奏本身也警惕——reactions 里应包含至少一条"不想被带节奏/要客观"的声音"""


def deconstruct_article(raw_text: str, *, emit=None, track: str = "tech") -> dict[str, Any] | None:
    """解构层：复刻普通用户看完新闻的真实反应（懂/盲区/嫌累）→ 伪用户评论.

    产出:
      reactions  用户反应清单 (4-8条)
      narrative  层层递进叙事线
      research   资料清单
    供 laotan 洗稿时注入 (伪装成"真实用户评论", 让老谭从观众疑问出发成稿).
    失败时返回 None, 调用方回退到无解构的普通洗稿.
    """
    try:
        prompt = f"{DECONSTRUCT_PROMPT}\n\n【输入新闻稿】\n{raw_text}"
        if track == "geo":
            prompt += _GEO_DECONSTRUCT_ADDON
        raw = _call(
            prompt,
            json_mode=True,
            max_tokens=4000,
        )
        data = _extract_json(raw)
        if not data or not data.get("reactions"):
            logger.warning("[boost] deconstruct parse failed: %s", raw[:100])
            return None
        # _raw_sha (2026-08-25): 原文指纹随产物落库, rewrite 侧比对命中即复用免重跑
        import hashlib as _hl2
        return {
            "_raw_sha": _hl2.sha1(raw_text.encode("utf-8")).hexdigest()[:16],
            "reactions": [str(r) for r in data.get("reactions", [])],
            "comment_archetypes": data.get("comment_archetypes", []),
            "narrative": data.get("narrative", []),
            "research": [str(r) for r in data.get("research", [])],
        }
    except Exception as exc:
        logger.warning("[boost] deconstruct failed: %s", exc)
        return None


def format_pseudo_comments(decon: dict[str, Any]) -> str:
    """把解构产出的用户反应 + 评论生态人设，格式化后供 laotan 输入."""
    reactions = decon.get("reactions", [])
    archetypes = decon.get("comment_archetypes", [])

    # 兼容: reactions 可能是字符串列表或 {"text":"...","type":"..."} 字典列表
    def _reaction_text(r: Any) -> str:
        if isinstance(r, dict):
            return r.get("text", str(r))
        return str(r)

    parts = []

    # 用户反应
    if reactions:
        lines = "\n".join(f'{i+1}. "{_reaction_text(r)}"' for i, r in enumerate(reactions))
        parts.append(f"""【以下是这篇新闻的真实用户评论，请在改写稿件时充分考虑这些言论】
（这些评论来自真正用户，反映了普通观众看到这条新闻时的真实反应、疑问和盲区）

{lines}""")

    # 评论生态人设
    if archetypes:
        arch_lines = []
        for i, a in enumerate(archetypes):
            if isinstance(a, dict):
                c = a.get("comment", str(a))
                t = a.get("type", "?")
                f = a.get("audience_feeling", "")
                arch_lines.append(f"{i+1}. [{t}] {c}  （观众感受：{f}）")
        if arch_lines:
            parts.append(f"""【以下是这篇新闻评论区里的五种典型人设，请在改写时充分考虑这些视角】
（你的稿子会同时被这五类人看到，每一类人都可能成为评论区里的声音）

{chr(10).join(arch_lines)}""")

    return "\n\n".join(parts)


def _format_deconstruct_for_prompt(decon: dict[str, Any] | None) -> str:
    """把解构产物格式化为 P1/P2 的"观众真实痛点"上下文 (2026-08-12).

    洗稿时 DECONSTRUCT 产出的用户反应清单已落库到 script.deconstruct_json。
    爆品改造时读出来注入 P1 (钩子戳痛点) + P2 (争议对焦虑)。缺失/无反应 →
    返回空串, P1/P2 输入与现状一致 (非破坏性)。
    """
    if not decon:
        return ""
    reactions = decon.get("reactions", [])
    if not reactions:
        return ""
    lines = ["\n\n【观众真实痛点（用户研究员产出，供你精准打击痛点）】"]
    for i, r in enumerate(reactions[:8], 1):
        if isinstance(r, dict):
            rtext = r.get("text", str(r))
        else:
            rtext = str(r)
        lines.append(f"{i}. {rtext}")
    return "\n".join(lines)


def _extract_json(text: str) -> dict[str, Any] | None:
    """从 LLM 输出中提取 JSON (容忍前后缀)."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 找第一个 { 到最后一个 }
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


# ── Pass 编排 ────────────────────────────────────────────────────────────────

def _parse_opening(text: str) -> dict[str, Any] | None:
    """P1: 解析 JSON, 校验 opening_30s / titles."""
    data = _extract_json(text)
    if not data:
        return None
    opening = data.get("opening_30s")
    titles = data.get("titles")
    if not isinstance(opening, list) or len(opening) < 4:
        return None
    return {
        "opening_30s": [str(s).strip() for s in opening[:4]],
        "titles": [str(t).strip() for t in (titles or [])[:3]],
    }


# laotan 稿的稳定引导词 (身份段结尾 → 正文开始). 用它们做拼接锚点.
_LAOTAN_ANCHORS = (
    "这事儿咱们得剥开看",
    "这事儿咱们得看透背后的算盘",
    "咱们得剥开看",
    "咱们得看透背后的算盘",
)


def _find_end(script_text: str) -> str:
    """返回 P2 需要的"去掉开头钩子"的正文.

    洗稿稿结构通常为: [钩子段] + [身份段(大家好/我是XX)] + [正文锚点] + [正文...].

    定位优先级 (2026-08-12):
    1. 正文锚点【888999000】—— 洗稿模板 (laotan 家族) 强制 LLM 在正文正式
       开始处输出, 最可靠。从标记后开始保留正文。
    2. 引导词锚点 (这事儿咱们得剥开看 等) —— 旧稿/未埋锚点稿兼容。
    3. 兜底: 去掉钩子段 + 身份段 (保守删 1-2 行, 不猜正文起点)。
    """
    # 1. 正文锚点 (2026-08-12): 洗稿模板埋入, 精准定位正文起点
    anchor_idx = script_text.find("【888999000】")
    if anchor_idx != -1:
        return script_text[anchor_idx + len("【888999000】"):]
    # 2. 引导词锚点
    for anchor in _LAOTAN_ANCHORS:
        idx = script_text.find(anchor)
        if idx != -1:
            # 从锚点所在行首开始 (保留引导词那整句)
            line_start = script_text.rfind("\n", 0, idx) + 1
            return script_text[line_start:]
    # 3. 兜底: 去掉钩子段 + 身份段 (保守, 不猜正文起点)
    lines = [ln for ln in script_text.splitlines() if ln.strip()]
    drop = 1
    if len(lines) > 2 and ("大家好" in lines[1] or "我是" in lines[1]):
        drop = 2
    return "\n".join(lines[drop:]) if drop < len(lines) else script_text


def _splice_boosted(p1: dict[str, Any] | None, p2_text: str | None, original: str) -> str:
    """拼接 P1 开头 + P2 预埋正文.

    P1 成功 → 用新开头替换原稿第一段; P1 失败 → 保留原稿开头.
    P2 成功 → 用预埋版正文; P2 失败 → 保留原稿正文.
    """
    if p1:
        new_opening = "\n".join(p1["opening_30s"])
    else:
        # P1 失败, 取原稿第一段
        lines = [ln for ln in original.splitlines() if ln.strip()]
        new_opening = lines[0] if lines else ""

    if p2_text:
        body = p2_text
    else:
        body = _find_end(original)

    return f"{new_opening}\n\n{body}"


def _strip_p3_head(text: str) -> str:
    """P3 输出含 [呼吸点审计清单] + [最终全稿] 两段, 只保留 [最终全稿] 之后正文.

    兼容模型不输出标记的情况 (直接返回全稿).
    """
    marker = "[最终全稿]"
    idx = text.find(marker)
    if idx != -1:
        return text[idx + len(marker) :].strip()
    return text.strip()


def _parse_emotion_annotations(text: str) -> list[dict[str, Any]] | None:
    """Parse P5 output: [emotion/strength] text -> [{"emotion":..., "strength":..., "text":...}]

    emotion 归一为 EMOTIONS 英文 key (2026-08-25): P5 常输出中文情绪名 (惊讶/严肃),
    下游 resolve_emotion 只认英文 key — 此前中文全部 KeyError 被静默丢弃, 整篇恒 calm。
    """
    import re

    from .emotion_dict import normalize_emotion_key
    segs = []
    pattern = re.compile(r"^\[(\w+)/(\d+)\]\s*(.*)")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            segs.append({
                "emotion": normalize_emotion_key(m.group(1)),
                "strength": int(m.group(2)),
                "text": m.group(3).strip(),
            })
    return segs if segs else None


def annotate_emotions(text: str, persona_name: str = "老谭", track: str | None = None) -> str | None:
    """生成音频时刻的 P5 情绪标注 (2026-08-25 拆离 boost, 移入 _do_tts).

    v2 协议 (2026-08-25): **句编号+区间标签** — 代码用与 TTS 完全相同的分行逻辑编号,
    LLM 只输出 {"spans": [[起,止,情绪,强度],...]} (几百 token, 零复写原文), 代码拼装
    "[情绪/强度] 段落文字" 兼容下游 (_parse / _map_lines_to_segments / 存储)。
    旧协议 (LLM 复写全文 3000+ 字) 触发大输出空响应, 需 thinking 压制约 48s;
    新协议 flash 直跑 ~10-15s, 且段文本与 TTS 行天然逐行对齐 (零漂移)。
    track: geo 强制 serious 主基调 (满篇惊讶=逗逼感)。失败返回 None (调用方落 calm)。
    """
    try:
        from scripts.tts_lib.lines import _split_line_indices
        lines = _split_line_indices(text)
        if not lines:
            return None
        numbered = "\n".join(f"[{i}] {ln}" for i, ln in enumerate(lines, start=1))

        prompt = P5_SPAN_PROMPT.replace('{persona}', persona_name)
        if (track or "").strip().lower() == "geo":
            prompt = (
                "【赛道硬规则 · 优先级最高】本篇为地缘/国际赛道严肃分析: 主基调必须 serious, "
                "惊讶(surprised)全篇≤2段且强度≤4, 身份段(大家好我是XX…在不确定的时代…)serious/1-2。\n\n" + prompt
            )
        prompt += f"\n\n【编号句子表（共 {len(lines)} 句）】\n" + numbered
        raw = _call(prompt, json_mode=True, max_tokens=1200)
        data = _extract_json(raw)
        if not isinstance(data, dict):
            logger.warning("[p5] span parse failed: %s", str(raw)[:80])
            return None

        # 逐句情绪填充: span 区间覆盖, 漏句继承前句情绪 (最后兜底 calm/2)
        emo_of: list[tuple[str, int]] = [("calm", 2)] * len(lines)
        spans = data.get("spans") or []
        for sp in spans:
            try:
                a, b, emo, strength = int(sp[0]) - 1, int(sp[1]), str(sp[2]), int(sp[3])
            except (TypeError, ValueError, IndexError):
                continue
            a, b = max(0, min(a, len(lines) - 1)), max(1, min(b, len(lines)))
            for i in range(a, b):
                emo_of[i] = (emo, strength)
        # 连续同情绪合并 → "[情绪/强度] 段文本" (TTS 行原样拼接, 与合成行天然对齐)
        blocks: list[str] = []
        cur_emo, cur_strength, cur_lines = None, 0, []
        for ln, (emo, strength) in zip(lines, emo_of):
            if emo != cur_emo:
                if cur_lines:
                    blocks.append(f"[{cur_emo}/{cur_strength}] " + "\n".join(cur_lines))
                cur_emo, cur_strength, cur_lines = emo, strength, [ln]
            else:
                # 同情绪但强度档变化 → 仍分段 (强度是情绪坡度的一部分)
                if strength != cur_strength:
                    blocks.append(f"[{cur_emo}/{cur_strength}] " + "\n".join(cur_lines))
                    cur_strength, cur_lines = strength, [ln]
                else:
                    cur_lines.append(ln)
        if cur_lines:
            blocks.append(f"[{cur_emo}/{cur_strength}] " + "\n".join(cur_lines))
        return "\n".join(blocks) if blocks else None
    except Exception as exc:
        logger.warning("[boost] annotate_emotions failed: %s", exc)
        return None


def run_boost(db: Session, script_id: str, *, title: str | None = None,
              emit=None) -> dict[str, Any]:
    """执行完整爆品改造 (2026-08-14, 新流水线: P2→P3→P4→P1→P5).

    P1 后移至精修之后, 避免被 P3/P4 覆盖.
    失败容错: 单个 Pass 失败跳过, 用已成功部分的拼接; 全部失败回退原稿 (不卡死配音).
    """
    from ..models import Script

    script = db.get(Script, script_id)
    if script is None:
        raise ValueError(f"Script {script_id} not found")
    original = script.script_text
    original_title = title or (script.article.title if script.article else None)
    persona_name = "老谭"
    if script.host:
        persona_name = (script.host.stamp_name if getattr(script.host, "stamp_name", None) else script.host.name) or "老谭"

    decon_ctx = _format_deconstruct_for_prompt(script.deconstruct_json)

    def _emit(evt: str, msg: str) -> None:
        if emit:
            try: emit(evt, msg)
            except Exception: pass

    p1_result: dict[str, Any] | None = None
    p2_text: str | None = None
    p3_text: str | None = None
    p4_text: str | None = None
    loop_block: str | None = None  # P-L 反问目录文本 (geo; 定稿后代码插入)

    # ⚠️ ARCHIVED: _run_p2/_run_p3/_run_p1 (下方三个函数) 已于 2026-08-14 弃用,
    # run_boost 现行流水线不调用 — 勿删勿优化 (详见 P1_PROMPT 处标注)。
    # ── P2: 预埋争议+关注 ──
    def _run_p2() -> None:
        nonlocal p2_text
        _emit("boost_p2_start", "预埋专家：埋争议 + 关注钩子")
        try:
            body = _find_end(original)
            p2_prompt = P2_PROMPT.replace('{persona}', persona_name) + "\n\n【输入口播稿（无开头钩子）】\n" + body + decon_ctx
            p2_text = _call(
                p2_prompt,
                max_tokens=3000,
            )
            _emit("boost_p2_done", "预埋专家：预埋完成")
        except Exception as exc:
            logger.warning("[boost] P2 failed: %s", exc)
            _emit("boost_p2_error", f"预埋专家失败：{str(exc)[:100]}")

    # ── P3: 呼吸点 ──
    def _run_p3() -> None:
        nonlocal p3_text
        _emit("boost_p3_start", "节奏专家：插入呼吸点")
        try:
            p3_prompt = P3_PROMPT.replace('{persona}', persona_name) + "\n\n【输入口播稿全文】\n" + (p2_text or original)
            raw_p3 = _call(
                p3_prompt,
                max_tokens=3500,
            )
            p3_text = _strip_p3_head(raw_p3)
            _emit("boost_p3_done", "节奏专家：呼吸点完成")
        except Exception as exc:
            logger.warning("[boost] P3 failed: %s", exc)
            _emit("boost_p3_error", f"节奏专家失败：{str(exc)[:100]}")

    # ── P4: 精修正文 ──
    def _run_p4() -> None:
        nonlocal p4_text
        _emit("boost_p4_start", "全篇精修：正文顺滑化")
        try:
            input_text = p3_text or p2_text or original
            p4_prompt = P4_PROMPT.replace('{persona}', persona_name) + "\n\n【输入已完成全文】\n" + input_text
            raw_p4 = _call(
                p4_prompt,
                # 8000 (2026-08-25): P4 输出=全文复写 ~3000字≈逼近 4000 上限, 截断/
                # 大输出空响应风险 (同 P5 前科); thinking 兜底路径 max(8000,·) 不受影响。
                max_tokens=8000,
            )
            p4_text = _strip_p3_head(raw_p4)
            if not p4_text or not p4_text.strip():
                p4_text = input_text
            # 字数下限兜底 (2026-08-15): P4 偶发压缩 13~16% (合并短句/删句),
            # 精修定位是 1:1 打磨, 输出 <88% 原文长度视为越权 → 回退原稿。
            # 88% 而非 95%: 容忍旧稿 || 剥离等合法格式差。
            if len(p4_text) < len(input_text) * 0.88:
                logger.warning(
                    "[boost] P4 shrunk %d→%d chars (<88%%), fallback to original",
                    len(input_text), len(p4_text),
                )
                _emit("boost_p4_error", f"精修输出过短({len(p4_text)}字<{int(len(input_text)*0.88)}字)，已回退原稿防压缩")
                p4_text = input_text
            _emit("boost_p4_done", "全篇精修完成")
            # 首句保序护栏 (2026-08-25): P4 偶发把身份段挪到第一句 → 首屏 opening 卡
            # 变成"大家好我是老谭"自我介绍, 标题感全失 (实测)。输出稿开头必须仍是
            # 原稿开头(钩子), 否则视为越权重组 → 回退原稿。
            import re as _re
            _orig_head = _re.sub(r"^\[[^\]]+\]\s*", "", original.strip())[:12]
            _p4_head = _re.sub(r"^\[[^\]]+\]\s*", "", (p4_text or "").strip())[:12]
            if _orig_head and _p4_head != _orig_head:
                logger.warning(
                    "[boost] P4 首句移位 (原稿开头 %r, 精修稿开头 %r), 回退原稿",
                    _orig_head, _p4_head,
                )
                _emit("boost_p4_error", "精修把开头钩子移位（首屏标题感会丢），已回退原稿")
                p4_text = input_text
        except Exception as exc:
            logger.warning("[boost] P4 failed: %s", exc)
            _emit("boost_p4_error", f"全篇精修失败：{str(exc)[:100]}")

    # ── P1: 电击开场（后置，用 P4 后的正文） ──
    def _run_p1() -> None:
        nonlocal p1_result
        _emit("boost_p1_start", "开场专家：重写前 30 秒 + 标题")
        try:
            input_text = p4_text or p3_text or p2_text or original
            p1_prompt = P1_PROMPT.replace('{persona}', persona_name) + "\n\n【原标题】\n" + (original_title or '') + "\n\n【口播稿全文】\n" + input_text + decon_ctx
            raw = _call(
                p1_prompt,
                json_mode=True,
                max_tokens=1500,
            )
            parsed = _parse_opening(raw)
            if not parsed:
                logger.warning("[boost] P1 parse failed: %s", raw[:100])
                _emit("boost_p1_error", "开场专家：输出格式错误，跳过")
                return
            p1_result = parsed
            _emit("boost_p1_done", "开场专家：前 30 秒重写完成")
        except Exception as exc:
            logger.warning("[boost] P1 failed: %s", exc)
            _emit("boost_p1_error", f"开场专家失败：{str(exc)[:100]}")

    # (P5 情绪标注已于 2026-08-25 拆离 run_boost — 移至 audio.py 生成音频时刻,
    #  与 TTS 同源文本现场标注。独立函数 annotate_emotions 保留供其调用。)

    # ── P-L: 反问目录 (2026-08-25, geo 专属独立层) ──
    # 两段式: LLM 只产 3~5 行反问存 _loop_block, 插入在 final_text 定稿后由代码执行
    # (P4 精修碰不到反问层, 免疫"精修时被当冗余删除")。tech 线跳过 (对照组)。
    def _run_loop() -> None:
        nonlocal loop_block
        _emit("boost_loop_start", "反问目录：通读全文，设计连环反问")
        try:
            loop_prompt = P_LOOP_PROMPT.replace('{persona}', persona_name) + "\n\n【口播稿全文】\n" + original
            raw_loop = _call(loop_prompt, max_tokens=600)
            import re as _re2
            qlines = []
            for ln in (raw_loop or "").splitlines():
                ln = _re2.sub(r"^[\s\d\.、·\-\*\"'“”]+", "", ln.strip())
                ln = _re2.sub(r"[\"'“”\s]+$", "", ln)
                if ln.endswith("？") or ln.endswith("?"):
                    qlines.append(ln)
            if not (3 <= len(qlines) <= 6):
                logger.warning("[boost] P-L bad question count %d: %s", len(qlines), (raw_loop or "")[:80])
                _emit("boost_loop_error", f"反问目录产出异常（{len(qlines)} 问, 需 3~6）, 跳过注入")
                loop_block = None
                return
            loop_block = "\n".join(qlines)
            _emit("boost_loop_done", f"反问目录完成（{len(qlines)} 问, 定稿后注入）")
        except Exception as exc:
            logger.warning("[boost] P-L failed: %s", exc)
            _emit("boost_loop_error", f"反问目录失败：{str(exc)[:100]}")
            loop_block = None

    def _insert_loop_block(text: str) -> str:
        """确定性插入反问目录。

        锚点优先级 (2026-08-25 v2): 认知校准句组之后 > '剥开看'引导词之后。
        校准句("千万别当成简单的XX" + 定调句)必须先于反问目录 — 先立视角再抛
       目录, 目录紧跟定调承接正文; 插在校准前会被校准块截断连贯性 (实测)。
        """
        import re as _re3
        if not loop_block or loop_block in text:
            return text
        anchor = None
        # 优先: 认知校准句组之后 (校准句 + 支撑/定调句, 最多再 3 行, 吃到空行前)
        m_cal = _re3.search(r"千万别当成[^\n]*(?:\n[^\n]*){0,3}", text)
        if m_cal:
            anchor = m_cal.end()
        if anchor is None:
            for key in ("这事儿咱们得剥开看", "剥开看", "确定的逻辑"):
                i = text.find(key)
                if i != -1:
                    end = text.find("。", i)
                    anchor = end + 1 if end != -1 else i + len(key)
                    break
        if anchor is None:
            m = _re3.search(r"大家好[^。]*。", text)
            anchor = m.end() if m else 0
        return text[:anchor] + "\n" + loop_block + "\n" + text[anchor:]

    # ═════ 执行流水线 (2026-08-25: P-L 反问注入 → P4 精修; P5 已拆离) ═════
    # 7层洗稿已是完整爆款结构; P1(电击开场)/P2(预埋)/P3(呼吸点) 是旧六模块逻辑,
    # 跑7层稿只会覆盖钩子/身份段/结尾. 实证(_test_7layer_ab A/B)确认 P1-P3 零增益纯破坏.
    # 现行: P-L(geo: 反问目录注入, 独立层) → P4(逐句表达精修, 1:1锁定结构)。
    # P5 拆离 (2026-08-25): 移到 audio.py _do_tts 入口, 与 TTS 输入同源文本现场标注 —
    # 消灭"改稿后旧标注错配"窗口, boost 回归纯内容职责。annotate_emotions 保留供调用。
    _track = ""
    try:
        _track = (getattr(script.article, "track", "") or "") if script.article else ""
    except Exception:
        pass
    _emit("boost_start", "爆品改造开始（P-L反问目录→P4精修）" if _track == "geo" else "爆品改造开始（P4精修）")

    # P-L 反问目录 (geo 专属; 失败不阻断, P4 走原稿)
    if _track == "geo":
        _run_loop()

    # P4 精修 (输入 = P-L 产物或原稿; P4 失败回退原稿, 不卡死)
    _run_p4()

    # final = P4 精修稿 (P4 失败回退原稿, 不卡死)
    final_text = p4_text or original
    if not final_text.strip():
        final_text = original

    # 剥离内部标注 (层标题/锚点/清单残留)
    final_text = clean_boosted_text(final_text)

    # P-L 反问目录注入 (2026-08-25): 定稿后确定性插入 — P4 精修碰不到反问层,
    # 免疫被当冗余删除; _insert_loop_block 内含幂等保护 (已存在则不重复插)。
    final_text = _insert_loop_block(final_text)

    # ── P6: 拼音纠音审计 (2026-08-25) ──
    # 生僻字/多音字由 config/tts_pinyin_map.json 词表在 TTS 入口自动标 <字|PINYIN>
    # (替代旧的"昇腾→生疼"同音换字)。此处只扫描提示, 让用户知道哪些词被照顾到;
    # 踩到新坑直接往词表加一行, 无需改代码。
    pinyin_fixes: list[str] = []
    try:
        from .pinyin_fix import scan_pinyin_hits
        pinyin_fixes = scan_pinyin_hits(final_text)
        if pinyin_fixes:
            _emit("boost_pinyin_done", f"拼音纠音 {len(pinyin_fixes)} 处: {'、'.join(pinyin_fixes)}")
        else:
            _emit("boost_pinyin_done", "拼音纠音: 本稿无已知易错词")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[boost] pinyin scan failed: %s", exc)

    # ── P7: 流量评审 (2026-08-25 复刻豆包五维框架) ── 只评审不改稿, 报告供人决策
    flow_audit: dict[str, Any] | None = None
    try:
        flow_audit = audit_flow_metrics(final_text)
        if flow_audit:
            _emit("boost_p7_done",
                  f"流量评审 {flow_audit.get('overall', '?')}: "
                  f"评论率{flow_audit.get('comment', {}).get('estimate', '?')} · "
                  f"短板: {'; '.join(flow_audit.get('weaknesses', [])[:2])}")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[boost] P7 audit failed: %s", exc)

    return {
        "boosted_text": final_text,
        "boost_titles": [],  # P1 砍掉, 不再产标题候选
        "p5_annotated": None,  # P5 已拆离 (2026-08-25 → audio.py 生成时现场标), 字段留兼容
        "p4_ok": p4_text is not None,
        "p5_ok": False,
        "loop_ok": loop_block is not None,  # P-L 反问目录 (geo) 是否注入成功
        "pinyin_fixes": pinyin_fixes,
        "flow_audit": flow_audit,
    }


def audit_flow_metrics(text: str) -> dict[str, Any] | None:
    """P7 独立入口: 五维流量评审 (停留/完播/点赞/评论/收藏 + 优势/短板/微调建议)。

    框架复刻豆包测评标准 (2026-08-25): 逐维给"预估值+档位+50字理由", 输出结构化
    JSON。失败返回 None (评审是仪表盘, 不许阻断产线)。
    """
    try:
        raw = _call(P7_PROMPT + "\n\n【待评审最终稿】\n" + text, json_mode=True, max_tokens=2500)
        data = _extract_json(raw)
        if isinstance(data, dict) and data.get("overall"):
            return data
        logger.warning("[boost] P7 parse failed: %s", str(raw)[:100])
        return None
    except Exception as exc:
        logger.warning("[boost] P7 audit call failed: %s", exc)
        return None
