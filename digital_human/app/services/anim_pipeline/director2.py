# -*- coding: utf-8 -*-
"""导演引擎 v2→v3 (0915 三层画面心智模型定稿, 自 scripts/anim_director.py 系统化并入).

与 v1 (planner.py 两步法) 的本质差异 — v2/v3 是导演层正身:
  - 时间轴直出 TTS manifest (音频先行原生实现, 不需要事后 align 修正)
  - 场 (arcs) = 叙事段落边界 (0915: 不按时长算术); 每场一组 (组=容器)
  - v3 三层模型: 首帧(K2 具象+灭字+视角锁死+信息完备) / 动画层(H3 物品动+
    运镜白名单固定/极轻微推拉+禁大面积重绘) / 文字特效层(中文短词主角+
    艺术字体纪律); 美术圣经 = 书级资产; 系列风格锁 (ep2+ 继承 ep1)
  - 每镜: keyframe_zh (K2 首帧) + motion_zh (动画层+文字出场) + camera 机位
          + keyframe_en/motion_en (英文, 生成用)

生成层适配 (k2.py/h3.py 兼容):
  - image_prompt_zh = keyframe_zh 纯画面 (k2.build_prompt 配方注风格, 单一事实源)
  - anim.beats = 单拍 motion_en (h3.build_prompt 节拍壳直接用)
  - 镜长 >10s (H3 配方上限): beats 铺 10s, 草稿定格吸收, overrun_s 标记
"""
from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

from . import shots as shots_mod
from .config import load, resolve_style

logger = logging.getLogger(__name__)

H3_MAX_SPAN = 10.0  # H3 单镜配方上限 (低显存节点 24fps 实测档), 超出草稿定格吸收

DIRECTOR_SYS = """你是顶级动画短片的导演 (Motion Director)。你的任务不是给台词"配插图"，
而是像拍纪录片一样：用真实场景做代入感，用关键词动效做内容，把口播变成画面。

## 受众与双层定位（产线宪法, 优先级最高）

- 我们的视频发布在抖音。观众是在信息流里**高速滑动**的用户：3 秒抓不住就划走。
- 双层定位：**文稿已达内训级（内容深度）, 画面必须达到抖音级（视觉冲击）**。
  内容可以深，画面绝不许性冷淡。你的画面规划必须让一个不懂这本书的人停下滑动的手。

## 三层画面心智模型（PPT 三层, 一切画面设计按这个来 — 0915 用户定稿）

**第1层 · 背景图（代入感）= K2 首帧**
- **具象纪录片式**：真实年代 + 真实地点 + 真实场景 — "1972年的美国小镇空中俯瞰"
  而不是"书桌上一本发光的书"。抽象隐喻（光柱/账页/几何方块/悬浮符号）基本禁用；
  实在无法复原的场景也要有强代入感（街景/室内/人物/实物）
- **全灭字**：首帧必须干净 — AI 生图必出乱码。任何文字/数字/标志都不许画进首帧，
  需要的文字全部留给动画层和文字层
- **视角在生图那一刻锁死**：机位（空拍/俯瞰/街景平视/低角度/特写）在首帧描述里明确，
  之后整段视频不再换机位
- **首帧 = 动画的起始状态，信息完备**（0915 a2p3 用户定式）：动画要用到的所有元素、
  道具、**接触关系**必须在首帧里就位 — 要挤压就画"双手已经扶在两面墙上"、要用力就画
  "已经绷紧肌肉的开始状态"。动画只负责推进/增强首帧已有的东西，不从无到有

**第2层 · 动画层（沉浸感）= H3 让背景活起来**
- **环境物品原地动**：画面里已有的东西尽管动 — 汽车驶过、行人走动、炊烟、
  旗帜飘动、霓虹闪烁、水面波光、光线流转。生活气息越足越沉浸
- **运镜白名单：固定 / 极轻微推拉，仅此两样**（0915 用户实锤 a2p4 横移废）—
  禁横移/跟拍/摇镜/平移追踪；视角由首帧锁死
- **主体位移纪律**：主体人物不横穿画面（横移+追着人重绘=抖废片）。人物若要移动：
  短距离、放在镜内**前段**完成、到位后**静止**；大特效只在人物静止时触发
- **特效时序铁律**：先移动→后静止→再触发特效，移动和特效**绝不同时发生**；
  变身/换装/物体变形 = 大面积重绘，单镜内禁 — 用光效扫过+色彩反转表达转变，
  几何形变大改靠**切镜**（下一镜直接是新形态）

**第3层 · 文字特效层（内容主角）**
- 每镜识别这句话的**关键数字/关键词**（365户 / 90% / 1972 / 搬运工 / 美剧之王），
  设计成画面主角：**大而醒目的动效字，随口播节奏出场**（说到才出）
- **文字语言（0915 用户定稿: 中文优先）**：关键词动效用**中文短词（2-4 字）**—
  "标准""搬运工""美剧之王"直接砸中文；数字/年份/品牌标志保持数字与拉丁字母
  （365 / 1972 / 90% / HBO 天然如此）；中文长句走 text_layer 后期字幕
- **字体纪律（PPT 特性, 0915 用户实锤）**：
  - 每镜**一种**字体风格 — 同镜多组文字共用同一字体语言，禁多种字体混搭
  - **艺术字体优先**（书法/手写/复古装饰/立体描边），**禁黑体/默认无衬线** —
    字体没选好特效就垮（反面教材: 红色"LIVE #1"平淡字体=垮）
  - 字色融入场景色板（正面范本: 巨大的暖琥珀金艺术字"HBO"在他头顶怯生生地
    亮起闪烁）
  - **避让主体不压字**：文字落点规划好，不遮主体脸/关键物，不与其他文字重叠
- 文字出场事件只有超短标 (英文/数字/≤2字中文) 可写进 motion（H3 渲染）; 概念词走 text_layer overlay
- **构图带叙事判断**："公司当时弱小"→标志小、小镇辽阔；"占据90%"→数字铺满画面
- **R9 协同三件套律**（45期拆解提炼, 0915 接入）：每句口播的文字设计**三层同帧联动** —
  ① 字幕层：整句白字小号（caption）② 强调层：句内关键词大字**金**（hero_number，数字/
  金额/概念/引用**原词提取**）③ 冲击层：疑问/对比/负面词红色特大字（impact，"？" /
  "VS" / 负面冲击词）。**三色语义（抖音知识区标准）：白=正文 / 金=强调 / 红=冲击**。
  三层时间戳同帧（同一 t_start 出现）
- **H3 入画"一镜一事"铁律**（0915 六样本实锤, 叠字=结构性触发点, 同结构重抽必坏）：
  - 每镜最多 **1 个** H3 入画文字事件 — 数字/年份/拉丁标志 **或** 2 字中文超短词，二选一
  - **数字与中文绝不共现同镜**（1987 和"定价权"必须拆镜，或错开整拍互不重叠）
  - **3 字及以上中文词（定价权/美剧之王/标准制定者）→ 全走后期金字**，不进 H3
  - **文字密集场景（卡片阵/招牌墙/屏幕墙）→ 场景内全空白**，文字全部后期叠加
  - H3 入画只是锦上添花，后期才是文字主战场（字体保真零乱码）
- **同帧音效点**：音效对齐的是**强调大字的出现帧**（不是句子开头）；你在文字设计里定好
  大字时机，声音由后期按语义挂——语义映射：数字/金额→money(收银机类) / 引用·设问→
  suspense_hook / 对比·VS·冲击→impact / 概念·点题→punchline / 打字动画句→typing /
  转场新段→transition_soft；同类内轮换选音防腻

### 炫度纪律（每一镜都要过这把尺子）
1. **每镜首拍 1 秒内必须有可见变化**（文字浮出/物品运动/光效/色彩脉冲）— 没有慢热开场
2. **构图饱满、色块对比强**：鲜艳饱和的大色块 + 明确的视觉主体；禁大面积空旷单色底
3. **ending 动感化**：一道光扫过定格 / 大字定格 / 色彩收束脉冲 —
   "the scene settles, calm hold" 只作降级兜底；**白闪硬切绝对禁用**
   (0915 用户裁决"白闪绝对是个错误"——旧记录"白闪放开"作废)
4. 基调默认 **明亮鲜艳**（日光/暖色/高饱和）；深色暗段只给危机/转折叙事, 全集 ≤1/3 镜
5. **密度规则（45期实参）**：前 30s 高密度 — 每镜必有文字/特效事件，强调事件节拍
   ~每 2.4s 一个；30s 后降档留呼吸（高密度不是全程轰炸）

### 人物规范（0914 晚用户拍板: 卡通脸全放开）
- 人物可以出场并担任主角 — 叙事本质是"人的对比/决策/困境"时直接画人物
- 画法: 以【美术圣经·角色策略】为准 (人物形态按其锚执行), 全部人物（含历史名人）都露脸 —
  强风格化变形 (大头比/简化五官/夸张表情), 名人靠标志特征识别 (发型/眼镜/胡型/体态/标志物)
- **角色锁定卡 (圣经 characters, 0922 用户令)**: 出场角色的 keyframe_zh 必须原样携带其
  look 关键词 (服饰+脸型发型+标志道具一起入画) — 场景换了观众靠服饰认人; 禁改名换装
- 露脸角色当场双约 (年龄段长相+表情基调) 跨镜一致; 不同人物外形要有区分度
- 表情特写与双人表情反差是高级武器

## 输入
- 稿件文本（带段落标签【A-B秒｜段名】）
- TTS manifest（每个音频段落的精确时长和文本, 含气口停顿）

## 你的工作流程（严格按序）

### 叙事内功 (0923 用户令)
你熟读《拉片子：电影电视编剧讲义》和《故事的解剖》, 切场与画面策略时以这两本书的叙事方法论为内功底座。

### 第一步: 读 manifest 建时间骨架
每个 manifest segment = 一个时间块。把时间块映射到稿件段落，
得到每个段落的精确起止时间。

### 第二步: 切场 (叙事段落)
一场 = 一个完整的叙事段落/转折/论点（通常 2-5 句），**边界跟叙事逻辑走，不按时长算术**。
例: "从365户起步到90%份额的对比故事" = 一场；"从搬运工到标准制定者的身份反转" = 另一场。

### 第三步: 对每场设计画面策略
- **定隐喻 (visual_metaphor, 必填)**: 一句话声明这一场的核心视觉隐喻及映射 —
  "渠道=越铺越长的管道, 利润=越流越细的金币流"。场内每一镜都是这个隐喻的一个面/一个时刻,
  画面自己讲完因果。抽象概念禁止直接上画面, 必须先翻译成物理过程或物体
- **定场景**：这一场发生在哪 — 真实地点/年代/环境（1972年宾夕法尼亚小城、90年代的
  曼哈顿公寓客厅、院线影院门口的夜晚）。一场内共享同一场景，镜与镜之间只变机位/距离/时刻
- **定运动线**：一句话 — 这个场景里什么在动（车流/人群/光线/时间流逝）

### 第四步: 场内切镜 (画面单元)
一镜 = 一个画面单元（一个机位/一个动作/一个内容重点）。
**句子边界是自然参考，不是法律** — 导演按画面需要切，不数句子。
- 每镜 2-6 秒 (口播≤2句); 段内镜数 = 段时长÷4 向上取整 不封顶; 整集镜数 ≈ 集时长÷5 — 视觉密度是留存硬指标, 宁密勿疏
- 相邻镜必须换构图 (景别/机位/主体动作至少一项不同); 严禁「同一场景 机位不变」式续镜
- 每场固定一组（组 = 场的容器，组不再有独立画面语义）
- 相邻镜是机位/距离/时刻的推进（空拍的下一镜给街道平视），禁跳场景

### 画面句丰富度规格 (0923 用户令: 对齐风格选型试镜镜基准)
- 每镜 keyframe_zh = **电影场景描述** (像给摄影师讲戏), 不是物体技术规格书
- **人物优先**: 画面必须有人在做事(走路/翻书/惊讶/攀爬), 禁止纯物体静态陈列; 人物露脸带表情
- **叙事驱动**: 每镜讲一个微型故事(谁在什么困境中做了什么), 禁止"X占据画面中央"式说明书
- **自然语言**: 用电影视觉语言 (光线洒落/背影消失在走廊尽头/手指颤抖着翻开书页), 禁止色值hex码(如#E67E50)和重复质感词(如每句都写"手工捏制痕迹")
- 色板/质感由 K2 风格配方自动注入, 你**不需要**在 keyframe 里写色值和质感 — 只写画面内容和情绪
- 服饰写明具体单品且能区分人物关系
- 出场角色必须携带圣经角色锁定卡的 look 关键词串 (整串, 禁只写名字)
- 切镜密度/数量由装包制槽位系统决定 (每槽一镜), 你只负责把每镜的画面句写丰富

### 景别升级 (0923 用户实锤: 73%小景别=桌面幻灯片, 格局未打开)
- **画面格局**: 每3-4镜中至少有1镜用大场景构图 — 全景/远景/鸟瞰/广角 (远山/天空/大地平线/宏伟建筑/广阔空间), 让观众看到"世界"而不仅是"桌面"
- **特写控制**: 连续2镜特写后, 下一镜必须切大场景
- **景深三层**: 前景(主体/道具) + 中景(配角/动作) + 远景(环境/天空) 三层共存, 禁只有单层
- **注意**: 景别多样性体现在 keyframe_zh 的构图描述中, 切镜数量/密度仍由装包制槽位系统决定 (每槽一镜, 不多不少)

### 清单/导览段铁律 (0916 卡牌事故 + 0917 拍板, 用户最不想要)
口播逐条列举时 (第X集/工具清单/多条测试), **严禁把条目物化成卡牌/卡片/图鉴式陈列**
— 被毙实锤, 全片禁卡牌/集换式陈列画面。**正解 (0917 拍板, 强制): 全段一个连贯视觉
隐喻 (旅程/流水线/地图/登山线), 每镜推进一站 — 每条目是隐喻路上的一站, 不是一张卡**。
条目文字信息一律交给 text_layer/花字层, 画面只管隐喻的推进。

### 通用商务素材黑名单 (0917 用户裁决, 全片默认禁)
知识口播的画面想象力禁退回"商务PPT素材池"。以下画面**默认禁用, 出现即废稿**:
白板/写字板前讲PPT、咖啡厅对坐聊天、落地窗前望城市天际线、报表/文件/笔记本电脑特写、
会议室开会。它们零信息零隐喻 — 跟任何口播都兼容, 等于跟任何口播都没有增益。
唯一例外: 口播本身在叙述真实场景/历史事件时, 按叙事对象画 (辩论现场/听证会现场)。
替代方向: 把概念画成物理过程 (管道/漏斗/天平/多米诺/滚雪球/登山), 或一帧同屏对比。

### 政治敏感画面绝对禁区 (0917 用户令, 平台红线 — 出现即废稿, 变形不改性质)
任何画面禁止出现: ① **中国地图** (含示意/局部/变形拼图 — 需要地理概念改用抽象
网格/光带); ② **任何国旗、国徽** (任何国家, 含卡通化旗帜徽章); ③ **国家领导人形象**
— 中国历任领导人绝对禁入画 (含卡通/大头变形/剪影/雕塑/画像/演员扮相), 现任外国
元首同禁; ④ 天安门/人民大会堂等政治地标。替代: 概念隐喻 (权力=聚光灯, 国家=舞台,
地理=发光网格); 书中非领导人历史人物按名人卡通规范画。

### 第五步: 每镜三层设计
1. keyframe_zh/en — 首帧（第1层）：具象场景 + 全灭字 + 视角锁死 + 自然语言完整句
   （含明确镜头词与光线描述）
2. motion_zh/en — 动画层（第2层）+ 文字出场（第3层）：背景里什么在动 + 轻微运镜 +
   关键词动效事件（什么字、何时浮现、多大、什么效果）
3. text_layer — 后期字幕/补充文字（中文长句、上字幕明确年份等, 带节奏 t_start/t_end）

## 六条铁律（违反任何一条=废稿）

1. **音频先行**: 每镜的 t_start/t_end 必须精确对齐 manifest 时间块边界（可跨块组合，不可自造时间点）
2. **首帧=运动起点**: keyframe 是视频第一帧 — 画面里要有"即将发生什么"的张力,
   给运动留出空间; 场景必须已在运动状态中（街上已有车人）
3. **双向增益**: 画面必须补充/放大/对比口播，禁复述口播
4. **时间预算**: 场内总镜时长 = 场时长，不多不少
5. **场内连贯·每镜必换构图**: 同一场共享场景/年代/色调, 但每镜景别/机位/时刻至少一项不同 — 续镜(机位不变)=废稿
6. **全片统一**: 所有镜头风格一致（美术圣经约束）

## 生图/生视频技术禁忌 (K2+H3 实测)

### K2 首帧全灭字（铁律）
- keyframe 里**禁止任何可读文字/数字/字母/标志** — 屏幕留空, 招牌牌匾一律空白无字
- 文字全部走: H3 动画层浮出（英文/数字/短标志）或 text_layer 后期（中文长句）

### H3 动画层约束 (0915 a2p4 实锤: 横移+边走边变身 = 抖废片)
- **运镜白名单**: 固定 / 极轻微推近 / 极轻微拉远 — **横移/跟拍/摇/平移追踪全禁**
- **环境动效不限**: 远处车流/行人/烟/旗/光/水/云尽管动 (原地环境级, 不带镜头跟)
- **主体移动短距先行**: 人物移动 = 短距离 + 镜内前段完成 + 到位静止; 移动期间无特效
- **特效只在静止主体上触发** (用户定式: 走到画面中央→站定→光效扫过→触发变身)
- **动画 = 已有元素的原位增强**: 墙推进/肌肉紧绷/脸色红涨/表情变化/光效增强 — 全是
  首帧里已有元素的变形推进; **禁引入首帧没有的元素, 禁让分离的元素建立新接触**
  (墙从远处"移动到"人身上 = 新接触关系 = 大重绘; 正确: 首帧双手已扶墙, 动画墙直接挤压)
- **大面积重绘禁**: 换装/物体变形/场景变身 → 用光效+色彩反转表达, 几何大改靠切镜
- 文字出场事件: **只有**英文/数字/≤2字中文超短标才写进 motion（H3 渲染）; 其余一律
  text_layer overlay（落盘前有确定性军规, 违规浮字会被整段删掉转 overlay — 白写）

### text_layer (文字后期叠加, 中文长句保真通道)
  [{"kind": "title|caption|hero_number|year|impact|overlay|logo_note|typewriter", "text": "...", "t_start": 0.5, "t_end": 3.0, "color": "gold|red"}]
  impact = 红色冲击大字 (?/VS/负面词); overlay = 军规下沉大字 (3字+概念词/书法冲击体,
  H3 画不了 → 剪辑层贴, color gold|red); 三色: 白=正文 金=强调 红=冲击
  t_start/t_end 是镜内相对时间 (0 = 镜头开始); 随口播节奏定

## 金标准范本 (照这个水平写首帧 — 三型各一; 每条同时示范: 卡通大头变形/圣经色引用/全灭字/视角锁死)

【范本一 · 隐喻型: 概念画成物理过程】口播"流量越做越多，利润反而越来越薄"
首帧: "平视中景，一条发光的青蓝色管道从画面左侧蜿蜒铺向右侧地平线，管道越铺越远越细，
末端滴落的暖琥珀金金币流越来越稀薄（近处金币堆成小山，远处只剩零星两三枚），一个1988
赛璐璐卡通大头老板（大头比、夸张愁眉、领带松垮）在管道近端拼命往前铺新管，天青蓝天空与
暖米纸白大地为主色，金币为暖琥珀金，画面无任何文字，固定机位"
— 金在: 渠道=管道、利润=金币流, 两个抽象概念变成一个自己讲完因果的物理过程, 画面补充
而非复述口播。

【范本二 · 对比同屏型: 冲突一帧讲完】口播"听广播的认为尼克松赢，看电视的看到他满头大汗"
首帧: "对称构图正中一道垂直金线把画面一分为二: 左半深夜收音机特写, 暖琥珀金声波中浮现
1988赛璐璐卡通大头尼克松（发型整齐、下颌坚毅）的威严剪影; 右半一台老式电视机, 屏幕里
同一个卡通大头尼克松满头豆大汗珠、脸色发信号红、憔悴眨眼; 左半暖米纸白底对右半深青蓝底,
收音机旋钮与电视屏幕全部空白无字, 平视机位"
— 金在: "同一人两种呈现→判断反转"的知识核心, 一个同屏对比画完, 分割线本身就是论点。

【范本三 · 构图叙事型: 画面比例即论点】口播"HBO刚起步，手里只有365个订阅用户"
首帧: "俯瞰空拍, 画面九成留给辽阔空旷的暖米纸白原野, 原野中央一间小木屋亮着一点暖琥珀金
灯光, 地平线尽头挤着一线灰蓝色城市剪影, 一个1988赛璐璐卡通大头男人站在木屋旁渺小如豆,
天青蓝天空占画面上方三分之一, 无任何文字, 极轻微推近"
— 金在: "弱小"不用台词讲, 用比例讲 — 九成空旷 vs 一点灯光。

## 输出格式
严格 JSON (场 arc → 组 group(每场一组) → 镜 shot):
{
  "ep_summary": "一句话本集画面策略",
  "arcs": [
    {
      "arc_id": "A1",
      "narrative": "一句话描述这个场讲什么故事",
      "visual_metaphor": "一句话: 核心视觉隐喻及映射 (A=B), 场内每镜都是它的一个面",
      "motion": "一句话描述这个场景里什么在动",
      "t_start": 0.0, "t_end": 4.9
    }
  ],
  "groups": [
    {
      "group_id": "S01",
      "arc_id": "A1",
      "t_start": 0.0, "t_end": 4.9,
      "narration": "这一场的完整口播文本",
      "camera": "空拍|平视|低角度|俯瞰|特写|缓推|固定",
      "keyframe_zh": "场的场景定调（真实地点/年代/环境一句话, 中文）",
      "motion_zh": "场内什么在动（车流/人群/光线变化, 中文）",
      "shots": [
        {
          "t_start": 0.0, "t_end": 4.9,
          "narration": "该镜对应的口播片段（原句或句段）",
          "keyframe_zh": "首帧（中文自然语言完整句: 具象场景+机位+光线+色调; 全灭字; 视角锁死）",
          "keyframe_en": "English keyframe description, same composition, no text",
          "motion_zh": "动画层: 背景什么在动 + 轻微运镜 + 文字出场事件（什么字何时怎么浮出）",
          "motion_en": "English: ambient object motion + slight camera + text appearance events (H3 renders short text)",
          "camera": "空拍|平视|低角度|俯瞰|特写|缓推|固定",
          "text_layer": [{"kind":"hero_number","text":"365户","t_start":0.5,"t_end":2.0}]
        }
      ]
    }
  ]
}
"""


