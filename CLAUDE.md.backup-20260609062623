# AI-Agent-Local 项目配置和约定

**项目名称**: AI-Agent-Local
**项目类型**: AI 代理和技能开发平台
**配置更新**: 2026-02-25
**工作流程版本**: v2.6.0

---

## 🎯 项目核心信息

**项目根目录**: `C:\AI-Agent-Local`
**项目规范文档**: `docs/` 目录

### 三份核心规范（每次启动自动加载）

| 规范文档 | 说明 | 位置 |
|---------|------|------|
| **项目组织规范** | 目录结构、命名规范、项目分类 | `docs/项目组织规范.md` |
| **代码可维护性规范** | 模块化设计、命名、配置管理 | `docs/代码可维护性规范.md` |
| **开发指南** | 工作流程、AI辅助开发、测试标准 | `docs/开发指南.md` |

---

## 📁 标准项目结构

```
AI-Agent-Local/
├── projects/              # 【核心】所有项目
│   ├── skills/           # 技能类项目（可复用）
│   ├── apps/             # 应用类项目（完整应用）
│   └── tools/            # 工具类项目（小工具）
├── shared/               # 共享资源
│   ├── scripts/          # 脚本工具
│   │   └── create_project.py  # 【重要】项目生成器
│   ├── lib/              # 共享库
│   ├── templates/        # 项目模板
│   └── configs/          # 共享配置
├── docs/                 # 全局文档（核心规范）
├── archives/             # 归档目录
├── logs/                 # 日志目录
└── github_downloads/     # 第三方代码
```

---

## 🔐 权限配置

### Bash 工具权限（自动允许）

**开发操作** - 无需确认：
- ✅ 运行 Python 脚本和测试
- ✅ 运行系统命令（dir、ls、pwd 等）
- ✅ 安装依赖包（pip install）
- ✅ 查看文件内容和目录结构
- ✅ 运行编译器和代码生成工具
- ✅ 创建目录和文件
- ✅ Git 查看、提交、推送
- ✅ 查看进程和系统信息

**关键操作** - 需要确认：
- ⚠️ 删除文件或目录（rm -rf、del /s）
- ⚠️ 修改系统配置文件
- ⚠️ 关闭或杀死进程
- ⚠️ Git reset --hard

### 文件操作权限（自动允许）

- ✅ 读取任何文件（Read 工具）
- ✅ 编辑代码文件（Edit、Write 工具）
- ✅ 创建新文件和目录
- ✅ 搜索文件内容（Glob、Grep 工具）

### 🔴 服务器操作权限（严格禁止）

**绝对禁止的操作** - 会破坏三地统一：
- ❌ **直接修改服务器上的代码文件**
- ❌ **使用 SSH 上传代码到服务器**
- ❌ **在服务器上使用编辑器修改文件**
- ❌ **绕过 git 直接部署到生产环境**

**后果说明**：
```
直接修改服务器 → 服务器代码 ≠ Git仓库代码
              → 任何 git pull 会覆盖你的工作
              → 无法回滚到稳定版本
              → 服务器变成"野生"代码库
```

**允许的服务器操作**：
- ✅ 查看服务器状态（psql、pm2 status、systemctl）
- ✅ 查看日志文件（tail -f、grep log）
- ✅ 执行 git pull 拉取最新代码
- ✅ 重启服务（pm2 restart、systemctl restart）
- ✅ 运行数据库迁移

---

## 🪟 Windows 环境特定配置 ⚠️ **2026-05-07 新增**

### 路径双轨映射规则

Bash 工具使用 `/tmp/` 和 `~/`，但 Read/Edit/Write/Glob/Grep 工具需要 Windows 绝对路径。

| Bash 路径 | Read/Edit/Write 路径 |
|-----------|---------------------|
| `/tmp/xxx` | `C:/Users/tanha/AppData/Local/Temp/xxx` |
| `~/.claude/xxx` | `C:/Users/tanha/.claude/xxx` |
| 项目相对路径 | `C:/AI-Agent-Local/xxx` |

**强制规则**：
- Bash 命令可用 `/tmp/` 或 `~/`，Read/Edit/Write/Glob/Grep **必须**用 `C:/Users/tanha/...`
- 从 Bash 输出拿到路径后先转换为 Windows 格式再传给 Read 工具
- 不确定路径时用 `pwd` 或 `ls` 确认

### GitHub 访问策略 ⚠️

HTTPS (443) 被墙，仅 SSH (22) 可用：

**不可用**：
- ❌ `git clone https://github.com/...` — 超时
- ❌ `gh` CLI — API 走 HTTPS 全挂
- ❌ WebFetch 访问 `github.com` — 被屏蔽

**可用**：
- ✅ `git clone git@github.com:owner/repo.git`
- ✅ `ssh -T git@github.com`（已验证通过）

**强制规则**：
1. 所有 git 远程操作**强制 SSH**：`git@github.com:owner/repo.git`
2. 需要 repo 信息时：先 SSH clone → 读本地文件；其次 WebSearch
3. `gh` CLI 不可用，用 WebSearch 替代 `gh repo view`，用 git 命令替代 `gh pr/issue`
4. `GH_TOKEN` 待用户配置 PAT 后 `gh` 可能恢复

---

## 🚀 标准开发工作流程（v2.6.0）

> **重要**：AI-AGENT-LOCAL项目文件夹下所有项目开发必须遵守此工作流程

### 工作流程概述

建立**需求确认 → 理解验证 → 代码实现 → 自动测试 → 持续修复**的闭环，确保开发工作的准确性和质量。

### 8 个标准阶段

```
需求讨论 → 改进意见 → 读取方案 → 理解确认 → 代码实现 → 回看验证 → 自动测试 → 完成报告
   (1)        (2)        (3)       ⚠️(4)       (5)       (6)       (7)       (8)
```

