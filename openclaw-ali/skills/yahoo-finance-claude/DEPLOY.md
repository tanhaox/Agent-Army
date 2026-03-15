# 雅虎财经 Skill - OpenClaw集成指南

## 🎯 目标

将雅虎财经数据同步功能包装成OpenClaw可识别的Skill，让OpenClaw能够：
- 理解用户的股票数据查询需求
- 自动调用雅虎财经同步工具
- 查询和分析已同步的股票数据

## 📦 Skill组件

```
openclaw-ali/skills/yahoo-finance/
├── SKILL.md          # Skill定义（OpenClaw核心）
├── tool.py           # Python工具包装器
├── README.md         # 使用文档
└── DEPLOY.md         # 本文档（部署指南）
```

## 🚀 部署步骤

### 方式1：本地Skill（推荐用于测试）

#### 步骤1：确定OpenClaw工作目录

```bash
# 查看OpenClaw配置
cat ~/.openclaw/openclaw.json | grep workspace

# 通常在
~/.openclaw/workspace/
```

#### 步骤2：复制Skill

```bash
# 复制到共享skill目录（所有agent可见）
cp -r openclaw-ali/skills/yahoo-finance ~/.openclaw/skills/

# 或者复制到特定agent工作空间
cp -r openclaw-ali/skills/yahoo-finance ~/.openclaw/workspace/skills/
```

#### 步骤3：设置权限

```bash
chmod +x ~/.openclaw/skills/yahoo-finance/tool.py
```

#### 步骤4：刷新OpenClaw

在OpenClaw Control UI或命令行中：
```
refresh skills
```

或重启Gateway：
```bash
openclaw gateway restart
```

#### 步骤5：验证

在OpenClaw中询问：
```
有哪些可用的skills？
```

应该能看到：
- **yahoo_finance**: 雅虎财经A股数据同步

### 方式2：通过ClawHub安装（推荐用于分享）

#### 步骤1：发布到ClawHub

```bash
# 安装clawhub CLI
npm install -g @openclaw/clawhub

# 登录
clawhub login

# 发布
cd openclaw-ali/skills/yahoo-finance
clawhub publish
```

#### 步骤2：其他人安装

```bash
# 搜索
clawhub search yahoo

# 安装
clawhub install yahoo-finance
```

### 方式3：Git Submodule（推荐用于团队）

```bash
# 在OpenClaw仓库中添加submodule
cd ~/.openclaw/skills
git submodule add https://github.com/yourname/openclaw-ali.git yahoo-finance

# 更新
git submodule update --remote
```

## 🔧 配置说明

### SKILL.md核心字段

```yaml
---
name: yahoo_finance                    # Skill唯一标识
description: 雅虎财经A股数据同步       # 简短描述
metadata:
  openclaw:
    emoji: "📈"                      # 图标
    homepage: "https://finance.yahoo.com/"
    requires:
      bins: ["python3"]              # 依赖的命令
      config: []                     # 依赖的配置项
user-invocable: true                 # 用户可直接调用
---
```

### 工具定义

SKILL.md中定义的工具：

1. **sync_yahoo_kline**: 同步K线数据
2. **sync_yahoo_info**: 同步个股信息
3. **sync_yahoo_complete**: 完整版同步
4. **query_stock_data**: 查询数据

OpenClaw会根据SKILL.md中的说明自动理解何时调用这些工具。

## 📊 OpenClaw如何使用这个Skill

### 场景1：用户询问股票数据

**用户输入**：
```
贵州茅台最近的股价是多少？
```

**OpenClaw的处理流程**：
1. 识别股票名称和代码（600519.SS）
2. 检查数据库是否有数据
3. 如果没有或数据过旧，调用 `sync_yahoo_kline` 同步数据
4. 查询数据库返回最新股价

### 场景2：用户要求同步数据

**用户输入**：
```
同步平安银行和比亚迪的数据
```

**OpenClaw的处理流程**：
1. 识别两只股票：000001.SZ, 002594.SZ
2. 调用 `sync_yahoo_kline` 同步K线数据
3. 调用 `sync_yahoo_info` 同步个股信息
4. 返回同步结果

### 场景3：用户查询条件筛选

**用户输入**：
```
找出市盈率低于15且股息率高于3%的股票
```