def _substitution_block() -> str:
    """国家指代表 → 宪法拼装块 (0917 用户令, 央视同款手法).

    表在 config/compliance_visual.json substitutes — 改表即宪法同步 (模块加载时
    拼入, 双源永不漂移); 拼装失败不炸模块加载 (空块=只靠禁区条款)。
    """
    try:
        from app.services import compliance as _cmp
        subs = _cmp.visual_substitutes()
    except Exception:  # noqa: BLE001
        return ""
    if not subs:
        return ""
    rows = "；".join(f"{k}＝{v}" for k, v in subs.items())
    return ("\n### 国家指代手法 (0917 用户令, 央视同款 — 表现国家概念的正解)\n"
            "画面需要指代某个国家/地区/民族时, **禁画国旗/国徽/地图**, 一律用公认指代物: "
            f"{rows}。指代物按赛璐璐卡通风格画 (实体或拟人均可) — 央视等主流媒体同款手法; "
            "表外国家用其最具代表性的动物/植物意象, 同样禁用其国旗国徽图案。\n")


DIRECTOR_SYS = DIRECTOR_SYS + _substitution_block()


# ── 美术圣经 (书级资产, 缓存复用) ─────────────────────────────

def _bible_cache_path(book_title: str) -> Path:
    return shots_mod.anim_output_root() / "_资产" / f"圣经_{shots_mod._safe(book_title)}.json"


def load_or_derive_bible(book_id: str, book_title: str, force: bool = False) -> dict[str, Any]:
    """圣经一次生成全系列锁定 (书级资产); 缓存在 _资产/圣经_{书}.json.

    force (0922 艺术圣经页): 无视缓存重掷一版 (风格绑定/灵魂三问可能已变)."""
    cache = _bible_cache_path(book_title)
    if cache.exists() and not force:
        try:
            data = json.loads(cache.read_text(encoding="utf-8"))
            if data.get("style_prefix"):
                logger.info("[plan] 圣经复用 (书级锁定): %s", cache.name)
                return data
        except Exception:  # noqa: BLE001
            logger.warning("[plan] 圣经缓存损坏, 重新生成: %s", cache)
    import sqlite3
    con = sqlite3.connect(load().db_path)
    con.row_factory = sqlite3.Row
    row = con.execute("select input_json from book_projects where id=?", (book_id,)).fetchone()
    # 0923 角色依据增强 (用户问"人物造型依据是什么"): 总纲各集主题+贯穿人物喂给圣经 LLM —
    # 角色不再是凭核心主张瞎推的原型, 而是吃书内真实叙事脊柱 (导演层的贯穿人物字段)
    eps_rows = con.execute(
        "select ep_index, title, roadmap_json from book_episodes where book_id=? order by ep_index",
        (book_id,)).fetchall()
    con.close()
    ij = json.loads((row["input_json"] if row else None) or "{}")
    soul = ij.get("灵魂三问") or {}
    audience = (ij.get("受众地图") or {}).get("value") or {}
    ep_lines = []
    for er in eps_rows or []:
        try:
            rm = json.loads(er["roadmap_json"] or "{}")
        except Exception:  # noqa: BLE001
            rm = {}
        ep_lines.append(f"- 第{er['ep_index']}集《{er['title']}》贯穿人物: {rm.get('贯穿人物') or '未定'}")
    ep_block = ("\n【总纲·各集主题与贯穿人物 (characters 必须覆盖这些真实叙事脊柱, "
                "可再补 0-2 个概念原型角色)】\n" + "\n".join(ep_lines)) if ep_lines else ""
    # 0923 樊登全书稿 (用户令): 讲述稿含书内真实人物/故事原味 — 角色取材第一来源
    ff_text = ""
    try:
        from app.services.book_service.fandeng_full import load_fandeng_full
        ff_text = str(load_fandeng_full(book_title) or "")[:20000]
    except Exception as exc:  # noqa: BLE001
        logger.warning("[plan] 圣经喂樊登稿跳过: %s", exc)
    ff_block = ("\n【樊登全书讲述稿 (characters 优先从这里取真实人物与故事角色, "
                "服饰道具贴合其在书中的真实形象)】\n" + ff_text) if ff_text else ""

    from app.config import load_config, set_config
    set_config(load_config())
    from app.services.book_service.creation_common import _llm, _parse_json
    sys_p = (
        "你是动画短片的美术指导 (Art Director)。为一系列拆书动画短片制定美术圣经 — "
        "全系列从头到尾一个视觉身份, 像迪士尼动画一样统一。\n\n"
        "产出以下字段:\n"
        "- style_prefix: ComfyUI 提示词前缀 (英文, 逗号分隔, 定义整体风格; 每镜必带)\n"
        "- color_palette: 色彩体系 (主色/辅色/情绪色/禁用色, 中文描述)\n"
        "- texture: 线条与质感 (扁平/厚涂/水彩/3D 选一, 加描述)\n"
        "- character_policy: 角色出场策略 (出场密度与叙事用法; 画法以【风格家族】为准 — 人物形态按其锚 "
        "(2D/3D/Q版) 执行, 全部人物含名人都露脸, 名人靠标志特征识别不做写实肖像)\n"
        "- 服饰与露脸铁律 (0922 用户令): **卡通脸必须有脸有表情** — 禁无脸/背影/剪影偷懒; "
        "**服饰细节到位且能快速区分人物关系** — 身份/阵营/地位一眼可辨\n"
        "- characters 角色锁定卡 (0922 用户令): 本书 2-4 个主要角色, 每个给 "
        "{name, role, look} — look=服饰+脸型发型+标志道具的关键词串 (中文 25-50 字, "
        "全书每镜原样携带, 观众靠服饰跨场景认人); look 禁文字载体道具 (标语牌/横幅/"
        "招牌/带字物件 — K2 出字即乱码), 道具一律造型物; 禁军装警服制式与国徽类元素\n"
        "- text_graphic: 大字卡/数字卡与动画的融合方式 (底色/入场动画风格)\n"
        "- mood_keywords: 整体氛围关键词 (英文, 3-5 个)\n\n"
        "铁律: 风格选一种并锁死, 禁多风格混用; 色板贯穿全片; 质感统一。\n"
        "受众铁律 (产线宪法): 视频发布在抖音, 观众是高速滑动的用户 — 基调必须 "
        "bright / vivid / 高视觉密度, 构图饱满色块对比强; 禁大面积暗底、禁 restrained "
        "性冷淡、禁'一束光照暗房'式电影感低调; 深色仅限危机叙事段且全集 ≤1/3 镜。\n"
        '输出严格 JSON: {"style_prefix": "...", "color_palette": "...", '
        '"texture": "...", "character_policy": "...", "text_graphic": "...", '
        '"mood_keywords": "..."}'
    )
    l1 = ((audience or {}).get("L1") or {}).get("reader", "")
    # 0923 宪法进源头 (用户令): 圣经/角色卡生成时注入画面宪法 — 角色look从源头规避
    # 政治图像/军警制式/文字载体道具, 下游守门只是兜底
    from app.services import compliance as _cmp_law
    _law = _cmp_law.visual_constitution_prompt()
    from .config import resolve_style
    style = resolve_style(book_title)
    user = (f"书名：《{book_title}》\n"
            f"核心：{soul.get('core', '')}\n"
            f"收益：{str(soul.get('gain', ''))[:150]}\n"
            f"目标观众：{l1[:80]}\n"
            f"系列集数：约 6-9 集, 每集 5 分钟\n"
            f"风格家族 (已由书级风格配方锁定, 你的 style_prefix 必须融入此家族, 不得另起风格): "
            f"{style.get('desc') or style['style_prompt_head']}"
            + ep_block + ff_block + "\n" + _law)
    data = _parse_json(_llm().chat(sys_p, user, model="pro", temperature=0.4)) or {}
    if not data.get("style_prefix"):
        logger.warning("[plan] 圣经生成失败, 走空 (每镜自带风格尾兜底)")
        return {}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    logger.info("[plan] 圣经生成并缓存 (书级锁定): %s", cache)
    return data


# ── 规划主流程 ─────────────────────────────────────────────────

# ── 字符级对账: LLM 只管切分意图, 时间轴/narration 由 manifest 确定性推导 ──

_STRIP_CH = set(" \t\r\n，。！？；：、,.!?:;\"'“”‘’（）《》〈〉【】[](){}<>—…·")


_TTS_MARK_RE = re.compile(r"-\d+(?:\.\d+)?s-|<[^|>]+\|[^>]+>")


def _norm_with_map(text: str) -> tuple[str, list[int]]:
    """规范化文本 + norm 字符 → 原文下标映射 (剥标点空白, 同 shots.norm_for_match 语义).

    0918 口径同步: TTS 指令同步剥 — 停顿标记 -Xs- 整段丢; 拼音 <字|PINYIN>
    保留"字"的下标 (丢 <、|PINYIN> 部分)。不同步则旧形态镜 narration 锚定
    失配 → 错位重分配 (align s07 槽 7.7→8.8 误打回链实锤)。"""
    drop: set[int] = set()
    for m in _TTS_MARK_RE.finditer(text):
        s = m.group(0)
        if s.startswith("<"):
            word_len = len(s[1:].split("|", 1)[0])
            drop.add(m.start())  # '<'
            drop.update(range(m.start() + 1 + word_len, m.end()))  # '|PINYIN>'
        else:
            drop.update(range(m.start(), m.end()))  # -Xs- 整段
    keep = [i for i, ch in enumerate(text) if i not in drop and ch not in _STRIP_CH]
    return "".join(text[i] for i in keep), keep


# ── 窗口锁定对齐的公共件 (plan_scene 用; _realign_narrations 内有同款闭包,
#    全集路径已实证不动, 刻意不合并 — 0915) ──────────────────────────

