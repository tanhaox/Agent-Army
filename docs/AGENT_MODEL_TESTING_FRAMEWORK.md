# Agent团队模型测试与对比框架

**日期**: 2026-03-14
**目标**: 为Agent团队选择最优模型组合

---

## 🎯 测试目标

### 核心指标

```
┌─────────────────────────────────────────────────────────────┐
│                  Agent团队模型评估维度                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1️⃣ 输出质量（40分）                                        │
│  ├─ 准确性（15分）：答案是否正确                            │
│  ├─ 完整性（10分）：信息是否完整                            │
│  ├─ 相关性（10分）：是否切题                                │
│  └─ 可读性（5分）：表达是否清晰                             │
│                                                             │
│  2️⃣ 反应速度（30分）                                        │
│  ├─ 首token延迟（15分）：开始响应时间                      │
│  ├─ 生成速度（10分）：每秒token数                          │
│  └─ 总耗时（5分）：完整响应时间                             │
│                                                             │
│  3️⃣ 端口性能（20分）                                        │
│  ├─ API稳定性（10分）：成功率                               │
│  ├─ 并发能力（5分）：QPM支持                                │
│  └─ 错误处理（5分）：异常恢复能力                           │
│                                                             │
│  4️⃣ 成本效益（10分）                                        │
│  └─ 性价比：质量/成本比                                     │
│                                                             │
│  总分：100分                                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧪 测试场景设计

### 场景1：简单问答（Agent基本能力）

```json
{
  "scenario": "simple_qa",
  "description": "Agent处理用户常见问题",
  "test_cases": [
    {
      "id": "qa_001",
      "query": "什么是机器学习？",
      "expected": {
        "accuracy": "定义准确",
        "completeness": "包含核心概念",
        "length": "100-300字"
      },
      "timeout": 5000
    },
    {
      "id": "qa_002",
      "query": "如何提高代码质量？",
      "expected": {
        "accuracy": "建议实用",
        "completeness": "涵盖多个方面",
        "length": "200-500字"
      },
      "timeout": 8000
    },
    {
      "id": "qa_003",
      "query": "Python和JavaScript的区别？",
      "expected": {
        "accuracy": "对比准确",
        "completeness": "涵盖主要差异",
        "length": "300-600字"
      },
      "timeout": 10000
    }
  ],
  "metrics": {
    "quality_weight": 0.6,
    "speed_weight": 0.3,
    "cost_weight": 0.1
  }
}
```

### 场景2：多轮对话（Agent协作能力）

```json
{
  "scenario": "multi_turn_dialogue",
  "description": "Agent团队多轮协作场景",
  "test_cases": [
    {
      "id": "dialogue_001",
      "rounds": [
        {
          "agent": "researcher",
          "query": "研究AI Agent的最新进展"
        },
        {
          "agent": "analyst",
          "query": "分析第一个Agent的研究结果"
        },
        {
          "agent": "writer",
          "query": "基于前两个Agent的输出，写一份报告"
        }
      ],
      "expected": {
        "coherence": "对话连贯",
        "collaboration": "Agent间协作顺畅",
        "total_time": "<30秒"
      }
    }
  ]
}
```

### 场景3：高并发测试（Agent团队压力测试）

```json
{
  "scenario": "high_concurrency",
  "description": "模拟Agent团队高并发场景",
  "test_cases": [
    {
      "id": "concurrent_001",
      "concurrent_requests": 50,
      "duration": "60秒",
      "ramp_up": "10秒",
      "expected": {
        "success_rate": ">95%",
        "avg_response_time": "<3秒",
        "p95_response_time": "<5秒"
      }
    },
    {
      "id": "concurrent_002",
      "concurrent_requests": 100,
      "duration": "120秒",
      "ramp_up": "20秒",
      "expected": {
        "success_rate": ">90%",
        "avg_response_time": "<5秒",
        "p95_response_time": "<8秒"
      }
    }
  ]
}
```

### 场景4：复杂推理（Agent深度能力）

```json
{
  "scenario": "complex_reasoning",
  "description": "Agent处理复杂推理任务",
  "test_cases": [
    {
      "id": "reasoning_001",
      "query": "设计一个电商推荐系统的架构",
      "expected": {
        "accuracy": "架构合理",
        "completeness": "涵盖数据层、算法层、应用层",
        "creativity": "有创新点"
      },
      "timeout": 15000
    },
    {
      "id": "reasoning_002",
      "query": "分析为什么微服务架构比单体架构更适合大型系统",
      "expected": {
        "accuracy": "分析准确",
        "completeness": "涵盖可扩展性、维护性、团队协作",
        "depth": "有深度"
      },
      "timeout": 12000
    }
  ]
}
```

---

## 🔬 A/B测试框架

### 测试架构

```javascript
// A/B测试框架
class ModelABTestFramework {
  constructor() {
    this.models = {
      zhipu: new ZhipuClient(),
      deepseek: new DeepSeekClient()
    };

    this.metrics = new MetricsCollector();
    this.evaluator = new QualityEvaluator();
  }