### 阶段详解

#### 🗣️ 阶段 1：需求讨论
- 触发：用户提出改进方案或新需求
- 行为：进入讨论模式，明确需求细节
- 输出：明确的需求描述
- **约束**：不进行任何代码修改

#### 📝 阶段 2：改进意见形成
- 触发：用户确认"退出讨论"
- 行为：创建改进意见文档
- 位置：`docs/improvements/待改进-YYYYMMDD-功能名.md`
- 内容：需求描述、技术方案、预期结果、影响范围

#### 🔍 阶段 3：读取现有方案
- 触发：改进意见形成后
- 行为：分析现有代码，识别需要修改的文件
- 工具：Read / Glob / Grep
- 输出：现有方案分析报告

#### ✋ 阶段 4：理解确认 ⚠️ **关键环节**
- 触发：现有方案分析完成
- 行为：**必须停顿，给出对改进意见的理解**
- 输出：修改计划、关键改动点、实现顺序
- **约束**：⚠️ **未得到用户明确确认前，绝对不能进入代码修改状态**
- 用户确认方式：
  - ✅ "理解正确，开始修改" → 进入阶段 5
  - ❌ "不对，我指的是..." → 返回阶段 1 重新讨论
  - ❓ "这个部分不太清楚..." → 进一步澄清

#### 💻 阶段 5：代码实现
- 触发：用户确认理解正确
- 行为：按照改进意见修改代码
- 工具：Edit / Write / TodoWrite
- **规范**：使用专业日志库（Winston/Pino），不使用 console.log

#### 👀 阶段 6：回看验证
- 触发：代码修改完成后
- 行为：**重新读取改进意见，逐条对比改进意见 vs 实际修改**
- 输出：验证报告（✅ 一致 / ❌ 不一致）
- **约束**：如果不一致，必须补充修改，重新验证

#### 🧪 阶段 7：自动化测试与修复 **持续循环**
- 触发：回看验证通过
- 行为：**自主执行，无需频繁中断用户**
- 步骤：
  1. 缓存清理（rm -rf .next）
  2. 重新编译（pnpm build）
  3. 运行测试（pnpm test）
  4. 启动服务（pnpm dev / pnpm start）
  5. 模拟用户操作
  6. 循环修复直到无 BUG
- **原则**：只在遇到无法自主解决的问题时才询问用户

#### 📊 阶段 8：完成报告
- 触发：所有测试通过，功能确实实现
- 行为：生成完整的实现报告
- 内容：
  - 修改的文件列表
  - 测试结果
  - 版本号更新
  - 文档更新
  - 日志位置
- 归档：移动改进意见到 `docs/improvements/已完成/`

### 关键约束（必须遵守）

| 编号 | 约束 | 说明 | 严重性 |
|------|------|------|--------|
| 1 | **阶段 4 必须确认** | 未得到用户明确确认，不得进入阶段 5 | 🔴 严重 |
| 2 | **阶段 6 必须回看** | 修改完成后必须对比改进意见，确保一致 | 🔴 严重 |
| 3 | **阶段 7 自主执行** | 测试和修复循环自主进行，不频繁中断用户 | 🟡 重要 |
| 4 | **使用专业日志库** | 所有修改必须使用 Winston/Pino，不使用 console.log | 🟡 重要 |
| 5 | **更新文档和版本** | 改进完成后更新相关文档和版本号 | 🟡 重要 |

### 工作流程检查清单

在每次改进过程中，AI 会按顺序完成：

- [ ] **阶段 1**：明确需求和方案（讨论模式）
- [ ] **阶段 2**：创建改进意见文档
- [ ] **阶段 3**：分析现有代码
- [ ] **阶段 4**：**展示理解并等待用户确认** ⚠️
- [ ] **阶段 5**：按照改进意见修改代码
- [ ] **阶段 6**：**回看验证，确保修改一致**
- [ ] **阶段 7.1**：清理缓存
- [ ] **阶段 7.2**：重新编译
- [ ] **阶段 7.3**：运行测试
- [ ] **阶段 7.4**：启动服务
- [ ] **阶段 7.5**：模拟用户操作
- [ ] **阶段 7.6**：**循环修复直到无 BUG**
- [ ] **阶段 8**：生成完成报告

### 改进意见管理

**文档结构**：
```
docs/improvements/
├── README.md                      # 系统使用指南
├── 模板-改进意见.md               # 文档模板
├── 待改进-YYYYMMDD-功能名.md      # 待处理的改进
├── 进行中-YYYYMMDD-功能名.md      # 正在处理的改进
└── 已完成/
    ├── YYYYMMDD-功能名.md         # 已完成的改进
    └── ...
```

**状态流转**：
```
待改进 → 进行中 → 已完成 → 归档
  ↓        ↓         ↓
讨论中   实现中    已发布
```

### 回滚机制

**Git 备份点**（推荐）：
```bash
# 在阶段 5 之前创建备份
git add .
git commit -m "backup: before implementing [功能名]"

# 如果需要回滚
git reset --hard HEAD~1
```

**手动备份**：
```bash
# 创建备份目录
mkdir backup
cp -r src backup/src-$(date +%Y%m%d)
```

### 版本号管理

**版本号规则**：
- **重大改进**：主版本号 +1（v2.5.2 → v3.0.0）
- **功能新增**：次版本号 +1（v2.5.2 → v2.6.0）
- **Bug 修复**：修订号 +1（v2.5.2 → v2.5.3）

**需要更新版本号的文件**：
- 项目 README（版本号）
- package.json（version 字段）
- 批处理脚本（VERSION 变量）
- 相关文档（更新日期）

---

