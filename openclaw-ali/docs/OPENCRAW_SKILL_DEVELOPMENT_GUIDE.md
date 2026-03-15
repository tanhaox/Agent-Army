# OpenClaw Skill 开发完整指南

> **基于 yahoo-finance-claude 开发经验总结**
> **版本**: v1.0
> **日期**: 2026-03-13

---

## 🎯 核心经验

### 1. 正确的 Skill 目录结构 ⭐⭐⭐

**必需文件结构**：
```
skill-name/
├── _meta.json                 ⭐ 必需！元数据
├── .clawhub/
│   └── origin.json             ⭐ 必需！来源追踪
├── SKILL.md                    ⭐ 必需！Skill文档
├── main.py                     ⭐ 入口文件（不是tool.py！）
└── tool.py                     （实际功能代码）
```

**关键发现**：
- ❌ `tool.py` **不是** OpenClaw 识别的入口文件
- ✅ `main.py` / `cli.py` / `__init__.py` 才是标准入口
- ✅ `_meta.json` 和 `.clawhub/origin.json` 是必须的元数据文件

---

### 2. 正确的部署位置 ⭐⭐⭐

**错误位置**：
- ❌ `~/.openclaw/skills/skill-name/`
- ❌ `~/.openclaw/.agents/skills/skill-name/`

**正确位置**：
- ✅ `/root/.openclaw/workspace/skills/skill-name/`

---

### 3. _meta.json 格式 ⭐⭐⭐

```json
{
  "ownerId": "your-owner-id",
  "slug": "skill-name",
  "version": "1.0.0",
  "publishedAt": 1234567890
}
```

**说明**：
- `ownerId`: 所有者ID（可以是任意字符串，用于标识）
- `slug`: skill 的唯一标识符（必须与目录名匹配）
- `version`: 版本号
- `publishedAt`: 发布时间戳（Unix时间戳或ISO格式）

---

### 4. .clawhub/origin.json 格式 ⭐⭐

```json
{
  "version": 1,
  "registry": "https://clawhub.ai",
  "slug": "skill-name",
  "installedVersion": "1.0.0",
  "installedAt": 1234567890
}
```

---

### 5. SKILL.md 格式 ⭐⭐

**YAML frontmatter + Markdown**：
```markdown
---
name: skill-name
description: Skill描述
---

# Skill 名称

功能说明...

## 使用方法

...
```

**关键点**：
- **必须有 YAML frontmatter**（`---` 包围的部分）
- `name` 必须与目录名匹配
- 描述要简洁明了

---