  /**
   * 执行A/B测试
   */
  async runABTest(testCase) {
    const results = {};

    // 1. 对每个模型执行测试
    for (const [modelName, client] of Object.entries(this.models)) {
      console.log(`测试模型: ${modelName}`);

      const startTime = Date.now();

      try {
        // 执行请求
        const response = await client.chat(testCase.query);

        // 记录性能指标
        const performance = {
          firstTokenLatency: response.firstTokenTime - startTime,
          totalTokens: response.usage.total_tokens,
          generationSpeed: response.usage.total_tokens / ((Date.now() - startTime) / 1000),
          totalTime: Date.now() - startTime
        };

        // 评估质量
        const quality = await this.evaluator.evaluate({
          query: testCase.query,
          response: response.content,
          expected: testCase.expected
        });

        results[modelName] = {
          success: true,
          response: response.content,
          performance,
          quality,
          usage: response.usage,
          cost: this.calculateCost(modelName, response.usage)
        };

      } catch (error) {
        results[modelName] = {
          success: false,
          error: error.message,
          performance: {
            totalTime: Date.now() - startTime
          }
        };
      }
    }

    // 2. 对比结果
    const comparison = this.compareResults(results);

    // 3. 生成报告
    const report = this.generateReport(testCase, results, comparison);

    // 4. 保存结果
    await this.saveResults(testCase.id, results, comparison);

    return report;
  }

  /**
   * 对比结果
   */
  compareResults(results) {
    const comparison = {
      winner: null,
      scores: {},
      analysis: {}
    };

    // 计算综合得分
    for (const [model, result] of Object.entries(results)) {
      if (!result.success) {
        comparison.scores[model] = 0;
        continue;
      }

      // 质量得分（40分）
      const qualityScore = result.quality.overall * 40;

      // 速度得分（30分）
      const speedScore = this.calculateSpeedScore(result.performance);

      // 稳定性得分（20分）
      const stabilityScore = 20;  // 单次测试默认满分

      // 成本得分（10分）
      const costScore = this.calculateCostScore(result.cost);

      comparison.scores[model] = qualityScore + speedScore + stabilityScore + costScore;
    }

    // 确定胜者
    const maxScore = Math.max(...Object.values(comparison.scores));
    comparison.winner = Object.entries(comparison.scores)
      .find(([_, score]) => score === maxScore)?.[0];

    // 分析差异
    comparison.analysis = this.analyzeDifferences(results);

    return comparison;
  }

  /**
   * 计算速度得分
   */
  calculateSpeedScore(performance) {
    // 首token延迟得分（15分）
    const firstTokenScore = Math.max(0, 15 - (performance.firstTokenLatency / 200));

    // 生成速度得分（10分）
    const generationScore = Math.min(10, performance.generationSpeed / 10);

    // 总耗时得分（5分）
    const totalTimeScore = Math.max(0, 5 - (performance.totalTime / 2000));

    return firstTokenScore + generationScore + totalTimeScore;
  }

