# 雅虎财经Skill手动部署指南

## 🚀 部署到新加坡服务器

### 方式1：使用SCP（需要密码）

在本地Windows PowerShell或CMD中执行：

```bash
# 1. 上传skill目录（会提示输入密码）
scp -r C:\AI-Agent-Local\openclaw-ali\skills\yahoo-finance root@112.126.61.223:~/.openclaw/skills/

# 输入密码: Dandanyi2024!&Root
```

### 方式2：使用Git（推荐）

如果服务器上有git仓库：

```bash
# 1. 在本地提交到git
cd C:/AI-Agent-Local/openclaw-ali
git add skills/yahoo-finance/
git commit -m "feat: 添加雅虎财经Skill"
git push git@github.com:tanhaox/openclaw-ali.git master

# 2. 在服务器上拉取
ssh root@112.126.61.223
# 输入密码: Dandanyi2024!&Root

cd ~/.openclaw/skills
git clone https://github.com/tanhaox/openclaw-ali.git temp
mv temp/openclaw-ali/skills/yahoo-finance .
rm -rf temp
```

### 方式3：直接在服务器上创建

登录服务器后直接创建：

```bash
ssh root@112.126.61.223
# 输入密码

# 创建skill目录
mkdir -p ~/.openclaw/skills/yahoo-finance
cd ~/.openclaw/skills/yahoo-finance

# 创建SKILL.md
cat > SKILL.md << 'EOF'
---
name: yahoo_finance
description: 雅虎财经A股数据同步 - 获取K线数据和个股信息（100+字段）
metadata:
  {
    "openclaw": {
      "emoji": "📈",
      "homepage": "https://finance.yahoo.com/",
      "requires": {
        "bins": ["python3"],
        "config": []
      }
    }
  }
user-invocable: true
---

# 雅虎财经数据同步 Skill 📈

## 功能说明
- K线数据：开盘价、最高价、最低价、收盘价、成交量
- 个股信息：市值、市盈率、财务数据、分红数据（99个字段）

## 使用方法
```
同步贵州茅台的数据
```

```
查询伊利股份的市值和市盈率
```
EOF

# 下载tool.py（如果有URL）
# 或者从本地复制粘贴内容
```

### 方式4：使用Base64编码（绕过SCP）

```bash
# 在本地将目录打包并base64编码
cd C:/AI-Agent-Local/openclaw-ali/skills
tar czf yahoo-finance.tar.gz yahoo-finance/
base64 yahoo-finance.tar.gz > yahoo-finance.b64

# 复制yahoo-finance.b64的内容到服务器
ssh root@112.126.61.223
# 在服务器上解码
base64 -d > yahoo-finance.tar.gz << 'END_OF_FILE'
# 粘贴base64内容
END_OF_FILE

tar xzf yahoo-finance.tar.gz -C ~/.openclaw/skills/
rm yahoo-finance.tar.gz
```

## ✅ 部署后续步骤

上传完成后，在服务器上执行：

```bash
# 1. 设置权限
chmod +x ~/.openclaw/skills/yahoo-finance/tool.py
chmod 644 ~/.openclaw/skills/yahoo-finance/SKILL.md

# 2. 重启OpenClaw Gateway
openclaw gateway restart

# 3. 验证部署
ls -lh ~/.openclaw/skills/yahoo-finance/
```

## 🔍 验证部署

在OpenClaw Control UI或命令行中：

```
refresh skills
```

然后询问：
```
有哪些可用的skills？
```

应该能看到：
- **yahoo_finance**: 雅虎财经A股数据同步

## 💬 测试Skill

在OpenClaw中测试：

```
同步伊利股份的雅虎财经数据
```

```
查询股息率超过3%的股票
```

## ⚠️ 注意事项

1. **数据库路径**: tool.py会自动检测数据库位置
2. **依赖检查**: 需要Python3、yfinance、duckdb
3. **网络访问**: 需要能访问雅虎财经API
4. **权限问题**: 确保OpenClaw有权限执行tool.py

## 📞 故障排查

### 问题1：Skill未被识别

**检查**:
```bash
ls -lh ~/.openclaw/skills/yahoo-finance/
cat ~/.openclaw/skills/yahoo-finance/SKILL.md | head -20
```

**解决**:
```bash
openclaw gateway restart
```

### 问题2：工具调用失败

**检查**:
```bash
cd ~/.openclaw/skills/yahoo-finance
python3 tool.py sync_kline 600887 伊利股份 SS
```

**解决**:
- 检查Python依赖
- 检查数据库路径
- 检查网络连接

### 问题3：权限被拒绝

**解决**:
```bash
chmod +x ~/.openclaw/skills/yahoo-finance/tool.py
```
