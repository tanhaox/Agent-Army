# MCP Server 集成指南 - Claude Code ↔ Claw

## 📋 前置条件

1. **Node.js 已安装**（需要 v18+）
2. **claw 系统正在运行**并提供了 HTTP API
3. **知道 claw 的 API 地址和端口**

---

## 🚀 快速开始（3 步完成）

### 步骤 1：安装依赖

```bash
cd C:/AI-Agent-Local/examples
npm init -y
npm install @modelcontextprotocol/sdk
```

### 步骤 2：配置 MCP Server

编辑 `C:\AI-Agent-Local\.mcp.json`，添加：

```json
{
  "claw": {
    "type": "stdio",
    "command": "node",
    "args": [
      "C:/AI-Agent-Local/examples/mcp-server-claw-bridge.js"
    ]
  }
}
```

### 步骤 3：重启 VS Code

重载 VS Code 窗口：
- 按 `Ctrl+Shift+P`
- 输入 "Reload Window"
- 回车

---

## 🎯 使用方式

重启后，在 Claude Code 中直接调用：

```
请在 claw 中执行命令：status
```

```
获取 claw 的当前状态
```

---

## 🔧 自定义配置

### 修改 claw 的 API 地址

编辑 `mcp-server-claw-bridge.js` 第 48 行：

```javascript
const CLAW_API_BASE = 'http://localhost:3000/api'; // 改成你的 claw 地址
```

### 添加新工具

在 `tools` 数组中添加：

```javascript
{
  name: 'claw_custom_tool',
  description: '你的自定义工具',
  inputSchema: {
    type: 'object',
    properties: {
      param1: { type: 'string', description: '参数1' },
    },
  },
}
```

---

## 🧪 测试连接

### 手动测试 MCP Server

```bash
# 进入示例目录
cd C:/AI-Agent-Local/examples

# 运行测试
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node mcp-server-claw-bridge.js
```

### 查看日志

MCP Server 的错误输出会显示在 VS Code 的开发者工具中：
- 按 `Ctrl+Shift+I`
- 查看 Console 标签

---

## ❓ 常见问题

### Q1: "command not found: node"
**解决**：
1. 确认 Node.js 已安装：`node --version`
2. 或使用完整路径：`C:\Program Files\nodejs\node.exe`

### Q2: "ECONNREFUSED: claw API 不可用"
**解决**：
1. 确认 claw 正在运行
2. 检查端口是否正确
3. 使用浏览器测试 claw API：`http://localhost:3000/api/status`

### Q3: MCP Server 没有加载
**解决**：
1. 检查 `.mcp.json` 语法是否正确
2. 查看 VS Code 输出面板（MCP 日志）
3. 确认文件路径使用正斜杠 `/`

---

## 📚 进阶：自定义协议

如果你的 claw 不支持 HTTP API，可以：

### 方案 A：WebSocket
```javascript
import WebSocket from 'ws';

const ws = new WebSocket('ws://localhost:3000/ws');
ws.on('message', (data) => {
  // 处理 claw 响应
});
```

### 方案 B：直接调用 claw 命令行
```javascript
import { exec } from 'child_process';

exec('claw command', (error, stdout) => {
  // 处理输出
});
```

### 方案 C：文件/数据库共享
通过共享文件或数据库表交换数据

---

## 🎉 完成！

现在 Claude Code 和 claw 可以通信了！你可以：

- ✅ 在对话中调用 claw 功能
- ✅ 让 Claude Code 读取 claw 状态
- ✅ 实现自动化任务协作

需要帮助？告诉我你的 claw 的具体 API 文档！