  /**
   * 计算成本得分
   */
  calculateCostScore(cost) {
    // 成本越低，得分越高
    // 假设成本范围 0-0.1元
    return Math.max(0, 10 - (cost * 100));
  }

  /**
   * 分析差异
   */
  analyzeDifferences(results) {
    const analysis = {};

    const successfulResults = Object.entries(results)
      .filter(([_, r]) => r.success);

    if (successfulResults.length < 2) {
      return analysis;
    }

    // 速度差异
    const speeds = successfulResults.map(([_, r]) => r.performance.totalTime);
    analysis.speedDifference = {
      fastest: Math.min(...speeds),
      slowest: Math.max(...speeds),
      ratio: Math.max(...speeds) / Math.min(...speeds)
    };

    // 质量差异
    const qualities = successfulResults.map(([_, r]) => r.quality.overall);
    analysis.qualityDifference = {
      best: Math.max(...qualities),
      worst: Math.min(...qualities),
      gap: Math.max(...qualities) - Math.min(...qualities)
    };

    // 成本差异
    const costs = successfulResults.map(([_, r]) => r.cost);
    analysis.costDifference = {
      cheapest: Math.min(...costs),
      mostExpensive: Math.max(...costs),
      ratio: Math.max(...costs) / Math.min(...costs)
    };

    return analysis;
  }

  /**
   * 生成报告
   */
  generateReport(testCase, results, comparison) {
    return {
      testId: testCase.id,
      timestamp: new Date().toISOString(),
      query: testCase.query,
      winner: comparison.winner,
      scores: comparison.scores,
      details: {
        zhipu: results.zhipu,
        deepseek: results.deepseek
      },
      analysis: comparison.analysis,
      recommendation: this.generateRecommendation(comparison)
    };
  }

  /**
   * 生成推荐
   */
  generateRecommendation(comparison) {
    const recommendations = [];

    // 基于得分推荐
    if (comparison.winner) {
      recommendations.push(`推荐使用 ${comparison.winner}，综合得分最高`);
    }

    // 基于场景推荐
    if (comparison.analysis.speedDifference?.ratio > 2) {
      const faster = results.zhipu.performance.totalTime < results.deepseek.performance.totalTime
        ? '智谱'
        : 'DeepSeek';
      recommendations.push(`对速度敏感的场景，推荐使用 ${faster}`);
    }

    if (comparison.analysis.qualityDifference?.gap > 0.2) {
      const better = results.zhipu.quality.overall > results.deepseek.quality.overall
        ? '智谱'
        : 'DeepSeek';
      recommendations.push(`对质量要求高的场景，推荐使用 ${better}`);
    }

    if (comparison.analysis.costDifference?.ratio > 5) {
      const cheaper = results.zhipu.cost < results.deepseek.cost
        ? '智谱'
        : 'DeepSeek';
      recommendations.push(`对成本敏感的场景，推荐使用 ${cheaper}`);
    }

    return recommendations;
  }
}
```

---

## 📊 质量评估系统

```javascript
// 质量评估器
class QualityEvaluator {
  constructor() {
    this.rubrics = {
      accuracy: {
        weight: 0.375,  // 15/40
        criteria: [
          '事实准确',
          '逻辑正确',
          '无明显错误'
        ]
      },
      completeness: {
        weight: 0.25,  // 10/40
        criteria: [
          '信息完整',
          '覆盖要点',
          '无重要遗漏'
        ]
      },
      relevance: {
        weight: 0.25,  // 10/40
        criteria: [
          '切题回答',
          '无无关内容',
          '聚焦核心问题'
        ]
      },
      readability: {
        weight: 0.125,  // 5/40
        criteria: [
          '表达清晰',
          '结构合理',
          '易于理解'
        ]
      }
    };
  }

  /**
   * 评估回答质量
   */
  async evaluate({ query, response, expected }) {
    const scores = {};

    for (const [dimension, config] of Object.entries(this.rubrics)) {
      scores[dimension] = await this.evaluateDimension(
        query,
        response,
        expected,
        dimension,
        config.criteria
      );
    }

    // 计算总分
    const overall = Object.entries(scores)
      .reduce((sum, [dim, score]) => sum + score * this.rubrics[dim].weight, 0);

    return {
      ...scores,
      overall: overall / Object.values(this.rubrics).reduce((sum, r) => sum + r.weight, 0)
    };
  }