### 6. main.py 入口文件格式 ⭐⭐

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill 名称
OpenClaw 入口文件
"""

# 导入实际功能
from tool import sync_yahoo_kline, sync_yahoo_info, query_stock_data

# 暴露给 OpenClaw 的函数
__all__ = ['sync_yahoo_kline', 'sync_yahoo_info', 'query_stock_data']
```

**关键点**：
- 从 `tool.py` 导入功能，不直接实现
- 使用 `__all__` 明确暴露接口
- 保持入口文件简洁

---

## 📋 完整开发流程

### 步骤 1：本地创建 Skill 结构

```bash
cd ~/projects/skills/
mkdir my-skill
cd my-skill

# 创建文件
touch _meta.json SKILL.md main.py tool.py
mkdir .clawhub
touch .clawhub/origin.json
```

### 步骤 2：填充内容

1. **_meta.json** - 添加元数据
2. **.clawhub/origin.json** - 添加来源信息
3. **SKILL.md** - 编写 Skill 文档
4. **main.py** - 创建入口文件
5. **tool.py** - 实现功能

### 步骤 3：测试本地功能

```bash
python main.py  # 或直接调用 tool.py
```

### 步骤 4：部署到服务器

**选项A：使用 paramiko 自动部署**（推荐）
```python
import paramiko

# 连接服务器
ssh = paramiko.SSHClient()
ssh.connect(hostname='157.245.195.58', pkey=key)

# 创建 SFTP
sftp = ssh.open_sftp()

# 创建目录
sftp.mkdir('/root/.openclaw/workspace/skills/my-skill/.clawhub')

# 上传文件
sftp.put('local/_meta.json', '/root/.openclaw/workspace/skills/my-skill/_meta.json')
sftp.put('local/main.py', '/root/.openclaw/workspace/skills/my-skill/main.py')
# ... 上传其他文件

sftp.close()
ssh.close()
```

**选项B：使用 SSH 命令**
```bash
# 1. 创建目录
ssh root@157.245.195.195.58 "mkdir -p /root/.openclaw/workspace/skills/my-skill/.clawhub"

# 2. 上传文件
scp local/* root@157.245.195.58:/root/.openclaw/workspace/skills/my-skill/
```

### 步骤 5：注册 Skill

**方法A：在 openclaw.json 中注册**
```json
{
  "skills": {
    "entries": {
      "my-skill": {
        "enabled": true
      }
    }
  }
}
```

**方法B：在 OpenClaw 中手动记录**
```
请记录以下 Skill 信息到 Identity 表：
路径：/root/.openclaw/workspace/skills/my-skill/
入口：main.py
...
```

### 步骤 6：刷新和验证

```
# 在 OpenClaw 中
refresh skills

# 列出 skill
列出所有skill

# 测试功能
（输入具体的测试命令）
```

---

## 🚨 常见陷阱

### 陷阱 1：入口文件命名错误 ❌
```
tool.py       ❌ OpenClaw 不识别
func.py      ❌ OpenClaw 不识别
handler.py   ❌ OpenClaw 不识别

main.py     ✅ 正确
cli.py      ✅ 正确
__init__.py ✅ 正确
```

### 陷阱 2：目录位置错误 ❌
```
~/.openclaw/skills/              ❌ 错误位置
~/.openclaw/.agents/skills/       ❌ 错误位置

~/.openclaw/workspace/skills/    ✅ 正确位置
```

### 陷阱 3：缺少元数据文件 ❌
```
_no_meta.json/         ❌ 缺少 _meta.json
_no_clawhub_dir/      ❌ 缺少 .clawhub/

_meta.json + .clawhub/origin.json  ✅ 完整
```

###  陷阱 4：SKILL.md 没有 YAML frontmatter ❌
```
# Skill Name              ❌ 直接写 Markdown
## Description
...

---
name: skill-name            ✅ 必须有 YAML frontmatter
description: ...
---

# Skill Name
## Description
...
```

---

## ✅ 检查清单

在部署前确认：

- [ ] `_meta.json` 存在且格式正确
- [ ] `.clawhub/origin.json` 存在且格式正确
- [ ] `SKILL.md` 有 YAML frontmatter
- [ ] `main.py` (或其他标准入口) 存在
- [ ] `name` 与目录名匹配
- [ ] 部署到 `/root/.openclaw/workspace/skills/skill-name/`
- [ ] 已添加到 `openclaw.json` 或 Identity 表

---

## 🔧 调试技巧

### 检查 Skill 是否被识别

```bash
# 在服务器上
ls -la ~/.openclaw/workspace/skills/your-skill/

# 应该看到：
# _meta.json
# .clawhub/origin.json
# SKILL.md
# main.py
# tool.py
```

### 查看 Gateway 日志

```bash
tail -f /tmp/openclaw-gateway.log | grep -i skill
```

### 对比成功的 Skill

```bash
# 对比目录结构
diff -y <successful-skill> <your-skill>

# 检查文件差异
ls -la ~/.openclaw/workspace/skills/successful-skill/
ls -la ~/.openclaw/workspace/skills/your-skill/
```

---

## 📚 参考资料

### 成功的 Skill 示例
- `self-improvement-agent` - 自我学习系统
- `a-share-real-time-data` - A股实时数据
- `browser` - 浏览器控制

### OpenClaw 相关
- Gateway 配置：`~/.openclaw/openclaw.json`
- Workspace 路径：`/root/.openclaw/workspace/`
- Skills 目录：`/root/.openclaw/workspace/skills/`

---

## 🎯 快速模板

### _meta.json 模板
```json
{
  "ownerId": "your-owner-id",
  "slug": "skill-name",
  "version": "1.0.0",
  "publishedAt": 1741804800000
}
```

### .clawhub/origin.json 模板
```json
{
  "version": 1,
  "registry": "https://clawhub.ai",
  "slug": "skill-name",
  "installedVersion": "1.0.0",
  "installedAt": 1741804800000
}
```

### main.py 模板
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill 名称
OpenClaw 入口文件
"""

# 导入实际功能
from tool import function1, function2

# 暴露接口
__all__ = ['function1', 'function2']
```

---

## 💡 最后的建议

1. **对比成功案例** - 开发前先看其他成功的 skills
2. **逐步验证** - 每添加一个文件就测试一次
3. **保持简洁** - main.py 只做导入和暴露，不实现逻辑
4. **元数据完整** - _meta.json 和 .clawhub/origin.json 不能少

---

**祝下次一次成功！** 🚀
