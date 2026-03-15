# DeepSeek API使用策略

**日期**: 2026-03-14
**用途**: 补充智谱Max套餐，处理高并发和轻量级任务

---

## 📊 DeepSeek计费详情

### 模型配置

| 配置项 | deepseek-chat | deepseek-reasoner |
|--------|--------------|------------------|
| **模型版本** | DeepSeek-V3.2 (非思考模式) | DeepSeek-V3.2 (思考模式) |
| **上下文长度** | 128K | 128K |
| **输出长度** | 默认4K，最大8K | 默认32K，最大64K |
| **JSON输出** | ✅ 支持 | ✅ 支持 |
| **Tool Calls** | ✅ 支持 | ✅ 支持 |
| **FIM补全** | ✅ 支持 | ❌ 不支持 |

### 价格体系

```
┌─────────────────────────────────────────────────────────────┐
│                  DeepSeek 价格（百万tokens）                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  输入（缓存命中）：  0.2元 💰 最便宜！                       │
│  输入（缓存未命中）：2元                                      │
│  输出：              3元                                      │
│                                                             │
│  成本对比（100万tokens）：                                   │
│  ├─ 缓存命中：  0.2 + 3 = 3.2元                             │
│  └─ 缓存未命中：2 + 3 = 5元                                  │
│                                                             │
│  vs 智谱GLM-4（Max套餐）：¥0（已付费）                       │
│  vs OpenAI GPT-4：~¥150                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 DeepSeek vs 智谱 使用场景

### 智谱GLM-4（主力）

```
适用场景：
✅ 复杂推理任务
✅ 需要联网搜索（搜索包9954次）
✅ 长文档分析（128K上下文）
✅ 代码生成（CodeGeeX-4）
✅ 多轮对话（需要上下文连贯）
✅ 专业领域（医疗、法律、金融）

优势：
- 季度套餐，几乎无限使用
- 联网搜索能力强
- 中文理解能力强
- 多种专业模型

劣势：
- 有QPM限制（30次/分钟）
- 有5小时配额（1600次）
- 周配额（8000次）
```

### DeepSeek（补充）

```
适用场景：
✅ 简单问答（FAQ、常识）
✅ 高并发场景（用户量大）
✅ 文本摘要（短文本）
✅ 格式转换（JSON、Markdown）
✅ 简单翻译
✅ 数据提取（从文本提取信息）

优势：
- 缓存命中极便宜（0.2元/百万tokens）
- 无QPM限制（推测）
- 支持Tool Calls
- 响应速度快

劣势：
- 需要单独计费
- 复杂推理不如智谱
- 无联网搜索
```

---

## 🔄 智能路由策略

### 双引擎路由逻辑

```javascript
// 智能路由：智谱 + DeepSeek
class DualEngineRouter {
  constructor() {
    this.zhipuQuota = new ZhipuQuotaManager();
    this.deepseekCache = new DeepSeekCacheManager();
  }

  /**
   * 智能路由决策
   */
  async route(request) {
    const { query, context, userTier } = request;

    // 1. 检查智谱配额
    const zhipuStatus = await this.zhipuQuota.getStatus();

    // 2. 任务分类
    const taskType = this.classifyTask(query, context);

    // 3. 路由决策
    switch (taskType) {
      case 'simple_qa':
        // 简单问答 → DeepSeek（缓存友好）
        return this.routeToDeepSeek(query, 'cache_optimized');

      case 'complex_reasoning':
        // 复杂推理 → 智谱
        return this.routeToZhipu(query, 'glm-4-plus');

      case 'web_search':
        // 联网搜索 → 智谱（独有能力）
        return this.routeToZhipu(query, 'web-search-pro');

      case 'code_generation':
        // 代码生成 → 智谱CodeGeeX
        return this.routeToZhipu(query, 'codegeex-4');

      case 'high_concurrency':
        // 高并发 → DeepSeek（无QPM限制）
        if (zhipuStatus.currentQPM > 25) {  // 智谱QPM快用完了
          return this.routeToDeepSeek(query, 'load_balancing');
        }
        return this.routeToZhipu(query, 'glm-4');

      case 'long_document':
        // 长文档 → 智谱（128K上下文）
        return this.routeToZhipu(query, 'glm-4-long');

      default:
        // 默认 → 智谱（已付费，免费）
        return this.routeToZhipu(query, 'glm-4');
    }
  }

