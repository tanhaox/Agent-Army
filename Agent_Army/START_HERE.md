# 🚀 Agent Army 启动卡片

## ⚡ 快速启动（3步）

### 步骤1: 打开CMD
```
Win+R → 输入 cmd → 回车
```

### 步骤2: 进入目录
```bash
cd c:\AI-Agent-Local\Agent_Army
```

### 步骤3: 启动
```bash
start.bat
```

### ✅ 成功标志
看到这个就成功了：
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
```

---

## 🎯 访问Dashboard

浏览器自动打开，或手动访问：
```
http://localhost:8501
```

---

## 🛑 停止服务

在CMD窗口按：
```
Ctrl + C
```

---

## 🔧 遇到问题？

### 问题1: Python未找到
```bash
# 安装Python 3.8+
# https://www.python.org/downloads/
```

### 问题2: Streamlit未找到
```bash
pip install streamlit
```

### 问题3: 缺少依赖
```bash
pip install -r requirements.txt
```

### 问题4: 端口被占用
```bash
# start.bat会自动处理
# 或手动杀进程
taskkill /F /IM python.exe
```

---

## 📞 需要帮助？

查看详细文档：
- [完整启动说明](docs/启动说明.md)
- [快速开始指南](00-快速开始.md)
- [项目README](README.md)

---

**创建时间**: 2026-03-20
**适用版本**: Agent Army v2.0
