# 凭证管理目录

**创建日期**: 2026-03-14
**目的**: 集中管理所有服务器和接口的凭证、密钥、许可证等

---

## ⚠️ 安全警告

**这个目录包含敏感信息，必须严格管理**：

1. ✅ **必须添加到 .gitignore**
2. ✅ **私钥文件权限必须设置为 600**
3. ✅ **API密钥建议加密存储**
4. ❌ **禁止提交到 Git 仓库**

---

## 📁 目录结构

```
credentials/
├── ssh/                    # SSH密钥
│   ├── aliyun/            # 阿里云服务器
│   │   ├── id_rsa        # 私钥（权限600）
│   │   ├── id_rsa.pub    # 公钥
│   │   └── config        # SSH配置
│   ├── malaysia/         # 马来西亚服务器
│   └── github/           # GitHub SSH密钥
│
├── api_keys/              # API密钥
│   ├── zhipu.key         # 智谱AI
│   ├── deepseek.key      # DeepSeek
│   └── openai.key        # OpenAI
│
├── licenses/              # 软件许可证
│   └── software.lic
│
└── tokens/                # 访问令牌
    ├── github.token
    └── npm.token
```

---

## 📋 凭证清单

### SSH密钥

| 服务器/服务 | 创建日期 | 过期日期 | 用途 | 状态 |
|------------|---------|---------|------|------|
| 阿里云 (112.126.61.223) | YYYY-MM-DD | - | SSH登录 | ✅ 正常 |
| 马来西亚 (157.245.195.58) | YYYY-MM-DD | - | SSH登录 | ✅ 正常 |
| GitHub | YYYY-MM-DD | - | Git推送 | ✅ 正常 |

### API密钥

| 服务 | 创建日期 | 过期日期 | 配额 | 状态 |
|------|---------|---------|------|------|
| 智谱AI (Max套餐) | 2026-XX-XX | - | 1600次/5小时 | ✅ 正常 |
| DeepSeek | 2026-XX-XX | - | 按量付费 | ✅ 正常 |
| OpenAI | 2026-XX-XX | - | 按量付费 | ⚠️ 备用 |

### 访问令牌

| 服务 | 创建日期 | 过期日期 | 权限 | 状态 |
|------|---------|---------|------|------|
| GitHub Token | YYYY-MM-DD | - | repo, workflow | ✅ 正常 |
| NPM Token | YYYY-MM-DD | - | publish | ✅ 正常 |

---

## 🔐 使用说明

### SSH密钥使用

**1. 生成新的SSH密钥对**：

```bash
# 阿里云服务器
ssh-keygen -t rsa -b 4096 -C "aliyun@agent-army" -f credentials/ssh/aliyun/id_rsa

# 马来西亚服务器
ssh-keygen -t rsa -b 4096 -C "malaysia@agent-army" -f credentials/ssh/malaysia/id_rsa

# GitHub
ssh-keygen -t ed25519 -C "github@agent-army" -f credentials/ssh/github/id_rsa
```

**2. 设置私钥权限**：

```bash
chmod 600 credentials/ssh/*/id_rsa
```

**3. 配置SSH客户端**：

编辑 `~/.ssh/config`：

```
# 阿里云服务器
Host aliyun
    HostName 112.126.61.223
    User root
    IdentityFile C:/AI-Agent-Local/Agent_Army/credentials/ssh/aliyun/id_rsa

# 马来西亚服务器
Host malaysia
    HostName 157.245.195.58
    User root
    IdentityFile C:/AI-Agent-Local/Agent_Army/credentials/ssh/malaysia/id_rsa

# GitHub
Host github.com
    IdentityFile C:/AI-Agent-Local/Agent_Army/credentials/ssh/github/id_rsa
```

### API密钥使用

**1. 存储API密钥**：

```bash
# 创建密钥文件
echo "your_zhipu_api_key_here" > credentials/api_keys/zhipu.key
echo "your_deepseek_api_key_here" > credentials/api_keys/deepseek.key
echo "your_openai_api_key_here" > credentials/api_keys/openai.key

# 设置权限
chmod 600 credentials/api_keys/*.key
```

**2. 在代码中读取**：

```typescript
import fs from 'fs';
import path from 'path';

// 读取API密钥
const zhipuKey = fs.readFileSync(
  path.join(__dirname, '../credentials/api_keys/zhipu.key'),
  'utf-8'
).trim();

// 或者使用环境变量（推荐）
const zhipuKey = process.env.ZHIPU_API_KEY;
```

**3. 加密存储（可选）**：

```bash
# 加密密钥文件
gpg -c credentials/api_keys/zhipu.key

# 解密
gpg -d credentials/api_keys/zhipu.key.gpg
```

---

## 🔄 凭证更新流程

### SSH密钥更新

```bash
# 1. 生成新密钥
ssh-keygen -t rsa -b 4096 -C "aliyun@agent-army" -f credentials/ssh/aliyun/id_rsa_new

# 2. 复制公钥到服务器
ssh-copy-id -i credentials/ssh/aliyun/id_rsa_new.pub root@112.126.61.223

# 3. 测试新密钥
ssh -i credentials/ssh/aliyun/id_rsa_new root@112.126.61.223

# 4. 确认成功后替换旧密钥
mv credentials/ssh/aliyun/id_rsa credentials/ssh/aliyun/id_rsa_old
mv credentials/ssh/aliyun/id_rsa_new credentials/ssh/aliyun/id_rsa

# 5. 删除旧密钥
rm credentials/ssh/aliyun/id_rsa_old
```

### API密钥更新

```bash
# 1. 备份旧密钥
cp credentials/api_keys/zhipu.key credentials/api_keys/zhipu.key.bak

# 2. 更新密钥
echo "new_zhipu_api_key_here" > credentials/api_keys/zhipu.key

# 3. 测试新密钥
npm run test:zhipu

# 4. 确认成功后删除备份
rm credentials/api_keys/zhipu.key.bak
```

---

## 📊 凭证有效期检查

### 定期检查（每月）

```bash
# 检查SSH密钥
ssh-keygen -l -f credentials/ssh/aliyun/id_rsa.pub

# 检查API密钥配额
curl -H "Authorization: Bearer $(cat credentials/api_keys/zhipu.key)" \
  https://open.bigmodel.cn/api/paas/v4/usage

# 检查GitHub Token
curl -H "Authorization: token $(cat credentials/tokens/github.token)" \
  https://api.github.com/user
```

### 过期提醒

- **SSH密钥**：建议每2年更新一次
- **API密钥**：根据服务商政策
- **访问令牌**：根据权限需求，建议每年更新

---

## 🚨 安全检查清单

### 每周检查

- [ ] 所有私钥权限是否为600
- [ ] API密钥文件是否在.gitignore中
- [ ] 是否有未加密的敏感文件
- [ ] 凭证清单是否最新

### 每月检查

- [ ] SSH密钥是否需要更新
- [ ] API密钥配额是否充足
- [ ] 访问令牌是否过期
- [ ] 是否需要轮换密钥

---

## 📝 凭证申请流程

### 新增服务器SSH密钥

1. 生成密钥对
2. 将公钥添加到服务器 `~/.ssh/authorized_keys`
3. 测试SSH连接
4. 更新凭证清单
5. 更新SSH配置文件

### 新增API密钥

1. 在服务商平台申请密钥
2. 存储密钥文件到 `credentials/api_keys/`
3. 设置文件权限600
4. 更新 `.env` 文件（使用环境变量）
5. 更新凭证清单

---

**最后更新**: 2026-03-14
**维护人**: AI-Agent-Local
