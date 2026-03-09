# LLM OCR 性能优化方案

## 问题分析

当前每次OCR识别包含 **4-5次** LLM API调用：
1. Vision识别（图片→文字）：doubao-seed-1-6-vision-250815 - 最慢（2-5秒）
2. 页面类型识别1：deepseek-chat - 快（0.5-1秒）
3. 数据提取：deepseek-chat/reasoner - 中等（1-2秒）
4. 页面类型识别2：可能重复调用 - 快（0.5-1秒）
5. AI修正验证：额外调用 - 中等（1-2秒）

**总耗时**：5-11秒/次（取决于网络和模型负载）

## 优化方案

### 🎯 方案1：规则优先，LLM兜底（推荐）⭐⭐⭐⭐⭐

**原理**：80%的页面可以用规则快速识别，只需LLM处理特殊情况

**实施**：
```typescript
// 步骤1：规则快速判断页面类型（<10ms）
function detectPageTypeByRules(ocrText: string): string | null {
  // 订单列表页
  if (ocrText.includes('全部订单') && ocrText.includes('已支付')) {
    return 'order-list';
  }
  // 订单详情页
  if (ocrText.includes('订单详情') && ocrText.includes('行程码')) {
    return 'order-detail';
  }
  // 可能有更多规则...

  return null; // 规则无法判断，需要LLM
}

// 步骤2：只有在规则无法判断时才调用LLM
async function smartPageTypeDetection(ocrText: string): Promise<string> {
  // 先用规则判断（几乎瞬间完成）
  const ruleBased = detectPageTypeByRules(ocrText);
  if (ruleBased) {
    console.log('[优化] 用规则识别页面类型，跳过LLM');
    return ruleBased;
  }

  // 规则无法判断，调用LLM
  console.log('[优化] 规则无法判断，使用LLM');
  const response = await deepseekClient.chat([...]);
  return extractPageType(response);
}
```

**效果**：
- ✅ 80%的情况：减少4-5次LLM调用 → 只需1次Vision识别
- ✅ 节省时间：从5-11秒 → 2-5秒（Vision识别时间）
- ✅ 成本降低：减少75%的API调用

---

### ⚡ 方案2：并发LLM调用（中等收益）⭐⭐⭐⭐

**原理**：某些独立的LLM调用可以并行执行

**实施**：
```typescript
// 当前：串行执行（慢）
const pageType = await detectPageTypeLLM(ocrText);  // 1秒
const orders = await extractOrdersLLM(ocrText);     // 2秒
// 总耗时：3秒

// 优化：并发执行（快）
const [pageType, orders] = await Promise.all([
  detectPageTypeLLM(ocrText),  // 1秒
  extractOrdersLLM(ocrText),   // 2秒
]);
// 总耗时：2秒（取最慢的）
```

**适用场景**：
- 页面类型识别和数据提取相互独立
- 多个订单的批量验证

**效果**：
- ✅ 节省时间：30-40%（针对并发部分）
- ⚠️ 不适用于有依赖关系的调用

---

### 🗜️ 方案3：Prompt优化（小幅收益）⭐⭐⭐

**原理**：更短的prompt = 更快的响应

**实施**：
```typescript
// 当前prompt（冗长）
const longPrompt = `
你是一个网约车订单数据提取专家。
你的任务是从OCR识别的文字中提取订单信息。
请注意以下规则：
1. 每个订单以"专车"开头
2. 订单包含时间、地址、状态等信息
3. 如果某个字段缺失，标注为"未知"
...
（共500+字）
`;

// 优化prompt（简洁）
const shortPrompt = `
从网约车OCR文字中提取订单信息（JSON格式）：
规则：专车开头，包含时间/地址/状态
缺失字段用null表示
输入：${ocrText}
`;
```

**效果**：
- ✅ 节省时间：10-20%（每次调用）
- ✅ 降低token成本：30-50%

---

### 🔄 方案4：使用更快的模型（需要测试）⭐⭐⭐

**选项A：更快的DeepSeek模型**
```typescript
// 当前
model: 'deepseek-chat'  // 平衡速度和质量

// 更快（如果可用）
model: 'deepseek-coder'  // 可能更快
model: 'deepseek-lite'   // 轻量级模型（如果推出）
```

**选项B：其他高速模型**
- **通义千问-Turbo**：速度快，价格低
- **智谱GLM-4-Flash**：专为速度优化
- **Claude-Haiku**：速度快但需要代理

**效果**：
- ✅ 节省时间：20-40%（取决于模型）
- ⚠️ 需要测试准确性

---

### 💾 方案5：智能缓存（特定场景）⭐⭐⭐

**原理**：相同内容不重复调用LLM

**实施**：
```typescript
const cache = new Map<string, any>();

async function cachedLLM(key: string, prompt: string) {
  // 检查缓存
  if (cache.has(key)) {
    console.log('[缓存] 命中，跳过LLM调用');
    return cache.get(key);
  }

  // 调用LLM
  const result = await deepseekClient.chat([...]);
  cache.set(key, result);
  return result;
}
```

**适用场景**：
- 重复识别同一订单
- 测试/调试阶段

**效果**：
- ✅ 命中时接近0秒
- ⚠️ 仅限重复内容

---

### 🎛️ 方案6：max_tokens限制（小幅优化）⭐⭐

**实施**：
```typescript
// 当前：无限制，可能生成大量不必要的内容
const response = await deepseekClient.chat([...], {
  temperature: 0.2,
});

// 优化：限制输出长度
const response = await deepseekClient.chat([...], {
  temperature: 0.2,
  max_tokens: 1000,  // 足够返回订单数据，避免冗余输出
});
```

**效果**：
- ✅ 节省时间：10-20%
- ✅ 降低成本：减少token消耗

---

## 📋 推荐实施顺序

### 阶段1：快速优化（1-2小时实施）⚡
1. ✅ **方案1**：添加规则判断（最大收益）
2. ✅ **方案3**：简化prompt
3. ✅ **方案6**：添加max_tokens限制

**预期效果**：60-70%的性能提升

### 阶段2：并发优化（半天实施）🔄
4. ✅ **方案2**：识别可并发的调用，使用Promise.all

**预期效果**：额外20-30%提升

### 阶段3：高级优化（可选）🚀
5. ⚠️ **方案4**：测试更快的模型
6. ⚠️ **方案5**：添加缓存层

**预期效果**：额外10-20%提升

---

## 🎯 综合优化效果预测

| 场景 | 当前耗时 | 优化后耗时 | 提升 |
|------|---------|-----------|------|
| 规则可识别（80%） | 5-11秒 | 2-5秒 | **60-70%** |
| 规则不可识别（20%） | 5-11秒 | 3-7秒 | **30-40%** |
| 平均 | 5-11秒 | **2-5秒** | **55-65%** |

---

## 📝 下一步

需要我帮你：
1. 实施方案1（规则优先）？
2. 实施方案2（并发优化）？
3. 还是先看看具体哪个LLM调用最慢？

告诉我你想从哪里开始！
