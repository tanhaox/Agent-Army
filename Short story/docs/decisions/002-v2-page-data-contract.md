# 002-v2-page-data-contract.md — 21 页面 → 数据契约（v2）

> **历史**：原 `002-page-logic-organization.md`
> **反转依据**：P5'（Web 不再降级为 mockup，而是 spec）
> **v2 依据**：P5' + Q23 + Q24
> **状态**：✅ 当前活跃决策

---

## 🎯 设计目标

把 21 个 Web HTML 页面**从 mockup 升级为 spec**：

- Web 字段 = 数据契约
- CLI 命令输出 = 按数据契约生成
- Phase 4 实现 Web 时直接复用

---

## 📋 21 页面分组（继承 v1）

### 入口页（2 个）

| 页面 | 路径 | 数据契约文件名 |
|------|------|---------------|
| 书库首页 | `index.html` | `contracts/library.yaml` |
| 单本书总览 | `dashboard.html` | `contracts/dashboard.yaml` |

### Step 1 设定页（7 个）

| 页面 | 路径 | 数据契约 |
|------|------|---------|
| 设置入口 | `setup.html` | `contracts/setup.yaml` |
| 02 人物 | `setup-02-characters.html` | `contracts/setup-characters.yaml` |
| 03 框架 | `setup-03-framework.html` | `contracts/setup-framework.yaml` |
| 04 基调 | `setup-04-tone.html` | `contracts/setup-tone.yaml` |
| 05 伏笔 | `setup-05-foreshadow.html` | `contracts/setup-foreshadow.yaml` |
| 06 受众 | `setup-06-audience.html` | `contracts/setup-audience.yaml` |
| 主角卡 | `character-profile-protagonist.html` | `contracts/character-profile.yaml` |

### 角色卡（4 个）

| 页面 | 路径 |
|------|------|
| 盟友 1 | `character-profile-ally1.html` |
| 对手 1 | `character-profile-rival1.html` |
| 中立 1 | `character-profile-neutral1.html` |
| 特定角色 | `character-profile-xu-qi-an.html` |

### 角色辅助页（3 个）

| 页面 | 路径 | 数据契约 |
|------|------|---------|
| 角色列表 | `characters.html` | `contracts/character-list.yaml` |
| 角色声纹 | `character-voice.html` | `contracts/character-voice.yaml` |
| 角色弧光 | `character-arc.html` | `contracts/character-arc.yaml` |

### Step 2 规划页（2 个）

| 页面 | 路径 | 数据契约 |
|------|------|---------|
| 章节规划 | `plan.html` | `contracts/plan.yaml` |
| 时间线 | `timeline.html` | `contracts/timeline.yaml` |

### Step 3 写作页（1 个）

| 页面 | 路径 | 数据契约 |
|------|------|---------|
| 单章写作 | `write.html` | `contracts/chapter.yaml` |

### Step 4 审核页（3 个）

| 页面 | 路径 | 数据契约 |
|------|------|---------|
| 伏笔追踪 | `foreshadow.html` | `contracts/foreshadow-display.yaml` |
| 跨章审核 | `audit.html` | `contracts/audit.yaml` |
| 弧光追踪 | `character-arc.html` | `contracts/character-arc.yaml` |

### 工具页（5 个）

| 页面 | 路径 | 数据契约 |
|------|------|---------|
| AI 助手 | `ai-assistants.html` | `contracts/ai-assistants.yaml` |
| 聊天填卡 | `chat-fill.html` | `contracts/chat-fill.yaml` |
| TXT 导入 | `import-txt.html` | `contracts/import-txt.yaml` |
| 上传小说 | `upload-novel.html` | `contracts/upload-novel.yaml` |
| 测试报告 | `test-reports.html` | `contracts/test-reports.yaml` |

---

## 🔑 数据契约（核心要求）

每个数据契约文件**必须**包含以下字段：

```yaml
# 模板: contracts/<page>.yaml
page_id: write       # 唯一 ID
title: 单章写作       # 显示标题
fields:                # HTML 中所有显示字段
  - name: current_paragraph
    type: textarea
    required: true
    binding: chapter.content  # 绑定到 markdown 哪个字段
  - name: settings_summary
    type: panel
    readonly: true
    binding: settings.summary
buttons:                # 触发命令
  - name: save
    command: python -m ai_coauthor write --save
  - name: ignore_warning
    command: python -m ai_coauthor ignore
ai_panels:              # AI 命令输出的展示
  - command: consistency_check
    trigger: on_save
  - command: foresight_track
    trigger: on_chapter_end
```

---

## 🔄 CLI 与 Web 的同步约束

### 约束 1：CLI 输出字段 ⊇ Web 字段

CLI 命令输出的 JSON 字段必须**包含** Web 页面所有 input 字段。

### 约束 2：CLI 命令名 ⊆ Web 按钮

Web 页面所有按钮必须有对应的 CLI 命令。

### 约束 3：AI 触发器一致

Web 端 AI 自动触发的场景 = CLI 自动触发的场景。

### 约束 4：数据校验规则相同

Web 端表单校验 = CLI 端 schema 校验。

---

## 🛠️ MVP 阶段要求

### 必做

1. **21 个数据契约文件**全部创建（`contracts/` 目录）
2. **CLI 命令**输出符合对应契约
3. **CI 检测**：任何 Web HTML 字段变化 → 提示 contract 同步

### 不做（MVP 之外）

- ❌ Web 实际渲染逻辑（Phase 4）
- ❌ React/Vue 等前端实现（Phase 4）
- ❌ 实时保存 / 多人协作（Phase 4+）

---

## 📊 CLI 命令 → Web 页面映射表（核心）

| CLI 命令 | 对应 Web 页面 | 数据契约 |
|---------|--------------|---------|
| `setup_consult` | setup.html + setup-02~06 | setup.yaml |
| `character_card` | character-profile-XXX | character-profile.yaml |
| `plan_chapter` | plan.html | plan.yaml |
| `write` | write.html | chapter.yaml |
| `foreshadow_track` | foreshadow.html | foreshadow-display.yaml |
| `audit` | audit.html | audit.yaml |
| `kickoff_meeting` | dashboard.html | kickoff.yaml |

---

## 🧪 测试用例

1. **CLI 字段一致性**：CLI 输出 JSON 字段 = HTML input 字段
2. **数据契约加载**：每个 CLI 命令能加载对应 contract.yaml
3. **Web 字段变更检测**：CI 检测 HTML 字段变化 → 提示 contract 同步
4. **按钮命令可达**：所有 Web 按钮的命令都必须实现

---

## 🔗 关联

- `docs/subsystems/web_spec_sync.md` —— Web spec 同步层
- `docs/MVP_AUTHORITY.md` §五 —— CLI 与 Web 映射
- `/web/*.html` —— 当前 mockup（21 个）

---

## 📌 元信息

- **历史决策**：[002-page-logic-organization.md](./002-page-logic-organization.md)
- **反转触发**：Q23 + Q24（用户多次强调 Web 不能白设计）
- **创建日期（原版）**：2026-07-08
- **v2 创建日期**：2026-07-10
- **重要性**：🟡 重要（Phase 1 不实现 Web，但数据契约必出）