  /**
   * 任务分类
   */
  classifyTask(query, context) {
    const queryLength = query.length;
    const hasComplexKeywords = this.hasComplexKeywords(query);
    const needsSearch = this.needsWebSearch(query);

    // 1. 需要联网搜索
    if (needsSearch) {
      return 'web_search';
    }

    // 2. 复杂推理
    if (hasComplexKeywords || context.complexity === 'high') {
      return 'complex_reasoning';
    }

    // 3. 代码生成
    if (this.isCodeRequest(query)) {
      return 'code_generation';
    }

    // 4. 长文档
    if (queryLength > 10000 || context.hasLongContext) {
      return 'long_document';
    }

    // 5. 简单问答
    if (queryLength < 500 && !hasComplexKeywords) {
      return 'simple_qa';
    }

    // 6. 默认
    return 'general';
  }

  /**
   * 检测复杂关键词
   */
  hasComplexKeywords(query) {
    const complexKeywords = [
      '分析', '推理', '为什么', '如何理解',
      '对比', '评估', '优化', '设计',
      'analyze', 'reasoning', 'why', 'how'
    ];
    return complexKeywords.some(kw => query.includes(kw));
  }

  /**
   * 检测是否需要联网搜索
   */
  needsWebSearch(query) {
    const searchKeywords = [
      '今天', '最新', '当前', '最近', '实时',
      'today', 'latest', 'current', 'recent'
    ];
    return searchKeywords.some(kw => query.includes(kw));
  }

  /**
   * 检测代码请求
   */
  isCodeRequest(query) {
    const codeKeywords = [
      '代码', '函数', '算法', '编程', '实现',
      'code', 'function', 'algorithm', 'programming'
    ];
    return codeKeywords.some(kw => query.includes(kw));
  }

  /**
   * 路由到智谱
   */
  async routeToZhipu(query, model) {
    // 检查配额
    await this.zhipuQuota.checkQuota(model);

    // 调用智谱API
    const result = await this.callZhipuAPI(query, model);

    // 记录使用
    await this.zhipuQuota.recordUsage(model);

    return result;
  }

  /**
   * 路由到DeepSeek
   */
  async routeToDeepSeek(query, mode) {
    // 检查缓存
    if (mode === 'cache_optimized') {
      const cached = await this.deepseekCache.checkCache(query);
      if (cached) {
        console.log('DeepSeek缓存命中，成本：0元');
        return cached;
      }
    }

    // 调用DeepSeek API
    const result = await this.callDeepSeekAPI(query);

    // 如果是缓存优化模式，存储到缓存
    if (mode === 'cache_optimized') {
      await this.deepseekCache.setCache(query, result);
    }

    return result;
  }
}
```

---

## 📊 成本优化策略

### 场景1：日常使用（低并发）

```
用户请求: 100次/天
├─ 简单问答: 70次 → DeepSeek
│  └─ 成本: ~0.1元/天（缓存命中率高）
├─ 复杂任务: 20次 → 智谱
│  └─ 成本: ¥0（Max套餐）
└─ 联网搜索: 10次 → 智谱
   └─ 成本: ¥0（搜索包）

总计: ~0.1元/天 = 3元/月
```

### 场景2：高并发（用户量大）

```
用户请求: 1000次/小时
├─ 智谱QPM限制: 30次/分钟 = 1800次/小时
│  └─ 可用，但接近上限
│
├─ 策略：
│  ├─ 前1500次/小时 → 智谱（免费）
│  └─ 后500次/小时 → DeepSeek（补充）
│     └─ 成本: ~0.5元/小时
│
└─ 高峰期总成本: ~12元/天 = 360元/月
```

### 场景3：缓存优化

```
DeepSeek缓存策略:

输入缓存命中率提升技巧:
1. 系统提示词统一 → 提高缓存命中率
2. 常见问题标准化 → 提高缓存命中率
3. 用户查询规范化 → 提高缓存命中率

示例:
❌ 差的查询: "帮我翻译一下"（无上下文）
✅ 好的查询: "将以下英文翻译成中文: [text]"

缓存命中率对比:
├─ 无优化: 20% → 成本: 2元/百万tokens
├─ 中等优化: 50% → 成本: 1.1元/百万tokens
└─ 高度优化: 80% → 成本: 0.56元/百万tokens

节省: 高度优化比无优化节省72%成本
```

---

## 🔧 DeepSeek缓存管理器

```javascript
// DeepSeek缓存管理
class DeepSeekCacheManager {
  constructor() {
    this.redis = new Redis({ host: 'localhost', port: 6379 });
  }

  /**
   * 生成缓存key（标准化查询）
   */
  generateCacheKey(query, context = {}) {
    // 1. 标准化查询
    const normalized = this.normalizeQuery(query);

    // 2. 提取关键信息
    const keyInfo = {
      intent: this.extractIntent(normalized),
      entities: this.extractEntities(normalized),
      template: context.template || 'default'
    };

    // 3. 生成hash
    const crypto = require('crypto');
    const hash = crypto
      .createHash('md5')
      .update(JSON.stringify(keyInfo))
      .digest('hex');

    return `deepseek:cache:${hash}`;
  }

