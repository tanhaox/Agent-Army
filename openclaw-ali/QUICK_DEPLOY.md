# 雅虎财经Skill部署 - 3步完成

## 步骤1：上传到服务器

在本地PowerShell中执行（会提示输入密码）：

```powershell
scp -r C:\AI-Agent-Local\openclaw-ali\skills\yahoo-finance root@112.126.61.223:/root/.openclaw/skills/
```

密码：`Dandanyi2024!&Root`

## 步骤2：设置权限并重启

SSH登录到服务器：

```bash
ssh root@112.126.61.223
# 输入密码：Dandanyi2024!&Root
```

然后执行：

```bash
# 设置权限
chmod +x /root/.openclaw/skills/yahoo-finance/tool.py

# 重启OpenClaw Gateway
openclaw gateway restart

# 退出SSH
exit
```

## 步骤3：在OpenClaw中验证

在OpenClaw Control UI中输入：

```
refresh skills
```

然后测试：

```
同步伊利股份的雅虎财经数据
```

---

## 或者：一键复制脚本

如果您已经在服务器上，可以直接复制粘贴以下内容：

```bash
# 创建SKILL.md
mkdir -p /root/.openclaw/skills/yahoo-finance
cd /root/.openclaw/skills/yahoo-finance

cat > SKILL.md << 'EOF'
---
name: yahoo_finance
description: 雅虎财经A股数据同步
metadata: {"openclaw": {"emoji": "📈", "requires": {"bins": ["python3"]}}}
user-invocable: true
---
# 雅虎财经数据同步

同步股票数据：同步<股票>的数据
查询股票信息：查询<股票>的市值和市盈率
EOF
```

然后从本地复制 `tool.py` 的内容到服务器。

---

需要我帮您生成完整的`tool.py`内容以便直接复制到服务器吗？