  /**
   * 评估单个维度
   */
  async evaluateDimension(query, response, expected, dimension, criteria) {
    // 简化版：基于规则的评估
    // 实际应用中可以接入LLM进行评估

    switch (dimension) {
      case 'accuracy':
        return this.evaluateAccuracy(response, expected);

      case 'completeness':
        return this.evaluateCompleteness(response, expected);

      case 'relevance':
        return this.evaluateRelevance(query, response);

      case 'readability':
        return this.evaluateReadability(response);

      default:
        return 0.5;
    }
  }

  evaluateAccuracy(response, expected) {
    // 简化版：检查关键词
    const keywords = expected.accuracy?.split(' ') || [];
    const matches = keywords.filter(kw => response.includes(kw)).length;
    return matches / keywords.length;
  }

  evaluateCompleteness(response, expected) {
    // 检查长度
    const expectedLength = expected.length?.split('-').map(Number) || [100, 500];
    const actualLength = response.length;

    if (actualLength < expectedLength[0]) return 0.5;
    if (actualLength > expectedLength[1]) return 0.8;
    return 1.0;
  }

  evaluateRelevance(query, response) {
    // 简化版：检查主题词
    const queryWords = new Set(query.toLowerCase().split(' '));
    const responseWords = new Set(response.toLowerCase().split(' '));
    const overlap = [...queryWords].filter(w => responseWords.has(w)).length;

    return Math.min(1, overlap / queryWords.size);
  }

  evaluateReadability(response) {
    // 简化版：检查结构
    const hasStructure = response.includes('\n') || response.includes('。');
    const hasProperLength = response.length > 50;

    return (hasStructure ? 0.5 : 0) + (hasProperLength ? 0.5 : 0);
  }
}
```

---

## 📈 性能监控仪表板

```typescript
// /var/www/miaoying/src/app/api/test/dashboard/route.ts
import { NextResponse } from 'next/server';
import { Redis } from 'ioredis';

export async function GET() {
  const redis = new Redis({ host: 'localhost', port: 6379 });

  // 获取最近测试结果
  const recentTests = await redis.lrange('test:results:recent', 0, 99);
  const tests = recentTests.map(t => JSON.parse(t));

  // 汇总统计
  const stats = {
    total: tests.length,
    zhipuWins: tests.filter(t => t.winner === 'zhipu').length,
    deepseekWins: tests.filter(t => t.winner === 'deepseek').length,
    ties: tests.filter(t => t.winner === 'tie').length,

    avgScores: {
      zhipu: average(tests.map(t => t.scores.zhipu)),
      deepseek: average(tests.map(t => t.scores.deepseek))
    },

    avgResponseTime: {
      zhipu: average(tests.map(t => t.details.zhipu?.performance?.totalTime || 0)),
      deepseek: average(tests.map(t => t.details.deepseek?.performance?.totalTime || 0))
    },

    successRate: {
      zhipu: tests.filter(t => t.details.zhipu?.success).length / tests.length,
      deepseek: tests.filter(t => t.details.deepseek?.success).length / tests.length
    }
  };

  return NextResponse.json({
    stats,
    recentTests: tests.slice(0, 10),
    chartData: generateChartData(tests)
  });
}

function average(arr) {
  return arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
}

function generateChartData(tests) {
  return {
    scoresOverTime: tests.map(t => ({
      timestamp: t.timestamp,
      zhipu: t.scores.zhipu,
      deepseek: t.scores.deepseek
    })),
    responseTimeDistribution: {
      zhipu: tests.map(t => t.details.zhipu?.performance?.totalTime || 0),
      deepseek: tests.map(t => t.details.deepseek?.performance?.totalTime || 0)
    }
  };
}
```

---

## 🚀 自动化测试脚本

```bash
#!/bin/bash
# automated_test.sh