## 🚢 三地统一部署流程规范 ⚠️ **2026-03-05 强制执行**

## 🔧 GitHub工作流程修复记录（2026-03-06）⭐ **重要**

> **问题**：HTTPS连接不稳定，git push经常失败
>
> **解决**：强制使用SSH协议

### ✅ 标准Git推送流程（强制使用SSH）

```bash
# 步骤1：本地修改和测试
npm run build      # 本地编译
npm run test       # 本地测试
# ⚠️ 人工确认修改有效后再继续！

# 步骤2：暂存和提交
git add .
git commit -m "feat: 功能描述"

# 步骤3：推送到GitHub（使用SSH协议）
git push git@github.com:tanhaox/dandanyi.git master

# 步骤4：验证GitHub真的更新了（重要！）
git ls-remote git@github.com:tanhaox/dandanyi.git master
# 对比输出的commit hash和本地是否一致

# 步骤5：验证通过后，才能操作服务器
```

### ⚠️ 禁止使用的Git命令

| 命令 | 原因 |
|------|------|
| `git push origin master` | Windows下HTTPS协议不稳定 |
| `git remote set-url origin git@github.com:...` | Windows下不生效 |
| 推送后不验证GitHub | 可能出现假成功（文件卡在本地） |

### 🔑 关键约束

1. **必须使用SSH格式推送**：`git push git@github.com:tanhaox/dandanyi.git master`
2. **推送后必须验证**：`git ls-remote git@github.com:tanhaox/dandanyi.git master`
3. **对比commit hash**：确保本地和远程一致

---

> **教训来源**：2026-03-05 发生的版本控制灾难
>
> 用户警告：
> > "你直接改服务器，如何保障本地文件、github文件、服务器文件三者的统一关系？
> > 如何保障一个正确的版本在服务器跑？？？
> > 这是个特别严重，且非常错误的执行路径！"
>
> **根本问题**：直接修改服务器文件破坏了三地统一，导致版本失控

### 三地统一架构

```
┌─────────┐      ┌─────────┐      ┌─────────┐
│ 本地开发 │ ───> │ GitHub  │ ───> │ 服务器  │
│ (Windows) │      │ 仓库     │      │ (生产)  │
└─────────┘      └─────────┘      └─────────┘
    ①               ②               ③

① 本地开发（唯一允许修改代码的地方）
   - 使用 Edit/Write 工具修改代码
   - npm run build 本地编译
   - npm run test 本地测试

② 版本控制（强制同步点）
   - git add . 暂存所有更改
   - git commit -m "feat: xxx" 提交
   - git push origin master 推送

③ 生产部署（只读拉取）
   - git pull origin master 拉取
   - npm run build 编译
   - pm2 restart miaoying 重启
```

### 部署流程（必须遵守）

#### ✅ 正确的流程

```bash
# 步骤1：本地开发
# （在本地使用 Edit/Write 工具修改代码）

# 步骤2：本地测试
npm run build
npm run test

# 步骤3：提交到git
git add .
git commit -m "feat: 功能描述"
git push origin master

# 步骤4：服务器部署（通过部署脚本）
python deploy.py
```

#### ❌ 错误的流程（绝对禁止）

```python
# ❌ 错误1：直接修改服务器文件
ssh.exec_command("echo 'code' > /var/www/app/src/app.ts")

# ❌ 错误2：使用SSH上传代码
subprocess.run(["scp", "src/app.ts", "root@server:/var/www/app/src/"])

# ❌ 错误3：在服务器上直接编辑
ssh.exec_command("vim /var/www/app/src/app.ts")

# ❌ 错误4：绕过git直接部署
subprocess.run(["rsync", "-av", "src/", "root@server:/var/www/app/src/"])
```

### 三地一致性检查清单

**部署前必须检查**：

- [ ] 本地所有更改已提交（`git status` 无未提交文件）
- [ ] 本地已推送到GitHub（`git push` 成功）
- [ ] GitHub上有新的commit记录
- [ ] 服务器当前版本已记录（用于回滚）

**部署后必须验证**：

```bash
# 本地commit hash
LOCAL_HASH=$(git rev-parse HEAD)

# GitHub commit hash
GITHUB_HASH=$(git ls-remote origin master | awk '{print $1}')

# 服务器commit hash（通过SSH获取）
SERVER_HASH=$(ssh root@server "cd /var/www/miaoying && git rev-parse HEAD")

# 三者必须一致
echo "本地: $LOCAL_HASH"
echo "GitHub: $GITHUB_HASH"
echo "服务器: $SERVER_HASH"

assert $LOCAL_HASH == $GITHUB_HASH
assert $GITHUB_HASH == $SERVER_HASH
```

### 部署脚本模板

**正确的部署脚本**（`deploy.py`）：

