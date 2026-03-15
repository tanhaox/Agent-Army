# Agent Army - Web界面使用指南

## 🚀 快速启动

### 方式1: 双击启动(Windows)

```bash
双击 start_web.bat
```

### 方式2: 命令行启动

```bash
cd C:/AI-Agent-Local/Agent_Army
streamlit run web_app.py
```

### 方式3: 指定端口

```bash
streamlit run web_app.py --server.port 8501 --server.address localhost
```

---

## 📋 功能说明

### 🏠 主页
- 项目概览
- 组织架构展示
- Phase 0完成度
- 下一步计划

### 🤖 Agent状态
- 管理层Agent状态监控
- Agent能力和工具展示
- 业务层Agent规划

### 📋 任务管理
- 下达任务(Phase 1实现执行逻辑)
- 查看任务历史
- 任务状态跟踪

### 📊 报告查看
- 投资分析报告(Phase 1实现)
- Phase 0完成报告
- 报告历史记录

### ⚙️ 系统配置
- 配置文件检查
- 环境变量说明
- 系统信息展示

---

## 💡 使用提示

1. **首次使用**:
   - 确保已安装依赖: `pip install -r requirements.txt`
   - 复制环境变量: `cp .env.template .env`
   - 填写实际API密钥

2. **Web界面**:
   - 默认地址: http://localhost:8501
   - 自动刷新: 代码修改后自动重载
   - 支持多标签页同时访问

3. **当前限制**:
   - Phase 0只提供界面框架
   - Agent执行逻辑将在Phase 1实现
   - 投资分析报告将在Phase 1生成

---

## 🔧 故障排除

### 问题1: 端口被占用
```bash
# 使用其他端口
streamlit run web_app.py --server.port 8502
```

### 问题2: 模块找不到
```bash
# 确保在项目根目录
cd C:/AI-Agent-Local/Agent_Army
streamlit run web_app.py
```

### 问题3: 中文乱码
```bash
# 确保终端使用UTF-8编码
chcp 65001
streamlit run web_app.py
```

---

## 📊 当前状态

- ✅ Web界面框架完成
- ✅ 管理层Agent正常运行
- ⏳ 业务层Agent待建设(Phase 1)
- ⏳ 投资分析功能待实现(Phase 1)

---

**下一步**: Phase 1 核心军团建设