def _packs_stream(segs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    """manifest segs → (packs, norm 流). pack = 单个 TTS 包的字符区间/原文/时间."""
    packs: list[dict[str, Any]] = []
    parts: list[str] = []
    off = 0
    for sg in segs:
        norm, keep = _norm_with_map(sg["text"])
        if norm:
            packs.append({"lo": off, "hi": off + len(norm), "text": sg["text"],
                          "keep": keep, "t0": sg["t_start"], "dur": sg["duration"]})
            parts.append(norm)
            off += len(norm)
    return packs, "".join(parts)


def _pos_to_time(packs: list[dict[str, Any]], pos: int) -> float:
    for p in packs:
        if p["lo"] <= pos < p["hi"]:
            frac = (pos - p["lo"]) / max(p["hi"] - p["lo"], 1)
            return p["t0"] + frac * p["dur"]
    return packs[-1]["t0"] + packs[-1]["dur"] if packs else 0.0


def _pos_to_orig(packs: list[dict[str, Any]], pos: int) -> tuple[dict[str, Any], int]:
    for p in packs:
        if p["lo"] <= pos < p["hi"]:
            return p, min(pos - p["lo"], len(p["keep"]) - 1)
    return packs[-1], len(packs[-1]["keep"]) - 1


def _slice_orig(packs: list[dict[str, Any]], a: int, b: int) -> str:
    """norm 区间 [a,b) → 原文切片 (跨包拼接)."""
    out: list[str] = []
    cur = a
    while cur < b:
        p, i0 = _pos_to_orig(packs, cur)
        end_rel = min(b - p["lo"], p["hi"] - p["lo"])
        i1 = p["keep"][min(end_rel - 1, len(p["keep"]) - 1)] + 1
        out.append(p["text"][i0:i1] if i1 > i0 else p["text"][i0:i0 + 1])
        cur = p["hi"]
    return "".join(out).strip()


def _realign_narrations(doc: dict[str, Any], segs: list[dict[str, Any]]) -> dict[str, int]:
    """组/镜的 t_start/t_end 与 narration 按 manifest 字符流重切 (确定性, 0916 v2).

    v1 (0914): 镜 narration 头 14 字 locate → 切点时间包内字符比例插值.
    v1 之坑 (ep1 实锤, 用户诊断"规划期时间轴没算明白"): ①包内插值=漂移源,
    定格补差泛滥; ②切点落包中=劈句尾 ("用户。"型 ragged); ③重跑对账时 ragged
    头做锚 + 空镜保留旧时间 → 时间轴跑散 (断裂/重叠).
    v2 (0916): 切点吸附包边界 (0913 包化=一包一句, 包边=句边=唯一合法切点,
    时间=包边界精确值零漂移); 文本锚失败用现有 t_start 时间锚兜底; 切点严格
    递增 + 空镜剔除; 口播超 H3_MAX_SPAN 自动按整句包拆镜 (用户令: 一个不够
    就两个, 物理上限不动).
    """
    import copy as _copy

    tc = float(load().brand_card.opening_sec)
    # 包级 norm 流 (全局)
    packs = []
    stream_parts = []
    offset = 0
    for sg in segs:
        norm, keep = _norm_with_map(sg["text"])
        if norm:
            packs.append({"lo": offset, "hi": offset + len(norm), "text": sg["text"],
                          "keep": keep, "t0": sg["t_start"], "dur": sg["duration"]})
            stream_parts.append(norm)
            offset += len(norm)
    if not packs:
        return {"split": 0, "dropped": 0}
    stream = "".join(stream_parts)
    audio_end_t = packs[-1]["t0"] + packs[-1]["dur"]

    def pos_to_time(pos: int) -> float:
        for p in packs:
            if p["lo"] <= pos < p["hi"]:
                frac = (pos - p["lo"]) / max(p["hi"] - p["lo"], 1)
                return p["t0"] + frac * p["dur"]
        return packs[-1]["t0"] + packs[-1]["dur"]

    def time_to_pos(t: float) -> int:
        """音频相对时间 → 字符位 (包内线性, 仅作吸附前粗锚/拆镜取文).
        缝隙容差 ±0.05s: 句包 t 值 2 位舍入会产生发丝缝 (ep1 实锤 59.27s
        落缝 → 兜底流尾 → 整组饿死), 落缝映射到邻包边."""
        if t <= 0:
            return 0
        for p in packs:
            if p["t0"] <= t < p["t0"] + p["dur"]:
                frac = (t - p["t0"]) / max(p["dur"], 1e-6)
                return int(round(p["lo"] + frac * (p["hi"] - p["lo"])))
            if t < p["t0"] and t >= p["t0"] - 0.05:
                return p["lo"]
            if t >= p["t0"] + p["dur"] and t < p["t0"] + p["dur"] + 0.05:
                return p["hi"]
        return len(stream) if t >= audio_end_t else packs[0]["lo"]

    def pos_to_orig(pos: int) -> tuple[str, int]:
        """norm 流位置 → (所在包原文, 包内原文下标)."""
        for p in packs:
            if p["lo"] <= pos < p["hi"]:
                return p, min(pos - p["lo"], len(p["keep"]) - 1)
        return packs[-1], len(packs[-1]["keep"]) - 1

    def slice_orig(a: int, b: int) -> str:
        """norm 区间 [a,b) → 原文切片 (跨包拼接)."""
        out = []
        cur = a
        while cur < b:
            p, i0 = pos_to_orig(cur)
            end_rel = min(b - p["lo"], p["hi"] - p["lo"])
            i1 = p["keep"][min(end_rel - 1, len(p["keep"]) - 1)] + 1
            out.append(p["text"][i0:i1] if i1 > i0 else p["text"][i0:i0 + 1])
            cur = p["hi"]
        return "".join(out).strip()

    def locate(needle_norm: str, frm: int, to: int) -> int | None:
        if not needle_norm:
            return None
        p = stream.find(needle_norm, frm)
        if 0 <= p < to:
            return p
        head = needle_norm[:10]
        if len(head) >= 5:
            p = stream.find(head, frm)
            if 0 <= p < to:
                return p
        return None

    def snap_mono(pos: int, floor: int) -> int:
        """切点吸附最近包边界 (整包归内容占比大的一侧, frac>0.5 归前段);
        吸附点已被前界占用则顺延下一个包边 — 严格递增, 杜绝空镜带旧时间."""
        if floor >= len(stream):
            return len(stream)
        if pos <= floor:
            pos = floor + 1
        cand = pos
        for p in packs:
            if p["lo"] <= pos < p["hi"]:
                frac = (pos - p["lo"]) / max(p["hi"] - p["lo"], 1)
                cand = p["hi"] if frac > 0.5 else p["lo"]
                break
        if cand <= floor:
            for p in packs:
                if p["lo"] > floor:
                    cand = p["lo"]
                    break
                if p["hi"] > floor:
                    cand = p["hi"]
                    break
            cand = min(cand, len(stream))
        return cand

    def anchor_pos(head: str, t_abs: float, frm: int, to: int) -> int:
        """切点粗锚: 时间锚为主 (t_start 反查字符位, 天然单调), 文本锚仅在
        ±25 字内采纳 (ragged 头总能"命中"但位置漂 — 文本只配微调不配导航)."""
        tp = time_to_pos(t_abs - tc)
        tp = min(max(tp, frm if to > frm else tp), to)
        lp = locate(head, frm, to)
        if lp is not None and abs(lp - tp) <= 25:
            return lp
        return tp

    # 组按时间序处理 (doc 列表序≠时间序 — ep1 实锤 S08 开场组在列表尾,
    # 按列表序单调推进会把整组压到流尾饿死; 时间锚+严格单调必须时间序)
    groups = sorted(doc.get("groups") or [], key=lambda g: float(g.get("t_start") or 0))
    # 组边界 (首组强制 0; 吸附包边)
    bounds: list[int] = []
    for gi, g in enumerate(groups):
        if gi == 0:
            bounds.append(0)
            continue
        pos = anchor_pos(_norm_with_map(g.get("narration") or "")[0][:16],
                         float(g.get("t_start") or 0), bounds[-1], len(stream))
        bounds.append(snap_mono(pos, bounds[-1]))
    bounds.append(len(stream))
    by_group_pre: dict[str, list[dict[str, Any]]] = {}
    for s in doc["shots"]:
        by_group_pre.setdefault(s.get("group_id"), []).append(s)
    for gi, g in enumerate(groups):
        _gshots = by_group_pre.get(g["group_id"]) or []
        # 0919 装包制组 (镜全 zone/packed): 组窗=槽包络已对, 不按包边重切
        if _gshots and all(s.get("zone") or s.get("packed") for s in _gshots):
            continue
        a, b = bounds[gi], bounds[gi + 1]
        if b > a:
            g["t_start"] = round(tc + pos_to_time(a), 2)
            g["t_end"] = round(tc + pos_to_time(b), 2)
            g["narration"] = slice_orig(a, b)[:300]
    # 镜边界 (组内; 组首镜锚组界; 空镜剔除不保留旧时间)
    by_group: dict[str, list[dict[str, Any]]] = {}
    for s in doc["shots"]:
        by_group.setdefault(s.get("group_id"), []).append(s)
    dropped = 0
    for gi, g in enumerate(groups):
        gs = by_group.get(g["group_id"]) or []
        if not gs:
            continue
        a, b = bounds[gi], bounds[gi + 1]
        mb: list[int] = [a]
        for s in gs[1:]:
            pos = anchor_pos(_norm_with_map(s.get("narration") or "")[0][:14],
                             float(s.get("t_start") or 0), mb[-1], b)
            mb.append(snap_mono(pos, mb[-1]) if pos < b else b)
        mb.append(b)
        keep: list[dict[str, Any]] = []
        for i, s in enumerate(gs):
            if s.get("zone") or s.get("packed"):  # 0919 特区/装包镜: 槽位神圣, 不按包边重切
                keep.append(s)
                continue
            ma, mbnd = mb[i], mb[i + 1]
            if mbnd <= ma:
                dropped += 1
                logger.warning("[d2] 空镜剔除 %s (切点吸附包边后无口播区间)", s.get("shot_id"))
                continue
            s["t_start"] = round(tc + pos_to_time(ma), 2)
            s["t_end"] = round(tc + pos_to_time(mbnd), 2)
            s["narration"] = slice_orig(ma, mbnd)[:300]
            keep.append(s)
        by_group[g["group_id"]] = keep
    doc["shots"] = [s for g in groups for s in (by_group.get(g.get("group_id")) or [])]
    doc["shots"].sort(key=lambda s: float(s["t_start"]))
    # 0919 特区缝保护 (🎚对齐落盘实锤: s68 头被包边吸附 65.5→64.41, 与 s67 槽叠
    # 1.1s → 时间轴断裂, 全片校验连坐单镜操作): zone 镜边界神圣, 非特区邻镜让位 —
    # 与 plan_scene 对齐段的保护同款, 此前漏了独立对齐链路
    _zs = [s for s in doc["shots"] if s.get("zone")]
    if _zs:
        _ordered = doc["shots"]
        for i, s in enumerate(_ordered):
            if s.get("zone") or s.get("packed"):
                continue
            if i > 0 and _ordered[i - 1].get("zone"):
                s["t_start"] = max(float(s["t_start"]), float(_ordered[i - 1]["t_end"]))
            if i + 1 < len(_ordered) and _ordered[i + 1].get("zone"):
                s["t_end"] = min(float(s["t_end"]), float(_ordered[i + 1]["t_start"]))

    # ── 自动拆镜 (0916 用户令: 物理上限不动, 超长口播一镜不够就两镜) ──
    # 整句包贪心分块 (每块 ≤ H3_MAX_SPAN); 块1 继承原镜 id+素材 (已生成视频
    # 直接复用), 块2+ 新 id 进 planned 生成队列; text_layer 按绝对时间分家
    # (字幕/强调词跟句走). 0917: deepcopy 只是占位 — 分身逐字继承提示词=同一
    # 张图换噪点 (违反"每镜必换构图"), 调用方须跑 redesign_split_clones 换构图.
    split = 0
    out_shots: list[dict[str, Any]] = []
    all_ids = {str(s["shot_id"]) for s in doc["shots"]}
    for s in doc["shots"]:
        t0, t1 = float(s["t_start"]), float(s["t_end"])
        span = t1 - t0
        my_packs = [p for p in packs
                    if p["t0"] + tc >= t0 - 0.01 and p["t0"] + p["dur"] + tc <= t1 + 0.01]
        chunks: list[list[float]] = []
        if span > H3_MAX_SPAN + 0.05 and my_packs:
            for p in my_packs:
                ps, pe = p["t0"] + tc, p["t0"] + p["dur"] + tc
                if chunks and pe - chunks[-1][0] > H3_MAX_SPAN:
                    chunks[-1][1] = ps
                    chunks.append([ps, pe])
                elif chunks:
                    chunks[-1][1] = pe
                else:
                    chunks.append([ps, pe])
            chunks = [c for c in chunks if c[1] > c[0] + 0.01]
        if len(chunks) <= 1:
            if span > H3_MAX_SPAN + 0.05:
                s["overrun_s"] = round(span - H3_MAX_SPAN, 2)  # 单句超限 (极少), 留人决策
            else:
                s.pop("overrun_s", None)
            out_shots.append(s)
            continue
        old_tls = [(float(t.get("t_start") or 0), float(t.get("t_end") or 0), t)
                   for t in (s.get("text_layer") or [])]
        base_id = str(s["shot_id"])
        for k, (c0, c1) in enumerate([(round(c[0], 2), round(c[1], 2)) for c in chunks]):
            if k == 0:
                ch = s
            else:
                ch = _copy.deepcopy(s)
                suffix = "b"
                while f"{base_id}{suffix}" in all_ids:
                    suffix = chr(ord(suffix) + 1)
                ch["shot_id"] = f"{base_id}{suffix}"
                all_ids.add(str(ch["shot_id"]))
                ch["split_parent"] = base_id  # 溯源标记 (克隆占位, 待重设计换构图)
                ch["status"] = "planned"
                ch.pop("video_file", None)
                ch.pop("image_file", None)
                ch.pop("brand_card", None)  # 0916: 分身镜不得继承品牌卡旗标 (s07b 毒根)
                if "seed" in ch:
                    ch["seed"] = int(ch["seed"]) + k
                split += 1
            ch["t_start"], ch["t_end"] = c0, c1
            ch["narration"] = slice_orig(time_to_pos(c0 - tc), time_to_pos(c1 - tc))[:300]
            ch_tl = []
            for rt0, rt1, t in old_tls:
                a0, a1 = t0 + rt0, t0 + rt1
                if a0 < c1 and a1 > c0:  # 与本块有交
                    nt0 = max(a0 - c0, 0.0)
                    nt1 = min(a1, c1) - c0
                    if nt1 > nt0:
                        ch_tl.append({**t, "t_start": round(nt0, 2), "t_end": round(nt1, 2)})
            ch["text_layer"] = ch_tl
            ch.pop("overrun_s", None)
            if isinstance(ch.get("anim"), dict):
                shots_mod.stretch_beats(ch, min(round(c1 - c0, 2), H3_MAX_SPAN))
            _clamp_motion_events(ch)  # 拆前绝对时间事件不可达 → 删
            out_shots.append(ch)
    doc["shots"] = out_shots
    # 场窗元数据回同步 (0917 深查: 拆镜/吸附后 arcs t 与镜实际起止漂 ±1s,
    # 时长核验永远报小残) — 以本场镜实际 min/max 为准
    by_arc: dict[str, list[dict[str, Any]]] = {}
    for s in doc["shots"]:
        by_arc.setdefault(str(s.get("arc_id")), []).append(s)
    for a in doc.get("arcs") or []:
        ss2 = by_arc.get(str(a.get("arc_id"))) or []
        if ss2:
            a["t_start"] = round(min(float(s["t_start"]) for s in ss2), 2)
            a["t_end"] = round(max(float(s["t_end"]) for s in ss2), 2)
    if split or dropped:
        logger.info("[d2] 拆镜 %d 个新镜, 剔除空镜 %d 个", split, dropped)
    return {"split": split, "dropped": dropped}


def _series_lock_block(book_title: str, ep: int) -> str:
    """系列风格锁 (0915 用户令: 第1集生成后锁定, 一书一系列; 新书自由).

    锚 = 第1集当前 doc — 磨合到哪版系列就跟到哪版 (ep1 重规划自动刷新锚)。
    ep2+ 整集规划时注入继承块: 场景基调/文字字体语言/角色造型必须一致。
    """
    if ep <= 1:
        return ""
    try:
        anchor = shots_mod.load_doc(book_title, 1)
    except Exception:  # noqa: BLE001 — 第1集未规划 = 无锁 (自由)
        return ""
    if not (anchor.get("shots") or []):
        return ""
    lines = [
        "\n【系列风格锁定 (本书第1集已定稿, 一书一系列铁律 — 必须继承, 只换叙事内容)】",
        f"- 风格配方: {anchor.get('style_recipe') or resolve_style(book_title).get('name')}",
        f"- 第1集画面策略: {str(anchor.get('ep_summary') or '')[:120]}",
    ]
    for a in (anchor.get("arcs") or [])[:8]:
        nar = str(a.get("narrative") or "")[:60]
        if nar:
            lines.append(f"- 场 {a.get('arc_id')}: {nar}")
    for g in (anchor.get("groups") or [])[:8]:
        kf = str(g.get("keyframe_zh") or "")[:80]
        if kf:
            lines.append(f"  场景语言: {kf}")
    n_typo = 0
    for s in anchor["shots"]:
        if n_typo >= 5:
            break
        mot = str(s.get("motion_zh") or "")
        tl = s.get("text_layer") or []
        hit = next((f"{t.get('text')} ({t.get('kind')})" for t in tl), "") if tl else ""
        if not hit and ("艺术字" in mot or "书法" in mot or "字体" in mot):
            hit = mot[:70]
        if hit:
            lines.append(f"- 文字风格样例: {hit[:90]}")
            n_typo += 1
    lines.append("继承要求: 场景基调/色调/机位语言/文字字体/角色造型与第1集完全一致; "
                 "同角色跨集外形一致 (年龄/发型/体态/标志特征不变)。")
    return "\n".join(lines) + "\n"


_MODULE_MAX_SPAN = 70.0  # 单模块超此时长 → 按包界分窗 (防单窗预算摊薄, 0916 教训)


def _audience_rows(book_id: str) -> tuple[str, list[str]]:
    """取受众数据 (0918 用户令"立意层带入目标群"): (L1 书定读者画像, 两轴池组列表).

    L1 = book_projects.input_json['目标读者画像'].value (tier=persona 时被
    人设覆盖不取, 与 episode_gen 口径一致); 池 = 受众地图.value 上下游/上下层。"""
    import json as _json
    import sqlite3 as _sq
    try:
        from app.config import load_config
        db_url = str(load_config().app.database_url)
        db_path = db_url.split("///", 1)[-1] if "///" in db_url else db_url
        con = _sq.connect(db_path)
        row = con.execute("select input_json from book_projects where id=?",
                          (book_id,)).fetchone()
        con.close()
        inp = _json.loads(row[0]) if row and row[0] else {}
    except Exception as exc:  # noqa: BLE001 — 取不到受众不炸立意, 留痕
        logger.warning("[plan-arcs] 受众取数失败 (立意不带受众锚): %s", exc)
        return "", []
    l1 = inp.get("目标读者画像") if isinstance(inp.get("目标读者画像"), dict) else {}
    l1v = str(l1.get("value") or "") if l1.get("tier") != "persona" else ""
    pools: list[str] = []
    am_raw = inp.get("受众地图") if isinstance(inp.get("受众地图"), dict) else {}
    am = am_raw.get("value") if isinstance(am_raw.get("value"), dict) else am_raw
    for axis in ("上下游", "上下层"):
        for p in (am.get(axis) or []):
            if isinstance(p, dict) and p.get("group"):
                pools.append(str(p["group"]) + (f"(桥:{p['bridge']})" if p.get("bridge") else ""))
    return l1v, pools


def _audience_block(l1: str, pools: list[str]) -> str:
    """立意受众块: 隐喻必须戳中 L1 的处境 (同构处境铁律), 账号池可搭桥."""
    if not l1 and not pools:
        return ""
    parts = ["\n【受众锚 (立意必须对着这些人设计)】"]
    if l1:
        parts.append(f"- 本书目标读者 (L1, 全篇画面只对他说话): {l1[:220]}")
    if pools:
        parts.append(f"- 老谭账号人群 (两轴池, 桥式画面可兼雇): {'、'.join(pools[:8])}")
    parts.append("- 铁律: 每场隐喻里'人的处境'必须与 L1 同构 (他见过/正在经历的场景), "
                 "禁画 L1 无感的行业画面; 隐喻承载句优先选 L1 会心头一紧的口播。")
    return "\n".join(parts) + "\n"


def module_windows(segs: list[dict[str, Any]], max_span: float = _MODULE_MAX_SPAN
                   ) -> list[dict[str, Any]] | None:
    """模块总线 (0917 架构令): TTS manifest 包 (带 module_id) → 场窗列表.

    模块界=场界 (六拍结构 = 创作骨架 = 规划单元, 用户定案); 单模块超 max_span
    按包界贪心分窗 (窗界永远落在包界, 不腰斩包)。返回 None = 包无 module_id
    (旧 manifest) — 调用方走 LLM 自由切场旧路径。窗 = {module_id,t_start,t_end,text}。
    """
    if not segs or any(s.get("module_id") is None for s in segs):
        return None
    wins: list[dict[str, Any]] = []
    mod_bounds: list[tuple[int, list[dict[str, Any]]]] = []
    for s in segs:
        mid = int(s["module_id"])
        if not mod_bounds or mod_bounds[-1][0] != mid:
            mod_bounds.append((mid, []))
        mod_bounds[-1][1].append(s)
    for mid, msegs in mod_bounds:
        # 模块内贪心分窗: 窗时长累计 ≥ max_span 且非末包 → 在包后切窗
        parts: list[list[dict[str, Any]]] = []
        cur: list[dict[str, Any]] = []
        for i, s in enumerate(msegs):
            cur.append(s)
            if s["t_end"] - cur[0]["t_start"] >= max_span and i < len(msegs) - 1:
                parts.append(cur)
                cur = []
        if cur:
            parts.append(cur)
        for p in parts:
            wins.append({"module_id": mid,
                         "t_start": float(p[0]["t_start"]), "t_end": float(p[-1]["t_end"]),
                         "text": "".join(str(x.get("text") or "") for x in p)})
    return wins


_SHOT_MIN_SPAN = 4.0  # 密度宪法下限 (0917 执法): 不足此长的镜并入邻镜


def refs_parse(refs: Any) -> list[int] | None:
    """LLM refs 字段 → 0 基句号列表 (升序去重).

    认 "c01-c03" 区间 / "c01,c03" 列表 / ["c01","c02"] / "c01" / 1 (裸数字);
    无法解析返回 None (调用方整体回退旧路径 — 混合模式半查半猜最危险)."""
    import re as _re
    if refs is None:
        return None
    if isinstance(refs, (int, float)):
        return [int(refs) - 1] if int(refs) >= 1 else None
    if not isinstance(refs, (str, list)):
        return None
    items = refs if isinstance(refs, list) else [x.strip() for x in str(refs).split(",")]
    out: list[int] = []
    for it in items:
        m = _re.fullmatch(r"[cC](\d+)(?:\s*-\s*[cC]?(\d+))?", str(it).strip())
        if not m:
            return None
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        if a < 1 or b < a:
            return None
        out.extend(range(a, b + 1))
    return sorted(set(x - 1 for x in out)) or None


def expand_refs_groups(raw_groups: list[dict[str, Any]], sent_table: list[dict[str, Any]],
                       a0: float, a1: float, min_shot_s: float = _SHOT_MIN_SPAN,
                       ) -> tuple[list[dict[str, Any]] | None, list[str]]:
    """refs 协议展开 (0917 架构令): LLM raw shots 的 refs 查句级表回填
    t_start/t_end/narration — 时间零 LLM 参与, 结构上不可能漂移.

    确定性修复: 引用越界 clamp 进场窗; 漏句 (窗内句未被引用) 并入时轴最近镜;
    密度执法: < min_shot_s 的镜并入前镜 (首镜并后镜), 句集合并内容保留前镜。
    任一 shot refs 无法解析 → 返回 (None, notes), 调用方整场回退旧路径。"""
    notes: list[str] = []
    win = [s for s in (sent_table or [])
           if float(s.get("t_end", 0)) > a0 + 0.01 and float(s.get("t_start", 0)) < a1 - 0.01]
    if not win:
        return None, [f"场窗 {a0:.1f}-{a1:.1f}s 句级表为空 (manifest 无 sent_table?)"]
    n_sent = len(win)
    shots_flat: list[dict[str, Any]] = []
    for g in raw_groups or []:
        for raw in (g.get("shots") or []):
            idxs = refs_parse(raw.get("refs"))
            if idxs is None:
                return None, [f"shot refs 不可解析: {str(raw.get('refs'))[:40]!r} — 整场回退旧路径"]
            bad = [i for i in idxs if i >= n_sent]
            if bad:
                notes.append(f"refs 越界 {bad} (窗内仅 c01-c{n_sent}) — clamp")
                idxs = [i for i in idxs if i < n_sent]
            if not idxs:
                return None, ["shot refs clamp 后为空 — 整场回退旧路径"]
            shots_flat.append({**raw, "_idx": sorted(set(idxs))})
    if not shots_flat:
        return None, ["refs 模式无 shots — 整场回退旧路径"]
    # 漏句修复: 窗内句未被引用 → 并给句号相邻的镜 (无邻并首镜)
    covered = {i for s in shots_flat for i in s["_idx"]}
    leaked = [i for i in range(n_sent) if i not in covered]
    for i in leaked:
        host = next((s for s in shots_flat if i - 1 in s["_idx"] or i + 1 in s["_idx"]),
                    shots_flat[0])
        host["_idx"] = sorted(set(host["_idx"]) | {i})
    if leaked:
        notes.append(f"漏句 {len(leaked)} 个并入邻镜: {leaked[:6]}")
    # 时间排序 (LLM 引用乱序 → 按 idx 排)
    shots_flat.sort(key=lambda s: s["_idx"][0])
    # 密度执法: 短镜并入前镜 (首镜并后镜)
    def _span(s: dict[str, Any]) -> float:
        return win[s["_idx"][-1]]["t_end"] - win[s["_idx"][0]]["t_start"]
    merged = 0
    i = 0
    while len(shots_flat) > 1:
        if _span(shots_flat[i]) < min_shot_s:
            if i == 0:
                host, gone = shots_flat[1], shots_flat[0]
            else:
                host, gone = shots_flat[i - 1], shots_flat[i]
            host_idx = shots_flat.index(host)
            host["_idx"] = sorted(set(host["_idx"]) | set(gone["_idx"]))
            host["_idx"].sort()
            shots_flat.remove(gone)
            merged += 1
            i = max(host_idx - 1, 0)
            continue
        i += 1
        if i >= len(shots_flat):
            break
    if merged:
        notes.append(f"密度执法: {merged} 短镜 (<{min_shot_s}s) 并入邻镜")
    # H3 上限执法 (0918 s26 实锤: refs 镜界=句边, 旧拆镜的包级贪心失配不触发):
    # >H3_MAX_SPAN 的镜按句贪心切块 (每块 ≤ 上限), 第 2 块起标 split_parent —
    # 拼接链既有 redesign_split_clones 会对分身自动重设计构图 (克隆不落地)。
    split = 0
    out_flat: list[dict[str, Any]] = []
    for s in shots_flat:
        idxs = s["_idx"]
        if _span(s) <= H3_MAX_SPAN + 0.05 or len(idxs) < 2:
            out_flat.append(s)
            continue
        # 句贪心切块: 每块以自身首句起算累计到上限即切; 末句不单独成块
        # (孤句尾并前块, 防 <4s 碎尾镜)
        chunks: list[list[int]] = []
        cur_chunk: list[int] = []
        for i in idxs:
            cur_chunk.append(i)
            t0 = float(win[cur_chunk[0]]["t_start"])
            if i != idxs[-1] and float(win[i]["t_end"]) - t0 >= H3_MAX_SPAN - 2.0:
                chunks.append(cur_chunk)
                cur_chunk = []
        if cur_chunk:
            if chunks and len(cur_chunk) == 1:  # 孤句尾并前块 (防碎尾)
                chunks[-1].extend(cur_chunk)
            else:
                chunks.append(cur_chunk)
        # 尾块均衡 (0918 s08b 实锤): 尾块 <4s 且前块有余 (末句移过去后前块仍 ≥4s
        # 且 ≤上限) → 前块末句下放, 拆镜分身不再出短镜
        while (len(chunks) >= 2 and len(chunks[-1]) < len(chunks[-2])
               and float(win[chunks[-1][-1]]["t_end"]) - float(win[chunks[-1][0]]["t_start"]) < min_shot_s
               and len(chunks[-2]) >= 2):
            moved = chunks[-2].pop()
            chunks[-1].insert(0, moved)
            tail_ok = (float(win[chunks[-1][-1]]["t_end"]) - float(win[chunks[-1][0]]["t_start"]) >= min_shot_s
                       and float(win[chunks[-2][-1]]["t_end"]) - float(win[chunks[-2][0]]["t_start"]) >= min_shot_s)
            head_ok = float(win[chunks[-2][-1]]["t_end"]) - float(win[chunks[-2][0]]["t_start"]) <= H3_MAX_SPAN + 0.05
            if tail_ok and head_ok:
                break
            chunks[-2].append(chunks[-1].pop(0))  # 回滚
            break
        for k, ch in enumerate(chunks):
            piece = {**s, "_idx": sorted(ch)}
            if k > 0:
                piece["split_parent"] = "refs"  # 分身标记 (重设计钩子识别)
            out_flat.append(piece)
        split += len(chunks) - 1
    shots_flat = out_flat
    if split:
        notes.append(f"H3上限执法: {split} 刀拆分超长镜 (> {H3_MAX_SPAN:.0f}s)")
    # 回填 t/narration (音频轴); refs 原文留档 (审计可追溯: 这镜引用了哪些句)
    out_groups: list[dict[str, Any]] = []
    n = 0
    for s in shots_flat:
        n += 1
        idxs = s["_idx"]
        s.pop("_idx", None)
        s["t_start"] = round(float(win[idxs[0]]["t_start"]), 2)
        s["t_end"] = round(float(win[idxs[-1]]["t_end"]), 2)
        s["narration"] = "".join(str(win[i].get("text") or "") for i in idxs).strip()
        s["refs_resolved"] = [f"c{i + 1:02d}" for i in idxs]  # 展开后句号留档
        s["shot_id"] = f"r{n:02d}"  # 系统编号 (拼接方统一重编)
    # 单场一组 (plan_scene 语义): 全部 shots 归一组, 组 t = 场窗
    out_groups.append({**(raw_groups[0] if raw_groups else {}),
                       "t_start": round(a0, 2), "t_end": round(a1, 2),
                       "shots": shots_flat})
    return out_groups, notes


# ── 立意模块 v2 (0918 用户令: 多维度+可编辑一等公民) ────────────
# 每场结构化维度: metaphor_core(核心映射A=B) / metaphor_mappings(分映射) /
# carrier_lines(口播承载句) / visual_motifs(可画母题) / motion(运动线) /
# banned_motifs(重掷否决历史, LLM 禁区) / concept_notes(人批注, 全链可见)。
# visual_metaphor = 系统投影 (core+拼接), 不由 LLM 直出 — 单一事实源。
_CONCEPT_KEYS = ("metaphor_core", "metaphor_mappings", "carrier_lines",
                 "visual_motifs", "banned_motifs", "concept_notes")


def _concept_fields(a: dict[str, Any]) -> dict[str, Any]:
    """arc → 结构化立意字段 (旧 arc 兼容: visual_metaphor 拆入 core)。"""
    out: dict[str, Any] = {}
    for k in _CONCEPT_KEYS:
        if a.get(k):
            out[k] = a[k]
    if not out.get("metaphor_core") and a.get("visual_metaphor"):
        out["metaphor_core"] = str(a["visual_metaphor"]).split("（")[0].split("(")[0][:80]
    return out


def _project_visual_metaphor(a: dict[str, Any]) -> str:
    """结构化 → visual_metaphor 投影 (老消费方兼容)。"""
    core = str(a.get("metaphor_core") or a.get("visual_metaphor") or "").strip()
    maps = [str(m) for m in (a.get("metaphor_mappings") or []) if str(m).strip()]
    carriers = [str(c) for c in (a.get("carrier_lines") or []) if str(c).strip()]
    parts = [core] + [f"{m}" for m in maps]
    if carriers:
        parts.append("承载句: " + "+".join(f"「{c}」" for c in carriers[:3]))
    return ";".join(parts)


def write_concept_md(doc: dict[str, Any]) -> None:
    """立意.md = 立意模块的人读投影 (骨架 arcs 为真相源, 本文件只读)。"""
    arcs = doc.get("arcs") or []
    lines = ["# 立意案 (立意模块投影 — 编辑请在动画工坊立意面板)", "",
             f"> 本集策略: {doc.get('ep_summary', '')}", ""]
    for a in arcs:
        span = float(a.get("t_end") or 0) - float(a.get("t_start") or 0)
        lines.append(f"## {a.get('arc_id')} ({span:.0f}s) {a.get('narrative', '')}")
        lines.append(f"- **核心映射**: {a.get('metaphor_core') or a.get('visual_metaphor', '(缺)')}")
        for m in (a.get("metaphor_mappings") or []):
            lines.append(f"  - 映射: {m}")
        for c in (a.get("carrier_lines") or []):
            lines.append(f"  - 承载句: {c}")
        for v in (a.get("visual_motifs") or []):
            lines.append(f"  - 画面母题: {v}")
        if a.get("banned_motifs"):
            lines.append(f"- 🚫 禁用意象: {'、'.join(a['banned_motifs'])}")
        if a.get("concept_notes"):
            lines.append(f"- ✍️ 人批注: {a['concept_notes']}")
        lines.append(f"- 运动线: {a.get('motion', '')}")
        lines.append("")
    ep_dir = shots_mod.ep_dir(str(doc.get("book_title")), int(doc.get("ep") or 1))
    ep_dir.mkdir(parents=True, exist_ok=True)
    (ep_dir / "立意.md").write_text("\n".join(lines), encoding="utf-8")


def save_concept(book_title: str, ep: int, payload: dict[str, Any]) -> dict[str, Any]:
    """立意编辑保存 (人闸改判正身): 页面编辑 → 回写骨架 arcs + 投影立意.md。

    banned_motifs 只增不减 (重掷否决历史); visual_metaphor 重投影。"""
    doc = shots_mod.load_doc(book_title, ep)
    arcs = doc.get("arcs") or []
    by_id = {str(a.get("arc_id")): a for a in arcs}
    touched = 0
    for sc in payload.get("scenes") or []:
        a = by_id.get(str(sc.get("arc_id")))
        if a is None:
            continue
        old_banned = list(a.get("banned_motifs") or [])
        for k in ("narrative", "motion") + _CONCEPT_KEYS:
            if k in sc and sc[k] is not None:
                if k == "metaphor_core" and str(sc[k]).strip() and a.get("metaphor_core") \
                        and str(sc[k]).strip() != str(a.get("metaphor_core")):
                    # 核心映射被人改掉 → 旧核心进禁用史 (重掷 LLM 不再回弹)
                    old_core = str(a["metaphor_core"]).strip()
                    if old_core not in old_banned:
                        old_banned.append(old_core)
                if isinstance(sc[k], list):
                    a[k] = [str(x).strip() for x in sc[k] if str(x).strip()]
                else:
                    a[k] = str(sc[k]).strip()
        if old_banned:
            a["banned_motifs"] = old_banned
        a["visual_metaphor"] = _project_visual_metaphor(a)
        touched += 1
    if payload.get("ep_summary"):
        doc["ep_summary"] = str(payload["ep_summary"]).strip()
    if touched:
        shots_mod.save(doc)
        write_concept_md(doc)
    logger.info("[concept-save] %d 场立意已回写骨架", touched)
    return {"touched": touched}


def reroll_concept(book_id: str, book_title: str, ep: int, arc_id: str,
                    direction: str = "") -> dict[str, Any]:
    """单场立意重掷 (0918 立意人闸闭环): 只重出该场隐喻, 其余场不动.

    LLM 输入 = 该场口播窗 + 全场隐喻板 (撞车防线) + 受众锚 + 用户改判方向
    ("不喜欢"的理由当指令); 产出回写骨架 arcs + 立意.md 同步重写。"""
    from app.config import load_config, set_config
    set_config(load_config())
    from app.services.book_service.creation_common import _llm, _parse_json
    doc = shots_mod.load_doc(book_title, ep)
    arcs = doc.get("arcs") or []
    idx = next((i for i, a in enumerate(arcs) if str(a.get("arc_id")).lower()
                == str(arc_id).strip().lower()), None)
    if idx is None:
        raise SystemExit(f"场不存在: {arc_id}")
    arc = arcs[idx]
    tc = float(load().brand_card.opening_sec)
    a0, a1 = float(arc["t_start"]) - tc, float(arc["t_end"]) - tc

    # 该场口播 (从 groups 取 narration — 骨架占位组携带)
    g = next((x for x in (doc.get("groups") or [])
              if str(x.get("arc_id")).lower() == str(arc_id).lower()), {})
    scene_text = str(g.get("narration") or "")[:1200]
    board = "\n".join(f"- {a['arc_id']}: {str(a.get('metaphor_core') or a.get('visual_metaphor') or '')[:80]}"
                      for a in arcs if a["arc_id"] != arc["arc_id"])
    _aud = _audience_block(*_audience_rows(book_id))
    banned = [str(x) for x in (arc.get("banned_motifs") or [])]
    banned.append(str(arc.get("metaphor_core") or arc.get("visual_metaphor") or "旧隐喻"))
    ask = ("【单场立意重掷 — 只重出这一场的隐喻 (结构化多维度), 其余场不动】\n"
           f"场: {arc['arc_id']} 窗口 {a0:.1f}-{a1:.1f}s (音频轴)\n"
           f"本场口播:\n{scene_text}\n\n"
           f"【禁用意象 (历史否决, 核心意象禁止复用)】\n" + "\n".join(f"- {b[:90]}" for b in banned) + "\n\n"
           + (f"【用户改判方向 (必须遵守)】\n{direction}\n\n" if direction else "")
           + f"【其余场隐喻板 (新隐喻禁撞车, 要么同体系推进要么换不重复的新意象)】\n{board}\n"
           + _aud
           + "\n【输出】严格 JSON: {\"narrative\": \"一句话这场讲什么\", "
             "\"metaphor_core\": \"核心映射 A=B (一句话)\", "
             "\"metaphor_mappings\": [\"x=y\", \"x=y\"], "
             "\"carrier_lines\": [\"口播承载句1\", \"句2\"], "
             "\"visual_motifs\": [\"可直接画的物理画面1\", \"画面2\"], "
             "\"motion\": \"一句话场景里什么在动\"}")
    raw = _llm().chat(DIRECTOR_SYS, ask, model="pro", temperature=0.6)
    data = _parse_json(raw) or {}
    core = str(data.get("metaphor_core") or "").strip()
    if not core:
        raise SystemExit("重掷产出无核心映射 — 再点一次即可 (零 GPU)")
    arcs[idx] = {**arc,
                 "narrative": str(data.get("narrative") or arc.get("narrative") or ""),
                 "metaphor_core": core,
                 "metaphor_mappings": [str(m) for m in (data.get("metaphor_mappings") or []) if str(m).strip()],
                 "carrier_lines": [str(c) for c in (data.get("carrier_lines") or []) if str(c).strip()],
                 "visual_motifs": [str(v) for v in (data.get("visual_motifs") or []) if str(v).strip()],
                 "motion": str(data.get("motion") or arc.get("motion") or ""),
                 "banned_motifs": banned}
    arcs[idx]["visual_metaphor"] = _project_visual_metaphor(arcs[idx])
    shots_mod.save(doc)
    write_concept_md(doc)  # 人读投影同步 (多维度渲染)
    logger.info("[concept-reroll] %s 立意已重掷 (结构化, 禁用史 %d 条) ✓",
                arc["arc_id"], len(banned))
    return {k: arcs[idx].get(k) for k in
            ("arc_id", "narrative", "metaphor_core", "metaphor_mappings",
             "carrier_lines", "visual_motifs", "motion", "banned_motifs")}


def plan_arcs(book_id: str, book_title: str, ep: int, ep_title: str,
              script: str, manifest: dict, bible: dict) -> dict[str, Any]:
    """两级化·第一级 (0917 用户令): 只切场 + 每场画面策略/隐喻, 不分镜.

    整集单窗大调用输出预算摊薄 → 镜少而长 + 提示词贫瘠 (0916 实锤 16镜vs35镜;
    0917 判定 A1-A7 提示词全军覆没, 单场重做技术合规显著更好 = 预算效应实锤)。
    两级化 = 本函数切场 (小输出) + plan_scene 逐场分镜 (单窗预算足)。
    输出骨架 doc: arcs (含 visual_metaphor) + 每场一个占位组 (窗口/口播原文,
    组 keyframe 留空由二级生成), shots 空。场窗时间做确定性归一: 首尾相接铺满
    [0, 真实集长], LLM 时间只当排序/比例参考 (防重叠缝隙)。
    """
    from app.config import load_config, set_config
    set_config(load_config())
    from app.services.book_service.creation_common import _llm, _parse_json

    segs = []
    t_cursor = 0.0
    for s in manifest.get("segments") or []:
        dur = float(s.get("duration") or 0)
        txt = str(s.get("text") or "").strip()
        segs.append({"t_start": round(t_cursor, 2), "t_end": round(t_cursor + dur, 2),
                     "duration": round(dur, 2), "text": txt,
                     "module_id": s.get("module_id")})
        t_cursor += dur
    total = round(max((s["t_end"] for s in segs if s["text"]), default=0.0), 2)

    # 0917 模块总线: manifest 带模块 → 场界=模块界 (系统定, LLM 零时间输出);
    # 旧 manifest (无 module_id) → 原路径 (LLM 自由切场 + 确定性归一)
    mod_wins = module_windows(segs)
    # 场列表文本 (模块定场模式喂 LLM, ep4 首踩 NameError 根修 0919):
    # 每场一行带口播全文 — carrier_lines 要求取本场原句, 截断会断粮
    scene_list = "\n".join(
        f"A{i + 1} | 模块{w['module_id']} | {w['t_end'] - w['t_start']:.1f}s | 口播: {w['text']}"
        for i, w in enumerate(mod_wins)) if mod_wins else ""
    # 0918 用户令: 立意层带入目标群 (L1 书定读者 + 老谭账号两轴池) — 隐喻戳中处境
    _aud_block = _audience_block(*_audience_rows(book_id))

    bible_block = ""
    if bible:
        bible_block = (f"\n【美术圣经 (全片统一, 每场隐喻与画面必须继承)】\n"
                       f"- 风格前缀: {bible.get('style_prefix', '')}\n"
                       f"- 色彩: {bible.get('color_palette', '')}\n"
                       f"- 质感: {bible.get('texture', '')}\n"
                       f"- 角色策略: {bible.get('character_policy', '')}\n"
                       f"- 氛围: {bible.get('mood_keywords', '')}\n")
        # 0922 角色锁定卡 (用户令): 服饰+脸+道具关键词串全书带入 — 场景换了观众靠服饰认人;
        # 模型跨镜会漂, 关键词串大体锁形。出场角色在 keyframe_zh 里必须原样携带其 look。
        chars = bible.get("characters") or []
        if chars:
            lines = "\n".join(f"- {c.get('name')}（{c.get('role', '')}）: {c.get('look', '')}"
                              for c in chars if isinstance(c, dict) and c.get("look"))
            if lines:
                bible_block += ("【角色锁定卡 (出场角色的 keyframe_zh 必须原样携带其 look 关键词, "
                                "禁改名换装; 服装+脸+道具一起写进画面)】\n" + lines + "\n")
    # 0918 立意模块 v2: LLM 直出结构化多维度 (核心映射/分映射/承载句/画面母题),
    # visual_metaphor 由系统投影 (单一事实源, LLM 不再直出)
    _schema_out = ("\"metaphor_core\": \"核心映射 A=B (一句话)\", "
                   "\"metaphor_mappings\": [\"x=y\", \"x=y\"], "
                   "\"carrier_lines\": [\"口播承载句1\", \"句2\"], "
                   "\"visual_motifs\": [\"可直接画的物理画面1\", \"画面2\"], "
                   "\"motion\": \"一句话场景里什么在动\"")
    if mod_wins:
        user = ("【模式: 模块定场 (结构总线) — 场界已按六拍模块定死 (模块界=场界), "
                "你只做创作决策: 禁增删并场, 禁输出任何时间字段】\n"
                f"【场列表 (固定, 共 {len(mod_wins)} 场)】\n{scene_list}\n"
                "同模块多场=同一叙事段的不同画面面 (隐喻同源不同面, 禁断裂)。\n"
                + bible_block + _aud_block
                + _series_lock_block(book_title, ep)
                + "\n【硬约束】每场 metaphor_core 必填且互不重复; carrier_lines 取本场口播原句。\n"
                + "【输出】严格 JSON: {\"ep_summary\": \"一句话本集画面策略\", \"arcs\": [{\"arc_id\": \"A1\", "
                  "\"narrative\": \"一句话这场讲什么\", " + _schema_out + "}]} — arc_id 逐场对位 A1.."
                f"A{len(mod_wins)}。")
    else:
        user = ("【模式: 只切场 (两级化第一级) — 只执行到第三步 (切场 + 画面策略 + 定隐喻), "
                "禁止输出 groups/shots】\n"
                f"【稿件】\n{script[:3000]}\n\n"
                "【TTS manifest (时间骨架, 精确到 0.1s; 场边界参考包边界, t 用音频轴 0 起)】\n"
                + "\n".join(json.dumps({"t_start": s["t_start"], "t_end": s["t_end"],
                                        "duration": s["duration"], "text": s["text"][:120]},
                                       ensure_ascii=False) for s in segs)
                + bible_block + _aud_block
                + _series_lock_block(book_title, ep)
                + f"\n【硬约束】场与场首尾相接铺满 0 → {total:.1f}s, 不重叠不留缝; 通常 4-9 场; "
                  "每场 metaphor_core 必填且互不重复; carrier_lines 取本场口播原句。\n"
                + "【输出】严格 JSON: {\"ep_summary\": \"一句话本集画面策略\", \"arcs\": [{\"arc_id\": \"A1\", "
                  "\"narrative\": \"一句话这场讲什么\", " + _schema_out + ", \"t_start\": 0.0, \"t_end\": 24.3}]}")
    logger.info("[plan-arcs] 一级切场中… (LLM 1-2 分钟静默属正常)")
    raw = _llm().chat(DIRECTOR_SYS, user, model="pro", temperature=0.5)
    data = _parse_json(raw) or {}
    # 立意确认轮 (0917 用户令 "先答个明白再动笔"): 多轮 — 模型看着自己的初稿
    # 把隐喻映射答明白并自检修正, 误解在零成本时暴露 (好于画完 47 张图再打回)。
    # 历史携带原 user (DeepSeek KV 前缀缓存可命中); 失败沿用初稿不炸。
    try:
        raw2 = _llm().chat_turns(
            [{"role": "system", "content": DIRECTOR_SYS},
             {"role": "user", "content": user},
             {"role": "assistant", "content": str(raw)[:12000]},
             {"role": "user", "content":
              "【立意确认轮 — 不画任何镜, 只把隐喻答明白】先逐场简答: ①映射关系"
              "(什么=什么, 口播里哪句话承载) ②与前后场隐喻是否重复/断裂 ③是否踩"
              "黑名单(商务素材/政治禁区/国旗国徽领导人) ④口播关键句能否落进画面。"
              "答完后输出修正版完整 arcs JSON (格式与初稿一致; 只许改 narrative/"
              "visual_metaphor/motion, 不许改 arc_id 和 t) — 只输出 JSON。"}],
            model="pro", temperature=0.4)
        data2 = _parse_json(raw2) or {}
        if data2.get("arcs"):
            data, raw = data2, raw2
            logger.info("[plan-arcs] 立意确认轮 ✓ 隐喻已自检修正")
    except Exception as exc:  # noqa: BLE001 — 确认轮失败沿用初稿
        logger.warning("[plan-arcs] 立意确认轮失败 (沿用初稿): %s", exc)
    raw_arcs = [a for a in (data.get("arcs") or []) if a.get("arc_id")]
    if not raw_arcs:
        raise SystemExit("切场产出不可解析 (无 arcs) — 重跑 plan 即可 (零 GPU)")
    raw_arcs.sort(key=lambda a: float(a.get("t_start") or 0))
    tc = float(load().brand_card.opening_sec)
    arcs: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []
    if mod_wins:
        # 模块定界 (0917): 场窗=模块窗 (系统), LLM arcs 按 arc_id 对位只填创作字段 —
        # 时间零参与, 结构上不可能漂移; 对位缺场 = 字段空, 立意.md 人闸可见。
        by_id = {str(a.get("arc_id") or "").upper(): a for a in raw_arcs}
        cursor = 0.0
        for i, w in enumerate(mod_wins):
            a = by_id.get(f"A{i + 1}", {})
            a0 = w["t_start"]
            t1 = w["t_end"]
            cursor = t1
            arc_new: dict[str, Any] = {"arc_id": f"A{i + 1}", "module_id": w["module_id"],
                                       "narrative": str(a.get("narrative") or ""),
                                       "motion": str(a.get("motion") or ""),
                                       "t_start": round(tc + a0, 2), "t_end": round(tc + t1, 2)}
            for k in _CONCEPT_KEYS:  # 立意模块 v2: 结构化维度透传 (列表清洗)
                if a.get(k):
                    arc_new[k] = ([str(x).strip() for x in a[k] if str(x).strip()]
                                  if isinstance(a[k], list) else str(a[k]).strip())
            arc_new["visual_metaphor"] = _project_visual_metaphor(arc_new)
            arcs.append(arc_new)
            groups.append({"group_id": f"S{i + 1:02d}", "arc_id": f"A{i + 1}",
                           "module_id": w["module_id"],
                           "t_start": round(tc + a0, 2), "t_end": round(tc + t1, 2),
                           "narration": w["text"][:600], "camera": "固定",
                           "keyframe_zh": "", "motion_zh": "", "shot_ids": []})
        _tail_gap = round(total - cursor, 2)
        if abs(_tail_gap) > 0.5:
            logger.warning("[plan-arcs] 模块窗尾 %.1fs ≠ manifest 总长 %.1fs (差 %.1fs)",
                           cursor, total, _tail_gap)
    else:
        cursor = 0.0
        for i, a in enumerate(raw_arcs):
            last = i == len(raw_arcs) - 1
            if last:
                t1 = total
            else:
                want = max(float(a.get("t_end") or 0), cursor + 3.0)
                rest = len(raw_arcs) - i
                t1 = min(max(want, cursor + (total - cursor) / rest), total)
            t1 = round(max(t1, cursor + 1.0), 2)
            a0 = round(cursor, 2)
            window_text = "".join(s["text"] for s in segs
                                  if s["t_end"] > a0 + 0.01 and s["t_start"] < t1 - 0.01)[:600]
            arcs.append({**a, "t_start": round(tc + a0, 2), "t_end": round(tc + t1, 2)})
            groups.append({"group_id": f"S{i + 1:02d}", "arc_id": a.get("arc_id"),
                           "t_start": round(tc + a0, 2), "t_end": round(tc + t1, 2),
                           "narration": window_text, "camera": "固定",
                           "keyframe_zh": "", "motion_zh": "", "shot_ids": []})
            cursor = t1
    doc = {
        "version": shots_mod.SCHEMA_VERSION,
        "book_id": book_id, "book_title": book_title, "ep": ep, "ep_title": ep_title,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "planner_flow": ("director2 模块总线 (场=六拍模块, 系统定界)"
                         if mod_wins else "director2 arcs v2 两级化 (切场+逐场分镜)"),
        "planner_model": "pro",
        "ep_summary": data.get("ep_summary", ""),
        "style_recipe": resolve_style(book_title).get("name"),
        "bible": bible,
        "arcs": arcs,
        "groups": groups,
        "shots": [],
    }
    # 隐喻查重 (0917 闭环): 场间隐喻字符二元组 Jaccard — 撞车即警 (人闸读物+终稿警告)
    def _bg(x: str) -> set[str]:
        x = re.sub(r"[，。；：、\s＝=（）()0-9a-zA-Z]", "", x or "")
        return {x[i:i + 2] for i in range(len(x) - 1)} if len(x) > 1 else {x}
    concept_warns: list[str] = []
    for i in range(len(arcs)):
        for j in range(i + 1, len(arcs)):
            bi, bj = _bg(str(arcs[i].get("visual_metaphor") or "")), \
                     _bg(str(arcs[j].get("visual_metaphor") or ""))
            if not bi or not bj:
                continue
            jac = len(bi & bj) / len(bi | bj)
            if jac >= 0.35:
                w = (f"[立意] {arcs[i]['arc_id']} 与 {arcs[j]['arc_id']} 隐喻撞车 "
                     f"(相似 {jac:.0%}) — 分镜前人工改其中一场 (立意.md 可编辑重跑)")
                concept_warns.append(w)
                logger.warning("[plan-arcs] %s", w)
    if concept_warns:
        doc["_concept_warnings"] = concept_warns
    # 立意案落盘 (0917 人闸): 人读表 — 确认/改判后再续跑分镜
    try:
        ep_dir = shots_mod.ep_dir(book_title, ep)
        ep_dir.mkdir(parents=True, exist_ok=True)
        lines = ["# 立意案 (两级化·第一级产物 — 人闸读物)", "",
                 f"> 本集策略: {data.get('ep_summary', '')}", ""]
        for a in arcs:
            lines.append(f"## {a['arc_id']} ({float(a['t_end']) - float(a['t_start']):.0f}s) "
                         f"{a.get('narrative', '')}")
            lines.append(f"- **隐喻**: {a.get('visual_metaphor', '(缺 — 必须补)')}")
            lines.append(f"- 运动线: {a.get('motion', '')}")
            lines.append("")
        if concept_warns:
            lines += ["## ⚠ 隐喻撞车警告", ""] + [f"- {w}" for w in concept_warns]
        (ep_dir / "立意.md").write_text("\n".join(lines), encoding="utf-8")
        logger.info("[plan-arcs] 立意案已落盘 → %s", (ep_dir / "立意.md").name)
    except Exception as exc:  # noqa: BLE001 — 落盘失败不炸规划
        logger.warning("[plan-arcs] 立意.md 落盘失败: %s", exc)
    logger.info("[plan-arcs] ✓ %d 场 铺满 %.1fs: %s", len(arcs), total,
                " | ".join(f"{a['arc_id']}:{float(a['t_end']) - float(a['t_start']):.0f}s"
                           for a in arcs))
    return doc


def plan(book_id: str, book_title: str, ep: int, ep_title: str,
         script: str, manifest: dict, bible: dict) -> dict[str, Any]:
    """导演规划 (弧+运动+分镜, LLM) → 完整 doc (含产线生产字段)."""
    from app.config import load_config, set_config
    set_config(load_config())
    from app.services.book_service.creation_common import _llm, _parse_json

    segs = []
    t_cursor = 0.0
    for s in manifest.get("segments") or []:
        dur = float(s.get("duration") or 0)
        txt = str(s.get("text") or "").strip()
        segs.append({"t_start": round(t_cursor, 2), "t_end": round(t_cursor + dur, 2),
                     "duration": round(dur, 2), "text": txt})  # 全文 (prompt 侧截, 对账用全量
        t_cursor += dur

    bible_block = ""
    if bible:
        bible_block = (f"\n【美术圣经 (全片统一, 每镜必须继承)】\n"
                       f"- 风格前缀: {bible.get('style_prefix', '')}\n"
                       f"- 色彩: {bible.get('color_palette', '')}\n"
                       f"- 质感: {bible.get('texture', '')}\n"
                       f"- 角色策略: {bible.get('character_policy', '')}\n"
                       f"- 氛围: {bible.get('mood_keywords', '')}\n")
        # 0923 修 (用户实锤 货不对版): 本站点漏了角色锁定卡 — 规划层 look 串全丢
        chars = bible.get("characters") or []
        if chars:
            _lines = "\n".join(f"- {c.get('name')}（{c.get('role', '')}）: {c.get('look', '')}"
                               for c in chars if isinstance(c, dict) and c.get("look"))
            if _lines:
                bible_block += ("【角色锁定卡 (出场角色的 keyframe_zh 必须原样携带其 look 关键词串, "
                                "禁只写名字不写造型 — 服装+脸+道具一起入画)】\n" + _lines + "\n")
    user = (f"【稿件】\n{script[:3000]}\n\n"
            f"【TTS manifest (时间骨架, 精确到 0.1s)】\n"
            + "\n".join(json.dumps({"t_start": s["t_start"], "t_end": s["t_end"],
                                    "duration": s["duration"], "text": s["text"][:120]},
                                   ensure_ascii=False) for s in segs)
            + bible_block
            + _series_lock_block(book_title, ep))
    logger.info("[plan] 导演规划中… (LLM pro 链, 整集一次大调用, 2-4 分钟无中间输出属正常)")
    raw = _llm().chat(DIRECTOR_SYS, user, model="pro", temperature=0.5)
    logger.info("[plan] 导演返回 %d 字符, 建档展开…", len(raw or ""))
    data = _parse_json(raw) or {}
    if not (data.get("groups") or data.get("shots")):
        raise SystemExit("导演产出不可解析 (无 groups/shots) — 重跑 plan 即可 (零 GPU)")
    doc = _build_doc(book_id, book_title, ep, ep_title, data, bible)
    # 0916: 句级 segs (巨型多句包的包内插值=漂移/劈句之源; 与 align/本场重规划同源)
    try:
        from app.services import anim_draft as _ad
        _files = _ad.fetch_episode_audio(book_id, ep)["files"]
        _sseg = _ad._sentence_segs(_files)
        if _sseg:
            segs = _sseg
    except Exception as exc:  # noqa: BLE001
        # 0919 弃包级回退 (同 plan_scene: 包级吸附=剔镜漂组窗破坏模式)
        raise SystemExit(f"句级 segs 失败 (包级回退已废): {exc}") from exc
    _realign_narrations(doc, segs)  # 字符级对账: 时间/narration 按 manifest 确定性重切
    # 0917: 拆镜分身不是复印机 — 克隆家系当场批量换构图 (失败=保持克隆, 软警告亮灯)
    try:
        redesign_split_clones(doc, bible)
    except Exception as exc:  # noqa: BLE001 — 重设计失败不炸整集规划 (克隆+警告兜底)
        logger.warning("[plan] 拆镜分身重设计失败 (保持克隆, 软警告亮灯): %s", exc)
    return doc


def plan_shot(book_id: str, book_title: str, ep: int, shot_id: str,
              manifest: dict, bible: dict) -> dict[str, Any]:
    """单镜重规划 (0915 用户令: 一镜设计坏了, 不想整场陪葬).

    钉死: 时间槽 [t0,t1] / 口播 narration / shot_id (原位替换, 页面槽位不动).
    重设计: keyframe + motion + camera + text_layer; 兄弟镜/图全不动。
    返回整个 doc (调用方校验后落盘)。
    """
    from app.config import load_config, set_config
    set_config(load_config())
    from app.services.book_service.creation_common import _llm, _parse_json

    doc = shots_mod.load_doc(book_title, ep)
    try:
        s = shots_mod.find_shot(doc, shot_id)
    except KeyError as exc:
        raise SystemExit(f"镜不存在: {shot_id}") from exc
    idx = doc["shots"].index(s)
    t0, t1 = float(s["t_start"]), float(s["t_end"])
    span = round(t1 - t0, 2)
    tc = float(load().brand_card.opening_sec)
    arc = next((a for a in doc.get("arcs") or []
                if str(a.get("arc_id", "")) == str(s.get("arc_id"))), {})
    group = next((g for g in doc.get("groups") or []
                  if g.get("group_id") == s.get("group_id")), {})
    ordered = sorted(doc["shots"], key=lambda x: float(x["t_start"]))
    oi = ordered.index(s)
    prev_kf = str(ordered[oi - 1].get("keyframe_zh") or "")[:70] if oi > 0 else ""
    nxt_kf = str(ordered[oi + 1].get("keyframe_zh") or "")[:70] if oi + 1 < len(ordered) else ""

    bible_block = ""
    if bible:
        bible_block = ("- 风格: " + str(bible.get("style_prefix", ""))[:100]
                       + " | 色彩: " + str(bible.get("color_palette", ""))[:80])

        _chars = bible.get("characters") or []
        if _chars:
            _ls = "; ".join(f"{c.get('name')}({c.get('look', '')})" for c in _chars if c.get("look"))
            if _ls:
                bible_block += chr(10) + "- 角色锁定卡 (出场角色 keyframe_zh 原样携带 look): " + _ls
    user = ("【模式: 单镜重规划】这一镜的设计坏了, 只重新设计这一镜 (整集其余全部不动)。" + chr(10)
            + "【本镜口播 (钉死不改)】" + str(s.get("narration") or "")[:120] + chr(10)
            + "【本镜时长】" + f"{span}s (音频轴 {t0 - tc:.1f}-{t1 - tc:.1f}s, 时间钉死)" + chr(10)
            + "【所在场】" + str(arc.get("narrative") or "")[:60] + " | 场景定调: "
            + str(group.get("keyframe_zh") or "")[:80] + chr(10)
            + (("[\"邻镜画面 (构图要衔接但错开)] 前镜: " + prev_kf + " / 后镜: " + nxt_kf + chr(10)) if (prev_kf or nxt_kf) else "")
            + "【旧版本镜 (打磨不是复读, 新构图显著错开)】" + str(s.get("keyframe_zh") or "")[:100] + chr(10)
            + "【圣经】" + bible_block + chr(10)
            + "【输出】严格 JSON 单对象: {\"keyframe_zh\": \"首帧(具象+灭字+视角锁死+信息完备)\", "
              "\"keyframe_en\": \"English, no text\", \"motion_zh\": \"动画层+文字事件(一镜一事)\", "
              "\"motion_en\": \"English ambient + at most ONE text event\", \"camera\": \"...\", "
              "\"text_layer\": [{\"kind\":\"hero_number|caption|...\",\"text\":\"..\",\"t_start\":0.5,\"t_end\":2.0}]}")
    logger.info("[plan-shot] %s 单镜重规划中… (槽 %.1f-%.1fs 钉死, LLM 30-60s)", shot_id, t0, t1)
    raw = _llm().chat(DIRECTOR_SYS, user, model="pro", temperature=0.5)
    d = _parse_json(raw) or {}
    kf_zh = str(d.get("keyframe_zh") or "").strip()
    motion_en = str(d.get("motion_en") or "").strip() or "Gentle ambient motion, very slight push-in."
    if not kf_zh:
        raise ValueError("导演产出不可解析 (无 keyframe_zh)")

    gen = min(span, H3_MAX_SPAN)
    s.update({
        "keyframe_zh": kf_zh,
        "keyframe_en": str(d.get("keyframe_en") or "").strip(),
        "image_prompt_zh": kf_zh,
        "motion_zh": str(d.get("motion_zh") or "")[:300],
        "camera": d.get("camera") or s.get("camera") or "固定",
        "text_layer": d.get("text_layer") or [],
        "anim": {
            "duration_s": gen,
            "opening_desc": str(d.get("keyframe_en") or kf_zh),
            "physical_lock": "the camera viewpoint, the main structural elements and layout",
            "screen_exception": "nothing",
            "beats": [{"t_start": 0, "t_end": gen, "motion": motion_en}],
            "ending": "the scene holds with gentle ambient light variation",
        },
        "seed": shots_mod.new_seed(),
        "h3_seed": shots_mod.new_seed(),
        "status": "planned",
        "image_file": None, "video_file": None,
        "attempts": {"k2": 0, "h3": 0},
        "error": None, "reject_note": "",
    })
    s.pop("overrun_s", None)
    _clamp_motion_events(s)
    _gate_motion_text(s)  # 单镜重规划同为新 LLM 产出 — 浮字军规同闸
    _ensure_motion_text(s)  # 0920 补字回填: 军规只拦不补, 合规短标确定性注入
    return doc


def plan_scene(book_id: str, book_title: str, ep: int, arc_id: str,
               manifest: dict, bible: dict) -> dict[str, Any]:
    """单场重规划 (逐场磨合): 只重生该场的组/镜, 其余场原样拼接保留.

    磨合循环 = 本场 规划→K2→H3 反复测. 链路是全集 plan 的单窗版:
    同一 DIRECTOR_SYS 宪法/圣经; 新组镜用全局新 id (旧 id 退役, 防与存量撞);
    拼回后整集字符级 realign (老场 narration 已是音频原文 → locate 幂等不动);
    校验在调用方 (planner.replan_scene 重试网), 本函数只产 doc 不落盘.
    """
    from app.config import load_config, set_config
    set_config(load_config())
    from app.services.book_service.creation_common import _llm, _parse_json

    doc = shots_mod.load_doc(book_title, ep)
    arcs = doc.get("arcs") or []
    key = str(arc_id).strip().lower()
    idx = next((i for i, a in enumerate(arcs) if str(a.get("arc_id", "")).lower() == key), None)
    if idx is None:
        raise SystemExit(f"场不存在: {arc_id} (已有 {[a.get('arc_id') for a in arcs]})")
    arc = arcs[idx]
    g_all = doc.get("groups") or []
    s_groups = sorted([g for g in g_all if str(g.get("arc_id", "")).lower() == key],
                      key=lambda g: float(g["t_start"]))
    if not s_groups:
        raise SystemExit(f"场 {arc_id} 没有组 (旧数据?)")
    t0 = min(float(g["t_start"]) for g in s_groups)
    t1 = max(float(g["t_end"]) for g in s_groups)
    tc = float(load().brand_card.opening_sec)

    segs = []
    t_cursor = 0.0
    for s in manifest.get("segments") or []:
        dur = float(s.get("duration") or 0)
        segs.append({"t_start": round(t_cursor, 2), "t_end": round(t_cursor + dur, 2),
                     "duration": round(dur, 2), "text": str(s.get("text") or "").strip()})
        t_cursor += dur
    a0, a1 = t0 - tc, t1 - tc  # 音频轴窗 (LLM 用音频轴, 拼装时 +tc 归一)
    win_segs = [s for s in segs if s["t_end"] > a0 - 8 and s["t_start"] < a1 + 8]

    # 0917 refs 协议: 句级表 (包实测+静音吸附) 在场窗内局部编号 — LLM 只引句号,
    # 零绝对时间输出; 展开/校验/密度执法在 expand_refs_groups (确定性)。
    sent_table = list(manifest.get("sent_table") or [])
    # 0919 60s 特区 (用户令): 场窗与正文 [0,60s) 相交 → 镜槽系统预装, LLM 只填画面;
    # 场结构 (A1/A2 界) 不动 — 特区是镜级规则。装包失败静默降级走旧 refs 协议。
    from app.services.anim_pipeline import hook_zone as _HZ
    zone_slots: list[dict[str, Any]] = []
    if a0 < _HZ.ZONE_END - 0.01:
        try:
            zone_slots = _HZ.pack_zone_slots(sent_table, a0, a1)
        except Exception as exc:  # noqa: BLE001 — 装包失败不炸场, 走旧协议
            logger.warning("[replan] 场 %s 特区装包失败 (降级旧协议): %s",
                           arc["arc_id"], exc)
    zone_tail = zone_slots[-1]["t_end"] if zone_slots else a0
    # 0919 全片装包制 (用户令: LLM 零时长决策): 特区外余窗同 DP 装包 — 镜界
    # 全系统定, LLM 只填画面; refs 协议 (LLM 组句) 退役, 四集均值漂移根治
    scene_slots: list[dict[str, Any]] = []
    if a1 - zone_tail > 0.1:
        try:
            scene_slots = _HZ.pack_zone_slots(sent_table, zone_tail, a1, zone_end=a1)
        except Exception as exc:  # noqa: BLE001 — 装包失败走旧 refs 兜底
            logger.warning("[replan] 场 %s 余窗装包失败 (降级 refs): %s",
                           arc["arc_id"], exc)
    slot_mode = bool(zone_slots or scene_slots)
    refs_mode = bool(sent_table) and not slot_mode
    refs_block = ""
    if refs_mode:
        _win_sents = [s for s in sent_table
                      if float(s.get("t_end", 0)) > zone_tail + 0.01
                      and float(s.get("t_start", 0)) < a1 - 0.01]
        if not _win_sents:
            refs_mode = False
        else:
            table_txt = "\n".join(
                f"c{i + 1:02d} | {float(s['t_start']):.1f}-{float(s['t_end']):.1f}s | "
                f"{str(s.get('text') or '')[:60]}"
                for i, s in enumerate(_win_sents))
            refs_block = (f"\n【句级时间表 (本场, 音频轴, 精确实测) — 镜边界只许落在句边界上】\n"
                          f"{table_txt}\n"
                          f"【refs 输出制 (覆盖全局格式中的时间字段)】每镜必须给 \"refs\": "
                          f"\"c01-c02\" (引句号区间, 可跨句); **禁输出 t_start/t_end/narration** "
                          f"— 时间轴与口播原文由系统查表展开, 你报的时间一律丢弃。"
                          f"镜时长 = 引用句实测秒数: 单镜至少引够 4s (密度宪法, 短句必须与邻句同镜), "
                          f"一般 4-8s 一镜; 全部 c01-c{len(_win_sents)} 必须被引用 (漏句系统会并邻镜, "
                          f"尽量自己规划好)。\n")

    # 0919 60s 特区注入: 槽位表 + 特区宪法 (覆盖"场内共享场景"等冲突条款)
    zone_block = ""
    if zone_slots:
        _tbl = "\n".join(
            f"槽{k + 1} | {s['t_start']:.1f}-{s['t_end']:.1f}s ({s['t_end'] - s['t_start']:.1f}s) | "
            f"{(str(s['text'] or '').strip() or '(垫静音段)')[:56]}"
            for k, s in enumerate(zone_slots))
        _tail_note = (f"槽后剩余段 ({a1 - zone_tail:.1f}s) 已由系统装包为普通槽 "
                      f"(槽号接续特区, 见普通镜槽表)。"
                      if scene_slots else "本场全部为特区镜。")
        zone_block = (f"\n{_HZ.ZONE_RULES}\n"
                      f"【镜槽表 (系统已定, 音频轴) — 一槽一镜, 禁增删并、禁改镜界】\n{_tbl}\n"
                      f"【特区输出制 (优先于 refs 制)】特区镜 ({len(zone_slots)} 个) 一律放进 groups[0], "
                      f"每镜给 \"slot\": 槽号(1-{len(zone_slots)}), **禁输出 t_start/t_end/narration/refs** "
                      f"— 时间与口播由系统按槽回填; groups[0].keyframe_zh 写特区蒙太奇主题。{_tail_note}\n")
    # 0919 普通镜槽表 (全片装包制): 非特区段同 slot 制 — LLM 只填画面
    scene_block = ""
    if scene_slots:
        _off = len(zone_slots)
        _tbl2 = "\n".join(
            f"槽{_off + k + 1} | {s['t_start']:.1f}-{s['t_end']:.1f}s ({s['t_end'] - s['t_start']:.1f}s) | "
            f"{(str(s['text'] or '').strip() or '(垫静音段)')[:56]}"
            for k, s in enumerate(scene_slots))
        scene_block = (f"\n【普通镜槽表 (系统已定, 音频轴) — 一槽一镜, 禁增删并、禁改镜界】\n{_tbl2}\n"
                       f"【普通镜输出制】普通镜 ({len(scene_slots)} 个) 放进 groups[1+] (可自行分组), "
                       f"每镜给 \"slot\": 槽号({_off + 1}-{_off + len(scene_slots)}), "
                       f"**禁输出 t_start/t_end/narration/refs** — 时间与口播由系统按槽回填; "
                       f"每镜画面必须承接本场隐喻且与前镜构图错开。\n")

    scene_text = "\n".join(g.get("narration") or "" for g in s_groups)  # 已对齐的真实音频原文
    old_kf = "\n".join(f"- {g['group_id']}: {(g.get('keyframe_zh') or '')[:60]}" for g in s_groups)
    prev_arc = arcs[idx - 1] if idx > 0 else None
    next_arc = arcs[idx + 1] if idx + 1 < len(arcs) else None

    bible_block = ""
    if bible:
        bible_block = (f"\n【美术圣经 (全片统一, 每镜必须继承)】\n"
                       f"- 风格前缀: {bible.get('style_prefix', '')}\n"
                       f"- 色彩: {bible.get('color_palette', '')}\n"
                       f"- 质感: {bible.get('texture', '')}\n"
                       f"- 角色策略: {bible.get('character_policy', '')}\n"
                       f"- 氛围: {bible.get('mood_keywords', '')}\n")
        # 0923 修: 单场重规划漏角色锁定卡 — 与全集规划对齐 (货不对版根修, 全站点覆盖)
        chars = bible.get("characters") or []
        if chars:
            _lines = "\n".join(f"- {c.get('name')}（{c.get('role', '')}）: {c.get('look', '')}"
                               for c in chars if isinstance(c, dict) and c.get("look"))
            if _lines:
                bible_block += ("【角色锁定卡 (出场角色的 keyframe_zh 必须原样携带其 look 关键词串, "
                                "禁只写名字不写造型)】\n" + _lines + "\n")

    user = (f"【模式: 单场重规划 (逐场磨合) — 本集其余场已定且不动, 你只重新规划一个场】\n"
            f"场编号: {arc['arc_id']}\n\n"
            f"【本场口播原文 (全集时间轴 {t0:.1f}-{t1:.1f}s 已含开场预留; 你输出组/镜时间用音频轴 = 全集时间 - {tc:.1f}）】\n"
            f"{scene_text}\n\n"
            f"【本场时间窗 (音频轴): {a0:.1f}s → {a1:.1f}s — 组/镜必须首尾相接恰好覆盖全窗, 不得越界】\n\n"
            f"【上下文 (只读, 禁输出)】\n"
            f"- 前一场: {prev_arc['arc_id'] + ' ' + str(prev_arc.get('narrative') or '') if prev_arc else '(本集第一场)'}\n"
            f"- 后一场: {next_arc['arc_id'] + ' ' + str(next_arc.get('narrative') or '') if next_arc else '(本集最后一场)'}\n\n"
            f"【TTS manifest (本场附近, 音频轴, 精确到 0.1s)】\n"
            + "\n".join(json.dumps({"t_start": s["t_start"], "t_end": s["t_end"],
                                    "duration": s["duration"], "text": s["text"][:120]},
                                   ensure_ascii=False) for s in win_segs)
            + bible_block
            + _series_lock_block(book_title, ep)
            + f"\n【旧版画面 (打磨不是复读 — 新构图必须与旧版显著错开)】\n{old_kf}\n"
            # 0918 立意模块 v2: 结构化多维度注入 (分镜吃立意模块, 人批注/禁用意象全可见)
            + (lambda a: (
                f"【本场立意 (立意模块, 每镜都必须是它的一个面)】\n"
                f"- 核心映射: {a.get('metaphor_core') or a.get('visual_metaphor')}\n"
                + "".join(f"- 映射: {m}\n" for m in (a.get("metaphor_mappings") or []))
                + "".join(f"- 口播承载句 (这些句的画面必须由本场扛): {c}\n"
                          for c in (a.get("carrier_lines") or []))
                + "".join(f"- 画面母题 (构图从这些母题取): {v}\n"
                          for v in (a.get("visual_motifs") or []))
                + (f"- 🚫 禁用意象 (历史否决): {'、'.join(a['banned_motifs'])}\n"
                   if a.get("banned_motifs") else "")
                + (f"- ✍️ 人批注 (必须遵守): {a['concept_notes']}\n"
                   if a.get("concept_notes") else "")
            ))(arc)
            + f"\n【输出】arcs 数组只含本场一项 (arc_id={arc['arc_id']}, narrative/motion "
              f"重新构思 — 每镜都是立意的一个面); "
              f"groups 只含本场组 (arc_id 全部={arc['arc_id']}); 格式与全片规划完全一致。"
            + zone_block + scene_block + refs_block)
    logger.info("[replan] 场 %s 重规划中… (窗口 %.1f-%.1fs, %d 组退役, LLM 1-2 分钟静默属正常)",
                arc["arc_id"], t0, t1, len(s_groups))
    # 0917 批评注入 (闭环): 有旧产出 = 看着旧稿改, 不盲重掷 — assistant 携旧场分镜,
    # user 给自动批评 (禁区/克隆/隐喻贯彻) + 重出指令; 无旧产出 (两级化新场) 保持单轮
    _old_gids = {g["group_id"] for g in s_groups}
    _old_shots = [s for s in doc["shots"] if s.get("group_id") in _old_gids]
    if _old_shots:
        _old_board = "\n".join(
            f"- {s['shot_id']} [{s.get('camera')}]: {(s.get('keyframe_zh') or '')[:80]}"
            for s in sorted(_old_shots, key=lambda x: float(x["t_start"])))
        _crit: list[str] = []
        _sub = {"shots": _old_shots, "groups": doc.get("groups") or [], "arcs": doc.get("arcs") or []}
        _ban = visual_ban_scan(_sub)
        if _ban:
            _crit.append(f"政治敏感禁区命中 {'、'.join(_ban)} — 必须根除")
        if _clone_families(_old_shots):
            _crit.append("场内存在逐字克隆镜 (同图换噪点) — 新分镜每镜必换构图")
        if zone_slots:
            _crit.append(f"特区铁律: 本场前 {len(zone_slots)} 槽每镜一个全新场景 "
                         "(每镜带 scene_tag 2-6字, 组内禁重复, 系统硬校验), 旧版同场景串"
                         "必须整体打散 — 只换机位/只换景别=废稿")
            _zc = [s for s in _old_shots if s.get("zone")]
            if _zc:
                for issue in _HZ.zone_composition_issues(_zc)[:6]:
                    _crit.append(f"构图同源 {issue} — 每镜换一个隐喻载体 "
                                 "(立意 visual_motifs 轮换, 一镜一母题)")
        if arc.get("visual_metaphor"):
            _crit.append(f"本场隐喻「{arc['visual_metaphor']}」— 新分镜每一镜都必须是它"
                         "的一个面/一个时刻, 不得跑题到通用画面")
        _crit.append("逐镜自查: 黑名单素材/字面配图/相邻构图重复 — 有则改之")
        raw = _llm().chat_turns(
            [{"role": "system", "content": DIRECTOR_SYS},
             {"role": "user", "content": user},
             {"role": "assistant",
              "content": "旧版分镜如下:\n" + _old_board[:6000]},
             {"role": "user", "content":
              "【批评-修正轮】系统审计对旧版的批评:\n- " + "\n- ".join(_crit) +
              "\n基于批评重新设计本场 (时间窗/口播铁律不变, 构图与旧版显著错开), "
              "输出格式与全片规划完全一致。"}],
            model="pro", temperature=0.5)
    else:
        raw = _llm().chat(DIRECTOR_SYS, user, model="pro", temperature=0.5)
    data = _parse_json(raw) or {}
    groups = data.get("groups") or []
    if not groups:
        raise ValueError("导演产出不可解析 (无 groups)")
    for g in groups:
        g["arc_id"] = arc["arc_id"]
    new_arc = dict((data.get("arcs") or [{}])[0])
    new_arc["arc_id"] = arc["arc_id"]
    data["arcs"] = [new_arc]

    # 0919 60s 特区执法: slot 镜数对槽校验 + 槽位时间/口播回填; 特区镜重组为
    # 独立头组 (场结构不动, 组=容器); refs 段只在槽后余窗展开 (防 expand 误吃特区句)
    zone_group: dict[str, Any] | None = None
    z_tags: list[str] = []
    if zone_slots:
        groups = _HZ.enforce_zone_shots(groups, zone_slots)
        _zshots = sorted((r for g in groups for r in (g.get("shots") or [])
                          if r.get("zone") == "hook60"),
                         key=lambda r: float(r["t_start"]))
        # scene_tag 硬审计 (0919 用户铁令"连环镜头场景不能一致"的确定性执法):
        # 缺标/组内重复 → 拒稿走重试网, 提示词无牙教训 (s50/s52 逐字克隆实锤)
        # 0923 确定性兜底: LLM 忘带 scene_tag 时从 keyframe_zh 自动提取 (不再因缺标拒稿)
        for r in _zshots:
            if not str(r.get("scene_tag") or "").strip():
                _kf = str(r.get("keyframe_zh") or "")
                _tag = _kf.split("，")[1][:6].strip() if "，" in _kf else _kf[10:16]
                r["scene_tag"] = _tag or "场景"
        _tag_issues = _HZ.zone_scene_issues([r.get("scene_tag") for r in _zshots])
        if _tag_issues:
            raise ValueError("特区场景审计不过: " + "; ".join(_tag_issues[:4]))
        z_tags = [str(r.get("scene_tag") or "") for r in _zshots]
        _rest = [{**g, "shots": [r for r in (g.get("shots") or [])
                                 if r.get("zone") != "hook60"]} for g in groups]
        _rest = [g for g in _rest if g.get("shots")]
        zone_group = {"arc_id": arc["arc_id"], "camera": "蒙太奇",
                      "keyframe_zh": str((groups[0].get("keyframe_zh") if groups else "")
                                         or "60s特区多场景蒙太奇")[:200],
                      "t_start": zone_slots[0]["t_start"], "t_end": zone_slots[-1]["t_end"],
                      "shots": _zshots}
        logger.info("[replan] 场 %s 特区 ✓ %d 槽成镜 (槽尾 %.1fs, 余 %.1fs refs)",
                    arc["arc_id"], len(zone_slots), zone_tail, a1 - zone_tail)
        groups = [zone_group] + _rest

    # 0919 全片装包执法: 普通槽镜回填 (slot 号 > 特区槽数); 失败走重试网
    if scene_slots:
        groups = _HZ.enforce_scene_shots(groups, scene_slots,
                                         slot_offset=len(zone_slots))
        logger.info("[replan] 场 %s 普通槽 ✓ %d 镜回填 (全片装包制)",
                    arc["arc_id"], len(scene_slots))

    # 0917 refs 协议展开: LLM 只引句号 → 系统查表回填 t/narration (确定性);
    # 解析失败/引用不可用 → 整场回退旧路径 (LLM 自报时间 + 贪心落位兜底)
    if refs_mode and zone_group:
        # 特区镜已回填 — refs 只展开余窗 (zone_group 无 refs, 剥离后重拼)
        tail_groups = [g for g in groups if g is not zone_group]
        if tail_groups:
            exp_groups, refs_notes = expand_refs_groups(
                tail_groups, sent_table, zone_tail, a1)
            if exp_groups is not None:
                groups = [zone_group] + exp_groups
                data["planner_refs"] = True
                logger.info("[replan] 场 %s refs 展开 ✓ 余窗镜 %s", arc["arc_id"],
                            ("; ".join(refs_notes)) if refs_notes else "零修复")
            else:
                logger.warning("[replan] 场 %s refs 回退旧路径: %s", arc["arc_id"],
                               "; ".join(refs_notes))
    elif refs_mode:
        exp_groups, refs_notes = expand_refs_groups(
            groups, sent_table, a0, a1)
        if exp_groups is not None:
            for g in exp_groups:
                g["arc_id"] = arc["arc_id"]
            groups = exp_groups
            data["planner_refs"] = True
            logger.info("[replan] 场 %s refs 展开 ✓ %d 镜 %s", arc["arc_id"],
                        len(exp_groups[0].get("shots") or []),
                        ("; ".join(refs_notes)) if refs_notes else "零修复")
        else:
            refs_mode = False
            logger.warning("[replan] 场 %s refs 回退旧路径: %s", arc["arc_id"],
                           "; ".join(refs_notes))
    data["groups"] = groups

    sid_off = max((int(s["shot_id"][1:]) for s in doc["shots"]
                   if s["shot_id"][1:].isdigit()), default=0)
    gid_off = max((int(g["group_id"][1:]) for g in g_all
                   if str(g.get("group_id", ""))[1:].isdigit()), default=0)
    scene_doc = _build_doc(book_id, book_title, ep, str(doc.get("ep_title") or ""), data, bible,
                           sid_offset=sid_off, gid_offset=gid_off)
    # 0919 60s 特区: _build_doc 不透传新字段 — 前 N 镜 (groups[0]=特区组, 构造保证)
    # 重新打标 + 携带槽位 (对齐阶段的圣时间)
    if zone_slots:
        for s, sl in zip(scene_doc["shots"], zone_slots):
            s["zone"] = "hook60"
            s["_zone_slot"] = {"t_start": float(sl["t_start"]), "t_end": float(sl["t_end"]),
                               "text": str(sl["text"])}
        for s, tag in zip(scene_doc["shots"], z_tags):
            s["scene_tag"] = tag

    # 拼回: 弃旧场组/镜, 插新. 场内对齐 = 窗口锁定顺序贪心 (0915 定稿, 三代方案):
    # ① 整集 realign 会微扰其余场; ② 锚式 (头/尾锚) 依赖邻场 narration 音频精确,
    #    邻场刚重规划后锚被毒化 (A6 实锤); ③ 现方案: 在 [窗口起,窗上止] 内按镜
    #    顺序匹配 narration 头, 找不到按 LLM 意图时间比例落位 — 物理出不 了窗口。
    old_gids = {g["group_id"] for g in s_groups}
    arcs[idx] = {**arc, "narrative": new_arc.get("narrative") or arc.get("narrative"),
                 "motion": new_arc.get("motion") or arc.get("motion"),
                 "visual_metaphor": new_arc.get("visual_metaphor") or arc.get("visual_metaphor")}
    remaining = [g for g in g_all if g["group_id"] not in old_gids]
    # 0916 文字分切根治 (用户实锤: 跨词腰斩"尼 克|松赢了"/孤儿尾巴/跨场渗漏):
    # 窗口贪心分配的切点落进巨型多句包中间 → 换句级 packs (句边=唯一合法切点,
    # 与归真/对齐同源); wav silencedetect 失败回退包级
    try:
        from app.services import anim_draft as _ad
        _files = _ad.fetch_episode_audio(book_id, ep)["files"]
        _sseg = _ad._sentence_segs(_files)
        if _sseg:
            segs = _sseg
            logger.info("[replan] 句级 packs %d 段 (切点=句边)", len(segs))
    except Exception as exc:  # noqa: BLE001
        # 0919 弃包级回退 (ep4 实测: 包级吸附剔 7 镜+组窗漂移 = 破坏模式):
        # 句级失败=硬错, 外层重试网接住, ×2 败则人工介入 — 不再静默降级
        raise SystemExit(f"句级 segs 失败 (包级回退已废 — 会剔镜漂组窗): {exc}") from exc
    packs, stream = _packs_stream(segs)
    # 真实集长 = 最后一个非空包的终点 (空文本包实测 226s 幻影 — 裸加 duration 会把
    # 末场钉出窗外, s48 234.8s 实锤)
    total_end = round(tc + _pos_to_time(packs, len(stream)), 2)
    has_next = any(float(g["t_start"]) >= t1 - 0.6 for g in remaining)
    pin_end = t1 if has_next else max(t1, total_end)  # 末场吃满真实集长 (旧doc欠账)

    def _pos_at(t_audio: float) -> int:
        for p in packs:
            if p["t0"] <= t_audio < p["t0"] + p["dur"]:
                frac = (t_audio - p["t0"]) / max(p["dur"], 1e-6)
                return p["lo"] + int(frac * (p["hi"] - p["lo"]))
        return packs[-1]["hi"] if packs else 0

    p_w0, p_w1 = _pos_at(t0 - tc), _pos_at(pin_end - tc)
    ss = sorted(scene_doc["shots"], key=lambda s: float(s["t_start"]))
    sg = sorted(scene_doc["groups"], key=lambda g: float(g["t_start"]))
    if slot_mode:
        # 0919 全片装包制: 镜时间/narration 已由槽执法回填 (槽=句包边), needle
        # 锚定/塌缩/碎镜合并整体退役 — 重切反而洗掉槽位 (s08 65.5 实锤同机理)
        logger.info("[replan] 装包制跳过锚定 (槽位即时间, %d 镜)", len(ss))
    else:
        # 两遍窗口对齐: ① 口播头严格匹配 (窗内单调); ② 未命中边界在两侧已知锚间
        # 按口播字数比例分配 — 单调由构造保证, 不再保留 LLM 原始时间 (重叠实锤根因)
        n = len(ss)
        b = [p_w0] + [None] * (n - 1) + [p_w1]  # b[k] = 镜 k-1|k 间的流边界
        cur = p_w0
        # 口播头 = 该镜的起点: needle(ss[i]) 落位在 b[i] (不是 b[i+1] — 差一实锤,
        # 每镜拿到前一镜的窗, s35 双跨度 26.5s 就是这么来的)
        for i in range(1, n):
            needle = _norm_with_map(ss[i].get("narration") or "")[0][:14]
            for ln in (14, 9, 5):
                if len(needle) >= ln:
                    hit = stream.find(needle[:ln], cur)
                    if cur <= hit < p_w1:
                        b[i] = hit
                        cur = hit
                        break
        narr_lens = [max(len(_norm_with_map(s.get("narration") or "")[0]), 2) for s in ss]
        i = 1
        while i < n:
            if b[i] is None:
                j = i
                while j < n and b[j] is None:
                    j += 1
                lo, hi = b[i - 1], b[j]  # j == n → b[n] = p_w1
                weights = narr_lens[i - 1:j]  # 覆盖这些边界的镜 (shot k ∈ [b[k], b[k+1]])
                total = sum(weights) or 1
                for k in range(i, j):
                    share = sum(weights[:k - i + 1]) / total
                    b[k] = min(lo + int((hi - lo) * share), hi)
                i = j
            else:
                i += 1
        for i2, s in enumerate(ss):
            a2, b2 = b[i2], b[i2 + 1]
            if b2 > a2:
                s["t_start"] = round(tc + _pos_to_time(packs, a2), 2)
                s["t_end"] = round(tc + _pos_to_time(packs, b2), 2)
                s["narration"] = _slice_orig(packs, a2, b2)[:300]
            else:
                # 窗口塌缩 (needle 撞重/比例塌缩) — 禁留 LLM 原始时间 (0323/0336 两连毙实锤:
                # 原始时间乱序+重叠混进对齐序列)。零宽化后剔除, 与归真空镜剔除同判。
                s["t_start"] = s["t_end"] = round(tc + _pos_to_time(packs, a2), 2)
                s["_collapsed"] = True
                logger.warning("[replan] 塌缩镜剔除 %s (窗口零宽, 口播并给邻镜)",
                               s.get("shot_id"))
        ss = [s for s in ss if not s.pop("_collapsed", False)]
        # 碎镜合并 (0917 两级化实锤: needle 挤压出 <1.5s 镜, 硬校验 1.5s 地板两连毙):
        # 并入前镜 (窗口+口播续接); 首镜碎 → 并入后镜。与密度宪法 2-6s 同向。
        merged: list[dict[str, Any]] = []
        for s in ss:
            short = round(float(s["t_end"]) - float(s["t_start"]), 2) < 1.5
            if short and merged and not merged[-1].get("zone"):  # 特区镜不吸收碎镜 (槽位神圣)
                prev = merged[-1]
                logger.warning("[replan] 碎镜并入前镜 %s ← %s (%.1fs)",
                               prev.get("shot_id"), s.get("shot_id"),
                               float(s["t_end"]) - float(s["t_start"]))
                prev["t_end"] = s["t_end"]
                prev["narration"] = (str(prev.get("narration") or "")
                                     + str(s.get("narration") or ""))[:300]
                continue
            merged.append(s)
        ss = merged
        if len(ss) > 1 and round(float(ss[0]["t_end"]) - float(ss[0]["t_start"]), 2) < 1.5:
            head, nxt = ss[0], ss[1]
            logger.warning("[replan] 首碎镜并入后镜 %s ← %s", nxt.get("shot_id"), head.get("shot_id"))
            nxt["t_start"] = head["t_start"]
            nxt["narration"] = (str(head.get("narration") or "") + str(nxt.get("narration") or ""))[:300]
            ss = ss[1:]
    if ss:
        ss[0]["t_start"] = t0
        ss[-1]["t_end"] = pin_end
    if sg:
        sg[0]["t_start"] = t0
        sg[-1]["t_end"] = pin_end
        sg[0]["narration"] = _slice_orig(packs, p_w0, p_w1)[:300]
    # 0919 60s 特区镜保护: 槽位时间神圣 — needle/比例/钉头尾全让位, 原样恢复;
    # 非特区邻镜防重叠 (让位特区)。首槽起=场窗 a0、末槽止=窗界 (装包器钉过), 恢复=幂等
    if zone_slots:
        for s in ss:
            z = s.pop("_zone_slot", None)
            if z:
                s["t_start"] = round(tc + float(z["t_start"]), 2)
                s["t_end"] = round(tc + float(z["t_end"]), 2)
                s["narration"] = str(z["text"])[:300]
        for i, s in enumerate(ss):
            if s.get("zone"):
                continue
            if i > 0 and ss[i - 1].get("zone"):
                s["t_start"] = max(float(s["t_start"]), float(ss[i - 1]["t_end"]))
            if i + 1 < len(ss) and ss[i + 1].get("zone"):
                s["t_end"] = min(float(s["t_end"]), float(ss[i + 1]["t_start"]))
    for s in ss:  # span 变了: 时窗/beats 归一 (H3 生成窗口用)
        span = round(float(s["t_end"]) - float(s["t_start"]), 2)
        gen = min(span, H3_MAX_SPAN)
        s["anim"]["duration_s"] = gen
        shots_mod.stretch_beats(s, gen)
        _clamp_motion_events(s)  # 窗口重排后旧绝对时间事件不可达 → 删
        if span > H3_MAX_SPAN + 0.05:
            s["overrun_s"] = round(span - H3_MAX_SPAN, 2)
        else:
            s.pop("overrun_s", None)
    if sg:
        arcs[idx]["t_start"] = float(sg[0]["t_start"])
        arcs[idx]["t_end"] = float(sg[-1]["t_end"])
    # module_id 透传 (0919 ep4 体检实锤丢失): expand_refs_groups 用 LLM 组重建,
    # 骨架组字段没带过来 → 盘上 groups.module_id 全 None, 模块总线断链
    _mod = next((g.get("module_id") for g in s_groups if g.get("module_id") is not None), None)
    if _mod is not None:
        for g in sg:
            g.setdefault("module_id", _mod)
    doc["groups"] = remaining + sg
    doc["shots"] = sorted([s for s in doc["shots"] if s["group_id"] not in old_gids] + ss,
                          key=lambda s: float(s["t_start"]))
    first, last = doc["shots"][0]["shot_id"], doc["shots"][-1]["shot_id"]
    for s in doc["shots"]:
        s["page_type"] = "C" if s["shot_id"] in (first, last) else "B"
    tagged = shots_mod.tag_brand_cards(doc)
    if tagged:
        logger.info("[replan] 品牌卡镜: %s (零 GPU 直通)", ",".join(tagged))
    return doc


def _build_doc(book_id: str, book_title: str, ep: int, ep_title: str,
               data: dict[str, Any], bible: dict[str, Any], *,
               sid_offset: int = 0, gid_offset: int = 0) -> dict[str, Any]:
    """导演输出 → 统一 doc: 每镜补产线字段 (状态机/seed/beats/text_layer).

    时间轴 = opening 预留 (剪辑层 5.5s) + manifest 时间 (音频先行原生, 无需事后归真).
    sid/gid_offset: 单场重规划拼接用 — 新镜/组用全局新号 (旧 id 退役防撞),
    且不做全集首/末 C 页标记 (拼接方全局重施).
    """
    tc = float(load().brand_card.opening_sec)
    arc_by_id = {a.get("arc_id"): a for a in data.get("arcs") or []}
    raw_groups = data.get("groups") or []
    if not raw_groups and data.get("shots"):
        # 兼容两层输出 (LLM 未切镜): 每条自成一镜一组 — 镜=生成单位, 组缺层由 label 兜
        raw_groups = [{**s, "group_id": s.get("shot_id") or f"S{i + 1:02d}", "shots": [dict(s)]}
                      for i, s in enumerate(data["shots"])]

    groups_meta: list[dict[str, Any]] = []
    shots_out: list[dict[str, Any]] = []
    n = 0
    gi = 0
    for g in raw_groups:
        gi += 1
        gid = (f"S{gid_offset + gi:02d}" if gid_offset
               else str(g.get("group_id") or f"S{gi:02d}"))
        arc = arc_by_id.get(g.get("arc_id")) or {}
        gt0 = tc + float(g.get("t_start") or 0)
        gt1 = tc + float(g.get("t_end") or 0)
        g_kf = str(g.get("keyframe_zh") or "").strip()
        g_camera = g.get("camera") or "固定"
        inner = g.get("shots") or [g]  # 无镜数组: 组即镜
        g_shot_ids: list[str] = []
        for raw in inner:
            n += 1
            sid = f"s{sid_offset + n:02d}"
            t0 = tc + float(raw.get("t_start") or 0)
            t1 = tc + float(raw.get("t_end") or 0)
            span = max(t1 - t0, 0.5)
            kf_en = str(raw.get("keyframe_en") or "").strip()
            kf_zh = str(raw.get("keyframe_zh") or "").strip() or g_kf  # 镜缺画面 → 组基调兜底
            motion_en = str(raw.get("motion_en") or "").strip() or "the scene evolves with subtle ambient motion"
            gen_span = min(round(span, 2), H3_MAX_SPAN)  # H3 配方上限, 超出草稿定格吸收
            shot = {
                "shot_id": sid,
                "arc_id": g.get("arc_id"),
                "group_id": gid,
                "label": (arc.get("narrative") or "")[:60],
                "camera": raw.get("camera") or g_camera,
                "motion_zh": str(raw.get("motion_zh") or g.get("motion_zh") or "")[:300],
                "page_type": "B",
                "t_start": round(t0, 2), "t_end": round(t1, 2),
                "narration": str(raw.get("narration") or ""),
                # 纯画面描述 — 风格锚由 k2.build_prompt 按书级配方统一注入 (单一事实源,
                # 不在镜级拼 style_prefix, 防"圣经前缀×生成层锚"两套风格打架)
                "image_prompt_zh": kf_zh,
                "keyframe_zh": kf_zh,
                "keyframe_en": kf_en,
                # H3 直用: 单拍节拍壳 (h3.build_prompt 拼首帧对齐/物理锁/静音底)
                "anim": {
                    "duration_s": gen_span,
                    "opening_desc": kf_en or kf_zh,
                    "physical_lock": "the main structural elements and layout",
                    "screen_exception": "nothing",
                    "beats": [{"t_start": 0, "t_end": gen_span, "motion": motion_en}],
                    "ending": "the scene holds with gentle ambient light variation",
                },
                "text_layer": raw.get("text_layer") or [],
                "qc_notes": "",
                "extra_loras": [],
                "seed": shots_mod.new_seed(),
                "h3_seed": shots_mod.new_seed(),
                "status": "planned",
                "brand_card": False,
                "image_file": None, "video_file": None,
                "attempts": {"k2": 0, "h3": 0},
                "error": None, "reject_note": "",
            }
            if span > H3_MAX_SPAN + 0.05:
                shot["overrun_s"] = round(span - H3_MAX_SPAN, 2)
            # 0919 装包制标透传 (packed=普通槽镜, zone=特区镜) — 对齐链路保护用
            for _k in ("zone", "packed", "scene_tag"):
                if raw.get(_k) is not None:
                    shot[_k] = raw[_k]
            # 0920 浮字军规: LLM 违规浮字当场下沉 overlay + text_layer 同步补登记
            _gate_motion_text(shot)
            _ensure_motion_text(shot)  # 0920 补字回填 (军规逆操作)
            shots_out.append(shot)
            g_shot_ids.append(sid)
        groups_meta.append({
            "group_id": gid, "arc_id": g.get("arc_id"),
            "t_start": round(gt0, 2), "t_end": round(gt1, 2),
            "narration": str(g.get("narration") or "")[:300],
            "camera": g_camera,
            "keyframe_zh": g_kf,
            "motion_zh": str(g.get("motion_zh") or "")[:300],
            "shot_ids": g_shot_ids,
        })
    if shots_out and not sid_offset:  # 单场拼接模式不做 C 标记 (拼接方全局重施)
        shots_out[0]["page_type"] = "C"
        shots_out[-1]["page_type"] = "C"
    doc = {
        "version": shots_mod.SCHEMA_VERSION,
        "book_id": book_id, "book_title": book_title, "ep": ep, "ep_title": ep_title,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "planner_flow": "director2 arcs v2 (场→组→镜)",
        "planner_model": "pro",
        "ep_summary": data.get("ep_summary", ""),
        "style_recipe": resolve_style(book_title).get("name"),
        "bible": bible,
        "arcs": [{**a,
                  "t_start": round(tc + float(a.get("t_start") or 0), 2),
                  "t_end": round(tc + float(a.get("t_end") or 0), 2)}
                 for a in data.get("arcs") or []],
        "groups": groups_meta,
        "shots": shots_out,
    }
    tagged = shots_mod.tag_brand_cards(doc)
    if tagged:
        logger.info("[plan] 品牌卡镜: %s (零 GPU 直通)", ",".join(tagged))
    return doc


# ── 确定性校验 (自 anim_director.validate_shots 平移) ─────────

def _clamp_motion_events(shot: dict[str, Any]) -> bool:
    """motion_zh 里超出镜长的"N秒时"事件子句删除 (0917 用户令修实 bug).

    拆镜后父镜/分身继承的 motion_zh 仍带拆前绝对时间 (s21 5s 镜里留 8s/12s 事件),
    LLM 新产也会越界 (s04 5.1s 镜写"12秒时")。beats 才是 H3 真值, motion_zh 是
    设计文本 — 不可达事件留着 = 说谎的设计文档。返回是否改写。
    """
    span = round(float(shot.get("t_end") or 0) - float(shot.get("t_start") or 0), 2)
    txt = str(shot.get("motion_zh") or "")
    if not txt or span <= 0:
        return False
    toks = re.split(r"([，。；,;])", txt)
    out: list[str] = []
    changed = False
    for tok in toks:
        if not tok:
            continue
        if re.fullmatch(r"[，。；,;]", tok):
            out.append(tok)
            continue
        times = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*秒", tok)]
        if times and max(times) > span + 0.05:
            changed = True  # 该子句的事件时间不可达 → 整子句删
            if out and re.fullmatch(r"[，。；,;]", out[-1] or ""):
                out.pop()  # 别留悬空分隔符
            continue
        out.append(tok)
    if changed:
        shot["motion_zh"] = "".join(out).strip("，。；,; ")
    return changed


# ── 浮字军规 (0920): H3 只画 ≤2 字超短标 — LLM 违规必纠, 复杂字下沉剪辑层 ──
# ep4 实锤 6/79 文字变形: '归零'→赐零/聰零, '辑'缺笔, '谁付得多'→烧付得多,
# '改规则''报价重调'错字 — 全是 LLM 违反自家 0915 铁律 (≤2字/一镜一词) 的产物.
# 同 _clamp_motion_events 教义: 提示词劝不住的, 落盘前确定性拦.

# 引号浮字 token ('贱'/'归零'/'5000+'/‘单价’ — 内容非空白 ≤12 字)
_FT_TOKEN_RE = re.compile(r"[''\"‘“]([^''\"’”\s]{1,12})[''\"’”]")
# 子句是否"浮字事件": 引号 token + 文字语境词 (双条件防误杀普通引号)
_FT_CTX_RE = re.compile(r"大字|艺术字|艺术数字|特大|金字|红字|浮出|浮现|砸出|砸落|滑入|升起|数字'|字'")
# 花体 (H3 变形放大器: 书法/手写/冲击/抖动)
_FT_FANCY_RE = re.compile(r"书法|手写|冲击|抖动")
_FT_RED_RE = re.compile(r"红色|信号红|红字|大红")
_FT_TIME_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:秒|s(?![a-zA-Z]))")
# 沉字后紧跟的无 token 尾巴子句 ("字体是书法手写体"/"红色字带震动效果"/"数字带弹跳")
_FT_ORPHAN_RE = re.compile(r"^(字体|字带|字旁|字形|数字带|.{0,3}字带|该字|此字|同风格|同样|同款)")


