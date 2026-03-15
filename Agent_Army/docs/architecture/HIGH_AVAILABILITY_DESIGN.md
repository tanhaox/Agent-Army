# 高可用架构设计：本地断电降级方案

**问题**: 本地笔记本断电后，系统是否崩溃？

**答案**: **不会！系统会自动降级到备用方案**

---

## 🛡️ 降级策略：多层保障

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI推理服务优先级（自动切换）                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  第1优先级: 本地Ollama (RTX 4060)                               │
│  ├─ 优点: 免费、快速                                           │
│  ├─ 缺点: 本地断电后不可用                                     │
│  └─ 降级条件: 连接失败 或 笔记本关机                           │
│                                                                 │
│  第2优先级: 国外服务器Ollama (备用)                             │
│  ├─ 优点: 仍然免费、7x24在线                                   │
│  ├─ 缺点: 稍慢（跨国延迟）                                     │
│  └─ 降级条件: 连接失败                                         │
│                                                                 │
│  第3优先级: DeepSeek API (国内便宜)                            │
│  ├─ 优点: 稳定、便宜                                           │
│  ├─ 缺点: 需要付费                                             │
│  └─ 降级条件: API限流 或 余额不足                              │
│                                                                 │
│  第4优先级: OpenAI API (最贵但最稳定)                          │
│  ├─ 优点: 质量最高、最稳定                                     │
│  ├─ 缺点: 昂贵                                                 │
│  └─ 兜底方案: 永不降级                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 自动降级代码实现

```javascript
// /var/www/miaoying/src/lib/ai-client.ts
// 国内服务器上的智能AI客户端

interface AIProvider {
  name: string;
  call: (prompt: string) => Promise<string>;
  isAvailable: () => Promise<boolean>;
}

class AIClient {
  private providers: AIProvider[] = [
    {
      name: '本地Ollama',
      call: async (prompt) => {
        const response = await fetch('http://笔记本IP:11434/api/generate', {
          method: 'POST',
          body: JSON.stringify({
            model: 'llama3.2',
            prompt,
            stream: false
          })
        });
        return response.json();
      },
      isAvailable: async () => {
        try {
          await fetch('http://笔记本IP:11434/api/tags', {
            signal: AbortSignal.timeout(2000) // 2秒超时
          });
          return true;
        } catch {
          return false;
        }
      }
    },

    {
      name: '国外Ollama备用',
      call: async (prompt) => {
        const response = await fetch('http://国外服务器IP:11434/api/generate', {
          method: 'POST',
          body: JSON.stringify({
            model: 'llama3.2',
            prompt,
            stream: false
          })
        });
        return response.json();
      },
      isAvailable: async () => {
        try {
          await fetch('http://国外服务器IP:11434/api/tags', {
            signal: AbortSignal.timeout(3000)
          });
          return true;
        } catch {
          return false;
        }
      }
    },

    {
      name: 'DeepSeek API',
      call: async (prompt) => {
        const response = await fetch('https://api.deepseek.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${process.env.DEEPSEEK_API_KEY}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: 'deepseek-chat',
            messages: [{ role: 'user', content: prompt }]
          })
        });
        return response.json();
      },
      isAvailable: async () => {
        // API服务总是可用的，除非余额不足
        return true;
      }
    },

    {
      name: 'OpenAI API (兜底)',
      call: async (prompt) => {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: 'gpt-4o-mini',
            messages: [{ role: 'user', content: prompt }]
          })
        });
        return response.json();
      },
      isAvailable: async () => {
        return true; // 永远兜底
      }
    }
  ];

  async callAI(prompt: string): Promise<string> {
    const errors = [];

    // 按优先级尝试每个provider
    for (const provider of this.providers) {
      try {
        // 检查是否可用
        const available = await provider.isAvailable();
        if (!available) {
          console.log(`${provider.name} 不可用，跳过`);
          continue;
        }

        // 尝试调用
        console.log(`尝试使用 ${provider.name}...`);
        const result = await provider.call(prompt);
        console.log(`✅ ${provider.name} 成功`);

        // 记录使用情况（用于成本分析）
        this.logUsage(provider.name);

        return result;

      } catch (error) {
        console.error(`❌ ${provider.name} 失败:`, error.message);
        errors.push(`${provider.name}: ${error.message}`);
      }
    }

    // 所有provider都失败
    throw new Error(`所有AI服务均不可用: ${errors.join('; ')}`);
  }

  private logUsage(provider: string) {
    // 记录到Redis或PostgreSQL
    // 用于分析成本和性能
  }
}

// 导出单例
export const aiClient = new AIClient();
```

