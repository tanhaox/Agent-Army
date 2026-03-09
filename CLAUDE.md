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
