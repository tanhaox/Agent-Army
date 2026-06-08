# Stock Analyst — A股量化分析系统

## 功能

- **TG 信号扫描**: V11.2 18步精准买卖指标，全市场 4,358 只股票扫描
- **11维深度评分**: 市值/流动性/估值/资金流/杠杆/基本面/筹码/筹码分布/标签/事件/跨市场
- **5 原型分类**: 大盘蓝筹/小盘题材/成长科技/价值防御/周期资源，各自独立评分权重
- **潜伏猎手**: 首板回调 N 字突破，4 阶段过滤
- **DeepSeek LLM 深度分析**: 百度千帆搜索新闻 + DeepSeek 推理 + 评分调整
- **外部分析反哺**: 浏览器扩展一键发送 DeepSeek 网页版分析结果
- **Bayesian 自学习**: Normal-Normal 共轭更新，4 参数组独立优化，T+5 滚动回测
- **持仓管理**: 组合分析、集中度警告、浮亏告警

## 启动

```bash
# 一键启动
StockAnalyst.bat

# 或手动分别启动
cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000
cd frontend && npx vite
```

## 浏览器扩展安装

1. 打开 `edge://extensions/` 或 `chrome://extensions/`
2. 开启「开发人员模式」
3. 加载解压缩的扩展 → 选择 `browser-extension/` 目录

## 技术栈

- 后端: Python 3.13 + FastAPI + SQLAlchemy 2.0 + PostgreSQL + asyncpg
- 前端: React 19 + TypeScript + Vite 8 + Ant Design 6
- 数据源: Tushare Pro API
- AI: DeepSeek API + 百度千帆 AI Search
