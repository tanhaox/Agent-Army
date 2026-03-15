# OpenClaw Skill: 外部记忆API工具

为OpenClaw Agent添加外部DuckDB记忆系统的访问能力。

## 创建位置

```
/root/.openclaw/workspace/skills/external-memory/
├── skill.json
├── skill.ts
└── README.md
```

## 功能

让Agent能够调用外部记忆API (端口18888):
- 存储记忆: `POST /api/memory/remember`
- 检索记忆: `POST /api/memory/recall`
- 搜索记忆: `POST /api/memory/search`

## 实现方式

### 方案1: 创建TypeScript Skill

```typescript
// skill.ts
import { z } from "zod";

const RememberSchema = z.object({
  content: z.string(),
  category: z.string(),
  importance: z.number().optional().default(80),
  tags: z.array(z.string()).optional()
});

export const skill = {
  name: "external-memory",
  description: "外部记忆API工具 - 存储和检索持久化记忆",
  tools: {
    remember: {
      description: "存储重要信息到外部记忆数据库",
      parameters: RememberSchema,
      execute: async (params) => {
        const response = await fetch("http://157.245.195.58:18888/api/memory/remember", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params)
        });
        return await response.json();
      }
    },
    recall: {
      description: "从外部记忆数据库检索信息",
      parameters: z.object({
        category: z.string().optional(),
        limit: z.number().optional().default(10)
      }),
      execute: async (params) => {
        const response = await fetch("http://157.245.195.58:18888/api/memory/recall", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params)
        });
        return await response.json();
      }
    }
  }
};
```

### 方案2: 创建Python脚本工具

```python
# /root/.openclaw/workspace/tools/external_memory_tool.py

import requests
import sys

MEMORY_API = "http://157.245.195.58:18888"

def remember(content, category, importance=80, tags=None):
    """存储记忆"""
    response = requests.post(f"{MEMORY_API}/api/memory/remember", json={
        "content": content,
        "category": category,
        "importance": importance,
        "tags": tags or []
    })
    return response.json()

def recall(category=None, limit=10):
    """检索记忆"""
    response = requests.post(f"{MEMORY_API}/api/memory/recall", json={
        "category": category,
        "limit": limit
    })
    return response.json()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "remember" and len(sys.argv) >= 3:
            result = remember(sys.argv[2], sys.argv[3])
            print(result)
        elif cmd == "recall":
            result = recall()
            print(result)
```

## 使用示例

### Agent会话中使用

```
User: 记住这个：我喜欢使用DuckDB作为分析数据库
Agent: [调用 external-memory.remember]
       已存储到外部记忆数据库

User: 我之前说过我喜欢什么数据库？
Agent: [调用 external-memory.recall]
       你说过你喜欢使用DuckDB作为分析数据库
```

## 配置OpenClaw

添加到 `/root/.openclaw/openclaw.json`:

```json
{
  "skills": {
    "entries": {
      "external-memory": {
        "enabled": true,
        "path": "/root/.openclaw/workspace/skills/external-memory"
      }
    }
  }
}
```

## 优势

1. **独立运行**: 不依赖OpenClaw版本
2. **持久化**: DuckDB数据库稳定存储
3. **灵活调用**: Agent和Python脚本都能用
4. **完整功能**: 存储检索搜索全覆盖