---

## 📊 各种状态下的系统表现

| 状态 | 本地状态 | 国外状态 | 系统表现 | 成本 |
|------|---------|---------|---------|------|
| **正常** | ✅ 在线 | ✅ 在线 | 使用本地Ollama（免费快） | $0 |
| **本地断电** | ❌ 离线 | ✅ 在线 | 自动切换国外Ollama | $0 |
| **国外也挂** | ❌ 离线 | ❌ 离线 | 自动切换DeepSeek API | ¥ |
| **网络全断** | ❌ 离线 | ❌ 离线 | 使用OpenAI API（最贵但最稳） | $$$ |

---

## 🖥️ 国外服务器部署Ollama（备用）

即使本地断电，国外服务器也可以跑Ollama：

```bash
# SSH到国外服务器
ssh root@国外服务器

# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 拉取模型
ollama pull llama3.2
ollama pull deepseek-coder

# 启动服务（默认后台运行）
ollama serve &

# 验证
curl http://localhost:11434/api/tags
```

**Docker部署方式（推荐）**：

```yaml
# 国外服务器的 docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama-backup
    restart: always
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_KEEP_ALIVE=24h  # 模型常驻内存
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    # 如果国外服务器有GPU，启用GPU加速
    # runtime: nvidia

volumes:
  ollama_data:
```

---

## 🌐 国内服务器也可部署轻量模型

如果国外服务器也没GPU，国内服务器可以部署更轻量的方案：

```yaml
# 国内服务器的 docker-compose.yml
services:
  # 方案1: 使用更小的模型
  ollama-lite:
    image: ollama/ollama:latest
    container_name: ollama-lite
    restart: always
    ports:
      - "11435:11434"
    volumes:
      - ollama_lite_data:/root/.ollama
    command: >
      sh -c "
        ollama serve &
        sleep 5 &&
        ollama pull phi3  # 3B参数，很小
        ollama pull qwen2.5-coder  # 代码专用
      "

  # 方案2: 使用LocalAI（支持更多格式）
  localai:
    image: localai/localai:latest
    container_name: localai
    restart: always
    ports:
      - "8080:8080"
    volumes:
      - ./models:/models
    environment:
      - MODELS_PATH=/models
```

---

## 📈 监控和告警

```javascript
// /var/www/miaoying/src/lib/health-monitor.ts

class HealthMonitor {
  private providers = [
    { name: '本地Ollama', url: 'http://笔记本IP:11434' },
    { name: '国外Ollama', url: 'http://国外IP:11434' },
    { name: 'DeepSeek', url: 'https://api.deepseek.com' },
  ];

  async checkHealth() {
    const status = {};

    for (const provider of this.providers) {
      try {
        const start = Date.now();
        await fetch(provider.url, {
          signal: AbortSignal.timeout(2000)
        });
        status[provider.name] = {
          status: 'healthy',
          latency: Date.now() - start
        };
      } catch (error) {
        status[provider.name] = {
          status: 'down',
          error: error.message
        };

        // 发送告警
        await this.sendAlert(provider.name, error);
      }
    }

    return status;
  }

  async sendAlert(provider: string, error: Error) {
    // 发送到企业微信/钉钉/邮件
    console.log(`🚨 告警: ${provider} 不可用 - ${error.message}`);
  }
}

// 定期检查（每分钟）
setInterval(async () => {
  const monitor = new HealthMonitor();
  await monitor.checkHealth();
}, 60000);
```

---

