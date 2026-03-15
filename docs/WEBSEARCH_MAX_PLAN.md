# 智谱AI Max套餐Token配额管理

**日期**: 2026-03-13
**套餐**: Max套餐（Token总量限制）

---

## ⚠️ 重要说明

**Max套餐限制是Token总量，不是专门针对联网搜索**

联网搜索功能本身在模型列表中显示：
- `web-search-pro`: 30 QPM
- `search-std`: 50 QPM
- `search-pro`: 5 QPM

这些是**搜索工具的调用频率限制**，与Token套餐不同。

---

## 📊 Max套餐Token配额详情

### Token配额规格

| 套餐 | 每5小时限额 | 每周限额 | 说明 |
|------|------------|---------|------|
| **Lite** | ~80次prompts | ~400次prompts | 轻度使用 |
| **Pro** | ~400次prompts | ~2000次prompts | 中度使用 |
| **Max（您）** | **~1600次prompts** | **~8000次prompts** | 重度使用 |

### 关键特性

- ✅ **动态刷新**：5小时后额度自动恢复
- ✅ **周期刷新**：每7天重置
- ✅ **充足配额**：Max套餐是Pro的4倍
- ⚠️ **限制单位**：以"prompts"（请求数）为单位，不是token数

---

## 🧮 双层配额系统

### 第一层：Max套餐Token配额（总体）

```
每5小时: ~1600次 prompts
每周:    ~8000次 prompts

说明: 这是所有API调用的总量限制，包括：
- 普通对话
- 联网搜索
- 代码生成
- 多轮对话
```

### 第二层：联网搜索工具频率限制

| 工具 | QPM限制 | 说明 |
|------|---------|------|
| **web-search-pro** | 30 QPM | 联网搜索主力 |
| **search-std** | 50 QPM | 基础搜索 |
| **search-pro** | 5 QPM | 高级搜索 |

### 实际使用约束

```
联网搜索受两层限制：
1. 不能超过 Max 套餐的总体配额（1600次/5小时）
2. 不能超过 web-search-pro 的 QPM 限制（30次/分钟）
```

### 示例计算

**场景1：持续使用联网搜索**
```
每分钟30次搜索（QPM上限）
    ↓
每小时 30 × 60 = 1800次
    ↓
每5小时 1800 × 5 = 9000次
    ↓
❌ 超过Max套餐的1600次限制

结论：不能一直用QPM上限跑
```

**场景2：合理使用**
```
每分钟5次搜索（合理使用）
    ↓
每小时 5 × 60 = 300次
    ↓
每5小时 300 × 5 = 1500次
    ↓
✅ 在Max套餐限制内（1600次）

结论：平均每分钟5次以内是安全的
```

### 使用场景分析（基于双层限制）

| 使用模式 | 每分钟搜索 | 每5小时总量 | Max套餐 | web-search-pro (30 QPM) |
|---------|-----------|------------|---------|------------------------|
| 极低频 | 0.5次 | 150次 | ✅ 充足 | ✅ 充足 |
| 低频 | 2次 | 600次 | ✅ 充足 | ✅ 充足 |
| **推荐** | **5次** | **1500次** | ✅ 充足 | ✅ 充足 |
| 中频 | 10次 | 3000次 | ⚠️ 超限 | ✅ 充足 |
| 高频 | 20次 | 6000次 | ❌ 超限 | ✅ 充足 |
| 极高频 | 30次 | 9000次 | ❌ 超限 | ⚠️ 达限 |

### 实际应用场景

| 场景 | 每分钟调用 | 每5小时总量 | Max套餐支持 | 建议策略 |
|------|-----------|------------|------------|---------|
| 个人使用 | 1-2次 | 300-600次 | ✅ 充足 | 直接用 |
| 小团队(10人) | 5次 | 1500次 | ✅ 充足 | **推荐** |
| 中团队(50人) | 25次 | 7500次 | ❌ 超限 | 需要缓存 |
| 大规模应用 | 100+次 | 30000+次 | ❌ 超限 | 需要+降级 |

**结论：Max套餐适合个人到小团队使用，大规模应用需要优化策略**

---

## 🔧 双层配额管理实现

### 配额追踪器（更新版）

