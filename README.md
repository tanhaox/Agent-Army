# AI-Agent-Local

AI 代理本地开发环境 - 集成多种 AI 技能和应用项目的统一开发平台。

## 📖 项目简介

AI-Agent-Local 是一个统一的本地 AI 开发环境，包含技能（Skills）、应用（Apps）、工具（Tools）三类项目，旨在提供可复用、可维护、可扩展的 AI 能力。

### 核心特点

- ✅ **统一管理**：所有项目集中管理，结构清晰
- ✅ **高度模块化**：基于技能模板，易于扩展
- ✅ **本地优先**：使用 Ollama 本地模型，保护隐私
- ✅ **完整规范**：遵循代码可维护性规范
- ✅ **中文友好**：完整中文文档，UTF-8 编码

---

## 📁 项目结构

```
AI-Agent-Local/
│
├── projects/              # 【核心】所有项目
│   ├── skills/           # 技能类项目（可复用功能）
│   │   ├── api_manager/  # API 管理技能
│   │   ├── ollama_ai/    # Ollama AI 技能
│   │   └── local_ocr/    # 本地 OCR 技能
│   │
│   ├── apps/             # 应用类项目（完整应用）
│   │   └── intelligent-tutor/  # 智能辅导系统
│   │
│   └── tools/            # 工具类项目（小工具）
│       ├── ddg-search/   # DuckDuckGo 搜索
│       ├── github-ai/    # GitHub AI 助手
│       └── file-operations/  # 文件操作工具
│
├── shared/               # 【共享】共享资源
│   ├── lib/              # 共享库
│   ├── templates/        # 项目模板
│   └── configs/          # 共享配置
│
├── docs/                 # 【文档】全局文档
│   ├── 项目组织规范.md
│   ├── 代码可维护性规范.md
│   └── 开发指南.md
│
├── logs/                 # 【日志】全局日志
│
├── github_downloads/     # 【外部】第三方代码
│
├── archives/             # 【归档】旧项目
│
└── README.md             # 本文档
```

---

## 🎯 项目分类

### Skills（技能）- 可复用功能模块

| 项目 | 功能 | 状态 | 文档 |
|------|------|------|------|
| **api_manager** | 统一管理多个 API KEY | ✅ 活跃 | [README](projects/skills/api_manager/README.md) |
| **ollama_ai** | Ollama AI 对话和生成 | ✅ 活跃 | [README](projects/skills/ollama_ai/README.md) |
| **local_ocr** | 本地图片文字识别 | ✅ 活跃 | - |

### Apps（应用）- 完整业务应用

| 项目 | 功能 | 状态 | 文档 |
|------|------|------|------|
| **intelligent-tutor** | 智能辅导系统（原"给我讲课"） | ✅ 活跃 | - |

### Tools（工具）- 独立小工具

| 项目 | 功能 | 状态 | 文档 |
|------|------|------|------|
| **ddg-search** | DuckDuckGo 搜索工具 | ✅ 活跃 | [README](projects/tools/ddg-search/README.md) |
| **github-ai** | GitHub AI 助手 | ✅ 活跃 | [README](projects/tools/github-ai/README.md) |
| **file-operations** | 文件操作工具集 | ✅ 活跃 | [README](projects/tools/file-operations/README.md) |

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.7+
- **Ollama**: 本地 LLM 服务（[下载地址](https://ollama.ai)）
- **Git**: 版本控制工具

### 安装步骤

```bash
# 1. 克隆或下载本项目
cd AI-Agent-Local

# 2. 安装项目依赖（根据需要选择）
# API 管理技能
pip install -r projects/skills/api_manager/requirements.txt

# Ollama AI 技能
pip install -r projects/skills/ollama_ai/requirements.txt

# 3. 启动 Ollama 服务
ollama serve

# 4. 运行项目
# 例如：启动 Ollama AI Web
cd projects/skills/ollama_ai
python ollama_web.py
```

---

## 📚 开发文档

### 核心规范

| 文档 | 说明 | 链接 |
|------|------|------|
| **项目组织规范** | 目录结构、命名规范、项目分类 | [查看](docs/项目组织规范.md) |
| **代码可维护性规范** | 模块化设计、命名规范、配置管理 | [查看](docs/代码可维护性规范.md) |
| **开发指南** | 工作流程、AI 辅助开发、测试标准 | [查看](docs/开发指南.md) |

### 新项目创建

```bash
# 1. 使用模板创建
cp -r shared/templates/skill_template projects/skills/my-new-skill

# 2. 或手动创建
mkdir -p projects/skills/my-new-skill/{tests,docs,logs}

# 3. 按照《项目组织规范》编写代码
# 4. 按照《代码可维护性规范》保证质量
# 5. 在本文件中登记项目信息
```

---

## 🛠️ 技术栈

### 核心框架

- **Flask**: Web 服务框架
- **LangChain**: AI 应用开发框架
- **Chroma**: 向量数据库
- **Ollama**: 本地 LLM 推理

### 主要依赖

- **langchain-ollama**: Ollama 集成
- **langchain-openai**: OpenAI API 集成
- **flask-cors**: CORS 支持
- **pytesseract**: OCR 引擎
- **requests**: HTTP 请求

---

## 📊 项目统计

| 类型 | 数量 | 说明 |
|------|------|------|
| **Skills** | 3 | 技能项目 |
| **Apps** | 1 | 应用项目 |
| **Tools** | 3 | 工具项目 |
| **总计** | 7 | 活跃项目 |

---

## 🔄 更新日志

### 2026-02-08

- ✅ 完成项目重组，建立标准目录结构
- ✅ 创建完整的项目规范文档
- ✅ 重构工具脚本为标准项目结构
- ✅ 迁移现有项目到新目录
- ✅ 创建根目录索引文档

---

## 🤝 贡献指南

欢迎贡献新的技能、应用或工具！

### 开发流程

1. 阅读核心规范文档
2. 使用项目模板创建新项目
3. 按照规范编写代码
4. 添加测试和文档
5. 在 README.md 中登记项目

### AI 辅助开发

使用 Claude Code 或其他 AI 工具时，请参考《开发指南》中的最佳实践。

---

## 📞 联系方式

- **项目位置**: `C:\AI-Agent-Local`
- **文档位置**: `docs/`
- **问题反馈**: 请创建 Issue 或查看项目文档

---

## 📄 许可证

MIT License

---

**最后更新**: 2026-02-08
**维护者**: AI-Agent-Local
**版本**: 1.0.0
