# 智谱AI搜索资源包管理（正确版本）

**日期**: 2026-03-14
**更新**: 基于实际购买的搜索资源包

---

## ⚠️ 重要更正

**之前理解错误**：
- ❌ 以为是QPM限制（30次/分钟）
- ❌ 以为是套餐内的频次限制

**实际情况**：
- ✅ 是购买的**搜索资源包**（总次数限制）
- ✅ 按次计费，消耗资源包额度
- ✅ 有时效性限制（半年有效期）

---

## 📊 搜索资源包详情

### 已购买资源包

| 资源包名称 | 适用引擎 | 当前余额 | 购买时间 | 到期时间 | 剩余天数 |
|-----------|---------|---------|---------|---------|---------|
| **Search-Pro** | search-pro | 2,492次 | 2026-03-12 | 2026-09-12 | ~182天 |
| **Search-Pro-Quark** | search-pro-quark | 2,500次 | 2026-03-12 | 2026-09-12 | ~182天 |
| **Search-Std** | search-std | 4,962次 | 2026-03-12 | 2026-09-12 | ~182天 |

**总计**：**9,954次搜索额度**

### 搜索引擎类型和价格

| 搜索引擎 | 特性 | 价格 | 资源包 | 推荐场景 |
|---------|------|------|--------|---------|
| **search_std** | 基础版（智谱自研） | 0.01元/次 | 4962次 | 日常查询、性价比高 |
| **search_pro** | 高级版（多引擎协作） | 0.03元/次 | 2492次 | 精准搜索、降低空结果 |
| **search_pro_sogou** | 搜狗（腾讯生态+知乎） | 0.05元/次 | - | 垂直领域、医疗、百科 |
| **search_pro_quark** | 夸克（垂直内容） | 0.05元/次 | 2500次 | 特定垂直领域 |

### 总价值计算

```
search_std:   4962次 × 0.01元 = 49.62元
search_pro:   2492次 × 0.03元 = 74.76元
search_pro_quark: 2500次 × 0.05元 = 125.00元
─────────────────────────────────────────
总价值:                     249.38元
```

---

## 🧮 使用策略分析

### 时效性压力

```
剩余时间: 182天（约6个月）
剩余额度: 9954次
平均每天可用: 9954 ÷ 182 ≈ 54.7次
平均每小时可用: 54.7 ÷ 24 ≈ 2.3次
```

### 分配策略

| 搜索引擎 | 余额 | 每天使用 | 使用场景 |
|---------|------|---------|---------|
| **search_std** | 4962次 | 27次/天 | 常规查询（主力） |
| **search_pro** | 2492次 | 14次/天 | 重要搜索（精准） |
| **search_pro_quark** | 2500次 | 14次/天 | 垂直领域（专业） |

### 优先级建议

```
┌─────────────────────────────────────────────────────────────┐
│                  搜索引擎选择策略                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣ 默认选择: search_std (0.01元/次)                       │
│     - 余额最多（4962次）                                   │
│     - 性价比最高                                           │
│     - 适用80%的搜索场景                                    │
│                                                             │
│  2️⃣ 精准搜索: search_pro (0.03元/次)                       │
│     - 多引擎协作                                           │
│     - 降低空结果率                                         │
│     - 适用重要查询（15%场景）                              │
│                                                             │
│  3️⃣ 垂直领域: search_pro_quark (0.05元/次)                 │
│     - 专业内容                                             │
│     - 特定领域                                             │
│     - 适用专业查询（5%场景）                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 资源包管理系统

### 资源包追踪器

```javascript
// 智谱AI搜索资源包管理
class SearchResourceManager {
  constructor() {
    this.redis = new Redis({ host: 'localhost', port: 6379 });

    // 资源包配置
    this.resourcePacks = {
      'search_std': {
        balance: 4962,
        price: 0.01,
        expiresAt: new Date('2026-09-12'),
        description: '基础版搜索'
      },
      'search_pro': {
        balance: 2492,
        price: 0.03,
        expiresAt: new Date('2026-09-12'),
        description: '高级版搜索'
      },
      'search_pro_quark': {
        balance: 2500,
        price: 0.05,
        expiresAt: new Date('202-09-12'),
        description: '夸克垂直搜索'
      }
    };

    // 初始化Redis数据
    this.initializeBalances();
  }