## 🎯 最终架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     用户请求（不感知后端状态）                   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    国内服务器 (API Gateway)                     │
│                  智能路由 + 自动降级                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            AI客户端（智能选择最优Provider）               │   │
│  │                                                          │   │
│  │  if (本地Ollama可用) → 使用本地（免费）                   │   │
│  │  else if (国外Ollama可用) → 使用国外（免费）              │   │
│  │  else if (DeepSeek可用) → 使用API（便宜）                 │   │
│  │  else → 使用OpenAI（兜底）                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │本地状态  │  │国外状态  │  │API状态   │  │备用状态  │       │
│  │  检查    │  │  检查    │  │  检查    │  │  检查    │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
         │              │              │              │
         │              │              │              │
    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐
    │ 本地    │    │ 国外    │    │ DeepSeek│    │ OpenAI  │
    │ Ollama  │    │ Ollama  │    │  API    │    │  API    │
    │ (可选)  │    │ (备用)  │    │ (便宜)  │    │ (兜底)  │
    └─────────┘    └─────────┘    └─────────┘    └─────────┘
      ──✗──断电       ✅在线        ✅在线        ✅在线
         无影响
```

---

## 💡 关键设计原则

1. **本地Ollama = 成本优化方案，非必需**
   - 有它：省钱（0成本）
   - 没它：系统正常运行，使用备用方案

2. **多层降级 = 永不宕机**
   - 第1层挂了 → 自动切第2层
   - 第2层挂了 → 自动切第3层
   - ...直到兜底方案

3. **对用户透明**
   - 用户不知道用的是哪个AI
   - 只知道"系统能用"

4. **成本可控**
   - 本地在线时：$0
   - 本地离线时：$0.001-0.01/次
   - 可以设置预算告警

---

## 🛠️ 部署步骤

### 1. 国外服务器部署Ollama（一次性）

```bash
# SSH到国外服务器
ssh root@国外服务器IP

# 安装
curl -fsSL https://ollama.com/install.sh | sh

# 下载模型
ollama pull llama3.2

# 后台运行
nohup ollama serve > /dev/null 2>&1 &

# 验证
curl http://localhost:11434/api/tags
```

### 2. 国内服务器配置智能客户端（一次性）

```bash
# 添加配置文件
cat > /var/www/miaoying/.env.ai << EOF
LOCAL_OLLAMA_URL=http://你的笔记本IP:11434
OVERSEAS_OLLAMA_URL=http://国外服务器IP:11434
DEEPSEEK_API_KEY=your-key
OPENAI_API_KEY=your-key
EOF

# 重启服务
pm2 restart miaoying
```

### 3. 测试降级

```bash
# 测试1: 正常状态
curl -X POST http://国内服务器/api/ai/test \
  -d '{"prompt": "test"}'
# 应该返回: 使用本地Ollama

# 测试2: 关闭本地笔记本后
curl -X POST http://国内服务器/api/ai/test \
  -d '{"prompt": "test"}'
# 应该返回: 使用国外Ollama

# 测试3: 关闭国外服务器后
curl -X POST http://国内服务器/api/ai/test \
  -d '{"prompt": "test"}'
# 应该返回: 使用DeepSeek API
```

---

## 📊 成本对比

| 场景 | 使用的AI | 月成本 | 备注 |
|------|----------|--------|------|
| 本地在线 | 本地Ollama | $0 | 免费利用GPU |
| 本地离线 | 国外Ollama | $0 | 还是免费 |
| 两者离线 | DeepSeek API | ¥50-200 | 按使用量 |
| API限流 | OpenAI API | $100-500 | 最贵但最稳 |

---

## ✅ 总结

```
┌─────────────────────────────────────────────────────────┐
│               本地断电 ≠ 系统崩溃                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ❌ 错误认知: 本地Ollama是必需品                         │
│  ✅ 正确认知: 本地Ollama是"省钱插件"                     │
│                                                         │
│  有它: 0成本运行                                        │
│  没它: 自动切换备用方案（仍然可用）                      │
│                                                         │
│  设计原则:                                              │
│  1. 多层降级，永不宕机                                  │
│  2. 对用户透明，无感知切换                              │
│  3. 成本可控，按需使用                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

**需要我帮您在国外服务器上部署Ollama备用吗？**
