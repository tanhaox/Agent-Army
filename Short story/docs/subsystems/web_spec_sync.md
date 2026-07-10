# web-spec-sync.md — Web spec 同步层子系统

> **决策依据**：P5'（35 题压力测试锁定）
> **重要性**：🟡 **重要**（CLI 必须按 web 字段设计，未来 web 实现时无缝对接）
> **状态**：📋 设计阶段（Phase 1.MVP 不实现 Web，但 CLI 设计必须遵守）
> **关联**：MVP_AUTHORITY.md §五 / web/ 目录

---

## 🎯 系统职责

Web 21 个页面**已经以 mockup 形式存在**于 `web/` 目录。这些 mockup 不是"未来的产品"，而是**当前 MVP 的规格说明书（spec）**。

CLI 阶段的 6 个核心命令必须输出与 Web 设计稿**字段、表单、按钮**完全对齐的产物。

### 本质

把 21 个 mockup **当作 spec**，而不是当作"以后再做的东西"。

> 用户原话："能与 web 设计稿一致的，尽量一致！否则 web 稿不就没意义了吗"

---

## 📂 当前 Web 设计稿全景（21 个页面）

### 入口页（2 个）

| 页面 | 路径 | 字段 |
|------|------|------|
| 书库首页 | `index.html` | 所有书的列表 + 创建新书按钮 |
| 单本书总览 | `dashboard.html` | 设定完成度 + 进度 + 当前警告 |

### Step 1 设定页（7 个）

| 页面 | 路径 | 对应设定文件 |
|------|------|------------|
| 设置流程入口 | `setup.html` | 引导进入 Step 1 |
| 02 人物设定 | `setup-02-characters.html` | `02-characters.md` |
| 03 框架设定 | `setup-03-framework.html` | `03-framework.md` |
| 04 基调设定 | `setup-04-tone.html` | `04-tone.md` |
| 05 伏笔设定 | `setup-05-foreshadow.html` | `05-foreshadow.md` |
| 06 受众设定 | `setup-06-audience.html` | `06-audience.md` |
| 角色卡 - 主角 | `character-profile-protagonist.html` | `voice-prints/protagonist.md` |

### 角色卡（4 个）

| 页面 | 路径 |
|------|------|
| 盟友 1 | `character-profile-ally1.html` |
| 对手 1 | `character-profile-rival1.html` |
| 中立 1 | `character-profile-neutral1.html` |
| 特定角色（许七安） | `character-profile-xu-qi-an.html` |

### 角色辅助页（3 个）

| 页面 | 路径 |
|------|------|
| 角色列表 | `characters.html` |
| 角色声纹 | `character-voice.html` |
| 角色弧光 | `character-arc.html` |

### Step 2 规划页（3 个）

| 页面 | 路径 | 对应 |
|------|------|------|
| 章节规划 | `plan.html` | `chapters/chapter-XXX.md` 的规划 |
| 时间线 | `timeline.html` | `timeline.md` |
| 章节写作 | `write.html` | 当前章节编辑 |

### Step 3 写作页（1 个）

| 页面 | 路径 |
|------|------|
| 单章写入（实为 Step 3 主体）| `write.html` |

### Step 4 审核页（3 个）

| 页面 | 路径 |
|------|------|
| 伏笔追踪 | `foreshadow.html` |
| 跨章审核 | `audit.html` |
| 弧光追踪 | `character-arc.html` |

### 工具页（2 个）

| 页面 | 路径 |
|------|------|
| AI 助手 | `ai-assistants.html` |
| 聊天填卡 | `chat-fill.html` |
| TXT 导入 | `import-txt.html` |
| 上传小说 | `upload-novel.html` |
| 测试报告 | `test-reports.html` |

---

## 📋 CLI 与 Web 的契约

### 契约定义

每个 CLI 命令输出对应一个 Web 页面。CLI 的输出格式 = Web 的数据模型。

**例**：`character-profile-protagonist.html` 对应 CLI 命令 `python -m ai_coauthor character_card --name 主角 --book <book_name>`。

CLI 的输出 JSON 必须包含 Web 页面所有字段名（含 ID、表单字段名、显示字段）。

### 数据契约示例