  /**
   * 初始化余额到Redis
   */
  async initializeBalances() {
    for (const [engine, config] of Object.entries(this.resourcePacks)) {
      const key = `search:balance:${engine}`;
      const exists = await this.redis.exists(key);

      if (!exists) {
        await this.redis.set(key, config.balance);
        console.log(`初始化 ${engine} 余额: ${config.balance}次`);
      }
    }
  }

  /**
   * 选择最优搜索引擎
   */
  async selectEngine(query, context = {}) {
    // 1. 检查是否有专业领域关键词
    const professionalKeywords = {
      medical: ['医疗', '健康', '药物', '症状', 'medical', 'health'],
      encyclopedia: ['百科', '定义', '是什么', 'what is'],
      vertical: ['专业', '行业', '报告', '研究']
    };

    // 医疗健康 → 搜狗（但没买sogou包，用quark代替）
    if (professionalKeywords.medical.some(kw => query.includes(kw))) {
      const balance = await this.getBalance('search_pro_quark');
      if (balance > 0) {
        return {
          engine: 'search_pro_quark',
          reason: '医疗健康领域，使用夸克垂直搜索'
        };
      }
    }

    // 专业领域 → 夸克
    if (professionalKeywords.vertical.some(kw => query.includes(kw))) {
      const balance = await this.getBalance('search_pro_quark');
      if (balance > 0) {
        return {
          engine: 'search_pro_quark',
          reason: '专业领域查询，使用夸克搜索'
        };
      }
    }

    // 重要查询 → 高级版
    if (context.importance === 'high' || context.requiresAccuracy) {
      const balance = await this.getBalance('search_pro');
      if (balance > 0) {
        return {
          engine: 'search_pro',
          reason: '重要查询，使用高级版提高准确率'
        };
      }
    }

    // 默认 → 基础版
    const stdBalance = await this.getBalance('search_std');
    if (stdBalance > 0) {
      return {
        engine: 'search_std',
        reason: '常规查询，使用基础版（性价比高）'
      };
    }

    // 降级：选择任意有余额的引擎
    for (const engine of ['search_pro', 'search_pro_quark']) {
      const balance = await this.getBalance(engine);
      if (balance > 0) {
        return {
          engine,
          reason: '基础版余额不足，降级使用其他引擎'
        };
      }
    }

    throw new Error('所有搜索资源包余额已用完');
  }

  /**
   * 执行搜索（自动选择引擎）
   */
  async search(query, context = {}) {
    // 1. 检查缓存
    const cached = await this.checkCache(query);
    if (cached) {
      console.log('✅ 缓存命中，节省搜索额度');
      return cached;
    }

    // 2. 选择搜索引擎
    const { engine, reason } = await this.selectEngine(query, context);
    console.log(`🔍 使用 ${engine}: ${reason}`);

    // 3. 检查余额
    const balance = await this.getBalance(engine);
    if (balance <= 0) {
      throw new Error(`${engine} 余额不足`);
    }

    // 4. 调用智谱API
    const result = await this.callZhipuSearch(query, engine);

    // 5. 扣除余额
    await this.deductBalance(engine, 1);

    // 6. 缓存结果
    await this.setCache(query, result);

    // 7. 记录使用日志
    await this.logUsage(engine, query);

    return result;
  }

  /**
   * 获取余额
   */
  async getBalance(engine) {
    const key = `search:balance:${engine}`;
    const balance = await this.redis.get(key);
    return parseInt(balance || '0');
  }

  /**
   * 扣除余额
   */
  async deductBalance(engine, count = 1) {
    const key = `search:balance:${engine}`;
    const balance = await this.getBalance(engine);

    if (balance < count) {
      throw new Error(`${engine} 余额不足`);
    }

    await this.redis.decrby(key, count);
    console.log(`💰 ${engine} 余额: ${balance} → ${balance - count}`);
  }

