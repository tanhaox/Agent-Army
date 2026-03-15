# 智谱AI配额分析与路由策略

**日期**: 2026-03-13
**基于**: 智谱季度套餐QPM配额

---

## 📊 智谱AI模型配额分析

### 核心推理模型（按QPM排序）

| 模型 | QPM | 特点 | 适用场景 | 成本 |
|------|-----|------|---------|------|
| **glm-4-flash** | 200 | 最快 | 高并发简单任务 | 套餐内 |
| **glm-4-air** | 100 | 轻量快速 | 日常对话 | 套餐内 |
| **glm-z1-flash** | 30 | 新一代快速 | 通用任务 | 套餐内 |
| **glm-z1-air** | 30 | 新一代轻量 | 通用任务 | 套餐内 |
| **glm-4** | 30 | 标准模型 | 平衡性能 | 套餐内 |
| **glm-4-flashx** | 50 | 增强快速 | 中等复杂度 | 套餐内 |
| **glm-4-plus** | 20 | 最强模型 | 复杂推理 | 套餐内 |
| **glm-4-32b-0414-128k** | 15 | 超长上下文 | 长文档分析 | 套餐内 |
| **glm-4-long** | 10 | 长上下文 | 超长文档 | 套餐内 |

### 搜索能力

| 模型 | QPM | 特点 | 成本 |
|------|-----|------|------|
| **search-std** | 50 | 基础搜索 | 套餐内 |
| **search-pro** | 5 | 高级搜索 | 套餐内 |
| **web-search-pro** | 30 | 联网搜索 | 套餐内 |

### 专项能力

| 模型 | QPM | 特点 | 成本 |
|------|-----|------|------|
| **glm-4v** | 5 | 视觉理解 | 套餐内 |
| **glm-4v-plus** | 5 | 高级视觉 | 套餐内 |
| **codegeex-4** | 50 | 代码生成 | 套餐内 |
| **embedding-3** | 50 | 向量嵌入 | 套餐内 |
| **glm-ocr** | 2 | OCR识别 | 套餐内 |

---

## 🧠 智能路由策略设计

### 路由决策树

```javascript
// 智能路由 - 基于QPM和任务类型
class ZhipuRouter {
  constructor() {
    // 配额管理
    this.quotas = {
      'glm-4-flash': { qpm: 200, used: 0, resetAt: this.nextMinute() },
      'glm-4-air': { qpm: 100, used: 0, resetAt: this.nextMinute() },
      'glm-4': { qpm: 30, used: 0, resetAt: this.nextMinute() },
      'glm-4-plus': { qpm: 20, used: 0, resetAt: this.nextMinute() },
      'glm-4-32b-0414-128k': { qpm: 15, used: 0, resetAt: this.nextMinute() },
      'search-std': { qpm: 50, used: 0, resetAt: this.nextMinute() },
      'web-search-pro': { qpm: 30, used: 0, resetAt: this.nextMinute() },
      'codegeex-4': { qpm: 50, used: 0, resetAt: this.nextMinute() }
    };
  }

  // 主路由函数
  async route(task) {
    // 1. 高并发简单任务 → glm-4-flash (200 QPM)
    if (this.isSimpleTask(task) && this.hasQuota('glm-4-flash')) {
      return {
        model: 'glm-4-flash',
        reason: '简单高并发任务，使用最快模型'
      };
    }

    // 2. 日常对话 → glm-4-air (100 QPM)
    if (task.type === 'chat' && this.hasQuota('glm-4-air')) {
      return {
        model: 'glm-4-air',
        reason: '日常对话，使用轻量快速模型'
      };
    }

    // 3. 需要联网搜索 → web-search-pro (30 QPM)
    if (task.needsWebSearch && this.hasQuota('web-search-pro')) {
      return {
        model: 'glm-4',
        tools: [{ type: 'web_search', web_search: { enable: true } }],
        reason: '需要联网搜索'
      };
    }

    // 4. 代码生成 → codegeex-4 (50 QPM)
    if (task.type === 'code' && this.hasQuota('codegeex-4')) {
      return {
        model: 'codegeex-4',
        reason: '代码生成任务，使用专业代码模型'
      };
    }

    // 5. 长文档分析 → glm-4-32b-0414-128k (15 QPM, 128K上下文)
    if (task.contextLength > 32000 && this.hasQuota('glm-4-32b-0414-128k')) {
      return {
        model: 'glm-4-32b-0414-128k',
        reason: `长文档分析 (${task.contextLength} tokens)，使用超长上下文模型`
      };
    }

    // 6. 复杂推理 → glm-4-plus (20 QPM, 最强模型)
    if (task.complexity === 'high' && this.hasQuota('glm-4-plus')) {
      return {
        model: 'glm-4-plus',
        reason: '复杂推理任务，使用最强模型'
      };
    }

    // 7. 默认 → glm-4 (30 QPM, 平衡选择)
    return {
      model: 'glm-4',
      reason: '默认使用标准模型'
    };
  }

  // 检查配额
  hasQuota(model) {
    const quota = this.quotas[model];
    if (!quota) return true; // 没有限制的模型

    // 每分钟重置
    if (Date.now() > quota.resetAt) {
      quota.used = 0;
      quota.resetAt = this.nextMinute();
    }

    return quota.used < quota.qpm;
  }

  // 使用配额
  useQuota(model) {
    if (this.quotas[model]) {
      this.quotas[model].used++;
    }
  }

  nextMinute() {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 1);
    now.setSeconds(0);
    return now.getTime();
  }

  isSimpleTask(task) {
    return (
      task.message?.length < 500 ||  // 短消息
      task.type === 'simple' ||       // 明确标记
      !task.needsReasoning            // 不需要推理
    );
  }
}
```