```yaml
# contract: character-profile
{
  "character": {
    "name": "沈铁衣",
    "alias": ["铁衣", "沈家少主"],
    "role": "主角",
    "age": 18,
    "gender": "男",
    "background": "出身名门，幼年家道中落",
    "personality": "表面冷峻内心温柔",
    "motivation": "为家族复仇",
    "voice_features": [
      "语速慢",
      "用词古雅",
      "口头禅：'看清楚了'"
    ],
    "arc": {
      "current_stage": "觉醒期",
      "chapter_start": 1,
      "stages": [...]
    }
  }
}
```

CLI 命令必须输出符合这个 schema 的数据。

### CLI 命令 → Web 页面映射表

| CLI 命令 | 对应 Web 页面 | 数据契约文件 |
|---------|--------------|-------------|
| `setup_consult` | setup.html + setup-02~06 | `contracts/setup.yaml` |
| `character_card` | character-profile-XXX | `contracts/character.yaml` |
| `plan_chapter` | plan.html + timeline.html | `contracts/plan.yaml` |
| `write` | write.html | `contracts/chapter.yaml` |
| `foreshadow_track` | foreshadow.html | `contracts/foreshadow.yaml` |
| `audit` | audit.html + character-arc.html | `contracts/audit.yaml` |
| `kickoff_meeting` | dashboard.html | `contracts/kickoff.yaml` |

---

## 🔧 MVP 阶段 CLI 设计约束

### CLI 输出格式必须包含 Web 所需的字段

即使 Phase 1.MVP 不实现 Web，CLI 输出也要**预留** Web 字段：

```python
# MVP 时期 consistency_check 的输出
{
    "command": "consistency_check",
    "issues": [...],
    "web_spec": {
        "ui_panel": "write.html",
        "fields_shown": ["current_para", "settings_summary", "issues"],
        "buttons": ["ignore", "fix", "view_settings"],
    }
}
```

### CLI 命令的 exit code 必须与 Web 操作对应

| exit code | 含义 | Web 操作 |
|-----------|------|---------|
| 0 | 通过 | 隐藏警告 |
| 1 | 警告（可继续） | 显示黄色横幅 |
| 2 | 错误（必须处理） | 显示红色对话框 |
| 3 | 配置错误 | 报错页 |

---

## 📐 Web 设计稿的反向约束

CLI 设计时必须**遵守 Web 设计稿**：

1. **字段名**：CLI 输出字段名 = HTML input name 属性
2. **表单分组**：CLI 输出字段必须能与 Web 的 `<form>` 对应
3. **按钮触发**：CLI 命令参数 = Web 按钮的 onclick
4. **数据校验**：Web 端校验规则必须与 CLI 校验规则一致

### 例外

Web 设计稿本身有缺陷（如错误的状态、字段冲突）→ 必须**修订** Web 设计稿，不修改 CLI 适配 Web。

修订流程：

1. Web 设计稿错误 → 写入 `docs/web-revisions/` 目录
2. CLI 同步更新 → 写入 schema 变更
3. 与 `DECISION_REVISION.md` 流程保持一致

---

## 🎨 Phase 1.MVP 简化策略

虽然 Web 是 spec，但 MVP 阶段**不需要真去实现 Web**。MVP 阶段仅需：

1. **维护 21 个 Web 页面的字段清单**（已存在）
2. **CLI 输出符合字段清单**
3. **数据契约文件 (contracts/*.yaml) 编写完成**

Web 实际实现可以推迟到 Phase 4，但**接口不能变**。

---

## 🧪 测试用例

1. **CLI 字段一致性**：CLI 输出 JSON 字段 = Web 页面所有输入字段
2. **数据契约加载**：每个 CLI 命令能加载对应 contract.yaml
3. **Web 设计稿变更检测**：CI 检测 Web HTML 字段变化 → 提示 contract 同步

---

## 🔗 关联

- `MVP_AUTHORITY.md` §五 —— CLI 命令与 Web 页面映射
- `/web/` 目录 —— 当前 mockup（21 个 HTML）
- `docs/decisions/002-...`（旧）→ 已重写（详见决策文档）
- `routes.md`（待编写） —— Phase 2+ 实现

---

## 📌 元信息

- **创建者**：Claude（grill-me skill 驱动后）
- **重要性**：🟡 重要
- **关联决策**：P5'（反转 v1 的 mockup 降级）/ Q24
- **创建日期**：2026-07-10