```javascript
// 双层配额管理：Max套餐 + QPM限制
class DualQuotaManager {
  constructor() {
    this.redis = new Redis({ host: 'localhost', port: 6379 });

    // 第一层：Max套餐配额
    this.maxPlanConfig = {
      per5Hours: 1600,  // 每5小时1600次prompts
      perWeek: 8000,    // 每周8000次prompts
      windowDuration: 5 * 60 * 60 * 1000
    };

    // 第二层：web-search-pro QPM限制
    this.webSearchConfig = {
      qpm: 30,  // 每分钟30次
      windowDuration: 60 * 1000  // 1分钟窗口
    };
  }

  /**
   * 检查是否可以执行请求（双层检查）
   */
  async canRequest(useWebSearch = false) {
    // 1. 检查Max套餐配额
    const maxPlanUsage = await this.getMaxPlanWindowUsage();
    if (maxPlanUsage >= this.maxPlanConfig.per5Hours) {
      const resetTime = await this.getMaxPlanResetTime();
      throw new Error(`Max套餐配额已用完(${maxPlanUsage}/${this.maxPlanConfig.per5Hours})，${resetTime}后恢复`);
    }

    // 2. 如果使用联网搜索，检查QPM限制
    if (useWebSearch) {
      const qpmUsage = await this.getQPMUsage();
      if (qpmUsage >= this.webSearchConfig.qpm) {
        throw new Error(`联网搜索QPM已用完(${qpmUsage}/${this.webSearchConfig.qpm})`);
      }
    }

    return true;
  }

  /**
   * 记录请求使用
   */
  async recordRequest(useWebSearch = false) {
    const now = Date.now();

    // 1. 记录到Max套餐配额（5小时窗口）
    const windowKey = this.getMaxPlanWindowKey();
    await this.redis.zadd(windowKey, now, `${now}`);
    await this.redis.expire(windowKey, 5 * 60 * 60);

    // 2. 如果使用联网搜索，记录QPM
    if (useWebSearch) {
      const qpmKey = this.getQPMKey();
      await this.redis.incr(qpmKey);
      await this.redis.expire(qpmKey, 60);
    }

    // 3. 清理过期记录
    await this.cleanupWindow(windowKey, now - this.maxPlanConfig.windowDuration);
  }

  /**
   * 获取Max套餐5小时窗口使用量
   */
  async getMaxPlanWindowUsage() {
    const windowKey = this.getMaxPlanWindowKey();
    const fiveHoursAgo = Date.now() - this.maxPlanConfig.windowDuration;
    const count = await this.redis.zcount(windowKey, fiveHoursAgo, '+inf');
    return parseInt(count);
  }

  /**
   * 获取QPM使用量（当前分钟）
   */
  async getQPMUsage() {
    const qpmKey = this.getQPMKey();
    const usage = await this.redis.get(qpmKey);
    return parseInt(usage || '0');
  }

  /**
   * 获取Max套餐窗口重置时间
   */
  async getMaxPlanResetTime() {
    const windowKey = this.getMaxPlanWindowKey();
    const oldestRecord = await this.redis.zrange(windowKey, 0, 0, 'WITHSCORES');

    if (oldestRecord.length === 0) {
      return '立即';
    }

    const oldestTime = parseInt(oldestRecord[1]);
    const resetTime = oldestTime + this.maxPlanConfig.windowDuration;
    const minutesLeft = Math.ceil((resetTime - Date.now()) / 60000);

    return `${minutesLeft}分钟`;
  }

  /**
   * 清理窗口中的过期记录
   */
  async cleanupWindow(windowKey, beforeTime) {
    await this.redis.zremrangebyscore(windowKey, '-inf', beforeTime);
  }

  /**
   * 获取Max套餐窗口key
   */
  getMaxPlanWindowKey() {
    return `quota:maxplan:window`;
  }

  /**
   * 获取QPM key（当前分钟）
   */
  getQPMKey() {
    const now = new Date();
    return `quota:websearch:qpm:${now.getHours()}:${now.getMinutes()}`;
  }

  /**
   * 获取使用统计（双层）
   */
  async getStats() {
    const windowUsage = await this.getMaxPlanWindowUsage();
    const qpmUsage = await this.getQPMUsage();
    const windowReset = await this.getMaxPlanResetTime();

    return {
      maxPlan: {
        used: windowUsage,
        total: this.maxPlanConfig.per5Hours,
        remaining: this.maxPlanConfig.per5Hours - windowUsage,
        percentage: Math.round((windowUsage / this.maxPlanConfig.per5Hours) * 100),
        resetIn: windowReset
      },
      webSearch: {
        currentQPM: qpmUsage,
        maxQPM: this.webSearchConfig.qpm,
        percentage: Math.round((qpmUsage / this.webSearchConfig.qpm) * 100)
      }
    };
  }
}

export const dualQuotaManager = new DualQuotaManager();
```