### 路由表总结

| 任务类型 | 首选模型 | 备选模型 | QPM | 说明 |
|---------|---------|---------|-----|------|
| 简单问答 | glm-4-flash | glm-4-air | 200 | 高并发 |
| 日常对话 | glm-4-air | glm-4 | 100 | 轻量快速 |
| 代码生成 | codegeex-4 | glm-4 | 50 | 专业代码模型 |
| 需要搜索 | glm-4 + web-search-pro | - | 30 | 联网搜索 |
| 复杂推理 | glm-4-plus | glm-4 | 20 | 最强模型 |
| 长文档 | glm-4-32b-0414-128k | glm-4-long | 15 | 128K上下文 |
| 视觉理解 | glm-4v-plus | glm-4v | 5 | 图像分析 |
| OCR识别 | glm-ocr | - | 2 | 文字识别 |
| 向量嵌入 | embedding-3 | - | 50 | 向量化 |

---

## 🚦 限流和队列策略

### 配额管理器

```javascript
// 配额管理 - 防止超限
class QuotaManager {
  constructor() {
    this.redis = new Redis({
      host: 'localhost',
      port: 6379,
      db: 0  // 使用阿里云Redis
    });
  }

  // 获取当前使用量
  async getCurrentUsage(model) {
    const key = `quota:zhipu:${model}:${this.getMinuteKey()}`;
    const usage = await this.redis.get(key);
    return parseInt(usage || '0');
  }

  // 检查是否可用
  async isAvailable(model) {
    const quotas = {
      'glm-4-flash': 200,
      'glm-4-air': 100,
      'glm-4': 30,
      'glm-4-plus': 20,
      'search-std': 50,
      'web-search-pro': 30,
      'codegeex-4': 50
    };

    const qpm = quotas[model];
    if (!qpm) return true;  // 没有限制

    const usage = await this.getCurrentUsage(model);
    return usage < qpm;
  }

  // 增加使用量
  async incrementUsage(model) {
    const key = `quota:zhipu:${model}:${this.getMinuteKey()}`;
    await this.redis.incr(key);
    await this.redis.expire(key, 60);  // 60秒后过期
  }

  // 获取分钟级key
  getMinuteKey() {
    const now = new Date();
    return `${now.getHours()}:${now.getMinutes()}`;
  }

  // 等待配额（队列机制）
  async waitForQuota(model, maxWait = 60000) {
    const startTime = Date.now();

    while (Date.now() - startTime < maxWait) {
      if (await this.isAvailable(model)) {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    throw new Error(`等待${model}配额超时`);
  }
}
```

### 请求队列

