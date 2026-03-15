# 雅虎财经Skill部署到新加坡服务器 - 最简方案

## ⚡ 最简单的方法（推荐）

### 步骤1：SSH登录服务器

```bash
ssh root@112.126.61.223
# 密码: Dandanyi2024!&Root
```

### 步骤2：运行一键安装脚本

复制并粘贴以下内容到服务器终端：

```bash
curl -o- https://raw.githubusercontent.com/tanhaox/openclaw-ali/main/install_on_server.sh | bash
```

或者如果没有上传到GitHub，手动创建：

```bash
# 创建目录
mkdir -p /root/.openclaw/skills/yahoo-finance
cd /root/.openclaw/skills/yahoo-finance

# 创建简化的SKILL.md
cat > SKILL.md << 'EOF'
---
name: yahoo_finance
description: 雅虎财经A股数据同步
user-invocable: true
---
# 雅虎财经数据同步

使用方法：
- 同步股票数据：同步<股票名称>的数据
- 查询股票信息：查询<股票名称>的市值和市盈率
EOF

# 重启Gateway
openclaw gateway restart
```

### 步骤3：在OpenClaw中验证

在OpenClaw Control UI中输入：

```
refresh skills
```

---

## 📋 或者使用完整版（需要手动复制tool.py）

如果您需要完整功能（包括K线数据同步），从本地复制文件：

### 在本地PowerShell中：

```powershell
# 方式1：使用SCP（需要密码）
scp C:\AI-Agent-Local\openclaw-ali\skills\yahoo-finance\SKILL.md root@112.126.61.223:/root/.openclaw/skills/yahoo-finance/

# 方式2：复制内容到剪贴板，然后在服务器上粘贴创建
```

### 在服务器上：

```bash
# 创建目录
mkdir -p /root/.openclaw/skills/yahoo-finance
cd /root/.openclaw/skills/yahoo-finance

# 从本地复制SKILL.md的内容粘贴过来
vim SKILL.md
# 粘贴内容，保存退出

# 同样方式创建tool.py
vim tool.py
# 粘贴tool.py的内容，保存退出

# 设置权限
chmod +x tool.py

# 重启
openclaw gateway restart
```

---

## ✅ 部署完成后测试

在OpenClaw中：

```
refresh skills

同步伊利股份的雅虎财经数据

查询伊利股份的市值和市盈率
```

---

## 🔑 服务器信息

- **主机**: 112.126.61.223
- **用户**: root
- **密码**: Dandanyi2024!&Root
- **部署目录**: /root/.openclaw/skills/yahoo-finance/

---

## ⚠️ 如果遇到问题

### 问题1：Permission denied

**解决**：确保使用正确的密码登录

### 问题2：Skill未被识别

**解决**：
```bash
ls -lh /root/.openclaw/skills/yahoo-finance/
cat /root/.openclaw/skills/yahoo-finance/SKILL.md | head -10
```

### 问题3：OpenClaw命令找不到

**解决**：
```bash
which openclaw
# 或
systemctl status openclaw-gateway
```

---

**需要我帮您生成完整的、可以直接复制粘贴到服务器的内容吗？**