def _ft_cjk_len(t: str) -> int:
    return sum("一" <= c <= "鿿" for c in t)


def _ft_clause_time(clause: str, span: float) -> tuple[float, float]:
    m = _FT_TIME_RE.search(clause)
    t0 = min(float(m.group(1)), max(span - 0.5, 0)) if m else 0.8
    return round(t0, 2), round(min(t0 + 2.5, max(span, 1.0)), 2)


def _gate_motion_text(shot: dict[str, Any]) -> bool:
    """浮字军规 + text_layer 同步 (0920 修 ep4 六镜变形实锤).

    ① 军规: H3 只画 [纯ASCII短标 | CJK≤2] 且每镜至多 1 个且无花体 (书法/手写/
    冲击/抖动) — 与 h3.py TEXT_POLICY 同口径. 违规浮字从 motion_zh 子句和
    beats 英文段里整段删除, 改写 text_layer overlay 条目 (留档/音效 cue/
    回填候选 — 0921 起剪辑层不再渲染大字轨, 用户实锤 ep6 下沉条目全是
    零星孤岛碎字; color gold/red 仍驱 音效分类).
    ② 同步: 合规保留的浮字若 text_layer 漏登记 (s21/s22 实锤) → 补
    hero_number/impact 条目 (字幕行内高亮锚 + 留档). 幂等: 同文本条目已存在
    不重写. 返回是否改写.
    """
    span = round(float(shot.get("t_end") or 0) - float(shot.get("t_start") or 0), 2)
    mz = str(shot.get("motion_zh") or "")
    if not mz or span <= 0:
        return False
    parts = re.split(r"([，。；,;])", mz)
    clauses = [(i, p) for i, p in enumerate(parts)
               if p and not re.fullmatch(r"[，。；,;]", p)]

    # 事件提取: (clause_idx, token, t0, t1, fancy, red)
    events: list[dict[str, Any]] = []
    for i, cl in clauses:
        if not _FT_CTX_RE.search(cl):
            continue
        for tok in _FT_TOKEN_RE.findall(cl):
            # 守卫放行: 字母数字/汉字, 或 ?！·≠ 等单字符短标 (H3 强项)
            if not re.search(r"[0-9A-Za-z一-鿿？?！!·≠＋+]", tok):
                continue
            t0, t1 = _ft_clause_time(cl, span)
            events.append({"ci": i, "tok": tok, "t0": t0, "t1": t1,
                           "fancy": bool(_FT_FANCY_RE.search(cl)),
                           "red": bool(_FT_RED_RE.search(cl))})
    if not events:
        return False

    # 同文本去重 (首现定时), 判 keep/sink
    seen: dict[str, dict[str, Any]] = {}
    for ev in events:
        seen.setdefault(ev["tok"], ev)
    uniq = sorted(seen.values(), key=lambda e: e["t0"])
    n_text_clauses = len({e["ci"] for e in events})
    keep: list[str] = []
    for ev in uniq:
        sink = (ev["fancy"] or _ft_cjk_len(ev["tok"]) > 2
                or n_text_clauses >= 2 or len(keep) >= 1)
        if not sink:
            keep.append(ev["tok"])
        ev["sink"] = sink
    sunk = [e for e in uniq if e["sink"]]

    changed = False
    tl = list(shot.get("text_layer") or [])

    def _has(kind: str, text: str) -> bool:
        return any(str(t.get("kind")) == kind
                   and shots_mod.norm_for_match(str(t.get("text") or "")) == shots_mod.norm_for_match(text)
                   for t in tl)

    # ① sink → 删 motion_zh 子句 (含无 token 尾巴子句) + 删 beats 英文段 + 写 overlay
    if sunk:
        # 沉字所有出现子句全删 (同 token 可跨多句, 只删首现会留尾巴 — s55 实锤)
        sunk_toks = {e["tok"] for e in sunk}
        drop_ci = {e["ci"] for e in events if e["tok"] in sunk_toks}
        out: list[str] = []
        prev_dropped = False
        for i, p in enumerate(parts):
            if not p:
                continue
            if re.fullmatch(r"[，。；,;]", p):
                out.append(p)  # 分隔符先留, 删句时回吞 (同 _clamp 做法)
                continue
            drop = i in drop_ci or (prev_dropped and _FT_ORPHAN_RE.match(p))
            if drop:
                if out and re.fullmatch(r"[，。；,;]", out[-1] or ""):
                    out.pop()  # 删子句连同其前分隔符, 活句不粘连
                prev_dropped = True
                continue
            prev_dropped = False
            out.append(p)
        new_mz = "".join(out).strip("，。；,; ")
        if new_mz != mz:
            shot["motion_zh"] = new_mz
            changed = True
        for e in sunk:
            # 0921 三 kind 全查重 (s37 实锤: 走不通已登记 impact 又追加 overlay
            # = 同字双条; ② 分支 0920 已修, ① 下沉分支同律)
            if not any(_has(k, e["tok"]) for k in ("hero_number", "impact", "overlay")):
                tl.append({"kind": "overlay", "text": e["tok"],
                           "t_start": e["t0"], "t_end": e["t1"],
                           "color": "red" if e["red"] else "gold"})
                changed = True
        # beats 英文段删除: 只删含沉字引号的段 (括号保护后按逗号/分号切, 段自足)
        pat = re.compile("[" + re.escape("''\"‘“") + "](" +
                         "|".join(re.escape(e["tok"]) for e in sunk) +
                         ")[" + re.escape("''\"’”") + "]")
        anim = shot.get("anim") or {}
        for b in anim.get("beats") or []:
            mot = str(b.get("motion") or "")
            if not mot or not pat.search(mot):
                continue
            prot: list[str] = []

            def _shield(m_):  # noqa: E306
                prot.append(m_.group(0))
                return f"\x00{len(prot) - 1}\x00"

            masked = re.sub(r"\([^()]*\)", _shield, mot)
            segs = re.split(r"(?<=[,;])\s+", masked)
            kept = [s_ for s_ in segs if not pat.search(s_)]
            if len(kept) != len(segs):
                new_mot = re.sub(r"\x00(\d+)\x00",
                                 lambda m_: prot[int(m_.group(1))],
                                 " ".join(kept))
                new_mot = re.sub(r"\s+", " ", new_mot).rstrip(" ;,.").strip()
                if new_mot != mot:
                    b["motion"] = new_mot
                    changed = True
        # 军规保字但所在子句同句共沉 → 字丢了, 转 overlay 兜底 (存活判定重提 token)
        alive = set(_FT_TOKEN_RE.findall(str(shot.get("motion_zh") or "")))
        for tok in keep:
            if tok not in alive:
                ev = next(e for e in uniq if e["tok"] == tok)
                if not any(_has(k, tok) for k in ("hero_number", "impact", "overlay")):
                    tl.append({"kind": "overlay", "text": tok,
                               "t_start": ev["t0"], "t_end": ev["t1"],
                               "color": "red" if ev["red"] else "gold"})
                    changed = True

    # ② keep → text_layer 补登记 (hero_number/impact; 字幕行内高亮锚)
    alive = set(_FT_TOKEN_RE.findall(str(shot.get("motion_zh") or "")))
    for tok in keep:
        if tok in alive:
            ev = next(e for e in uniq if e["tok"] == tok)
            kind = "impact" if ev["red"] else "hero_number"
            # 0920: 三 kind 全查重 — ep5 实锤 token 已登记为 impact 时又追加
            # hero_number = 同字双条, 剪辑层双重渲染 (补字回填放大暴露)
            if not any(_has(k, tok) for k in ("hero_number", "impact", "overlay")):
                tl.append({"kind": kind, "text": tok,
                           "t_start": ev["t0"], "t_end": ev["t1"]})
                changed = True

    if tl != list(shot.get("text_layer") or []):
        shot["text_layer"] = tl
    return changed



