# 记忆保存功能使用指南

**更新日期**: 2026-02-10
**版本**: 1.0

---

## 📖 功能概述

记忆保存功能允许您在会话结束时保存当前的关键信息到 `MEMORY.md`，确保下次会话能够恢复上下文。

**核心优势**：
- ✅ 自动捕获项目状态
- ✅ 格式化保存为 Markdown
- ✅ 可选同步更新 1.md
- ✅ 支持手动或自动模式

---

## 🎯 使用方式

### 方式 1：触发口令（推荐）

当您希望保存当前会话时，只需说出：

> **"保存记忆"** 或 **"生成记忆"**

Claude 会自动执行记忆保存流程。

### 方式 2：手动命令

如果您希望手动控制保存的内容：

```bash
# 自动模式 - 快速保存当前状态
python shared/scripts/save_memory.py --auto

# 手动模式 - 详细记录会话
python shared/scripts/save_memory.py --title "会话标题" --desc "会话描述"
```

---

## 📋 参数说明

### 基础参数

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--title` | `-t` | 会话标题（必需） | `--title "新功能开发"` |
| `--description` | `-d` | 会话描述 | `--desc "完成用户认证功能"` |
| `--status` | `-s` | 当前状态 | `--status "[OK] 已完成"` |

### 详细记录参数

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--changes` | `-c` | 关键变更列表 | `--changes "修复 bug A" "优化性能"` |
| `--files-modified` | `-m` | 修改的文件 | `--m "app.py" "config.json"` |
| `--files-created` | `-f` | 创建的文件 | `--f "new_feature.py"` |
| `--bugs` | `-b` | 修复的问题 | `--b "事件循环问题"` |
| `--features` | - | 新增功能 | `--features "自定义验证" "响应返回"` |
| `--next` | `-n` | 下一步计划 | `--next "编写测试" "更新文档"` |

### 控制参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--auto` | `-a` | 自动生成当前状态摘要 |
| `--update-preload` | `-u` | 同时更新 1.md 文件 |

---

## 💡 使用场景

### 场景 1：完成功能开发后

```bash
python shared/scripts/save_memory.py \
  --title "服务管理技能 v1.1.0" \
  --desc "完成自定义验证和响应数据返回功能" \
  --features "自定义验证函数" "返回完整响应数据" \
  --files-modified "service_manager_skill.py" \
  --status "[OK] 已完成，可用于生产"
```

### 场景 2：修复 Bug 后

```bash
python shared/scripts/save_memory.py \
  --title "AutoGen 事件循环问题修复" \
  --desc "修复 Flask 多次请求时的 Event loop 错误" \
  --bugs "Event loop is closed 错误" \
  --files-modified "src/zhipu_client.py" \
  --status "[OK] 已完全修复"
```

### 场景 3：快速保存当前状态

```bash
# 最简单的方式
python shared/scripts/save_memory.py --auto
```

---

## 📝 生成的记录格式

保存的记忆会自动格式化为 Markdown，包含以下部分：

```markdown
## 会话标题（2026-02-10）

**描述**: 会话描述

### 关键变更

- 变更 1
- 变更 2

### 修改的文件

- `file1.py`
- `file2.py`

### 新增功能

- 功能 1
- 功能 2

### 状态

当前状态描述

### 下一步

- 计划 1
- 计划 2
```

---

## 🔧 Python API

如果您需要在代码中调用：

```python
from shared.scripts.save_memory import MemorySaver

saver = MemorySaver()

# 准备会话信息
session_info = {
    "title": "会话标题",
    "description": "会话描述",
    "key_changes": ["变更 1", "变更 2"],
    "files_modified": ["file1.py"],
    "bugs_fixed": ["Bug 描述"],
    "new_features": ["新功能"],
    "status": "[OK] 已完成",
    "next_steps": ["下一步计划"]
}

# 保存记忆
result = saver.save_memory(session_info, update_preload=True)

# 检查结果
if result["success"]:
    print("记忆保存成功！")
```

---

## 📂 文件位置

| 文件 | 位置 |
|------|------|
| **脚本** | `shared/scripts/save_memory.py` |
| **快捷方式** | `shared/scripts/save_memory.bat` |
| **记忆文件** | `C:\Users\<用户>\.claude\projects\c--AI-Agent-Local\memory\MEMORY.md` |
| **使用指南** | `shared/scripts/MEMORY_SAVE_GUIDE.md` |

---

## ✅ 最佳实践

### 1. 何时保存记忆

**建议保存的时机**：
- ✅ 完成一个功能开发后
- ✅ 修复重要 Bug 后
- ✅ 进行重大重构后
- ✅ 项目里程碑达成时
- ✅ 会话结束前

### 2. 记录内容建议

**应包含的信息**：
- 标题（简洁明了）
- 描述（做了什么）
- 关键变更（改动点）
- 修改的文件（便于追溯）
- 修复的问题（知识积累）
- 新增功能（功能清单）
- 当前状态（完成度）
- 下一步（后续计划）

### 3. 标题命名规范

**推荐格式**：
- `功能名 版本号` - 如："服务管理技能 v1.1.0"
- `问题描述 + 修复` - 如："AutoGen 事件循环问题修复"
- `日期 + 摘要` - 如："2026-02-10 记忆保存功能完成"

---

## 🎉 示例输出

```
======================================================================
记忆保存
======================================================================

标题: 记忆保存功能完成
记忆文件: [OK] 已更新
1.md 文件: 未变更
```

---

## 📚 相关文档

- [1.md - 系统预加载指引](../../1.md) - 包含记忆保存功能说明
- [MEMORY.md - 项目记忆](../../MEMORY.md) - 所有历史记录
- [CLAUDE.md - 项目配置](../../CLAUDE.md) - 项目核心配置

---

**注意**: 记忆保存是保持项目连续性的重要机制，建议定期保存关键会话信息。
