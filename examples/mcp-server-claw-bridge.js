#!/usr/bin/env node

/**
 * 最简单的 MCP Server - Claw 桥接示例
 *
 * 功能：将 Claude Code 的请求转发给 claw 的 HTTP API
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

// 1. 创建 MCP Server 实例
const server = new Server(
  {
    name: 'claw-bridge-server',
    version: '0.1.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// 2. 注册可用工具（告诉 Claude Code 能做什么）
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'claw_execute',
        description: '在 claw 系统中执行命令',
        inputSchema: {
          type: 'object',
          properties: {
            command: {
              type: 'string',
              description: '要执行的命令',
            },
            params: {
              type: 'object',
              description: '命令参数（可选）',
            },
          },
          required: ['command'],
        },
      },
      {
        name: 'claw_status',
        description: '获取 claw 系统状态',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
    ],
  };
});

// 3. 处理工具调用（实际执行逻辑）
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    // 配置 claw 的 API 地址
    const CLAW_API_BASE = 'http://localhost:3000/api'; // 根据实际情况修改

    switch (name) {
      case 'claw_execute': {
        // 调用 claw 的执行 API
        const response = await fetch(`${CLAW_API_BASE}/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            command: args.command,
            params: args.params || {},
          }),
        });

        const result = await response.json();

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      case 'claw_status': {
        // 获取 claw 状态
        const response = await fetch(`${CLAW_API_BASE}/status`);
        const result = await response.json();

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`未知工具: ${name}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `错误: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// 4. 启动服务器（使用 stdio 传输）
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Claw MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