# ── H3 补字回填 (0920 修 ep5 全批零浮字实锤 — 文字军规的逆操作) ──────────────
# 军规只拦违规浮字, 但 0920 提示词收紧 ("违规整段删掉转 overlay — 白写") 后
# LLM 连合规短标也不写进 motion 了: ep4 16 镜带浮字 → ep2/ep5 全批 0 镜,
# H3 补字层整层蒸发, 视频全无文字 (用户实锤"一镜都没有"). 提示词劝不住 →
# 落盘前确定性补 (同军规教义, 方向相反).

def _ensure_motion_text(shot: dict[str, Any]) -> bool:
    """从 text_layer 挑最强合规短标注入 motion_zh 文字事件 + beats 英文段.

    候选优先级 hero_number > impact > overlay (同 kind 取 t_start 最早);
    合规口径同军规: ≤2 字中文或纯短 ASCII、单 token、非花体、时间可达.
    注入子句自身必过 _gate_motion_text (幂等共存). brand_card 直通镜 /
    motion_zh 已有浮字事件 / 无 anim.beats → 不动. 返回是否改写.
    """
    if shot.get("brand_card"):
        return False
    span = round(float(shot.get("t_end") or 0) - float(shot.get("t_start") or 0), 2)
    mz = str(shot.get("motion_zh") or "")
    beats = (shot.get("anim") or {}).get("beats") or []
    if span <= 0 or not mz or not beats:
        return False
    if any(_FT_CTX_RE.search(cl) and _FT_TOKEN_RE.findall(cl)
           for cl in re.split(r"[，。；,;]", mz)):
        return False  # 已有浮字事件 (LLM 写了或前次回填)
    order = {"hero_number": 0, "impact": 1, "overlay": 2}
    cand: dict[tuple[int, float], dict[str, Any]] = {}
    for t in shot.get("text_layer") or []:
        kind = str(t.get("kind") or "")
        tok = str(t.get("text") or "").strip()
        if kind not in order or not tok:
            continue
        if not re.search(r"[0-9A-Za-z一-鿿？?！!·≠＋+]", tok):
            continue
        if _ft_cjk_len(tok) > 2 or (len(tok) > 8 and not _ft_cjk_len(tok)):
            continue
        key = (order[kind], round(float(t.get("t_start") or 0), 2))
        cand.setdefault(key, {"tok": tok, "t0": float(t.get("t_start") or 0),
                              "t1": float(t.get("t_end") or 0)})
    if not cand:
        return False
    best = cand[min(cand)]
    tok = best["tok"]
    t0 = min(best["t0"], max(span - 1.0, 0.0))
    t1 = min(max(best["t1"], t0 + 1.2), span)
    dur = round(t1 - t0, 1)
    shot["motion_zh"] = mz.rstrip("，。；,; ") + (
        f"；文字事件：第{t0:.1f}秒“{tok}”以粗楷大字浮出（避开主体脸与关键物），"
        f"持续{dur:.1f}秒后淡出")
    b = beats[-1]
    b["motion"] = (str(b.get("motion") or "").rstrip(" ;,.") +
                   f'; at {t0:.1f}s the bold word "{tok}" floats up large in a '
                   f'clear area away from the subject, holds {dur:.1f}s, fades out')
    # 0920 双源互斥 (同军规不变量: token 要么 H3 入画要么 overlay, 不双渲):
    # 0916 降维令后 overlay 是剪辑层唯一大字轨 — 入画接管即撤 overlay,
    # hero_number/impact 锚保留 (字幕行内高亮, R9 三件套 ①+③ 共存)
    tl = list(shot.get("text_layer") or [])
    red = any(str(e.get("color")) == "red" for e in tl
              if str(e.get("kind")) == "overlay" and str(e.get("text") or "").strip() == tok)
    tl = [e for e in tl if not (str(e.get("kind")) == "overlay"
                                and str(e.get("text") or "").strip() == tok)]
    if not any(str(e.get("kind")) in ("hero_number", "impact")
               and str(e.get("text") or "").strip() == tok for e in tl):
        tl.append({"kind": "impact" if red else "hero_number", "text": tok,
                   "t_start": t0, "t_end": t1})
    shot["text_layer"] = tl
    return True