  /**
   * 标准化查询（提高缓存命中率）
   */
  normalizeQuery(query) {
    return query
      .toLowerCase()
      .replace(/\s+/g, ' ')
      .replace(/[？?！!。，,]/g, '')
      .trim();
  }

  /**
   * 提取意图
   */
  extractIntent(query) {
    const intents = {
      translation: /翻译|translate/,
      summary: /总结|摘要|summary/,
      extraction: /提取|提取信息|extract/,
      formatting: /格式化|转换|format/,
      qa: /是什么|怎么样|如何/
    };

    for (const [intent, pattern] of Object.entries(intents)) {
      if (pattern.test(query)) {
        return intent;
      }
    }

    return 'general';
  }

  /**
   * 提取实体
   */
  extractEntities(query) {
    // 简单的实体提取（可以用NLP改进）
    const entities = [];

    // 提取数字
    const numbers = query.match(/\d+/g);
    if (numbers) entities.push(...numbers);

    // 提取专有名词（简化版）
    const properNouns = query.match(/[A-Z][a-z]+/g);
    if (properNouns) entities.push(...properNouns);

    return entities;
  }

  /**
   * 检查缓存
   */
  async checkCache(query, context = {}) {
    const key = this.generateCacheKey(query, context);
    const cached = await this.redis.get(key);

    if (cached) {
      console.log('✅ DeepSeek缓存命中');
      return JSON.parse(cached);
    }

    return null;
  }

  /**
   * 设置缓存
   */
  async setCache(query, result, context = {}, ttl = 86400) {
    const key = this.generateCacheKey(query, context);

    await this.redis.setex(
      key,
      ttl,
      JSON.stringify({
        query,
        result,
        timestamp: Date.now()
      })
    );

    console.log('✅ DeepSeek结果已缓存');
  }

  /**
   * 获取缓存统计
   */
  async getCacheStats() {
    const keys = await this.redis.keys('deepseek:cache:*');
    const total = keys.length;

    // 统计命中率（需要额外的计数器）
    const hits = parseInt(await this.redis.get('deepseek:cache:hits') || '0');
    const misses = parseInt(await this.redis.get('deepseek:cache:misses') || '0');
    const hitRate = total > 0 ? (hits / (hits + misses) * 100).toFixed(2) : 0;

    return {
      totalCached: total,
      hits,
      misses,
      hitRate: `${hitRate}%`,
      estimatedSavings: (hits * 0.0018).toFixed(2)  // 假设每次命中节省0.0018元
    };
  }
}
```

---

## 🚀 部署配置

### Next.js集成

```typescript
// /var/www/miaoying/src/lib/dual-engine-client.ts
import { ZhipuClient } from './zhipu-client';
import { DeepSeekClient } from './deepseek-client';
import { DualEngineRouter } from './dual-engine-router';

export class DualEngineClient {
  private zhipu: ZhipuClient;
  private deepseek: DeepSeekClient;
  private router: DualEngineRouter;

  constructor() {
    this.zhipu = new ZhipuClient();
    this.deepseek = new DeepSeekClient();
    this.router = new DualEngineRouter();
  }

  async chat(message: string, context: any = {}) {
    // 1. 路由决策
    const route = await this.router.route({
      query: message,
      context,
      userTier: context.userTier || 'free'
    });

    // 2. 执行请求
    let result;
    switch (route.engine) {
      case 'zhipu':
        result = await this.zhipu.chat(message, route.model);
        break;

      case 'deepseek':
        result = await this.deepseek.chat(message, route.mode);
        break;

      default:
        throw new Error('未知引擎');
    }

    // 3. 记录使用（用于成本分析）
    await this.recordUsage(route.engine, result.usage);

    return result;
  }

  private async recordUsage(engine: string, usage: any) {
    const key = `usage:${engine}:${new Date().toISOString().split('T')[0]}`;
    await this.redis.rpush(key, JSON.stringify({
      timestamp: Date.now(),
      ...usage
    }));
    await this.redis.expire(key, 30 * 24 * 60 * 60);  // 保留30天
  }
}

export const dualEngineClient = new DualEngineClient();
```

### API路由

```typescript
// /var/www/miaoying/src/app/api/chat/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { dualEngineClient } from '@/lib/dual-engine-client';

export async function POST(request: NextRequest) {
  try {
    const { message, context } = await request.json();

    // 使用双引擎客户端
    const result = await dualEngineClient.chat(message, context);

    return NextResponse.json({
      success: true,
      data: result,
      engine: result.engine,  // 返回使用的引擎
      cost: result.cost       // 返回成本（可选）
    });
  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error.message
    }, { status: 500 });
  }
}
```

---

## 📊 成本监控API

```typescript
// /var/www/miaoying/src/app/api/costs/daily/route.ts
import { NextResponse } from 'next/server';
import { Redis } from 'ioredis';

