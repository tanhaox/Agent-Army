# PolicyTool - 政策新闻数据采集工具

## 📋 功能概述

**PolicyTool** 是一个集成了多个数据源的政策新闻采集工具，支持：

- ✅ **Tushare Pro 财经新闻**（1000条，使用Cookie认证）
- ✅ **中国政府网政策**（1020条，JSON接口）
- ✅ **国家发改委政策**（56条，网页爬取）
- ✅ **SQLite数据库存储**（自动排重）
- ✅ **全文搜索功能**
- ✅ **JSON导出功能**
- ✅ **定时自动采集**（每天上下午各一次）

---

## 🚀 快速开始

### 1️⃣ 手动执行（测试用）

```bash
# 运行采集脚本
python C:\AI-Agent-Local\policy_tool.py
```

**输出示例**：
```
============================================================
PolicyTool - 政策新闻数据采集工具
============================================================

[1/3] Fetching Tushare Pro news...
[SUCCESS] Fetched 1000 news items

[2/3] Fetching Gov.cn policies...
[SUCCESS] Fetched 1020 policy items

[3/3] Fetching NDRC policies...
[SUCCESS] Fetched 56 policy items

Total fetched: 2076 items
Saved 1919 new items (duplicates filtered)

[Database Statistics]
Total items: 1919
Latest date: 2026-03-15

By source:
  Tushare Pro: 843
  中国政府网: 1020
  国家发改委: 56
```

---

## ⏰ 定时任务设置

### 方式1：Windows任务计划程序（推荐）

**步骤1**：右键点击 `setup_policy_scheduler.bat`，选择"以管理员身份运行"

**步骤2**：任务创建成功后，会自动在以下时间执行：
- 上午：09:00
- 下午：15:00

**管理命令**：
```bash
# 查看任务
schtasks /Query /TN "PolicyNews_Fetch_Morning"

# 删除任务
schtasks /Delete /TN "PolicyNews_Fetch_Morning" /F

# 手动触发任务
schtasks /Run /TN "PolicyNews_Fetch_Morning"
```

### 方式2：Python调度器（开发用）

```bash
# 安装依赖
pip install schedule

# 运行调度器
python C:\AI-Agent-Local\scheduler_policy_news.py
```

---

## 🔍 使用示例

### 基本使用

```python
from policy_tool import PolicyTool

# 初始化工具
tool = PolicyTool()

# 获取所有数据
all_policies = []
all_policies.extend(tool.fetch_tushare_news())
all_policies.extend(tool.fetch_gov_policies())
all_policies.extend(tool.fetch_ndrc_policies())

# 保存到数据库
saved = tool.save_to_db(all_policies)
print(f"保存了 {saved} 条新数据")

# 搜索
results = tool.search('央行', limit=10)
for item in results:
    print(f"{item['title']} - {item['source']}")
```

### 高级功能

```python
# 1. 获取统计信息
stats = tool.get_stats()
print(f"总数：{stats['total']}")
print(f"按来源：{stats['by_source']}")

# 2. 导出为JSON
tool.export_to_json('policies_export.json')

# 3. 搜索不同关键词
keywords = ['央行', '降息', 'GDP', '通胀']
for kw in keywords:
    results = tool.search(kw, limit=5)
    print(f"{kw}: 找到 {len(results)} 条")
```

---

## 📁 文件结构

```
C:\AI-Agent-Local\
├── policy_tool.py                    # 主工具类
├── scheduler_policy_news.py          # Python调度器版本
├── fetch_policy_news.bat             # Windows批处理脚本
├── setup_policy_scheduler.bat        # 定时任务安装脚本
├── policy_news.db                    # SQLite数据库
└── policies_export.json              # 导出的JSON文件
```

---

## 🔒 数据排重机制

**数据库约束**：
```sql
UNIQUE(title, source, publish_date)
```

**插入方式**：
```python
INSERT OR IGNORE INTO policies (...)
```

**效果**：
- 同一标题 + 同一来源 + 同一日期 = 视为重复
- 重复数据自动过滤，不会重复保存
- 多次爬取也不会占用额外硬盘空间

---

## ⚙️ 配置说明

### Cookie配置（Tushare Pro）

位置：`policy_tool.py` 第26行

```python
self.tushare_cookie = 'uid="2|1:0|10:1773285186|3:uid|12:MTAxNjY1NA==|afb938f4200448d1cf591d21cb4bd80a35bd3c3b087f4c27e041c9a3819dc8c8"; username=2|1:0|10:1773285186|8:username|12:MTM0KioqNTUy|222f214d539962e529bdf7cc055d3ed59d7ef8ad13c700aaff2fafa7bbf3ea77; session-id=f2b1682f-14f6-4f74-b5cd-16a302e0cd24'
```

**更新Cookie**：
1. 登录 Tushare Pro
2. 打开浏览器开发者工具（F12）
3. 复制Cookie值
4. 替换上述代码中的Cookie

### 数据库路径

默认路径：`C:/AI-Agent-Local/policy_news.db`

修改方式：
```python
tool = PolicyTool(db_path='C:/custom/path/news.db')
```

---

## 📊 数据源详情

| 数据源 | 数量 | 类型 | 认证 | 频率限制 |
|--------|------|------|------|----------|
| Tushare Pro | ~1000 | 财经新闻 | Cookie | 每天2次 |
| 中国政府网 | ~1020 | 政策文件 | 无 | 每天2次 |
| 国家发改委 | ~56 | 政策文件 | 无 | 每天2次 |

---

## ❓ 常见问题

### Q1: Cookie过期怎么办？

```bash
# 重新运行浏览器获取Cookie
# 然后更新 policy_tool.py 中的 tushare_cookie 变量
```

### Q2: 如何查看数据库内容？

```bash
# 使用SQLite命令行
sqlite3 C:\AI-Agent-Local\policy_news.db

# 查询命令
SELECT * FROM policies ORDER BY publish_date DESC LIMIT 10;
```

### Q3: 如何备份和恢复数据库？

```bash
# 备份
copy C:\AI-Agent-Local\policy_news.db C:\backup\policy_news_backup.db

# 恢复
copy C:\backup\policy_news_backup.db C:\AI-Agent-Local\policy_news.db
```

### Q4: 定时任务没有执行？

```bash
# 查看任务计划程序
taskschd.msc

# 检查任务历史记录
# 或手动触发测试
schtasks /Run /TN "PolicyNews_Fetch_Morning"
```

---

## 📝 版本历史

**v1.0.0** (2026-03-15)
- ✅ 集成3个数据源（Tushare Pro、中国政府网、发改委）
- ✅ 实现自动排重机制
- ✅ 支持全文搜索和JSON导出
- ✅ 创建Windows定时任务（每天2次）

---

## 🎯 后续优化建议

1. **数据清洗**：添加更智能的标题和内容提取
2. **分类标签**：使用AI对政策进行自动分类
3. **相似度检测**：检测相似政策，避免重复信息
4. **邮件通知**：重要政策自动邮件提醒
5. **Web界面**：开发可视化查询界面
6. **API接口**：提供REST API供其他程序调用

---

**创建日期**: 2026-03-15
**维护者**: AI Agent Team
**数据库位置**: `C:\AI-Agent-Local\policy_news.db`
