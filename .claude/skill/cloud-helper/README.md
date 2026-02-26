# Cloud Helper 使用说明

## 架构设计

- **本地任务**：使用本地 Ollama，零 Token
- **云端任务**：使用小号 AI Token，处理复杂任务

## 快速开始

### 1. 配置 API Key（仅云端任务需要）

```bash
# 本地任务不需要配置
# 云端任务需要配置小号 API Key
set CLOUD_API_KEY=你的小号_API_Key
```

### 2. 本地任务（零 Token）

```bash
cd C:\AI-Agent-Local\.claude\skill\cloud-helper\scripts

# 翻译
python local_task.py translate "Hello, how are you?"

# 摘要
python local_task.py summarize "这是一段很长的文本..."

# 提取关键信息
python local_task.py extract "这是文章内容..."

# 修复格式
python local_task.py fix "有一些格式问题..."
```

### 3. 云端任务（消耗小号 Token）

```bash
# 翻译
python cloud_task.py translate "Hello, how are you?"

# 智能分析
python cloud_task.py analyze "这是一段很长的文本..."

# 创意写作
python cloud_task.py write "人工智能的发展" --length medium

# 多轮对话
python cloud_task.py chat "你好，能帮我写一首诗吗？"
```

## Token 管理

| 任务类型 | Token 消耗 |
|---------|-----------|
| 本地任务 | 0 |
| 翻译 | ~2000 tokens/次 |
| 分析 | ~3000 tokens/次 |
| 创意写作 | ~5000 tokens/次 |
| 对话 | ~1000 tokens/轮 |

### 使用小号 Token 的原因

1. **本地 AI 局限**：Ollama 是本地运行，受硬件限制
2. **隐私保护**：小号 Token 用于云端任务，保护主号
3. **成本控制**：简单任务零 Token，复杂任务小号 Token

### 扩展

如需添加更多云端服务，编辑 `cloud_task.py` 中的 `alt_models` 字典。