export async function GET() {
  const redis = new Redis({ host: 'localhost', port: 6379 });
  const today = new Date().toISOString().split('T')[0];

  // 获取今日使用情况
  const zhipuUsage = await redis.lrange(`usage:zhipu:${today}`, 0, -1);
  const deepseekUsage = await redis.lrange(`usage:deepseek:${today}`, 0, -1);

  // 计算成本
  const zhipuCost = 0;  // Max套餐已付费
  const deepseekCost = calculateDeepSeekCost(deepseekUsage);

  return NextResponse.json({
    date: today,
    zhipu: {
      requests: zhipuUsage.length,
      cost: zhipuCost
    },
    deepseek: {
      requests: deepseekUsage.length,
      cost: deepseekCost,
      cacheHitRate: await getCacheHitRate()
    },
    total: {
      requests: zhipuUsage.length + deepseekUsage.length,
      cost: deepseekCost
    },
    recommendations: generateRecommendations(zhipuUsage.length, deepseekUsage.length)
  });
}

function calculateDeepSeekCost(usage: string[]) {
  let totalTokens = 0;
  let cacheHits = 0;

  for (const record of usage) {
    const data = JSON.parse(record);
    totalTokens += data.total_tokens || 0;
    if (data.cache_hit) cacheHits++;
  }

  // 假设50%缓存命中率
  const cacheHitRate = usage.length > 0 ? cacheHits / usage.length : 0;
  const avgInputTokens = totalTokens * 0.7;
  const avgOutputTokens = totalTokens * 0.3;

  const inputCost = (avgInputTokens / 1000000) * (cacheHitRate * 0.2 + (1 - cacheHitRate) * 2);
  const outputCost = (avgOutputTokens / 1000000) * 3;

  return inputCost + outputCost;
}

async function getCacheHitRate() {
  const redis = new Redis({ host: 'localhost', port: 6379 });
  const hits = parseInt(await redis.get('deepseek:cache:hits') || '0');
  const misses = parseInt(await redis.get('deepseek:cache:misses') || '0');

  return (hits + misses) > 0 ? (hits / (hits + misses) * 100).toFixed(2) + '%' : '0%';
}

function generateRecommendations(zhipuCount: number, deepseekCount: number) {
  const recommendations = [];

  if (deepseekCount > zhipuCount * 2) {
    recommendations.push('DeepSeek使用比例过高，建议更多使用智谱（已付费）');
  }

  if (deepseekCount > 100) {
    recommendations.push('建议启用DeepSeek缓存优化，可节省70%成本');
  }

  return recommendations;
}
```

---

## ✅ 总结

### DeepSeek使用策略

```
┌─────────────────────────────────────────────────────────────┐
│                  DeepSeek 最佳实践                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ 适用场景:                                               │
│  1. 简单问答（FAQ、常识）                                   │
│  2. 高并发补充（智谱QPM用完时）                             │
│  3. 文本摘要、格式转换                                      │
│  4. 数据提取、简单翻译                                      │
│                                                             │
│  ❌ 不适用场景:                                             │
│  1. 复杂推理（用智谱GLM-4-Plus）                           │
│  2. 需要联网搜索（智谱独有）                                │
│  3. 代码生成（用智谱CodeGeeX-4）                           │
│  4. 长文档分析（用智谱GLM-4-Long）                         │
│                                                             │
│  💰 成本优化:                                               │
│  1. 缓存命中率提升到80% → 节省72%成本                      │
│  2. 标准化查询 → 提高缓存命中率                            │
│  3. 统一系统提示词 → 提高缓存命中率                        │
│                                                             │
│  📊 推荐配比:                                               │
│  - 智谱: 70%（主力，免费）                                 │
│  - DeepSeek: 30%（补充，便宜）                             │
│                                                             │
│  💵 月度成本估算:                                           │
│  - 低并发（100次/天）: ~3元/月                             │
│  - 中并发（500次/天）: ~15元/月                            │
│  - 高并发（1000次/天）: ~30元/月                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 双引擎协同优势

```
智谱 + DeepSeek = 最佳性价比

智谱Max套餐:
- 几乎无限token（季度套餐）
- 联网搜索（9954次）
- 专业模型（代码、医疗等）
- 成本: 已付费

DeepSeek:
- 缓存极便宜（0.2元/百万tokens）
- 无QPM限制
- 响应快
- 成本: 按需付费

组合策略:
- 主力用智谱（免费）
- 补充用DeepSeek（便宜）
- 总成本: 最低
```

---

**准备好集成DeepSeek了吗？**
