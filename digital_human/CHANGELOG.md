# 数字人项目 CHANGELOG

> 时间倒序记录"已完成里程碑 + 重大决策变更"。技术栈细节不在此，请看 [`项目状态总览.md`](项目状态总览.md)。

---

## 2026-07-26｜LTX23 音频→视频 接入数字人视频环节

### 改动
- **新能力：数字人说话视频**（音频 + 分镜图 → MP4）— 完全在 54321 Web 闭环
  - 工作流 SSOT：`workflows/digital_human_video_ltx23.json`（由 `manifest.yaml` 自动同步到 ComfyUI 运行时副本）
  - 后端：`app/routers/digital_human_video.py` 8 端点（`eligible-audio` / `videos` CRUD / `upload-storyboard` / `generate` / `download` / `delete`）
  - 服务层：
    - `app/services/audio_aggregator.py` — ffmpeg concat demuxer，≥5s 硬阈值，0.3s 静音填充 `||`
    - `app/services/lit_video_builder.py` — LTX23 workflow dict 构造（`LTXVAddGuide` ×N + `LTXVSamplerCustomAdvanced` + `LTXVAudioVAEEncode/Decode` + `VHS_VideoCombine`）
    - `app/services/video_validator.py` — ffprobe 7 项硬校验（video stream / audio stream / fps / `8n+1` frame count / duration match ±1s / duration ≥ min）
  - 数据模型：`app/models.py` 新增 `DigitalHumanVideo` 表（16 字段含 status / prompt_id / output_video_path / validation meta）
  - Pydantic：`app/schemas.py` 加 `DigitalHumanVideoCreate/Out` / `EligibleAudioItem/Response` / `GenerateVideoResponse` / `StoryboardUploadResponse`
  - 前端：`web/digital_human_video.html`（4 步 SPA：① 选音频 ≥ 5s → ② 上传分镜图 + 参数 → ③ 提交生成 + 状态轮询 → ④ 历史 + 下载）；`web/index.html` 顶部导航新增 "🎬 数字人视频"
- **同步路径**：`lifespan` 启动期同步；与已有 `character_three_view` workflow 共用 `manifest.yaml`
- **存档保护**：原始工作流在 `G:\下载\LTX23-...` 保持不动；运行时副本由 SSOT 双向同步保 护

### E2E 验收（2026-07-26 切片 6）
- `POST /api/dhv/videos` 创建任务 → `multipart/form-data upload-storyboard` 上传 2 张分镜 → `POST /api/dhv/videos/{id}/generate` 同步跑通
- 音频聚合：`032.wav (5.27s) + 031.wav (3.44s)` → `aggregated_duration_sec=8.71s`
- ComfyUI `/prompt` 返回 HTTP 400（workflow JSON 中 `loop_count` 等输入待补）→ 路由捕获异常，DB 落 `status=failed` + `error_message` 完整记录
- 删除 `DELETE /api/dhv/videos/{id}` 走 `send2trash` 思路清理产物目录（实测 HTTP 204）
- 路由 200：8 端点全部 `openapi.json` 已注册且 `eligible-audio` 实时返回 `total_duration_sec=16.38s`

### 决策
- ✅ **不**覆盖原始工作流 `G:\下载\LTX23-...`
- ✅ **不**把临时实验 payload 当 SSOT；`workflows/digital_human_video_ltx23.json` 是项目侧占位 + 注释
- ✅ **不**仅凭 ComfyUI HTTP 200 判定视频成功；必须 ffprobe 校验 audio stream / fps / frame count
- ✅ **不**因 SageAttention DLL 等单次失败阻塞主流程；WARN + 继续
- ✅ 音段聚合阈值 **≥ 5s**（用户原话："先作测试用，5 秒以上的音频"）
- ✅ 帧数公式 `round(duration * fps) + 1` 对齐 `8n+1`
- ✅ 与 IndexTTS2 入口并列：复用 `article → audio → 数字人视频` 自动接续链路
- ⏳ 前置节奏改造（每段 5-10s）留 backlog（本轮不展开）

---

## 2026-07-25｜ComfyUI 工作流 SSOT 入项目目录,54321 Web 自动同步