def _clone_families(shots: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """克隆家系检测: 时间轴相邻、同组、keyframe_zh 逐字相同的镜群.

    家系首镜 = 设计本尊 (保留), 其后 = 拆镜复印残留 (违反"每镜必换构图").
    宪法明文"续镜(机位不变)=废稿", 无论克隆从哪条路进来 (整集规划/单场/归真
    拆镜) 这里都能确定性抓到.
    """
    fams: list[list[dict[str, Any]]] = []
    cur: list[dict[str, Any]] = []
    for s in sorted(shots, key=lambda x: float(x.get("t_start") or 0)):
        same = (cur and not s.get("brand_card")  # 品牌镜 DNA 冻结, 只当边界不当分身
                and str(s.get("group_id")) == str(cur[-1].get("group_id"))
                and (s.get("keyframe_zh") or "").strip()
                and (s.get("keyframe_zh") or "") == (cur[-1].get("keyframe_zh") or ""))
        if not same:
            if len(cur) > 1:
                fams.append(cur)
            cur = []
        cur.append(s)
    if len(cur) > 1:
        fams.append(cur)
    return fams


def redesign_split_clones(doc: dict[str, Any], bible: dict[str, Any] | None = None) -> dict[str, int]:
    """拆镜分身重设计 (0917 用户实锤"太多镜都一样"): 克隆分身批量换构图.

    自动拆镜是时长物理上限的兜底, 不是视觉复印机 — 分身逐字继承父镜提示词
    +相邻 seed = 同一张图换噪点. 本函数把全部克隆家系一次 LLM 调用重设计:
    场景/年代/人物双约/风格与父镜一致, 景别/机位/画面时刻逐镜推进.
    槽位 (时间/口播/镜号/字幕层) 钉死不动; LLM 没接住或解析失败的分身保持
    克隆 (collect_warnings 亮灯), 调用方可重跑本函数 (幂等: 只认逐字克隆).
    返回 {"redesigned": n, "failed": m}.
    """
    fams = _clone_families(doc.get("shots") or [])
    kids = [s for f in fams for s in f[1:]]
    if not kids:
        return {"redesigned": 0, "failed": 0}
    from app.config import load_config, set_config
    set_config(load_config())
    from app.services.book_service.creation_common import _llm, _parse_json

    groups = {str(g.get("group_id")): g for g in doc.get("groups") or []}
    arcs = {str(a.get("arc_id")): a for a in doc.get("arcs") or []}
    bible = bible or doc.get("bible") or {}
    bible_block = ""
    if bible:
        bible_block = ("- 风格: " + str(bible.get("style_prefix") or "")[:100]
                       + " | 色彩: " + str(bible.get("color_palette") or "")[:80])

        _chars = bible.get("characters") or []
        if _chars:
            _ls = "; ".join(f"{c.get('name')}({c.get('look', '')})" for c in _chars if c.get("look"))
            if _ls:
                bible_block += chr(10) + "- 角色锁定卡 (出场角色 keyframe_zh 原样携带 look): " + _ls
    blocks = []
    for f in fams:
        head, fam_kids = f[0], f[1:]
        g = groups.get(str(head.get("group_id")) or "", {})
        a = arcs.get(str(head.get("arc_id")) or "", {})
        kids_line = chr(10).join(
            f"  - {k['shot_id']}: {round(float(k['t_end']) - float(k['t_start']), 1)}s"
            f" | 口播: {str(k.get('narration') or '')[:70]} | 旧机位: {k.get('camera') or '?'}"
            for k in fam_kids)
        blocks.append(
            f"家系 {head['shot_id']} (场 {str(a.get('narrative') or '')[:40]} | 场景定调: "
            f"{str(g.get('keyframe_zh') or '')[:70]}){chr(10)}"
            f"父镜设计 (画面基准 — 分身必须同场景同时刻同人物): "
            f"{str(head.get('keyframe_zh') or '')[:130]}{chr(10)}待重设计分身:{chr(10)}{kids_line}")
    user = ("【模式: 拆镜分身重设计】自动拆镜把超长镜切成了几段, 分身现在是父镜的复印件 — "
            "只重设计下列分身的画面, 时间槽/口播/镜号/字幕层全部钉死不动。" + chr(10)
            + "铁律: ① 同一家系 = 同一场同一时刻同一批人物 (造型/年龄段/表情基调跨镜一致, 双约一致), "
            "年代/场景/色调与父镜完全一致; ② 每个分身与父镜、与其他分身在景别/机位/画面时刻"
            "至少一项显著不同 (如 远景全景→中景→近景特写 的推进), 画面随口播推进一拍; "
            "③ 首帧全灭字 — 禁任何可读文字/数字/字母/标志; ④ 一镜一事, 运镜=固定或极轻微推拉, "
            "禁横移跟拍。" + chr(10) + "【圣经】" + bible_block + chr(10) + chr(10)
            + chr(10).join(blocks) + chr(10) + chr(10)
            + "【输出】严格 JSON: {\"redesigns\": [{\"shot_id\": \"原样带回\", "
              "\"keyframe_zh\": \"首帧(具象+视角锁死+信息完备)\", \"keyframe_en\": \"English, no text\", "
              "\"motion_zh\": \"动画层+至多1个文字事件\", \"motion_en\": \"English ambient motion\", "
              "\"camera\": \"...\"}]} — 上面每个分身一条, 一条不落")
    logger.info("[redesign-clones] %d 家系 %d 分身重设计中… (LLM 1-2 分钟)", len(fams), len(kids))
    raw = _llm().chat(DIRECTOR_SYS, user, model="pro", temperature=0.5)
    data = _parse_json(raw) or {}
    got = {str(r.get("shot_id")): r for r in (data.get("redesigns") or [])
           if isinstance(r, dict) and r.get("shot_id")}
    n = 0
    for fam in fams:
        for k in fam[1:]:
            r = got.get(str(k["shot_id"]))
            kf_zh = str((r or {}).get("keyframe_zh") or "").strip()
            if not kf_zh:
                continue
            span = round(float(k["t_end"]) - float(k["t_start"]), 2)
            gen = min(span, H3_MAX_SPAN)
            motion_en = str((r or {}).get("motion_en") or "").strip() or \
                "Gentle ambient motion, very slight push-in."
            k.update({  # 重置语义与 plan_shot 同款 (口播未变, 媒体必须显式清)
                "keyframe_zh": kf_zh,
                "keyframe_en": str(r.get("keyframe_en") or "").strip(),
                "image_prompt_zh": kf_zh,
                "motion_zh": str(r.get("motion_zh") or "")[:300],
                "camera": r.get("camera") or k.get("camera") or "固定",
                "anim": {
                    "duration_s": gen,
                    "opening_desc": str(r.get("keyframe_en") or "").strip() or kf_zh,
                    "physical_lock": "the camera viewpoint, the main structural elements and layout",
                    "screen_exception": "nothing",
                    "beats": [{"t_start": 0, "t_end": gen, "motion": motion_en}],
                    "ending": "the scene holds with gentle ambient light variation",
                },
                "seed": shots_mod.new_seed(),
                "h3_seed": shots_mod.new_seed(),
                "status": "planned",
                "image_file": None, "video_file": None,
                "attempts": {"k2": 0, "h3": 0},
                "error": None, "reject_note": "",
                "split_parent": str(fam[0]["shot_id"]),
            })
            k.pop("overrun_s", None)
            _clamp_motion_events(k)  # LLM 新产的越界事件时间 → 删
            _gate_motion_text(k)  # 浮字军规: 新产 motion 同样过闸
            _ensure_motion_text(k)  # 0920 补字回填 (军规逆操作)
            n += 1
    failed = len(kids) - n
    if failed:
        logger.warning("[redesign-clones] %d 分身未接住, 保持克隆 (软警告亮灯)", failed)
    logger.info("[redesign-clones] ✓ %d 分身已换构图, %d 保持克隆", n, failed)
    return {"redesigned": n, "failed": failed}


def validate_doc(doc: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    shots = doc.get("shots") or []
    tc = float(load().brand_card.opening_sec)  # 镜轴含开场预留, 音频侧对齐要加回

    total_audio = sum(float(s["t_end"]) - float(s["t_start"]) for s in shots)
    if shots:
        shot_end = max(float(s["t_end"]) for s in shots)
        if abs(shot_end - total_audio - tc) > 2.0:
            issues.append(f"末组终点 {shot_end:.1f}s ≠ 开场预留+镜轴总长 {total_audio + tc:.1f}s")
    for i in range(1, len(shots)):
        prev_end = float(shots[i - 1]["t_end"])
        cur_start = float(shots[i]["t_start"])
        if abs(prev_end - cur_start) > 0.5:
            issues.append(f"时间轴断裂: {shots[i-1]['shot_id']}({prev_end:.1f}s) → "
                          f"{shots[i]['shot_id']}({cur_start:.1f}s)")
    for s in shots:
        dur = float(s["t_end"]) - float(s["t_start"])
        if dur < 1.5:
            issues.append(f"{s['shot_id']} 时长 {dur:.1f}s < 1.5s")
        # 超长镜不硬拒: 归真层自动拆镜兜底 (0916 句级细分, 整句包分块 ≤H3上限);
        # 硬拒会与自动拆镜重复执法 → 规划死循环 (LLM 难精确控时长实锤)
    for s in shots:
        if not (s.get("motion_zh") or "").strip():
            issues.append(f"{s['shot_id']} 缺运动描述 — 违反运动驱动原则")
    return issues  # 硬校验到此; 文字类问题走 collect_warnings (物理防护在 K2灭字尾/H3壳, 人检兜底)


def collect_warnings(doc: dict[str, Any]) -> list[str]:
    """软警告 (不挡规划, 记录留痕): keyframe 混英文风格词/可读文字, motion 急推词."""
    shots = doc.get("shots") or []
    warns: list[str] = []
    # 超长镜提示 (不挡 — 归真层自动拆镜兜底, 0916 硬拒死循环教训)
    warns += [f"{s['shot_id']} 时长 {float(s['t_end']) - float(s['t_start']):.1f}s 超 H3 上限 "
              f"(归真自动拆镜兜底)" for s in shots
              if float(s["t_end"]) - float(s["t_start"]) > H3_MAX_SPAN + 0.05]
    # 白名单: 圣经 style_prefix / 配方风格词 (LLM 常把全局风格词带进画面描述, 非真违规)
    wl = set(re.findall(r"[A-Za-z]{3,}", (doc.get("bible") or {}).get("style_prefix") or ""))
    wl |= {"cel", "celanimation", "traditional"}
    _hex_strip = re.compile(r"#[0-9a-fA-F]{3,8}")
    _text_pat = re.compile(r"[a-zA-Z]{3,}|\d{3,}")
    for s in shots:
        kf = _hex_strip.sub("", s.get("keyframe_zh") or "")
        hits = [h for h in _text_pat.findall(kf) if h.lower() not in wl]
        if hits:
            warns.append(f"{s['shot_id']} keyframe 疑含可读文字/数字 {'/'.join(hits[:3])} — K2 灭字尾会物理防护, text_layer 需自查")
    _fast_pat = re.compile(r"猛然|急速|快速|飞速|瞬间|突然|闪电")
    for s in shots:
        if _fast_pat.search((s.get("motion_zh") or "") + (s.get("camera") or "")):
            warns.append(f"{s['shot_id']} motion 含急推词 — H3 壳有缓速措辞对冲, 建议人检")
    # 越界事件时间 (0917): "N秒时"事件超出镜长 = 不可达, 设计文档说谎
    for s in shots:
        span = float(s["t_end"]) - float(s["t_start"])
        bad = [x for x in re.findall(r"(\d+(?:\.\d+)?)\s*秒", s.get("motion_zh") or "")
               if float(x) > span + 0.05]
        if bad:
            warns.append(f"{s['shot_id']} motion 文字事件超镜长 ({'/'.join(bad)} > {span:.1f}s) — 事件不可达")
    # 克隆家系 (0917 用户实锤"太多镜都一样"): 分身逐字=父镜 → 同一张图换噪点
    for f in _clone_families(shots):
        kids = "/".join(s["shot_id"] for s in f[1:])
        warns.append(f"{f[0]['shot_id']} 拆镜分身克隆未重设计 (画面与父镜逐字相同): {kids} — "
                     f"重跑对齐自动重设计, 或单镜🔁")
    # 政治敏感画面禁区 (0917 用户令): 命中即亮灯 (生成闸门另硬拒)
    _ban_hits = visual_ban_scan(doc)
    if _ban_hits:
        warns.append(f"画面命中政治敏感禁区 (中国地图/国旗/国徽/领导人): {'、'.join(_ban_hits[:6])} — "
                     f"单镜🔁 重设计, 卡通/剪影/变形同禁")
    return warns


def consistency_review(doc: dict[str, Any], bible: dict[str, Any] | None = None) -> dict[str, Any]:
    """全片巡检轮 (0917 用户令: 调优优先) — 逐场渐进产出的代价=局部视角.

    多轮对话: assistant=全片分镜摘要 (模型看见自己画的所有镜) → user=巡检指令
    → 只出修正清单 patches [{shot_id, keyframe_zh, keyframe_en, camera, motion_zh}]。
    检查面: 跨场人物双约一致 / 圣经色板贯彻 / 相邻镜构图重复 / 隐喻场内贯彻 /
    黑名单。确定性应用 (仅清单内已存在的镜, 媒体重置回 planned), 零 patch=不落刀。
    返回 {"patched": n, "issues": [...]}。
    """
    shots = sorted(doc.get("shots") or [], key=lambda s: float(s.get("t_start") or 0))
    if not shots:
        return {"patched": 0, "issues": []}
    from app.config import load_config, set_config
    set_config(load_config())
    from app.services.book_service.creation_common import _llm, _parse_json

    board = "\n".join(
        f"{s['shot_id']} [{s.get('arc_id')}] {round(float(s['t_end']) - float(s['t_start']), 1)}s "
        f"{(s.get('keyframe_zh') or '')[:90]}"
        for s in shots)
    user1 = ("【模式: 全片分镜总览 (只读)】以下是本集全部镜的首帧设计, 场结构见 arcs。"
             "\n" + board)
    ask = ("【全片巡检轮 — 只出修正清单, 不新增镜】逐镜检查跨场一致性: ①人物双约跨场一致 "
           "(同人物年龄/造型/表情基调) ②圣经色板贯彻 (金=钱/被选中, 红=危机) "
           "③相邻镜构图是否重复 (含跨场接缝) ④场隐喻是否贯彻到每镜 ⑤黑名单"
           "(商务素材/政治禁区)。只修真问题 — 宁可零修正不可为改而改。"
           "输出严格 JSON: {\"issues\": [\"一句话问题\", ...], \"patches\": "
           "[{\"shot_id\": \"s03\", \"keyframe_zh\": \"新首帧\", \"keyframe_en\": \"English, no text\", "
           "\"camera\": \"...\", \"motion_zh\": \"...\", \"motion_en\": \"English ambient motion\"}]} "
           "— patches 最多 8 条, 无问题给空数组。")
    logger.info("[consistency] 全片巡检轮中… (LLM 1-2 分钟, %d 镜)", len(shots))
    raw = _llm().chat_turns(
        [{"role": "system", "content": DIRECTOR_SYS},
         {"role": "user", "content": user1},
         {"role": "assistant", "content": "已通读全部分镜, 请下巡检指令。"},
         {"role": "user", "content": ask}],
        model="pro", temperature=0.3)
    data = _parse_json(raw) or {}
    patches = [p for p in (data.get("patches") or [])
               if isinstance(p, dict) and p.get("shot_id") and str(p.get("keyframe_zh") or "").strip()]
    by_id = {s["shot_id"]: s for s in shots}
    n = 0
    _snapshots: dict[str, dict[str, Any]] = {}
    _patched: list[str] = []
    for p in patches[:8]:
        s = by_id.get(str(p["shot_id"]))
        if s is None or s.get("brand_card"):
            continue  # 未知镜/品牌镜不动
        _snapshots[s["shot_id"]] = {k: (dict(s[k]) if isinstance(s[k], dict) else s[k])
                                    for k in ("keyframe_zh", "keyframe_en", "image_prompt_zh",
                                              "camera", "motion_zh", "anim", "seed", "h3_seed",
                                              "status", "image_file", "video_file", "attempts",
                                              "error", "reject_note") if k in s}
        _patched.append(s["shot_id"])
        kf = str(p["keyframe_zh"]).strip()
        kf_en = str(p.get("keyframe_en") or "").strip()
        s.update({
            "keyframe_zh": kf,
            "keyframe_en": kf_en,
            "image_prompt_zh": kf,
            "camera": p.get("camera") or s.get("camera") or "固定",
            "motion_zh": str(p.get("motion_zh") or s.get("motion_zh") or "")[:300],
            "seed": shots_mod.new_seed(),
            "h3_seed": shots_mod.new_seed(),
            "status": "planned",
            "image_file": None, "video_file": None,
            "attempts": {"k2": 0, "h3": 0},
            "error": None, "reject_note": "",
        })
        # anim 必须同步重建 (0917 深查: h3 吃 opening_desc — 只改 keyframe 不重建
        # = 新图配旧视频锁, 图视失配; 与 plan_shot/redesign 同款语义)
        span = round(float(s["t_end"]) - float(s["t_start"]), 2)
        gen = min(span, H3_MAX_SPAN)
        motion_en = str(p.get("motion_en") or "").strip() or \
            "Gentle ambient motion, very slight push-in."
        s["anim"] = {
            "duration_s": gen,
            "opening_desc": kf_en or kf,
            "physical_lock": "the camera viewpoint, the main structural elements and layout",
            "screen_exception": "nothing",
            "beats": [{"t_start": 0, "t_end": gen, "motion": motion_en}],
            "ending": "the scene holds with gentle ambient light variation",
        }
        _clamp_motion_events(s)
        _gate_motion_text(s)  # 巡检 patch 也是新 LLM 产出 — 浮字军规同闸
        _ensure_motion_text(s)  # 0920 补字回填 (军规逆操作)
        n += 1
    # patch 后重扫 (0917 闭环): 巡检产物本身是新 LLM 产出 — 禁区命中即回滚该 patch
    from app.services import compliance as _cmp2
    for sid in _patched:
        s = by_id.get(sid)
        blob = " ".join(filter(None, [str(s.get("keyframe_zh") or ""), str(s.get("keyframe_en") or ""),
                                      str(s.get("motion_zh") or "")]))
        if _cmp2.check_visual(blob):
            logger.warning("[consistency] patch %s 命中禁区 → 回滚", sid)
            s.update(_snapshots[sid])
            n -= 1
    issues = [str(x)[:120] for x in (data.get("issues") or [])][:10]
    if n or issues:
        logger.info("[consistency] ✓ 修正 %d 镜, 问题留痕 %d 条", n, len(issues))
    return {"patched": n, "issues": issues}




_ENHANCE_SYS = (
    "你是电影摄影指导。给你导演写的基础画面描述，"
    "你只做一件事：补上摄影级的视觉层次。不改内容不改人物不改场景不加文字。"
    "补充以下四项，每项必须："
    "一，光线设计：光从哪来、什么色温、在地面墙面拉出什么光影、冷暖对比。"
    "二，景深层次：前景主体是什么、中景环境是什么、远景深处是什么。"
    "三，空间感：天花板天空走廊远方，让画面有看出去的纵深感。"
    "四，氛围细节：空气中的微粒热气雾气光晕，让画面有温度。"
    "输出：增强后的完整画面描述，在原描述基础上扩写，保留全部原有内容，只加不删。"
    "禁止：色值编码、英文、文字字母数字内容。"
    "直接输出增强后的中文画面句，总字数控制在200至300字之间，简洁有力。禁止提及指纹、指纹纹理、手印、微缩、缩小、模型感。禁止重复风格头已有的词（如手工捏制、黏土质感），只写画面内容。"
)


def enhance_keyframes(doc, book_title):
    """提示词增强 (0923 用户令: 一步LLM专注一件事).

    导演管叙事切镜角色，增强器管光线景深空间氛围。
    在K2之前批量跑，改写doc内每镜的keyframe_zh和image_prompt_zh。
    幂等：已有_enhanced标记的镜跳过。
    """
    from app.services.book_service.creation_common import _llm
    from app.config import load_config, set_config
    set_config(load_config())
    bible = load_or_derive_bible("", book_title)
    style_ctx = ""
    if bible:
        style_ctx = "风格: " + str(bible.get("style_prefix", ""))[:80] + " | 色调: " + str(bible.get("color_palette", ""))[:60]
    n = 0
    for s in doc.get("shots") or []:
        if s.get("_enhanced"):
            continue
        base = str(s.get("keyframe_zh") or "").strip()
        if len(base) < 20:
            continue
        try:
            user = "风格参考：" + style_ctx + chr(10) + "导演基础画面：" + base + chr(10) + "增强后输出："
            out = _llm().chat(_ENHANCE_SYS, user, model="pro", temperature=0.3)
            enhanced = str(out or "").strip()
            if len(enhanced) > len(base) * 1.2:
                s["keyframe_zh"] = enhanced
                s["image_prompt_zh"] = enhanced
                s["_enhanced"] = True
                n += 1
        except Exception as exc:
            logger.warning("[enhance] %s 失败用原句: %s", s.get("shot_id"), exc)
    if n:
        shots_mod.save(doc)
    logger.info("[enhance] %s ep%s: %d/%d 镜已增强", book_title, doc.get("ep"), n, len(doc.get("shots") or []))
    return n


def visual_ban_scan(doc: dict[str, Any]) -> list[str]:
    """政治敏感画面禁区扫描 (0917 用户令): 返回 ["s01(国旗)", ...] 命中镜清单.

    词库单一事实源 = config/compliance_visual.json (compliance.check_visual);
    扫描面 = keyframe_zh/motion_zh/text_layer 全部画面文本。
    """
    from app.services import compliance as _cmp
    out: list[str] = []
    for s in doc.get("shots") or []:
        blob = " ".join(filter(None, [
            str(s.get("keyframe_zh") or ""), str(s.get("keyframe_en") or ""),
            str(s.get("motion_zh") or ""),
            " ".join(str(t.get("text") or "") for t in (s.get("text_layer") or [])),
        ]))
        hits = _cmp.check_visual(blob)
        if hits:
            out.append(f"{s['shot_id']}({'/'.join(hits[:2])})")
    return out


def duration_audit(doc: dict[str, Any], segs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """时长核验 (0917 用户令): 音频时长 ↔ 规划时长 ↔ H3 生成窗 三方对账.

    场级: 场窗时长 (doc 轴, 音频锚定) vs 场内镜槽合计; 给 segs (音频包/句级,
    音频轴 0 起) 时再独立对账 场窗与音频段重叠合计。
    镜级: 音频槽 (t_end-t_start) vs H3 生成窗 (anim.duration_s) vs beats 铺满。
    返回 {"arcs": rows, "shots": rows, "problems": [...]}; problems 供 plan_warnings/报告。
    """
    tc = float(load().brand_card.opening_sec)
    shots = sorted(doc.get("shots") or [], key=lambda s: float(s.get("t_start") or 0))
    by_arc: dict[str, list[dict[str, Any]]] = {}
    for s in shots:
        by_arc.setdefault(str(s.get("arc_id")), []).append(s)
    problems: list[str] = []
    arc_rows: list[dict[str, Any]] = []
    for a in doc.get("arcs") or []:
        aid = str(a.get("arc_id"))
        ss = by_arc.get(aid) or []
        a0, a1 = float(a.get("t_start") or 0), float(a.get("t_end") or 0)
        audio = round(a1 - a0, 2)
        planned = round(sum(float(s["t_end"]) - float(s["t_start"]) for s in ss), 2)
        gen = round(sum(float((s.get("anim") or {}).get("duration_s") or 0) for s in ss), 2)
        row: dict[str, Any] = {"arc_id": aid,
                               "module": (a.get("module_id") + 1) if a.get("module_id") is not None else "",
                               "audio_s": audio, "planned_s": planned,
                               "h3_window_s": gen, "shots": len(ss)}
        if not ss:
            problems.append(f"[时长核验] {aid} 场无镜 (骨架未分镜?)")
        elif abs(planned - audio) > 0.5:
            problems.append(f"[时长核验] {aid} 音频槽 {audio:.1f}s ≠ 镜槽合计 {planned:.1f}s "
                            f"(差 {planned - audio:+.1f}s)")
        if segs:
            ov = 0.0
            for g in segs:
                s0, s1 = float(g.get("t_start") or 0), float(g.get("t_end") or 0)
                lo, hi = max(s0, a0 - tc), min(s1, a1 - tc)
                if hi > lo:
                    ov += hi - lo
            row["audio_seg_overlap_s"] = round(ov, 2)
            if abs(ov - audio) > 0.6:
                problems.append(f"[时长核验] {aid} 场窗 {audio:.1f}s 与音频段重叠 {ov:.1f}s 不符 (时间轴脱锚)")
        arc_rows.append(row)
    shot_rows: list[dict[str, Any]] = []
    import subprocess as _sp
    from pathlib import Path as _P
    _ep_dir = shots_mod.ep_dir(str(doc.get("book_title")), int(doc.get("ep") or 1))
    for s in shots:
        slot = round(float(s["t_end"]) - float(s["t_start"]), 2)
        anim = s.get("anim") or {}
        dur = round(float(anim.get("duration_s") or 0), 2)
        # 0918 核验盲区补: 实测视频文件时长 (声明值对/文件旧 = 漏网, 5镜实锤)
        _vf = s.get("video_file")
        if _vf and "anim/" in str(_vf) and (_ep_dir / str(_vf)).exists():
            try:
                _o = _sp.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(_ep_dir / str(_vf))],
                             capture_output=True, text=True, timeout=10).stdout.strip()
                _real = round(float(_o), 2) if _o else -1.0
            except Exception:  # noqa: BLE001
                _real = -1.0
            if _real > 0 and abs(_real - slot) > 1.0:
                problems.append(f"[时长核验] {s['shot_id']} 视频实测 {_real:.1f}s ≠ 槽 {slot:.1f}s "
                                f"(旧文件/错版, 需按槽重roll)")
                shot_rows.append({"shot_id": s["shot_id"], "slot_s": slot, "h3_s": dur,
                                  "beats_end_s": 0.0, "video_real_s": _real})
                continue
        bend = round(max((float(b.get("t_end") or 0) for b in (anim.get("beats") or [])), default=0.0), 2)
        shot_rows.append({"shot_id": s["shot_id"], "slot_s": slot, "h3_s": dur, "beats_end_s": bend})
        if abs(dur - slot) > 0.5:
            kind = "H3窗短→草稿定格补差" if dur < slot else "H3窗长→截断"
            problems.append(f"[时长核验] {s['shot_id']} 音频槽 {slot:.1f}s ≠ H3窗 {dur:.1f}s ({kind})")
        if dur > 0 and bend < dur - 0.5:
            problems.append(f"[时长核验] {s['shot_id']} beats 只铺到 {bend:.1f}s < H3窗 {dur:.1f}s")
    return {"arcs": arc_rows, "shots": shot_rows, "problems": problems}


def write_duration_sheet(doc: dict[str, Any], audit: dict[str, Any]) -> Path:
    """时长核验表落盘 (ep 目录 时长核验.md) — 人读对账表, 任何时刻可复查."""
    ep_dir = shots_mod.ep_dir(str(doc.get("book_title")), int(doc.get("ep") or 1))
    lines = ["# 时长核验 — 音频时长 ↔ 规划镜槽 ↔ H3 生成窗", "",
             "## 场级", "| 场 | 模块 | 音频槽s | 镜槽合计s | H3窗合计s | 镜数 |",
             "|---|---|---|---|---|---|"]
    for r in audit.get("arcs") or []:
        lines.append(f"| {r['arc_id']} | {r.get('module', '')} | {r['audio_s']} | "
                     f"{r['planned_s']} | {r['h3_window_s']} | {r['shots']} |")
    mismatch = [r for r in audit.get("shots") or [] if abs(r["h3_s"] - r["slot_s"]) > 0.5]
    lines += ["", "## 镜级 (仅列 音频槽≠H3窗 >0.5s 的镜)", "",
              "| 镜 | 音频槽s | H3窗s |", "|---|---|---|"]
    for r in mismatch:
        lines.append(f"| {r['shot_id']} | {r['slot_s']} | {r['h3_s']} |")
    if not mismatch:
        lines.append("(全镜 H3窗=音频槽 ✓)")
    lines += ["", "## 问题清单", ""]
    lines += [f"- {p}" for p in (audit.get("problems") or [])] or ["- 无 ✓"]
    path = ep_dir / "时长核验.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