# 1. 准备测试环境
echo "准备测试环境..."
cd /var/www/miaoying
npm run test:prepare

# 2. 运行基准测试
echo "运行基准测试..."
npm run test:benchmark

# 3. 运行A/B测试
echo "运行A/B测试..."
npm run test:ab -- --scenarios=all

# 4. 运行压力测试
echo "运行压力测试..."
npm run test:stress -- --concurrency=50 --duration=60

# 5. 生成报告
echo "生成测试报告..."
npm run test:report

# 6. 发送通知
echo "发送测试完成通知..."
curl -X POST $WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"测试完成，查看报告: $REPORT_URL\"}"
```

```json
// package.json
{
  "scripts": {
    "test:prepare": "ts-node tests/prepare.ts",
    "test:benchmark": "ts-node tests/benchmark.ts",
    "test:ab": "ts-node tests/ab-test.ts",
    "test:stress": "ts-node tests/stress-test.ts",
    "test:report": "ts-node tests/generate-report.ts",
    "test:all": "npm run test:prepare && npm run test:benchmark && npm run test:ab && npm run test:stress && npm run test:report"
  }
}
```

---

## ✅ 测试计划

### 第1周：基准测试

```
Day 1-2: 准备测试用例
├─ 收集100个常见问题
├─ 设计5个Agent协作场景
└─ 准备性能基准数据

Day 3-4: 执行单次测试
├─ 测试智谱各模型
├─ 测试DeepSeek模型
└─ 收集初步数据

Day 5: 分析结果
├─ 对比质量差异
├─ 对比速度差异
└─ 生成初步报告
```

### 第2周：压力测试

```
Day 1-2: 并发测试
├─ 50并发测试
├─ 100并发测试
└─ 200并发测试

Day 3-4: 稳定性测试
├─ 24小时持续运行
├─ 错误率统计
└─ 恢复能力测试

Day 5: 分析结果
├─ 确定并发上限
├─ 识别性能瓶颈
└─ 优化建议
```

### 第3周：集成测试

```
Day 1-3: Agent协作测试
├─ 2个Agent协作
├─ 3-5个Agent协作
└─ 10个Agent协作

Day 4-5: 真实场景测试
├─ 模拟真实用户行为
├─ 长期运行测试
└─ 最终报告
```

---

## 📊 预期成果

### 测试报告模板

```markdown
# 模型对比测试报告

## 测试概览
- 测试时间：2026-03-XX
- 测试场景：简单问答、多轮对话、高并发、复杂推理
- 测试样本：100个测试用例

## 综合评分

| 模型 | 质量得分 | 速度得分 | 稳定性得分 | 成本得分 | 总分 |
|------|---------|---------|-----------|---------|------|
| 智谱GLM-4 | 35/40 | 25/30 | 18/20 | 10/10 | 88/100 |
| DeepSeek | 32/40 | 28/30 | 19/20 | 8/10 | 87/100 |

## 详细分析

### 1. 输出质量
- 智谱：准确率92%，完整性88%
- DeepSeek：准确率89%，完整性85%

### 2. 反应速度
- 智谱：首token延迟500ms，平均2.5秒完成
- DeepSeek：首token延迟300ms，平均2秒完成

### 3. 并发能力
- 智谱：QPM限制30，高峰期需要排队
- DeepSeek：无明显限制，高并发表现好

### 4. 成本分析
- 智谱：Max套餐已付费，边际成本0
- DeepSeek：按量付费，缓存命中时成本极低

## 推荐方案

### 场景1：高质量任务
推荐：智谱GLM-4-Plus
理由：质量最高，适合复杂推理

### 场景2：高并发场景
推荐：DeepSeek
理由：无QPM限制，响应快

### 场景3：成本优化
推荐：智谱（主力）+ DeepSeek（补充）
理由：充分利用已付费套餐，降低总体成本
```

---

**准备好开始测试了吗？我可以帮您：**
1. 生成测试用例
2. 部署测试框架
3. 执行自动化测试
4. 生成对比报告