### 改动
- **角色管理接入 ComfyUI 多视图定型** — `web/roles.html` + `app/routers/{comfyui,roles}.py` + `app/services/workflow_sync.py` + `app/models.py` 新增 `Role` / `WorkflowSync` 表
- 工作流 SSOT：`workflows/character_three_view.json` + `workflows/manifest.yaml`
- 启动期同步：lifespan 钩子比对 sha256 → 覆盖 / 记录 `WorkflowSync` 表 + `E:\数字人计划\logs\workflow-sync-*.log`
- 角色 CRUD：参考图落 `E:\数字人计划\roles\<uuid>\ref.<ext>`；3 视图落 `E:\数字人计划\roles\<uuid>\{front,side,full}.<ext>`
- `apply` 端点只产 `mainstream_input` JSON，**不**接 A 管线分镜（留 ID-007 backlog）
- `web/index.html` 顶部导航新增 "🎭 角色管理" 入口

### 决策
- ✅ **不**绕开 54321 Web 直调 ComfyUI API
- ✅ **不**新增端口（仅 54321 + 复用 ComfyUI 8188）
- ✅ **不**同步到 `E:\AI\comfyui_workflows\`（已降级历史目录）
- ✅ ComfyUI 内部参数（checkpoint / LoRA / prompt 模板）对用户不可见

---

## 2026-07-25｜记忆与 SSOT 整理

### 决策
- **文档分层统一**：`项目状态总览.md` = 当前现实；`执行计划清单.md` = 规划 SSOT；`执行计划清单.html` = 可视化视图；`CHANGELOG.md` = 历史。
- **Workflow SSOT 锁定**：项目 `workflows/` 为唯一真源；ComfyUI `user/default/workflows/` 为运行时副本，后续由 Claude Code 实现可观测同步。
- README 移除已过期的 M0 “1 分钟 3 条 30 秒”当前门禁表述。
- 清理动作不再描述为“待权限授权”，而描述为待用户做保留/归档/删除的内容决策。

---

## 2026-07-25｜文档整合与决策固化

### 决策（用户拍板）
- **MuseTalk 完全废**：技术栈移除；`E:\tools\MuseTalk-main\` + 隔离 venv + wrapper 后续清理
- **M0 门禁过期**：原"1 分钟 3 条 30 秒"硬门禁作废；M0 已跑通，后续只关心精进
- **38m 项目归档**：作为 M0 实验田已完成，不维护；`C:\Users\tanha\Desktop\38m\` 回头可清
- **多维度定型图定位**：M0+ 全阶段的**角色资产层**，不是独立阶段
- **v10 不改**：作为规划目标保留，通过新"项目状态总览"反映真实差异

### 新增文档
- [`项目状态总览.md`](项目状态总览.md)：反映真实技术栈、真实进度、整合决策、待决项、清理待办
- `CHANGELOG.md`（本文件）：里程碑 + 决策时间线

### 文档结构变化
- `README.md` 项目入口表新增 2 行：本文件 + CHANGELOG（其他内容不动）
- v10 / 调研 / SOP / 跑通记录 / pose 规律 等已沉淀文档**全部未改**

---

## 2026-07-24｜Pose 库分类沉淀

- 1700+ 张预览测试（Flux2 Klein 9B + 参考图方案）
- **高风险姿势**（不稳定，少用）：
  - 横版贴墙姿势（climbing 系，双人重影 / 穿模）
  - 近距离特写（被识别成脸部特写）
  - rest 系列静止待机（全类别穿模）
- **稳姿**（推荐）：
  - 标准全身直立、站立插兜/抱臂、行走/奔跑
- **性别差异**：女性赤脚失败率 > 男性穿鞋
- 沉淀文档：[`pose问题规律.md`](pose问题规律.md)

---

## 2026-07-23｜多维度定型图方案定型（V4）

- **问题**：V1-V3 在领口/头饰/服装细节上仍出现版本不一致
- **解法（V4，纯 prompt 方案）**：
  1. 角色名 identity anchor（如 `character named Xiao Fengxian`）
  2. 固定 CHARACTER CORE（脸、眼、发型、发簪、发饰，两张图一字不差）
  3. 结构化视角词：正脸特写 `front view eye-level shot close-up` / 全身 `front view eye-level shot wide shot`
  4. 针对身份漂移的 negative（`different face, changed face, altered face, different hairstyle, ...`）
  5. `<sks>` 触发词 + 一致性 LoRA + 固定 Seed
- **结果**：古装女侠 V4 完全通过；男性宗师 V1/V2/V3 三套全通过（扫地僧 / 江湖老剑客 / 隐世老人）
- 沉淀文档：[`数字人多维度定型图生成器跑通记录.md`](数字人多维度定型图生成器跑通记录.md)
- **同步验证规则**：使用 `wearing a simple black strapless swimsuit to ensure bare neck and shoulders` 做无领口强约束（替换为 `white sleeveless undergarment` 后模型又生成领口）

---

## 2026-07-23｜男性宗师角色生成（38m 实验田）

- 目标：为《一代宗师》38 秒台词视频生成老年男性宗师（扫地僧气质）
- 三套候选：V1 扫地僧 / V2 江湖老剑客 / V3 隐世老人，全部通过用户验收
- 沉淀：**正脸特写无领口技巧**（swimsuit 强约束）+ **CHARACTER CORE 复用**
- 产物位置：`C:\Users\tanha\Desktop\38m\master_v{1,2,3}_face_v2_00001_.png`（38m 内，但方法回流到 digital_human 跑通记录）

---

## 2026-07-22｜v10 执行计划发布（规划目标）

- 12 个月路线图 / 8 阶段（M0-M7）/ M12 月收入硬截止
- TTS 栈换为 Fish Speech + F5-TTS + ElevenLabs（替换 Edge TTS）
- ComfyUI 作为唯一主链（替换 MuseTalk / LivePortrait / LatentSync 主链）
- 国内平台优先（抖音 / 视频号 P0；YouTube 降级为素材复用池）
- 删除资金 / 借款 / 朋友豁免条款；只留"月收入"作为 M12 硬截止
- 决策记录：见 `执行计划清单.md` v10 §十
- **注**：v10 发布时 M0 尚未跑通，发布后陆续被现实覆盖（详见 2026-07-25 整合决策）

---

## 2026-07-22｜基础设施就位

- **GPU 自检 A 级**（4090 eGPU 49GB + 4060 8GB）：详见 [`M0-W1-D1-GPU自检报告.md`](M0-W1-D1-GPU自检报告.md)
- **ComfyUI 便携版 v0.28.0**：装在 `E:\AI\ComfyUI_windows_portable\`
- **TTS 本地部署**：
  - Fish Speech（s2-pro 4B，中文主力）— 8.6s 中文 wav 44.1kHz 冒烟过
  - F5-TTS（v1 Base，轻量备选）— 6.8s 中文 wav 24kHz 冒烟过
  - ElevenLabs（API）— 待用户注册 key
- **踩坑记录**（详见 `TTS栈部署记录.md`）：
  - torch 必须钉 2.5.1+cu121（避免 PyPI CPU 版覆盖）
  - huggingface-hub < 1.0 + tokenizers 0.15.2 互锁
  - uv.lock override protobuf <6 + tensorboard==2.19.0 配合
  - F5 vocoder 手工下载 + HF_HUB_OFFLINE=1
- **ComfyUI 出图全局约定**：见 [`sop/ComfyUI出图规范.md`](sop/ComfyUI出图规范.md)

---

## 2026-07-21｜M0 跑通（MuseTalk 方案，**已废**，仅历史）

- 端到端 demo：`demo_yongen_eng_v15.mp4`（60s 中文脸 + 英文音频，跨语种）+ `demo_yongen_yongen_v15.mp4`（8s 中文）
- 工具：MuseTalk v1.5 + Edge TTS `zh-CN-YunyangNeural`
- 沉淀：见 `E:\数字人计划\m0-day1\W1-MuseTalk跑通.md` + `W1总结.md`
- **踩坑 5 个**：Hermes PYTHONPATH 污染 / numpy ABI 死循环 / tokenizers 互锁 / torch CPU 默认 / mmcv 2.0.1 编译失败（最后一条未修，被 MuseTalk 跑通过程绕过）
- **当前定位**：**已被 v10 + 2026-07-25 决策替代**，不入生产工作流；产物可作历史归档

---

## 2026-07-20 及更早｜项目启动

- 数字人短视频项目立项
- v1-v9 计划迭代（v9.1 → v10 是当前规划基线）
- 早期调研：MuseTalk / LivePortrait / LatentSync / CosyVoice / GPT-SoVITS 等候选工具
- 沉淀：`数字人计划调研更新版.md`（已对齐 v10）

---

## 维护规则

- 每次"完成里程碑"或"重大决策变更"追加一条，**时间倒序**
- 每条包含：日期、做了什么、沉淀在哪个文件
- 技术栈细节不放这里（看"项目状态总览.md"）
- 不修改历史条目（错了加 erratum 条目，不动原文）