### 配额监控API（更新版）

```typescript
// Next.js API: 获取双层配额使用情况
// /var/www/miaoying/src/app/api/quota/stats/route.ts

import { NextRequest, NextResponse } from 'next/server';
import { dualQuotaManager } from '@/lib/dual-quota-manager';

export async function GET(request: NextRequest) {
  try {
    const stats = await dualQuotaManager.getStats();

    // 判断是否需要告警
    const alert =
      stats.maxPlan.percentage > 80 ||
      stats.webSearch.percentage > 80;

    return NextResponse.json({
      success: true,
      data: stats,
      alert,
      recommendations: {
        maxPlan: stats.maxPlan.percentage > 80
          ? 'Max套餐配额即将用完，建议减少联网搜索或使用缓存'
          : '配额充足',
        webSearch: stats.webSearch.percentage > 80
          ? '联网搜索QPM即将用完，建议降低请求频率'
          : 'QPM充足'
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

### 配额监控API

```typescript
// Next.js API: 获取配额使用情况
// /var/www/miaoying/src/app/api/quota/websearch/route.ts

import { NextRequest, NextResponse } from 'next/server';
import { webSearchQuota } from '@/lib/websearch-quota';

export async function GET(request: NextRequest) {
  try {
    const stats = await webSearchQuota.getStats();

    return NextResponse.json({
      success: true,
      data: stats,
      alert: stats.window.percentage > 80 || stats.week.percentage > 80
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

## 🤖 智能搜索策略

### 何时使用联网搜索

```javascript
// 搜索决策器
class SearchDecisionMaker {
  /**
   * 判断是否需要联网搜索
   */
  async needsWebSearch(query: string, context: any = {}) {
    // 1. 明确的时间相关关键词
    const timeKeywords = [
      '今天', '明天', '昨天', '今年', '去年',
      '最新', '当前', '现在', '最近', '实时',
      'today', 'latest', 'current', 'now', 'recent'
    ];

    if (timeKeywords.some(kw => query.includes(kw))) {
      return { need: true, reason: '时间相关查询' };
    }

    // 2. 明确的数据查询关键词
    const dataKeywords = [
      '天气', '股价', '汇率', '新闻', '汇率',
      '价格', '数据', '资讯', '行情',
      'weather', 'price', 'stock', 'news'
    ];

    if (dataKeywords.some(kw => query.includes(kw))) {
      return { need: true, reason: '数据查询' };
    }

    // 3. 检查缓存是否命中
    if (await this.checkCache(query)) {
      return { need: false, reason: '缓存命中' };
    }

    // 4. 知识库检查（如果有Neo4j/Qdrant）
    if (await this.checkKnowledgeBase(query)) {
      return { need: false, reason: '知识库已有答案' };
    }

    // 5. 默认：复杂问题使用搜索
    if (query.length > 100 || context.complexity === 'high') {
      return { need: true, reason: '复杂问题，需要最新信息' };
    }

    return { need: false, reason: '简单问题，使用模型知识' };
  }

  async checkCache(query: string) {
    const redis = new Redis({ host: 'localhost', port: 6379 });
    const cached = await redis.get(`cache:query:${query}`);
    return !!cached;
  }

  async checkKnowledgeBase(query: string) {
    // TODO: 实现知识库检查
    // 可以用向量相似度或图谱查询
    return false;
  }
}
```

### 搜索执行器

```javascript
// 智能搜索执行
class SmartWebSearch {
  private quota: WebSearchQuotaManager;
  private decision: SearchDecisionMaker;

  constructor() {
    this.quota = new WebSearchQuotaManager();
    this.decision = new SearchDecisionMaker();
  }

  /**
   * 智能搜索（自动决策是否使用联网搜索）
   */
  async search(query: string, context: any = {}) {
    // 1. 判断是否需要搜索
    const decision = await this.decision.needsWebSearch(query, context);

    if (!decision.need) {
      console.log(`跳过联网搜索: ${decision.reason}`);
      // 不使用搜索，直接调用模型
      return this.callModelWithoutSearch(query);
    }

    // 2. 检查配额
    try {
      await this.quota.canSearch();
    } catch (error) {
      console.warn(`配额不足: ${error.message}`);
      // 配额不足，降级到无搜索模式
      return this.callModelWithoutSearch(query);
    }

    // 3. 执行联网搜索
    console.log(`使用联网搜索: ${decision.reason}`);
    const result = await this.callModelWithSearch(query);

    // 4. 记录配额
    await this.quota.recordSearch();

    return result;
  }

  /**
   * 调用模型（带联网搜索）
   */
  async callModelWithSearch(query: string) {
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
              search_result: true
            }
          }
        ]
      })
    });

    return response.json();
  }

  /**
   * 调用模型（不带联网搜索）
   */
  async callModelWithoutSearch(query: string) {
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
        ]
      })
    });

    return response.json();
  }
}

export const smartWebSearch = new SmartWebSearch();
```

---

## 📊 配额使用建议

### 高效使用策略

```
┌─────────────────────────────────────────────────────────────┐
│                  联网搜索使用策略                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ 应该使用联网搜索：                                       │
│  - 实时数据（天气、股价、新闻）                              │
│  - 最新信息（产品发布、政策更新）                            │
│  - 验证事实（数据准确性）                                    │
│  - 深度研究（行业动态、技术趋势）                            │
│                                                             │
│  ❌ 不应使用联网搜索：                                       │
│  - 通用知识（数学、历史、常识）                              │
│  - 重复问题（应该用缓存）                                    │
│  - 简单推理（模型足够）                                      │
│  - 私有数据（知识库已有）                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 缓存策略（节省配额）

```javascript
// 多级缓存策略
class MultiLevelCache {
  private redis: Redis;

  constructor() {
    this.redis = new Redis({ host: 'localhost', port: 6379 });
  }

  /**
   * 获取缓存（带时间衰减）
   */
  async get(query: string, maxAge: number = 3600) {
    const key = this.getCacheKey(query);
    const data = await this.redis.get(key);

    if (!data) return null;

    const { result, timestamp } = JSON.parse(data);
    const age = (Date.now() - timestamp) / 1000;

    if (age > maxAge) {
      await this.redis.del(key);
      return null;
    }

    console.log(`缓存命中 (${Math.round(age)}秒前)`);
    return result;
  }

  /**
   * 设置缓存
   */
  async set(query: string, result: any, ttl: number = 3600) {
    const key = this.getCacheKey(query);
    const data = {
      result,
      timestamp: Date.now()
    };

    await this.redis.setex(key, ttl, JSON.stringify(data));
  }

  /**
   * 根据查询类型设置不同的TTL
   */
  async setWithSmartTTL(query: string, result: any) {
    let ttl = 3600;  // 默认1小时

    // 实时数据缓存时间短
    if (this.isRealtimeQuery(query)) {
      ttl = 300;  // 5分钟
    }

    // 静态数据缓存时间长
    if (this.isStaticQuery(query)) {
      ttl = 86400;  // 24小时
    }

    await this.set(query, result, ttl);
  }

  isRealtimeQuery(query: string) {
    const keywords = ['天气', '股价', '汇率', 'weather', 'stock'];
    return keywords.some(kw => query.includes(kw));
  }

  isStaticQuery(query: string) {
    const keywords = ['历史', '百科', '定义', 'what is', 'who is'];
    return keywords.some(kw => query.includes(kw));
  }

  getCacheKey(query: string) {
    const crypto = require('crypto');
    return `cache:websearch:${crypto.createHash('md5').update(query).digest('hex')}`;
  }
}
```

---

## 🎯 完整的智能客户端（更新版）

```typescript
// /var/www/miaoying/src/lib/zhipu-smart-client.ts
import { Redis } from 'ioredis';
import { zhipuClient } from './zhipu-client';

interface SmartRequest {
  query: string;
  context?: {
    complexity?: 'low' | 'medium' | 'high';
    requiresRealtimeData?: boolean;
    userPreferences?: any;
  };
}

export class ZhipuSmartClient {
  private redis: Redis;
  private webSearchQuota: WebSearchQuotaManager;

  constructor() {
    this.redis = new Redis({ host: 'localhost', port: 6379 });
    this.webSearchQuota = new WebSearchQuotaManager();
  }

  /**
   * 智能处理（自动选择最优策略）
   */
  async process(request: SmartRequest) {
    const { query, context = {} } = request;

    // 1. 检查缓存
    const cached = await this.checkCache(query);
    if (cached) {
      console.log('✅ 缓存命中');
      return cached;
    }

    // 2. 判断是否需要联网搜索
    const needsSearch = this.decideWebSearch(query, context);

    // 3. 选择模型
    const model = this.selectModel(query, context);

    // 4. 执行请求
    let result;
    if (needsSearch) {
      try {
        await this.webSearchQuota.canSearch();
        result = await zhipuClient.chat({
          model,
          messages: [{ role: 'user', content: query }],
          tools: [{
            type: 'web_search',
            web_search: { enable: true, search_result: true }
          }]
        });
        await this.webSearchQuota.recordSearch();
      } catch (error) {
        console.warn(`联网搜索失败，降级: ${error.message}`);
        result = await zhipuClient.chat({
          model,
          messages: [{ role: 'user', content: query }]
        });
      }
    } else {
      result = await zhipuClient.chat({
        model,
        messages: [{ role: 'user', content: query }]
      });
    }

    // 5. 缓存结果
    await this.setCache(query, result);

    return result;
  }

  /**
   * 决定是否使用联网搜索
   */
  decideWebSearch(query: string, context: any): boolean {
    // 用户明确要求
    if (context.requiresRealtimeData) return true;

    // 时间相关关键词
    const timeKeywords = ['今天', '最新', '当前', 'latest', 'current'];
    if (timeKeywords.some(kw => query.includes(kw))) return true;

    // 数据查询关键词
    const dataKeywords = ['天气', '股价', '新闻', '天气', 'stock', 'news'];
    if (dataKeywords.some(kw => query.includes(kw))) return true;

    // 复杂问题使用搜索
    if (context.complexity === 'high') return true;

    return false;
  }

  /**
   * 选择模型
   */
  selectModel(query: string, context: any): string {
    // 简单任务使用快速模型
    if (context.complexity === 'low' || query.length < 500) {
      return 'glm-4-flash';
    }

    // 代码生成
    if (query.includes('代码') || query.includes('函数')) {
      return 'codegeex-4';
    }

    // 复杂任务使用强力模型
    if (context.complexity === 'high') {
      return 'glm-4-plus';
    }

    // 默认
    return 'glm-4';
  }

  async checkCache(query: string) {
    const key = `cache:smart:${this.getHash(query)}`;
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  async setCache(query: string, result: any) {
    const key = `cache:smart:${this.getHash(query)}`;
    await this.redis.setex(key, 3600, JSON.stringify(result));
  }

  getHash(str: string) {
    const crypto = require('crypto');
    return crypto.createHash('md5').update(str).digest('hex');
  }
}

export const zhipuSmartClient = new ZhipuSmartClient();
```

---

## ✅ 总结

### 双层配额系统

```
┌─────────────────────────────────────────────────────────────┐
│                    Max套餐双层限制                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  第一层：总体配额                                            │
│  - 每5小时 1600次 prompts                                   │
│  - 每周 8000次 prompts                                      │
│  - 限制所有API调用类型                                       │
│                                                             │
│  第二层：联网搜索QPM限制                                     │
│  - web-search-pro: 30 QPM                                   │
│  - 每分钟最多30次搜索调用                                    │
│  - 只影响联网搜索功能                                        │
│                                                             │
│  使用建议：                                                 │
│  - 平均每分钟5次以内 = 安全 ✅                              │
│  - 小团队(10人) = 充足 ✅                                    │
│  - 大规模应用 = 需要优化（缓存+降级）                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 关键优化策略

1. **智能决策**：自动判断是否需要联网搜索
2. **多级缓存**：减少重复搜索（节省Max套餐配额）
3. **双层配额管理**：同时监控Max套餐和QPM限制
4. **优雅降级**：配额不足时自动降级到无搜索模式
5. **请求合并**：批量请求减少调用次数

### 推荐配置

```javascript
// 安全的频率配置
const SAFE_CONFIG = {
  每分钟联网搜索: 5次,      // 远低于30 QPM限制
  每5小时总请求: 1500次,     // 略低于1600限制
  缓存命中率: 目标70%+,      // 减少实际调用
  降级策略: 自动启用          // 配额不足时自动降级
};
```

**继续回答其他问题：**

**请继续提供：**
3. 阿里云服务器配置（CPU/内存/磁盘）？
4. 是否需要在阿里云部署Neo4j和Qdrant？
5. 国外服务器的具体用途？