```javascript
// 请求队列 - 处理配额耗尽情况
class RequestQueue {
  constructor() {
    this.queues = {
      high: [],     // 高优先级（glm-4-plus）
      normal: [],   // 普通优先级（glm-4）
      low: []       // 低优先级（glm-4-flash）
    };
    this.processing = false;
  }

  // 添加请求
  async enqueue(request, priority = 'normal') {
    return new Promise((resolve, reject) => {
      this.queues[priority].push({
        request,
        resolve,
        reject,
        timestamp: Date.now()
      });

      this.process();
    });
  }

  // 处理队列
  async process() {
    if (this.processing) return;
    this.processing = true;

    while (this.hasQueuedRequests()) {
      // 按优先级处理
      for (const priority of ['high', 'normal', 'low']) {
        if (this.queues[priority].length > 0) {
          const item = this.queues[priority].shift();

          try {
            // 检查配额
            const quotaManager = new QuotaManager();
            const model = item.request.model;

            if (await quotaManager.isAvailable(model)) {
              // 执行请求
              const result = await this.executeRequest(item.request);
              item.resolve(result);
              await quotaManager.incrementUsage(model);
            } else {
              // 配额不足，重新入队
              this.queues[priority].unshift(item);
              await new Promise(resolve => setTimeout(resolve, 1000));
            }
          } catch (error) {
            item.reject(error);
          }
        }
      }
    }

    this.processing = false;
  }

  hasQueuedRequests() {
    return this.queues.high.length > 0 ||
           this.queues.normal.length > 0 ||
           this.queues.low.length > 0;
  }

  async executeRequest(request) {
    // 实际API调用
    const response = await fetch('https://open.bigmodel.cn/api/paas/v4/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.ZHIPU_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(request)
    });
    return response.json();
  }
}
```

---

## 📈 性能优化建议

### 1. 模型选择策略

```javascript
// 根据并发压力动态调整
class AdaptiveRouter {
  async route(task) {
    const currentLoad = await this.getCurrentLoad();

    // 低负载时优先使用高质量模型
    if (currentLoad < 0.5) {
      return 'glm-4-plus';  // 使用最佳模型
    }

    // 高负载时使用快速模型
    if (currentLoad > 0.8) {
      return 'glm-4-flash';  // 使用最快模型
    }

    // 中等负载使用平衡模型
    return 'glm-4';
  }

  async getCurrentLoad() {
    const quotaManager = new QuotaManager();
    const flashUsage = await quotaManager.getCurrentUsage('glm-4-flash');
    return flashUsage / 200;  // 200是glm-4-flash的QPM
  }
}
```

### 2. 缓存策略

```javascript
// 缓存常见问题，减少API调用
class CacheManager {
  constructor() {
    this.redis = new Redis({ host: 'localhost', port: 6379 });
  }

  // 生成缓存key
  getCacheKey(model, messages) {
    const content = JSON.stringify({ model, messages });
    return crypto.createHash('md5').update(content).digest('hex');
  }

  // 获取缓存
  async get(model, messages) {
    const key = this.getCacheKey(model, messages);
    const cached = await this.redis.get(`cache:${key}`);
    if (cached) {
      console.log('缓存命中');
      return JSON.parse(cached);
    }
  }

  // 设置缓存
  async set(model, messages, result, ttl = 3600) {
    const key = this.getCacheKey(model, messages);
    await this.redis.setex(`cache:${key}`, ttl, JSON.stringify(result));
  }
}
```

### 3. 批处理优化

```javascript
// 批量请求合并
class BatchProcessor {
  constructor(batchSize = 10, maxWait = 1000) {
    this.batch = [];
    this.batchSize = batchSize;
    this.maxWait = maxWait;
  }

  // 添加到批次
  async add(request) {
    return new Promise((resolve) => {
      this.batch.push({ request, resolve });

      if (this.batch.length >= this.batchSize) {
        this.flush();
      } else {
        // 超时自动刷新
        setTimeout(() => this.flush(), this.maxWait);
      }
    });
  }

  // 执行批次
  async flush() {
    if (this.batch.length === 0) return;

    const requests = this.batch.splice(0);

    // 批量调用（如果API支持）
    // 智谱API可能不支持真正的批量，这里是示例
    const results = await Promise.all(
      requests.map(async ({ request }) => {
        const response = await fetch('https://open.bigmodel.cn/api/paas/v4/chat/completions', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${process.env.ZHIPU_API_KEY}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(request)
        });
        return response.json();
      })
    );

    // 返回结果
    requests.forEach((item, index) => {
      item.resolve(results[index]);
    });
  }
}
```

---

## 🎯 完整的API客户端