  /**
   * 调用智谱搜索API
   */
  async callZhipuSearch(query, engine) {
    const response = await fetch('https://open.bigmodel.cn/api/paas/v4/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.ZHIPU_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'glm-4',
        messages: [
          {
            role: 'user',
            content: query
          }
        ],
        tools: [
          {
            type: 'web_search',
            web_search: {
              enable: true,
              search_result: true,
              search_engine: engine  // 指定搜索引擎
            }
          }
        ]
      })
    });

    if (!response.ok) {
      throw new Error(`智谱API调用失败: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * 检查缓存
   */
  async checkCache(query) {
    const key = `cache:search:${this.hashQuery(query)}`;
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  /**
   * 设置缓存
   */
  async setCache(query, result, ttl = 3600) {
    const key = `cache:search:${this.hashQuery(query)}`;
    await this.redis.setex(key, ttl, JSON.stringify(result));
  }

  /**
   * 记录使用日志
   */
  async logUsage(engine, query) {
    const key = `search:usage:${engine}:${new Date().toISOString().split('T')[0]}`;
    await this.redis.rpush(key, JSON.stringify({
      query,
      timestamp: Date.now()
    }));
    await this.redis.expire(key, 30 * 24 * 60 * 60);  // 保留30天
  }

  /**
   * 获取使用统计
   */
  async getStats() {
    const stats = {};

    for (const engine of Object.keys(this.resourcePacks)) {
      const balance = await this.getBalance(engine);
      const initial = this.resourcePacks[engine].balance;
      const used = initial - balance;
      const percentage = Math.round((used / initial) * 100);

      // 计算剩余天数
      const now = new Date();
      const expiresAt = this.resourcePacks[engine].expiresAt;
      const daysLeft = Math.ceil((expiresAt - now) / (24 * 60 * 60 * 1000));

      // 计算每日推荐使用量
      const dailyRecommended = Math.ceil(balance / daysLeft);

      stats[engine] = {
        balance,
        initial,
        used,
        percentage,
        daysLeft,
        dailyRecommended,
        value: (balance * this.resourcePacks[engine].price).toFixed(2)
      };
    }

    // 总计
    const totalBalance = Object.values(stats).reduce((sum, s) => sum + s.balance, 0);
    const totalValue = Object.values(stats).reduce((sum, s) => sum + parseFloat(s.value), 0);

    stats.total = {
      balance: totalBalance,
      value: totalValue.toFixed(2),
      daysLeft: stats.search_std.daysLeft
    };

    return stats;
  }

  hashQuery(query) {
    const crypto = require('crypto');
    return crypto.createHash('md5').update(query).digest('hex');
  }
}

export const searchResourceManager = new SearchResourceManager();
```

---

## 📊 监控API

```typescript
// /var/www/miaoying/src/app/api/search/stats/route.ts
import { NextResponse } from 'next/server';
import { searchResourceManager } from '@/lib/search-resource-manager';

export async function GET() {
  try {
    const stats = await searchResourceManager.getStats();

    // 告警条件
    const alerts = [];

    // 余额告警
    for (const [engine, data] of Object.entries(stats)) {
      if (engine === 'total') continue;

      if (data.percentage > 80) {
        alerts.push({
          engine,
          type: 'balance_low',
          message: `${engine} 使用已超过80%，剩余${data.balance}次`
        });
      }

      if (data.daysLeft < 30) {
        alerts.push({
          engine,
          type: 'expiring_soon',
          message: `${engine} 将在${data.daysLeft}天后过期，剩余${data.balance}次`
        });
      }
    }

    return NextResponse.json({
      success: true,
      data: stats,
      alerts,
      recommendations: {
        dailyUsage: `建议每天使用${Math.ceil(stats.total.balance / stats.total.daysLeft)}次以内`,
        cacheStrategy: '启用缓存可节省30-50%搜索额度',
        enginePriority: '优先使用search_std（性价比最高）'
      }
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

## 🎯 高效使用策略

### 1. 缓存优先

```javascript
// 多级缓存策略
const CACHE_STRATEGY = {
  // 静态内容：缓存24小时
  static: {
    ttl: 86400,
    keywords: ['定义', '百科', '是什么', '历史']
  },

  // 半静态：缓存6小时
  semiStatic: {
    ttl: 21600,
    keywords: ['教程', '指南', '方法']
  },

  // 动态内容：缓存1小时
  dynamic: {
    ttl: 3600,
    keywords: ['新闻', '最新', '今天']
  },

  // 实时内容：缓存5分钟
  realtime: {
    ttl: 300,
    keywords: ['股价', '汇率', '天气']
  }
};

function getCacheTTL(query) {
  for (const [type, config] of Object.entries(CACHE_STRATEGY)) {
    if (config.keywords.some(kw => query.includes(kw))) {
      return config.ttl;
    }
  }
  return 3600;  // 默认1小时
}
```

### 2. 智能合并

```javascript
// 批量搜索合并
class BatchSearchMerger {
  private queue = [];
  private timer = null;

  add(query) {
    return new Promise((resolve) => {
      this.queue.push({ query, resolve });

      // 100ms内的请求合并处理
      if (!this.timer) {
        this.timer = setTimeout(() => this.flush(), 100);
      }
    });
  }

  async flush() {
    const batch = this.queue.splice(0);
    this.timer = null;

    // 去重
    const uniqueQueries = [...new Set(batch.map(b => b.query))];

    // 批量搜索
    const results = await Promise.all(
      uniqueQueries.map(q => searchResourceManager.search(q))
    );

    // 分发结果
    const resultMap = {};
    uniqueQueries.forEach((q, i) => {
      resultMap[q] = results[i];
    });

    batch.forEach(item => {
      item.resolve(resultMap[item.query]);
    });
  }
}
```

### 3. 降级策略

```javascript
// 当资源包即将耗尽时的降级策略
class SearchFallback {
  async search(query) {
    const stats = await searchResourceManager.getStats();

    // 如果总余额 < 1000次，启用严格缓存
    if (stats.total.balance < 1000) {
      // 只对非常新的信息才搜索
      const needsSearch = this.checkIfNeedsSearch(query);
      if (!needsSearch) {
        return this.useModelKnowledge(query);
      }
    }

    // 如果总余额 < 500次，完全停止搜索
    if (stats.total.balance < 500) {
      console.warn('⚠️ 搜索资源包余额不足，已停止搜索');
      return this.useModelKnowledge(query);
    }

    // 正常搜索
    return searchResourceManager.search(query);
  }

  checkIfNeedsSearch(query) {
    const realtimeKeywords = ['今天', '最新', '当前', 'now', 'latest'];
    return realtimeKeywords.some(kw => query.includes(kw));
  }

  async useModelKnowledge(query) {
    // 直接调用模型，不使用搜索
    const response = await fetch('https://open.bigmodel.cn/api/paas/v4/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.ZHIPU_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'glm-4',
        messages: [{ role: 'user', content: query }]
      })
    });
    return response.json();
  }
}
```

---

## ✅ 总结

### 关键信息

```
┌─────────────────────────────────────────────────────────────┐
│                智谱AI搜索资源包（正确理解）                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📦 资源包总额: 9954次搜索                                  │
│  ├─ search_std: 4962次 (0.01元/次) = 49.62元               │
│  ├─ search_pro: 2492次 (0.03元/次) = 74.76元               │
│  └─ search_pro_quark: 2500次 (0.05元/次) = 125.00元        │
│                                                             │
│  ⏰ 有效期: 182天（到2026-09-12）                           │
│  📊 推荐使用: ~55次/天                                      │
│  💰 总价值: 249.38元                                        │
│                                                             │
│  🎯 使用策略:                                               │
│  1. 优先使用search_std（性价比最高）                       │
│  2. 重要查询用search_pro（准确率高）                       │
│  3. 专业领域用search_pro_quark                             │
│  4. 启用缓存节省30-50%额度                                 │
│  5. 批量合并减少重复搜索                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 立即行动

1. ✅ 部署资源包管理系统
2. ✅ 配置缓存策略（节省额度）
3. ✅ 设置余额告警（低于1000次）
4. ✅ 监控每日使用量（~55次）

---

**继续等待其他问题：**

**3. 阿里云服务器配置（CPU/内存/磁盘）？**
**4. 是否需要在阿里云部署Neo4j和Qdrant？**
**5. 国外服务器的具体用途？**
