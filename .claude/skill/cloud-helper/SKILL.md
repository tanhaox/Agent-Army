---
name: cloud-helper
description: 云端助手 - 处理复杂任务，使用小号 AI Token。当任务需要智能分析、翻译等时使用。简单的本地任务使用本地 Ollama 零 Token。
---

# Cloud Helper

将简单任务留在本地处理，复杂任务发送到云端 AI 处理。

## 使用场景

### 本地处理（零 Token）
- 文件操作
- 简单文本处理
- 规则匹配
- 数据格式转换

### 云端处理（消耗小号 Token）
- 智能分析
- 高质量翻译
- 创意写作
- 复杂推理
- 多轮对话任务

## 调用方式

```bash
# 本地简单任务（零 Token）
python scripts/local_task.py <任务>

# 云端复杂任务（使用小号 Token）
python scripts/cloud_task.py <任务>
```

## API 配置

配置云端 AI 的 API Key（小号 Token）：

```bash
set CLOUD_API_KEY=你的小号_API_Key
```

### 可用的云端服务

- DeepSeek（推荐）
- 豆包
- Kimi
- Claude
- OpenAI

### Token 节省建议

- 简单翻译：使用本地 Ollama（零 Token）
- 复杂翻译：使用云端 API（小号 Token）