```typescript
// /var/www/miaoying/src/lib/zhipu-client.ts
import { Redis } from 'ioredis';

interface ZhipuRequest {
  model: string;
  messages: Array<{ role: string; content: string | Array<any> }>;
  tools?: any[];
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
}

export class ZhipuClient {
  private redis: Redis;
  private apiKey: string;
  private baseUrl = 'https://open.bigmodel.cn/api/paas/v4';

  constructor() {
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379')
    });
    this.apiKey = process.env.ZHIPU_API_KEY!;
  }

  // 智能调用
  async chat(request: ZhipuRequest) {
    // 1. 检查缓存
    const cached = await this.checkCache(request);
    if (cached) return cached;

    // 2. 选择模型
    const model = request.model || await this.selectModel(request);

    // 3. 检查配额
    await this.waitForQuota(model);

    // 4. 调用API
    const response = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ...request,
        model
      })
    });

    const result = await response.json();

    // 5. 缓存结果
    await this.setCache(request, result);

    // 6. 记录使用
    await this.recordUsage(model);

    return result;
  }

  // 模型选择
  async selectModel(request: ZhipuRequest) {
    const message = request.messages[request.messages.length - 1]?.content as string;

    // 简单任务
    if (message && message.length < 500) {
      return 'glm-4-flash';
    }

    // 需要工具（搜索等）
    if (request.tools && request.tools.length > 0) {
      return 'glm-4';
    }

    // 默认
    return 'glm-4';
  }

  // 检查配额
  async waitForQuota(model: string) {
    const quotas: Record<string, number> = {
      'glm-4-flash': 200,
      'glm-4-air': 100,
      'glm-4': 30,
      'glm-4-plus': 20
    };

    const qpm = quotas[model];
    if (!qpm) return;

    const key = `quota:${model}:${this.getMinuteKey()}`;
    const usage = parseInt(await this.redis.get(key) || '0');

    if (usage >= qpm) {
      // 等待下一个分钟
      await new Promise(resolve => setTimeout(resolve, 60000 - (Date.now() % 60000)));
    }
  }

  // 记录使用
  async recordUsage(model: string) {
    const key = `quota:${model}:${this.getMinuteKey()}`;
    await this.redis.incr(key);
    await this.redis.expire(key, 60);
  }

  getMinuteKey() {
    const now = new Date();
    return `${now.getHours()}:${now.getMinutes()}`;
  }

  // 缓存操作
  async checkCache(request: ZhipuRequest) {
    const key = this.getCacheKey(request);
    const cached = await this.redis.get(`cache:${key}`);
    return cached ? JSON.parse(cached) : null;
  }

  async setCache(request: ZhipuRequest, result: any) {
    const key = this.getCacheKey(request);
    await this.redis.setex(`cache:${key}`, 3600, JSON.stringify(result));
  }

  getCacheKey(request: ZhipuRequest) {
    const crypto = require('crypto');
    const content = JSON.stringify(request);
    return crypto.createHash('md5').update(content).digest('hex');
  }
}

// 导出单例
export const zhipuClient = new ZhipuClient();
```

---

## 📊 配额使用监控

```typescript
// 配额监控仪表板
export class QuotaMonitor {
  async getUsageStats() {
    const redis = new Redis({ host: 'localhost', port: 6379 });
    const now = new Date();

    const models = ['glm-4-flash', 'glm-4-air', 'glm-4', 'glm-4-plus', 'web-search-pro'];
    const stats = {};

    for (const model of models) {
      // 当前分钟使用量
      const currentKey = `quota:${model}:${now.getHours()}:${now.getMinutes()}`;
      const current = parseInt(await redis.get(currentKey) || '0');

      // 上分钟使用量
      const lastMin = new Date(now.getTime() - 60000);
      const lastKey = `quota:${model}:${lastMin.getHours()}:${lastMin.getMinutes()}`;
      const last = parseInt(await redis.get(lastKey) || '0');

      // 获取配额限制
      const qpm = this.getQPM(model);

      stats[model] = {
        current,
        last,
        qpm,
        usage: `${current}/${qpm}`,
        percentage: Math.round((current / qpm) * 100)
      };
    }

    return stats;
  }

  getQPM(model: string): number {
    const quotas: Record<string, number> = {
      'glm-4-flash': 200,
      'glm-4-air': 100,
      'glm-4': 30,
      'glm-4-plus': 20,
      'web-search-pro': 30
    };
    return quotas[model] || 0;
  }
}
```

---

## ✅ 总结

基于智谱AI的QPM配额，我们可以：

1. **充分利用高QPM模型**：glm-4-flash (200 QPM) 用于高并发简单任务
2. **智能降级**：当主模型配额耗尽时自动切换到备用模型
3. **队列管理**：处理配额耗尽时的请求排队
4. **缓存优化**：减少重复请求
5. **实时监控**：跟踪各模型配额使用情况

**继续回答其他问题，请提供：**
2. 智联网搜索配额详情
3. 阿里云服务器配置
4. Neo4j/Qdrant部署需求
5. 国外服务器用途