```python
#!/usr/bin/env python3
"""
三地统一部署脚本
强制遵守：本地 → GitHub → 服务器 的单向流程
"""
import subprocess
import sys

def check_local_clean():
    """检查本地是否有未提交的更改"""
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        print("❌ 错误：本地有未提交的更改")
        print("请先执行：")
        print("  git add .")
        print("  git commit -m 'feat: xxx'")
        print("  git push origin master")
        sys.exit(1)

def get_local_hash():
    """获取本地commit hash"""
    return subprocess.check_output(
        ['git', 'rev-parse', 'HEAD']
    ).decode().strip()

def push_to_github():
    """推送到GitHub"""
    print("\n[2/4] 推送到GitHub...")
    result = subprocess.run(
        ['git', 'push', 'origin', 'master'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"❌ 推送失败: {result.stderr}")
        sys.exit(1)
    print("✅ 推送成功")

def deploy_to_server(commit_hash):
    """部署到服务器"""
    print(f"\n[3/4] 服务器部署...")
    print(f"   Commit: {commit_hash[:8]}")

    # 这里使用 paramiko 或其他方式连接服务器
    # 服务器执行：
    #   cd /var/www/miaoying
    #   git fetch origin
    #   git reset --hard <commit_hash>
    #   npm run build
    #   pm2 restart miaoying
    print("✅ 部署成功（待实现）")

def verify_deployment():
    """验证三地一致"""
    print("\n[4/4] 验证三地一致...")
    # TODO: 对比本地、GitHub、服务器的commit hash
    print("✅ 验证通过")

def main():
    print("=" * 60)
    print("  三地统一部署脚本")
    print("=" * 60)

    print("\n[1/4] 检查本地状态...")
    check_local_clean()

    commit_hash = get_local_hash()
    print(f"   当前Commit: {commit_hash[:8]}")

    push_to_github()
    deploy_to_server(commit_hash)
    verify_deployment()

    print("\n" + "=" * 60)
    print("  部署完成")
    print("=" * 60)

if __name__ == '__main__':
    main()
```

### 回滚机制

```bash
# 查看最近10次提交
git log --oneline -10

# 回滚到指定版本
git reset --hard <commit-hash>
git push origin master --force

# 服务器回滚
cd /var/www/miaoying
git reset --hard <commit-hash>
npm run build
pm2 restart miaoying
```

### 约束规则（强制执行）

| 编号 | 约束 | 严重性 | 违规后果 |
|------|------|--------|----------|
| 1 | **代码只能在本地修改** | 🔴 致命 | 破坏三地统一，版本失控 |
| 2 | **所有变更必须通过git** | 🔴 致命 | 无法追踪变化，无法回滚 |
| 3 | **服务器只能拉取，不能直接修改** | 🔴 致命 | git pull 会覆盖工作 |
| 4 | **部署前必须本地测试** | 🟡 重要 | 可能引入bug到生产 |
| 5 | **部署后必须验证三地一致** | 🟡 重要 | 确保版本正确 |

### 工具使用规范

**允许的工具组合**：

```
✅ 本地开发阶段：
   - Edit/Write 工具修改本地文件
   - Bash 工具运行 git 命令
   - Bash 工具运行 npm test

✅ 部署阶段：
   - Bash 工具运行 deploy.py
   - deploy.py 内部使用 SSH 连接服务器
   - SSH 只执行 git pull 和 pm2 restart

✅ 监控阶段：
   - Bash 工具通过 SSH 查看服务器状态
   - Bash 工具通过 SSH 查看日志
```

**禁止的操作**：

```
❌ 直接使用 paramiko 修改服务器文件
❌ 使用 scp/rsync 上传代码到服务器
❌ 在服务器上运行编辑器
❌ 绕过 deploy.py 直接操作服务器
```

---

## 🎯 新项目创建流程

### 方式 1：使用项目生成器（推荐）⭐

```bash
cd shared\scripts
create_project.bat
```

**优势**：
- ⚡ 3分钟完成（vs 手动30分钟）
- ✅ 100% 符合规范
- ✅ 零错误率

### 方式 2：手动创建

1. 选择项目类型（skill/app/tool）
2. 按照《项目组织规范》创建目录结构
3. 按照《代码可维护性规范》编写代码
4. 添加测试和文档

---

## 📋 代码规范要求

### 必须遵守的规范

1. **模块化设计**
   - 遵循分层架构（Controller → Service → Model）
   - 单一职责原则
   - 依赖注入

2. **命名规范**
   - 项目目录：小写英文 + 连字符（如 `weather-skill`）
   - Python 文件：小写 + 下划线（如 `weather_skill.py`）
   - 类名：大驼峰（如 `WeatherSkill`）
   - 函数名：小写 + 下划线（如 `get_weather()`）

3. **注释规范**
   - 文件头注释（必须）
   - 类注释（必须）
   - 公共函数注释（必须）
   - 复杂逻辑行内注释

4. **日志系统** ⭐
   - **必须使用专业日志库**（Winston/Pino）
   - **禁止使用 console.log**（除临时调试外）
   - 日志文件化（持久化存储）
   - 支持日志级别（ERROR、WARN、INFO、DEBUG）
   - UTF-8 编码支持中文
   - 自动轮转和历史保留

5. **配置管理**
   - 配置与代码分离
   - 敏感信息使用环境变量
   - 统一配置管理

