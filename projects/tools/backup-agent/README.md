# Backup Agent - 自动备份系统

> 🤖 全自动备份系统，保护您的代码安全

[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

---

## 📖 简介

**Backup Agent** 是一个全自动的代码备份系统，专为 AI-Agent-Local 项目设计。

### 核心功能

- ✅ **实时监控**：监控改进意见文档创建，立即触发备份
- ✅ **定时备份**：每小时整点自动备份
- ✅ **AI 主动备份**：AI 检测到关键词时自动触发备份（bug、修复、优化等）
- ✅ **简单回滚**：支持按时间/关键词/ID 回滚到任意备份点
- ✅ **全自动运行**：无需用户干预，全程无感知
- ✅ **友好提示**：控制台输出"老板，我在备份..."等友好提示
- ✅ **日志记录**：完整的操作日志，方便追踪

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd projects/tools/backup-agent
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python backup_agent.py --daemon
```

启动后会看到：

```
============================================================
 🤖 Backup Agent 后台服务启动
============================================================

✅ Backup Agent 已启动！
📁 监控路径: C:\AI-Agent-Local
📝 监控目录: docs/improvements/
🕐 整点备份: 每小时
📄 日志文件: logs\backup-agent.log

💡 提示：按 Ctrl+C 停止服务
============================================================
```

### 3. 查看备份清单

```bash
python backup_agent.py --list
```

### 4. 回滚到指定备份

```bash
# 按 ID 回滚
python backup_agent.py --rollback 1

# 按时间回滚
python backup_agent.py --rollback "2026-02-26 14:35"

# 按关键词回滚
python backup_agent.py --rollback "bug讨论前"
```

---

## 📚 详细使用说明

### 启动选项

#### 启动后台服务

```bash
python backup_agent.py --daemon
```

启动后，Backup Agent 会：
- 📝 监控 `docs/improvements/` 目录
- 🕐 每小时整点执行备份
- 💾 检测到新改进意见文档时立即备份

#### 查看备份清单

```bash
# 查看最近 12 小时的备份
python backup_agent.py --list

# 查看最近 24 小时的备份
python backup_agent.py --list --hours 24
```

输出示例：

```
══════════════════════════════════════════════════════════════════════
 📋 最近 12 小时备份清单
══════════════════════════════════════════════════════════════════════
 ID   时间                 Hash     消息
──────────────────────────────────────────────────────────────────────
 1    2026-02-26 14:35    a1b2c3d  💾 [关键词触发] 在检测到'bug'讨论前
 2    2026-02-26 14:42    d4e5f6g  💾 [关键词触发] 在检测到'方案'讨论前
 3    2026-02-26 15:00    h7i8j9k  💾 [整点备份] 定时备份
══════════════════════════════════════════════════════════════════════
💡 提示：使用 --rollback [ID|时间|关键词] 回滚到指定备份
```

#### 查看当前状态

```bash
python backup_agent.py --status
```

输出示例：

```
══════════════════════════════════════════════════════════════════════
 📊 Backup Agent 状态
══════════════════════════════════════════════════════════════════════
 📁 监控路径: C:\AI-Agent-Local
 🌿 当前分支: main
 📝 是否有修改: 是
 📄 未跟踪文件: 3 个
 💾 最新提交: 💾 [整点备份] 定时备份 - 2026-02-26 15:00
══════════════════════════════════════════════════════════════════════
```

#### 回滚操作

```bash
# 按 ID 回滚（最简单）
python backup_agent.py --rollback 1

# 按时间回滚
python backup_agent.py --rollback "2026-02-26 14:35"

# 按关键词回滚
python backup_agent.py --rollback "bug讨论前"
```

回滚前会要求确认：

```
🔄 正在回滚到: 1
⚠️ 回滚会覆盖当前代码，是否继续？(yes/no): yes
🛡️ 回滚前安全备份: 💾 [关键词触发] 在检测到'回滚前安全备份'讨论前 - 2026-02-26 15:10
✅ 回滚完成！
💡 提示：如需恢复，可以使用 --rollback "回滚前安全备份"
```

#### 查看回滚帮助

```bash
python backup_agent.py --rollback-help
```

#### AI 主动备份

AI 可以在检测到关键词时自动触发备份：

**触发关键词**：
- 修复相关：`修复`、`bug`、`漏洞`、`错误`、`问题`
- 改进相关：`优化`、`改进`、`提升`、`增强`
- 开发相关：`添加`、`实现`、`开发`、`重构`
- 配置相关：`配置`、`调整`、`更新`、`部署`

**工作流程**：
```
您: "帮我修复订单匹配的bug"
   ↓
AI 检测到关键词: "bug"
   ↓
AI: "好的老板！检测到关键词'bug'，我先为您备份一下代码..."
   ↓
[执行备份 - 2-3秒]
   ↓
AI: "✅ 备份完成！Commit: 291e985
     现在开始修复订单匹配的bug..."
   ↓
[执行任务]
```

**详细文档**: [AI主动备份工作流程.md](AI主动备份工作流程.md)

---

## 🛠️ 配置说明

配置文件位于 `config.json`：

```json
{
  "monitor_path": "C:\\AI-Agent-Local",
  "backup_intervals": {
    "hourly": true
  },
  "keywords": [
    "方案", "bug", "漏洞", "升级", "修复",
    "添加功能", "改进", "开发", "实现",
    "重构", "优化", "部署", "更新"
  ],
  "commit_message_template": "💾 [{type}] 在检测到'{keyword}'讨论前 - {date}",
  "notification": {
    "backup_start": "老板，我在备份...",
    "backup_complete": "老板，我备份好了"
  },
  "rollback": {
    "list_hours": 12
  },
  "git": {
    "auto_init": true,
    "user_name": "Backup Agent",
    "user_email": "backup-agent@local"
  },
  "backup_cooldown": 60
}
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `monitor_path` | 监控路径 | `C:\AI-Agent-Local` |
| `backup_intervals.hourly` | 是否启用整点备份 | `true` |
| `keywords` | 关键词列表 | `["方案", "bug", ...]` |
| `notification.backup_start` | 备份开始提示 | `老板，我在备份...` |
| `notification.backup_complete` | 备份完成提示 | `老板，我备份好了` |
| `rollback.list_hours` | 默认查询多少小时的备份 | `12` |
| `git.auto_init` | 是否自动初始化 Git 仓库 | `true` |
| `backup_cooldown` | 备份冷却期（秒） | `60` |

---

## 📂 项目结构

```
backup-agent/
├── backup_agent.py         # 主程序入口
├── git_manager.py          # Git 操作封装
├── scheduler.py            # 定时任务模块
├── conversation_monitor.py # 对话监控模块
├── rollback_manager.py     # 回滚管理模块
├── logger.py               # 日志系统
├── config.py               # 配置加载模块
├── config.json             # 配置文件
├── requirements.txt        # 依赖清单
├── README.md               # 使用文档
└── logs/                   # 日志目录
    └── backup-agent.log    # 运行日志
```

---

## 🔧 工作原理

### 备份触发机制

Backup Agent 有两种备份触发方式：

#### 1. 改进意见触发

当您和 AI 讨论后，创建了改进意见文档（如 `待改进-20260226-xxx.md`），Backup Agent 会立即检测到并触发备份。

```
讨论方案/bug/改进 → 创建改进意见文档 → 立即备份
```

#### 2. 整点定时备份

每小时整点（00分），Backup Agent 会检查是否有文件修改，如果有则执行备份。

```
每小时整点 → 检查文件修改 → 有修改则备份
```

### Commit 消息格式

- **改进意见触发**：`💾 [改进意见触发] 在创建改进意见文档前 - 2026-02-26 14:35`
- **整点备份**：`💾 [整点备份] 定时备份 - 2026-02-26 15:00`

### 备份冷却期

为了防止频繁备份，默认有 60 秒的冷却期。

---

## 🔒 安全性说明

### Git 隐私安全

- ✅ Git 是**本地版本控制系统**，完全在您的电脑上运行
- ✅ 不会上传到任何云端（除非您手动推送到 GitHub）
- ✅ 所有数据都在 `.git` 目录中
- ✅ **没有任何隐私泄露风险**

### Git 费用

- ✅ Git 是**完全免费**的开源软件
- ✅ 本地使用**零费用**
- ✅ 无需任何账号或订阅

---

## ❓ 常见问题

### 1. Backup Agent 会影响性能吗？

**答**：不会。Backup Agent 占用资源很小：
- 内存占用：< 50MB
- CPU 占用：几乎为 0（仅在备份时短暂占用）
- 备份速度：< 2 秒

### 2. 如何停止 Backup Agent？

**答**：在运行 Backup Agent 的终端中按 `Ctrl+C` 即可停止。

### 3. 备份会占用很多空间吗？

**答**：不会。Git 使用增量存储，只保存修改的部分，通常 < 100MB。

### 4. 回滚后代码丢失了怎么办？

**答**：Backup Agent 在回滚前会自动创建一个"回滚前安全备份"，您可以随时恢复。

### 5. 如何查看日志？

**答**：日志文件位于 `logs/backup-agent.log`，包含完整的操作记录。

---

## 🚀 后续优化计划

- [ ] 增加 Web Dashboard（可视化备份历史）
- [ ] 增加系统通知（Windows 通知）
- [ ] 支持多个项目分别备份
- [ ] 支持远程备份（推送到 GitHub）
- [ ] 增加备份压缩（减少空间占用）

---

## 📄 许可证

MIT License

---

## 👨‍💻 作者

Backup Agent

**创建日期**: 2026-02-26
**版本**: v1.0.0

---

## 🙏 致谢

感谢使用 Backup Agent！如有问题或建议，欢迎反馈。
