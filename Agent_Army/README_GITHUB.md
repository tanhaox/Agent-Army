# Agent Army - AI价值投资分析系统

<div align="center">

**让AI价值投资更智能、更透明、更高效！**

[![Version](https://img.shields.io/badge/version-v2.1-blue)](https://github.com/tanhaox/Agent-Army/releases)
[![Python](https://img.shields.io/badge/python-3.10+-green)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

</div>

---

## 🎯 项目概述

**Agent Army** 是一个基于AI代理的价值投资分析系统，通过6大军团协同工作，为投资者提供全方位的股票分析服务。

### 核心特性

- 🤖 **6大军团协同** - 产业分析、热点捕捉、个股挖掘、目标预测、策略执行、结果验证
- 📊 **全面分析维度** - 技术面、基本面、资金面、情绪面、政策面
- 🎨 **现代化UI** - 基于Streamlit的响应式Web界面
- 🔧 **灵活配置** - 支持多种AI模型（OpenAI、Zhipu AI、DeepSeek）
- 📈 **可视化报告** - 图表展示、数据导出、历史回溯

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- pip 包管理器

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动应用

**Windows**:
```bash
start_ps1.bat
```

**Linux/Mac**:
```bash
bash start_web.sh
```

应用启动后，访问: `http://localhost:8501`

---

## 📖 功能模块

### 1. 🏠 Dashboard（仪表板）
- 系统概览
- 快速操作
- 最新任务

### 2. 🤖 Agent状态（军团状态）
- 6大军团实时状态
- Agent任务分配
- 性能监控

### 3. 📋 任务管理
- 创建分析任务
- 任务队列管理
- 执行进度跟踪

### 4. 📊 分析报告
- 综合评分
- 技术面分析
- 基本面分析
- 风险评估

### 5. 💼 投资组合
- 持仓管理
- 收益分析
- 风险控制

### 6. 🌐 市场监控
- 实时行情
- 涨跌幅排行
- 成交量分析

### 7. ⚙️ 系统配置
- API配置
- 模型配置
- 日志管理

### 8. 📖 导航指南
- 快速开始
- 功能说明
- 常见问题

---

## 🎨 6大军团

| 军团 | 颜色 | 功能 | Agent数量 |
|------|------|------|----------|
| 🏭 **产业分析军团** | 🔵 蓝色 | 产业链分析、宏观经济、政策影响 | 5个 |
| 🔥 **热点捕捉军团** | 🟠 橙色 | 资金流向、市场情绪、新闻监控 | 4个 |
| 🎯 **个股挖掘军团** | 🟢 绿色 | 财务健康、成长性、历史周期 | 4个 |
| 🎯 **目标预测军团** | 🟡 琥珀色 | 估值模型、目标定价、利润预测 | 5个 |
| ⚔️ **策略执行军团** | 🟣 紫色 | 买卖时机、仓位管理、风险控制 | 7个 |
| ✅ **结果验证军团** | 🔷 青色 | 回测分析、性能归因、预测验证 | 7个 |

**总计**: 32个专业Agent协同工作

---

## 🔧 技术架构

### 后端技术
- **Python 3.10+** - 核心语言
- **Streamlit 1.28+** - Web框架
- **Pandas** - 数据处理
- **Plotly** - 数据可视化

### AI模型
- **OpenAI** - GPT-4/GPT-3.5
- **Zhipu AI** - GLM-4
- **DeepSeek** - DeepSeek-V3

### 数据源
- **Tushare** - A股数据
- **AKShare** - 金融数据
- **东方财富** - 实时行情
- **Yahoo Finance** - 港股美股

---

## 📁 项目结构

```
Agent_Army/
├── src/
│   ├── agents/          # AI代理
│   │   ├── business/    # 业务层Agent（32个）
│   │   └── management/  # 管理层Agent（4个）
│   ├── core/            # 核心功能
│   │   ├── pages_v2/    # Web页面
│   │   ├── tools/       # 工具库
│   │   └── config/      # 配置管理
│   └── workflows/       # 工作流
├── tests/               # 测试代码
├── docs/                # 文档
├── config/              # 配置文件
├── examples/            # 示例代码
└── web_app_v2.py        # 主应用
```

---

## 🔐 配置说明

### API配置

首次使用需要配置API密钥：

1. 复制配置模板:
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，添加API密钥:
```env
# Tushare API（必需）
TUSHARE_TOKEN=your_tushare_token

# OpenAI API（可选）
OPENAI_API_KEY=your_openai_api_key

# Zhipu AI API（可选）
ZHIPU_API_KEY=your_zhipu_api_key
```

3. 在Web界面中配置:
   - 前往"⚙️ 系统配置"
   - 填写API密钥
   - 保存配置

---

## 📊 数据更新

### 手动更新
- 在Web界面点击"刷新数据"按钮

### 自动更新
- 系统会自动获取最新数据
- 更新频率可在配置中调整

---

## 🧪 测试

运行测试套件:

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_agent_status_v3.py

# 查看测试覆盖率
pytest --cov=src tests/
```

---

## 📝 更新日志

### v2.1 (2026-03-15) - Phase 3 深度优化 ⭐
- ✅ Agent状态页面 - 扁平化网格布局
- ✅ 任务管理页面 - 卡片式布局
- ✅ 分析报告页面 - 完整增强
- ✅ 系统配置页面 - 优化重构
- ✅ 导航指南页面 - 新增功能
- ✅ 100% Design Tokens 合规
- ✅ 6大军团主题色完整实施

### v2.0 (2026-03-14) - Phase 2 基础功能
- ✅ 8个核心页面
- ✅ 32个业务Agent
- ✅ 完整工作流

### v1.0 (2026-03-13) - 初始版本
- ✅ 基础架构
- ✅ 核心Agent
- ✅ Web界面

---

## 🤝 贡献指南

欢迎贡献代码、报告bug或提出新功能建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/tanhaox/Agent-Army/issues)
- **邮箱**: tanhaox@example.com

---

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！

特别感谢：
- Tushare 数据平台
- OpenAI AI模型
- Zhipu AI GLM模型
- Streamlit 框架

---

## 📚 相关文档

- [完整文档](docs/)
- [API文档](API.md)
- [架构设计](ARCHITECTURE.md)
- [快速开始](docs/QUICK_START_V2.md)
- [用户指南](docs/USER_GUIDE_V2.md)
- [版本更新](docs/VERSION_2.1_RELEASE_NOTES.md)

---

<div align="center">

**🎖️ Agent Army - 让AI价值投资更智能、更透明、更高效！**

Made with ❤️ by [tanhaox](https://github.com/tanhaox)

</div>