6. **Karpathy 编码四原则** ⭐ **每次编码自动遵守**

   来源：[Andrej Karpathy 对 LLM 编码行为的观察](https://x.com/karpathy/status/2015883857489522876)，120K+ Stars 验证有效。

   **原则 1：先想后写 (Think Before Coding)**
   - 不确定时先问，列出假设让用户选，该反驳就反驳
   - 有多个方案时全列出来，不要自己悄悄选
   - 有更简单的方案时直接说出来
   - 代码不清楚时停下来，说清楚哪里不清楚

   **原则 2：简洁至上 (Simplicity First)**
   - 不添加用户没要求的功能/抽象/灵活性
   - 不为单次使用创建抽象层
   - 不为不可能发生的场景写错误处理
   - 写了 200 行能缩成 50 行？重写

   **原则 3：精准修改 (Surgical Changes)**
   - 只改任务相关的代码，不动附近的代码、注释、格式
   - 匹配已有代码风格，即使不是你惯用的
   - 发现无关的死代码？说出来，但不要删除
   - 你引入的无用 import/变量，必须自己清理
   - 每行改动都能追溯到用户的需求

   **原则 4：目标驱动 (Goal-Driven Execution)**
   - "修好这个 bug" → "先写复现测试，让它通过"
   - "加个验证" → "写出无效输入的测试，然后让它们通过"
   - 多步骤任务给出验证计划：每步做什么 → 怎么验证成功
   - 强验证标准让 AI 可以独立循环，弱标准需要反复确认

---

## 🧪 测试要求

### 必须包含的测试

- ✅ 单元测试（核心功能）
- ✅ 集成测试（如有需要）
- ✅ 测试覆盖率 > 80%

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行测试并显示覆盖率
python -m pytest tests/ --cov=.
```

---

## 📚 文档要求

### 每个项目必须包含

1. **README.md**（必需）
   - 项目说明
   - 功能特点
   - 安装依赖
   - 使用方法
   - 项目结构
   - 开发信息

2. **开发文档**（可选）
   - 架构说明
   - API 文档
   - 变更日志

---

## 🔧 可用工具

### 项目生成器

**位置**: `shared/scripts/create_project.py`

**功能**：
- 交互式创建项目
- 自动生成标准结构
- 自动生成代码模板
- 自动生成文档

**使用**：
```bash
python create_project.py --type skill --name my-skill
```

---

## 🎯 特定项目配置

### 📦 单单易项目（dandanyi）⭐⭐⭐⭐⭐ **2026-03-05 新增**

> **项目状态**: ✅ 活跃项目
> **项目类型**: Next.js 16.0.10 + PostgreSQL
> **本地路径**: `C:\AI-Agent-Local\dandanyi\`
> **远程服务器**: 112.126.61.223:22（目录：`/var/www/miaoying`）
> **GitHub仓库**: git@github.com:tanhaox/dandanyi.git
> **PM2进程名**: miaoying

#### 命名规范（避免混淆）

| 术语 | 说明 | 示例 |
|------|------|------|
| **本地** | 本地测试环境，基于dandanyi文件夹 | `cd C:\AI-Agent-Local\dandanyi` |
| **远程** | 远程服务器上的操作 | "远程服务器"、"远程部署" |
| **秒应项目** | 🛑 已停止维护，禁止修改 | 除非用户明确提到 |

> **重要说明**：远程服务器目录名为 `/var/www/miaoying`，但运行的是 **dandanyi** 项目代码（历史原因）

#### 工作流程铁律（必须遵守）

```
① 本地修改（dandanyi文件夹）
   ↓
② 本地测试（跑通功能）
   ↓
③ Git提交
   ↓
④ GitHub推送（git push origin master）
   ↓
⑤ 远程服务器更新（git pull → npm run build → pm2 restart）
```

#### 禁止行为（🔴 严重违规）

❌ **直接修改远程服务器代码**（违反三地统一）
❌ **修改秒应项目**（已停止维护）
❌ **绕过本地测试直接部署**
❌ **使用SSH上传文件到服务器**

#### 允许行为

✅ **本地开发**：
   - 使用 Edit/Write 工具修改 `C:\AI-Agent-Local\dandanyi\` 下的文件
   - 运行本地测试：`npm run build`、`npm run test`

✅ **远程操作**（只读）：
   - 通过SSH执行 `git pull`、`pm2 restart`、`pm2 logs`
   - 查看服务器状态：`pm2 status`、`psql` 查询
   - 查看日志：`tail -f /var/www/miaoying/logs/*.log`

✅ **部署命令**：
   ```bash
   # 本地提交
   cd C:\AI-Agent-Local\dandanyi
   git add .
   git commit -m "feat: 功能描述"
   git push origin master

   # 远程更新（通过部署脚本）
   python deploy_to_server.py
   ```

#### 数据库信息

- **数据库类型**: PostgreSQL
- **数据库名**: dandanyi
- **用户名**: postgres
- **关键表**: arrival_flights（航班到达数据）

#### 重要说明

1. **目录命名差异**：服务器目录名是 `miaoying`（历史遗留），但运行的是 `dandanyi` 项目
2. **Git仓库**：服务器连接到 `git@github.com:tanhaox/dandanyi.git`
3. **版本同步**：每次部署后必须验证 本地=GitHub=远程 三地commit hash一致

### API 管理技能

**项目位置**: `projects/skills/api_manager/`
**主文件**: `api_manager_skill.py`
**配置文件**: `apis/api_config.json`

**允许的操作**：
- ✅ 运行所有测试命令
- ✅ 修改代码和配置
- ✅ 创建必要的文件和目录
- ✅ 安装依赖

### Ollama AI 技能

**项目位置**: `projects/skills/ollama_ai/`
**主文件**: `ollama_ai_skill.py`、`ollama_web.py`
**端口**: 5006

**允许的操作**：
- ✅ 修改代码和配置
- ✅ 启动/停止 Web 服务
- ✅ 测试 API 接口

### 智能辅导系统

**项目位置**: `projects/apps/intelligent-tutor/`
**原名称**: "给我讲课"

**允许的操作**：
- ✅ 修改教学逻辑
- ✅ 更新知识库
- ✅ 运行测试

---

## 📊 项目统计

### 当前项目（2026-02-08）

**Skills（3个）**：
- api_manager - API 管理技能
- ollama_ai - Ollama AI 技能
- local_ocr - 本地 OCR 技能

**Apps（1个）**：
- intelligent-tutor - 智能辅导系统

**Tools（3个）**：
- ddg-search - DuckDuckGo 搜索工具
- github-ai - GitHub AI 助手
- file-operations - 文件操作工具

**总计**: 7 个活跃项目

---

## 🔄 配置更新记录

| 日期 | 更新内容 |
|------|---------|
| 2026-02-07 | 创建全局约定 |
| 2026-02-07 | 部署项目组织规范 |
| 2026-02-07 | 部署代码可维护性规范 |
| 2026-02-08 | 实施项目重组 |
| 2026-02-08 | 实施项目生成器 |
| 2026-02-08 | 整合所有配置到启动加载 |
| 2026-02-25 | **部署标准开发工作流程 v2.6.0** ⭐ |
| 2026-02-25 | 新增改进意见管理系统 |
| 2026-02-25 | 新增 8 阶段开发流程 |
| 2026-02-25 | 新增关键约束（阶段 4 确认、阶段 6 回看） |
| 2026-02-27 | **部署自动备份系统** ⭐ |
| 2026-02-27 | 每次对话自动启动 Backup Agent |
| 2026-02-27 | 整点自动备份 + 改进意见触发备份 |
| 2026-03-05 | **三地统一部署流程规范** 🔴🔴🔴 **最严重约束** |
| 2026-03-05 | 禁止直接修改服务器代码文件 |
| 2026-03-05 | 强制执行 本地 → GitHub → 服务器 单向流程 |
| 2026-03-05 | 新增三地一致性检查清单 |
| 2026-03-05 | 新增部署脚本模板 |
| 2026-03-05 | **添加单单易项目规范** ⭐⭐⭐⭐⭐ |
| 2026-03-05 | 明确本地 vs 远程命名规范 |
| 2026-03-05 | 强调秒应项目已停止维护 |

---

## 🤖 自动启动服务

### Backup Agent 自动备份系统

**每次打开 Claude Code 对话时，AI 会自动**：

1. ✅ **启动 Backup Agent 后台服务**
   - 自动监控文件变化
   - 每小时整点自动备份
   - 检测到改进意见文档时立即备份

2. ✅ **显示服务状态**
   - 确认服务运行状态
   - 显示下次备份时间

**服务位置**: `projects/tools/backup-agent/`

**自动备份触发**:
- ⏰ **整点备份**: 每小时 :00 分自动执行
- 📝 **改进意见触发**: 创建 `待改进-*.md` 或 `进行中-*.md` 时

**管理命令**:
```bash
# 查看状态
python projects/tools/backup-agent/backup_agent.py --status

# 查看备份清单
python projects/tools/backup-agent/backup_agent.py --list

# 回滚到指定备份
python projects/tools/backup-agent/backup_agent.py --rollback 1
```

**日志位置**: `projects/tools/backup-agent/logs/backup-agent.log`

---

## ✅ 生效说明

**本配置从创建时起立即生效，Claude Code 每次启动时自动加载**

### 自动加载内容

1. ✅ 项目结构规范
2. ✅ 代码规范要求
3. ✅ **标准开发工作流程 v2.6.0** ⭐
4. ✅ 改进意见管理系统
5. ✅ 新项目创建流程
6. ✅ 测试要求
7. ✅ 文档要求
8. ✅ 回滚机制
9. ✅ 版本号管理

### 如何更新配置

**如需修改配置**：
1. 编辑本文件（`CLAUDE.md`）
2. Claude Code 会自动重新加载
3. 无需重启

---

**注意**: 本配置定义了 AI-Agent-Local 项目的所有核心约定和规范，AI 在每次启动时会自动读取并遵守。

### 核心变更（2026-02-25）

**✅ 已部署标准开发工作流程 v2.6.0**：
- 8 个标准开发阶段
- 改进意见管理系统
- 关键约束（阶段 4 确认、阶段 6 回看）
- 回滚机制
- 版本号管理规范

**✅ 日志系统要求**：
- 必须使用专业日志库（Winston/Pino）
- 禁止使用 console.log（除临时调试）
- 日志必须持久化到文件

如有需要，用户可以随时修改本文件的配置。

---

## 🌐 ScriptForge 网络资源规则

> **详见**: `scriptforge/MIRROR_RULES.md` — 禁止自动下载境外资源、模型本地化、网络超时降级等 5 条强制规则。

---

## 🤖 Skill 自动加载注册表 ⚠️ **2026-05-07 新增**

> **58 个 skill 全部注册在此，每次新会话自动加载。优先级体系: P:5=关键基础设施 > P:4=安全守卫 > P:3=领域专家 > P:2=过程增强 > P:1=后台支撑**

### P:5 — 关键基础设施（3 个）

| Skill | 来源 | 触发场景 |
|-------|------|---------|
| `self-improvement` | user | 操作失败/用户纠错/AI 知识过时/外部 API 失败 → 记录学习 |
| `clawcn-windows-setup` | user | Windows 命令兼容性/路径错误/网关令牌/中文编码 → 修复环境 |
| `claudeception` | user | 自动提取对话知识→ docs/knowledge/，无需用户命令 |

### P:4 — 安全守卫（3 个）

| Skill | 来源 | 触发场景 |
|-------|------|---------|
| `cancel` | user | 用户说"取消/停止/退出模式/stop" → 退出 OMC 模式 |
| `git-guardrails-claude-code` | user | git push/reset --hard/clean -f/branch -D → 强制确认 |
| `omc-reference` | user | 委派子代理/OMC 工具/多代理编排/提交协议 |

### P:3 — 领域专家（20 个）

| Skill | 来源 | 触发场景 |
|-------|------|---------|
| `frontend-design` | user | "做网页/创建页面/设计组件/登录页/仪表盘/UI不好看" → 前端设计 |
| `ui-ux-pro-max-skill` | project | "设计 UI/美化界面/配色方案/毛玻璃/新拟态/暗黑模式/字体搭配" |
| `web-design-guidelines` | user | "审查 UI/检查无障碍/审计设计/UX 审查" → Vercel 规范审查 |
| `playwright-skill` | user | "测试页面/自动化测试/E2E/截图/检查死链" → Playwright 测试 |
| `github` | omc | "PR 状态/CI 结果/创建 issue/查看 CI 日志" → GitHub 操作 |
| `local_ocr` | project | "读图/提取文字/OCR/图片转文字" → 本地 PaddleOCR |
| `ollama_ai` | project | "用本地AI/跑Ollama/本地模型/离线 AI" → Ollama 助手 |
| `multi-search-engine` | user | "搜索/查一下/找找/隐私搜索/WolframAlpha 计算" → 17 引擎 |
| `xinpi-disclosure` | omc | "搜索公告/查找披露/A 股公告/年报下载" → 中国资本市场 |
| `weather` | omc | "天气怎么样/今天会下雨吗/北京温度/周末预报" → 天气预报 |
| `summarize` | omc | "总结这个/提取文稿/转录音频/概括文章" → URL/播客/文件总结 |
| `openai-whisper` | omc | "转录/听写/语音转文字/whisper" → 本地音频转文字 |
| `openai-image-gen` | omc | "生成一张图/画一个/创建插图/DALL-E" → AI 图片生成 |
| `video-frames` | omc | "提取视频帧/截图/生成缩略图" → ffmpeg 帧提取 |
| `discord` | omc | "发到 Discord/查 Discord 消息/Discord 频道" → Discord 操作 |
| `notion` | omc | "创建 Notion 页面/加到数据库/搜 Notion/存到 Notion" |
| `react-native-best-practices` | user | "RN 性能优化/React Native 卡顿/FlatList 优化/bundle 太大" |
| `diffs` | extension | "生成 diff/对比差异/分享代码变更/查看版本差异" |
| `feishu-doc` | extension | "在飞书写文档/读取飞书/更新飞书文档" → 飞书操作 |
| `lobster` | extension | 多步骤工作流自动化，关键操作前人工批准 |
| `skill-creator` | omc | "创建 skill/写个 skill/做个技能/审查 skill" → Skill 开发 |
| `grill-with-docs` | user | "审查方案/审问设计/grill with docs/领域建模/统一术语" → 文档驱动设计 |

### P:2 — 过程增强（23 个）

| Skill | 来源 | 触发场景 |
|-------|------|---------|
| `omc-plan` | user | "做个计划/规划一下/设计方案/怎么入手" → 战略规划 |
| `ultrawork` | user | "并行处理/一起做/同时处理/批量处理" → 并行执行引擎 |
| `team` | user | "team/组队/多代理/分给多个代理" → 多代理协作 |
| `tdd` | user | "TDD/测试驱动/先写测试/red-green-refactor" → 测试驱动开发 |
| `triage` | user | "分诊/triage/创建 issue/分类 bug/manage issue workflow" |
| `grill-me` | user | "审查方案/审问设计/grill me/挑战方案" → 设计压力测试 |
| `diagnose` | user | "诊断 bug/调试错误/排查问题/性能回退" → 6 阶段调试流水线 |
| `to-prd` | user | "生成 PRD/写需求文档/创建产品需求/总结讨论" → 对话→PRD |
| `to-issues` | user | "拆成 issue/创建工单/分解任务/拆分工作" → 垂直切片 |
| `ai-slop-cleaner` | user | "清理代码/去冗余/简化代码/deslop" → AI 冗余清理 |
| `ai-slop-cleaner` | user | "清理代码/去冗余/简化代码/deslop" → AI 冗余清理 |
| `clawdhub` | user | "搜索 skill/安装 skill/从 clawdhub 下载" → Skill 市场 |
| `service_manager` | project | "服务面板/状态面板/skill 清单/启动服务/有哪些服务" → 统一管理 |
| `project-auditor` | project | "自检/审计项目/全面检查/project audit" → 6 维度全量审计 |
| `project-fixer` | user | "修复问题/自动修复/fix issues" → 读取审计报告 6 agent 并行修复 |
| `code-splitter` | user | "拆分文件/大文件重构/提取模块" → 按行范围安全拆分 |
| `py-security` | user | "安全检查/扫描安全漏洞/密钥泄露" → Python OWASP 检测修复 |
| `py-code-health` | user | "清理死代码/移除未使用代码" → Python 死代码检测 |
| `py-complexity` | user | "降低复杂度/简化函数" → Python 圈复杂度优化 |
| `py-refactor` | user | "全面重构/Python 重构/代码现代化" → 5 子 skill 编排 |
| `upgrading-react-native` | user | "升级 RN/RN 版本更新/升级 Expo SDK" → RN 升级 |
| `react-native-brownfield-migration` | user | "迁移到 RN/原生转 React Native/brownfield 集成" → RN 迁移 |

### P:1 — 后台支撑（9 个）

| Skill | 来源 | 触发场景 |
|-------|------|---------|
| `debug` | user | "调试/哪里出错了/诊断一下" → OMC 诊断 |
| `verify` | user | "验证一下/确认能用/验证修复" → 修改验证 |
| `deepinit` | user | "初始化项目/生成项目文档/分析代码库结构" → 项目初始化 |
| `setup` | user | "设置环境/安装配置/诊断环境/环境准备好了吗" → 环境管理 |
| `skill` | user | "管理 skill/列出 skill/删除 skill/有哪些 skill" → Skill 管理 |
| `hud` | user | "配置 HUD/改显示/切换显示模式" → HUD 配置 |
| `project-session-manager` | user | "创建隔离环境/开 worktree/管理会话" → 隔离环境 |
| `api_manager` | project | "API key/管理 API/查 API 用量/有哪些 API" → API 管理 |
| `ww` | project | 秒应/miaoying/dandanyi 项目管家/代理协调/备份管理 |

### 自动加载机制

```
新对话启动 → CLAUDE.md 加载 → Skill 注册表进入上下文
  → 58 个 skill 全部可见 → 用户消息匹配 Use when 条件
  → 对应 skill 自动激活 → 按 P:N 优先级裁决竞争
```

**关键规则**：
1. 所有 58 个 skill 均已写入此注册表，新会话自动知晓全部能力
2. 每个 skill 的 SKILL.md `description` 中包含具体 "Use when:" 触发条件
3. 多个 skill 竞争时，高优先级 (P:5 > P:4 > P:3 > P:2 > P:1) 优先触发
4. 同优先级按领域匹配精度裁决
5. 新增 skill 时同步更新此注册表

**快速查看**：
```bash
python -m projects.skills.service_manager          # 统一状态面板
python -m projects.skills.service_manager --skills # JSON 格式完整清单
```

---

## 🧠 知识自动沉淀机制 ⚠️ **2026-05-07 新增**

> 讨论→决策→执行信号 的完整闭环中，AI 自动将讨论结果写入 `docs/knowledge/`。

**触发条件**：用户发出执行信号——"开始开发"、"可以推进了"、"开干"、"没问题开始吧" 等。这意味着多轮讨论已完成、计划已敲定，此时此前的对话内容值得永久保存。

**提取范围**：领域知识、架构决策、技术方案、新安装的 skill、用户纠正反馈。

**不触发**：简单一问一答、单轮操作、未形成结论的讨论。

**存储格式**：一个主题一个 .md 文件，`docs/knowledge/README.md` 维护索引。

---

## 📈 Stock Analyst 量化系统 ⚠️ **2026-06-07 新增**

> **项目路径**: `C:\AI-Agent-Local\Stock\`
> **版本**: v4.5
> **核心定位**: A 股量化分析 + 个性化模型 + 自学习闭环

### 核心文档（每次启动自动加载）⭐⭐⭐

| 文档 | 位置 | 用途 |
|------|------|------|
| **系统架构文档** | `Stock/docs/architecture.md` | 完整架构、数据流、调用链、数据库、变更日志 |
| **开发施工手册** | `Stock/docs/DEVELOPER_GUIDE.md` | 跨模块依赖、连带影响表、全局约定、统一工具库 API |
| **新闻事件系统** | `Stock/docs/news.md` | 新闻管线数据流、LLM 输出规范、跨源去重 |
| **Tushare API 手册** | `Stock/docs/tushare.md` | Tushare Pro 接口参数速查、调用示例、权限边界 |

> **强制规则**：
> - 🔴 **开发前**必须阅读 `DEVELOPER_GUIDE.md` — 先查 §7"统一工具库"看所需功能是否已有全局实现，再查"连带影响"表
> - 🔴 **系统升级后**必须更新 `architecture.md` 的变更日志 + 已知问题
> - 🔴 **新增模块**必须先查"统一工具库"，不要在模块内打补丁
> - 🟡 **更新系统架构**后同步更新 `DEVELOPER_GUIDE.md` 全局约定
> - 🟡 **诊断问题时**先读 `DEVELOPER_GUIDE.md` "常见补丁原因速查"
> - 🟡 **调用 Tushare API** 前先查 `Stock/docs/tushare.md` — 确认接口权限、参数格式、调用限制

### 全局禁止事项

| 禁止行为 | 原因 | 替代方案 |
|---------|------|---------|
| ❌ 内联 NaN 守卫 (`isnan`/`nan_to_num`/`fillna`) | 14 处不一致 (回退值 0.0/0.5/50) | `safe_float()` / `sanitize_array()` |
| ❌ 自写 700001.TI SQL 查询 | 14 处分散 + 5 种写法 | `get_benchmark_closes()` (模块级缓存) |
| ❌ 日历日超额收益计算 | 影子训练系统性偏误 | `compute_excess_return()` (交易日计数) |
| ❌ 2/3 参数 Progress 回调 | 3 种签名混用导致崩溃 | 4 参数标准 + `make_progress_adapter()` |
| ❌ `startswith('6') → .SH` 内联 | 9 处复制 + 6 处 BJ 丢弃 bug | `normalize_ts_code()` |
| ❌ 跳过 `stock_name_cache` 直接查 `scan_results` | 5 处绕过 | `get_stock_name()` |
| ❌ 新增任何除权检测代码 | 系统已全局前复权 (`daily_kline.adj_factor`) | 直接用 `daily_kline` |
| ❌ 修改现有系统代码只为 DNA 实验室接入 | 违反并行原则 | DNA 在独立 schema/API/前端 |

### 开发工作流

```
接入 Stock 开发任务 →
  第一步: 读 DEVELOPER_GUIDE.md §7 "统一工具库" — 确认无全局实现
  第二步: 读 DEVELOPER_GUIDE.md 对应文件的"连带影响"表 → 注意上下游
  第三步: 读 architecture.md 数据流章节 → 确认全链路影响
  第四步: 读 CLAUDE.md 本节的"禁止事项" — 确认不踩红线
  第五步: 开始编码
```

### 快速索引

```
系统架构:    Stock/docs/architecture.md       (v4.5, 2026-06-07)
开发手册:    Stock/docs/DEVELOPER_GUIDE.md     (v2.0, 2026-06-07)
新闻系统:    Stock/docs/news.md                (v2.1, 2026-06-07)
Tushare API: Stock/docs/tushare.md             (8000积分 + A股分钟权限)
DNA 实验室:  Stock/docs/PHASE_PLAN.md          (施工执行清单)
DNA 服务:    Stock/backend/app/services/stock_dna/  (10 模块)
DNA API:     Stock/backend/app/api/dna.py      (7 端点)
P0 工具:     Stock/backend/app/utils/numpy_utils.py
             Stock/backend/app/core/market_data.py
             Stock/backend/app/core/progress.py
             Stock/backend/app/utils/stock_code.py
             Stock/backend/app/core/name_resolver.py
前复权:      Stock/backend/scripts/resync_all_kline.py
```