**OpenClaw的处理流程**：
1. 理解查询条件（PE < 15, 股息率 > 3%）
2. 调用 `query_stock_data` 执行SQL查询
3. 格式化返回结果

## 🔍 故障排查

### 问题1：Skill未被识别

**症状**：
```
列出可用的skills
```
输出中没有 `yahoo_finance`

**解决方案**：
```bash
# 检查文件是否存在
ls -la ~/.openclaw/skills/yahoo-finance/SKILL.md

# 检查权限
chmod 644 ~/.openclaw/skills/yahoo-finance/SKILL.md

# 刷新skills
openclaw gateway restart
```

### 问题2：工具调用失败

**症状**：
```
同步贵州茅台数据
```
返回错误：`tool not found`

**解决方案**：
```bash
# 检查tool.py是否可执行
ls -la ~/.openclaw/skills/yahoo-finance/tool.py

# 测试运行
cd ~/.openclaw/skills/yahoo-finance
python tool.py sync_kline 600519 贵州茅台 SS
```

### 问题3：数据库找不到

**症状**：
```
查询股票数据
```
返回错误：`数据库不存在`

**解决方案**：
```bash
# 检查数据库路径
ls -la openclaw-ali/data/stock_market_v2.db

# 如果不存在，初始化数据库
cd openclaw-ali/scripts
python init_database_phase2.py

# 同步初始数据
python sync_yahoo_complete.py
```

## 📝 开发指南

### 修改Skill行为

编辑 `SKILL.md`：
```markdown
---
name: yahoo_finance
description: 你的新描述
---

# 新的说明文档
...
```

### 添加新工具

1. 在 `tool.py` 中添加函数：
```python
def my_new_tool(param1, param2):
    """工具说明"""
    # 实现逻辑
    return {"status": "success", ...}
```

2. 在 `SKILL.md` 中添加文档：
```markdown
## my_new_tool

工具说明...

**参数**:
- param1: 说明
- param2: 说明
```

3. 在命令行接口中注册：
```python
if command == 'my_new_tool':
    result = my_new_tool(sys.argv[2], sys.argv[3])
    print(json.dumps(result))
```

## 🎓 最佳实践

1. **SKILL.md要简洁明了**
   - 告诉模型做什么，而不是怎么做
   - 提供清晰的参数说明和示例

2. **工具函数要有良好的错误处理**
   - 返回统一的JSON格式
   - 包含status、message、data字段

3. **使用logging而不是print**
   - 便于调试
   - 不干扰工具的JSON输出

4. **保持工具独立性**
   - tool.py可以独立运行
   - 便于测试和调试

## 📚 相关资源

- [OpenClaw文档](https://docs.openclaw.cn/)
- [Creating Skills Guide](../../openclaw-original/docs/tools/creating-skills.md)
- [Skills参考](../../openclaw-original/docs/tools/skills.md)
- [ClawHub](https://clawhub.com)

## 🔄 更新Skill

### 更新已有Skill

```bash
# 修改文件
vim ~/.openclaw/skills/yahoo-finance/SKILL.md

# 重启Gateway
openclaw gateway restart
```

### 版本管理

在 `SKILL.md` 的metadata中添加版本：
```yaml
metadata:
  {
    "openclaw": {
      "version": "1.0.0",
      "updated": "2026-03-13"
    }
  }
```

## ✅ 部署检查清单

部署前检查：

- [ ] SKILL.md格式正确（YAML frontmatter + Markdown）
- [ ] tool.py可独立运行
- [ ] 所有工具函数返回JSON格式
- [ ] 依赖已明确（Python 3.7+, yfinance, duckdb）
- [ ] 错误处理完整
- [ ] 文档齐全（README.md, DEPLOY.md）

部署后验证：

- [ ] Skill出现在OpenClaw的skill列表中
- [ ] 可以通过自然语言调用
- [ ] 工具函数执行正常
- [ ] 数据库操作成功
- [ ] 查询返回正确结果

---

**部署完成后**，你就可以在OpenClaw中使用：

```
同步贵州茅台的雅虎财经数据
```

```
查询伊利股份的市值和市盈率
```

```
找出股息率超过3%的股票
```

OpenClaw会自动识别这些需求并调用相应的工具！🎉
