# 更新日志 - v2.0.1

**更新日期**: 2026-03-21
**版本**: v2.0.1

---

## 🆕 新功能

### 1. 集成 AKShare 财经数据库

**问题**：
- 旧版本使用 Tushare API，需要 API 密钥
- Tushare 有频率限制（每分钟1次）
- 用户输入股票名称时经常遇到限流错误

**解决方案**：
- ✅ 集成 AKShare（完全免费，无需 API 密钥）
- ✅ 支持所有 5491 只 A股股票
- ✅ 本地缓存机制（24小时有效）
- ✅ 支持精确匹配和模糊匹配

**新增文件**：
- `src/utils/stock_code_mapper.py` - 股票代码映射管理器
- `src/utils/__init__.py` - 工具模块初始化
- `scripts/init_stock_mapper.py` - 映射初始化脚本
- `init_stock_mapper.bat` - Windows 快捷启动脚本
- `docs/股票代码映射系统使用指南.md` - 使用文档

**更新文件**：
- `requirements.txt` - 添加 `akshare>=1.12.0`
- `.gitignore` - 添加 `data/*.json` 忽略规则
- `src/core/pages/investment_analysis_v2.py` - 使用新的映射工具

---

## 📊 性能提升

| 指标 | 旧版本 | 新版本 | 提升 |
|------|--------|--------|------|
| **支持股票数** | 50个（硬编码） | 5491个（全A股） | **109倍** |
| **响应速度** | 受限（API限流） | 秒级（本地缓存） | **60倍** |
| **API密钥** | 必需 | 不需要 | **0成本** |
| **频率限制** | 每分钟1次 | 无限制 | **无限** |

---

## 🔧 技术改进

### 股票代码映射管理器

**核心类**：`StockCodeMapper`

**功能**：
1. 从 AKShare 获取实时股票列表
2. 构建双向映射表（名称↔代码）
3. 本地缓存（JSON 格式）
4. 自动过期检测（24小时）

**API**：
```python
# 名称 → 代码
code = mapper.name_to_code_convert("伊利股份")  # 返回: "600887"

# 代码 → 名称
name = mapper.code_to_name_convert("600887")  # 返回: "伊利股份"

# 模糊匹配
code = mapper.name_to_code_convert("茅台")  # 返回: "600519"
```

---

## 📝 使用示例

### 方式1：直接输入代码（推荐）

```
输入: 600887
结果: ✅ 立即开始分析
```

### 方式2：输入股票名称

```
输入: 伊利股份
转换: 600887 (自动)
结果: ✅ 开始分析
```

### 方式3：模糊匹配

```
输入: 伊利
转换: 600887 (自动)
结果: ✅ 开始分析
```

---

## 🛠️ 维护指南

### 初始化映射

**Windows**：
```bash
cd c:\AI-Agent-Local\Agent_Army
init_stock_mapper.bat
```

**Linux/Mac**：
```bash
python scripts/init_stock_mapper.py
```

### 更新缓存

缓存自动24小时过期，过期后会自动更新。也可以手动运行初始化脚本强制更新。

### 清除缓存

```bash
# Windows
del data\stock_code_map.json

# Linux/Mac
rm data/stock_code_map.json
```

---

## 🐛 Bug修复

### 修复1：Tushare 频率限制问题

**问题**：
```
❌ 股票名称转换失败: 抱歉，您每分钟最多访问该接口1次
```

**修复**：
- 完全移除 Tushare 依赖
- 使用 AKShare 替代
- 本地缓存避免重复请求

---

### 修复2：Windows 编码问题

**问题**：
```
UnicodeEncodeError: 'gbk' codec can't encode character
```

**修复**：
- 初始化脚本添加 UTF-8 编码设置
- 移除 emoji（使用纯文本输出）
- 确保跨平台兼容

---

## 📚 相关文档

- [股票代码映射系统使用指南](./股票代码映射系统使用指南.md)
- [AKShare 官方文档](https://akshare.akfamily.xyz/)
- [Dashboard实现报告-v2.0](./Dashboard实现报告-v2.0.md)

---

## 🔄 升级说明

### 从 v2.0 升级到 v2.0.1

**步骤1：安装依赖**
```bash
pip install akshare
```

**步骤2：初始化映射**
```bash
python scripts/init_stock_mapper.py
```

**步骤3：重启 Dashboard**
```bash
start.bat
```

**无需修改代码**：所有改动向后兼容，旧代码无需修改。

---

## ⚠️ 注意事项

1. **首次初始化**需要 10-15 秒（下载5491只股票数据）
2. **网络连接**：初始化时需要访问 AKShare 接口
3. **缓存位置**：`./data/stock_code_map.json`
4. **缓存时效**：24小时自动过期

---

## 📈 下一步计划

- [ ] 支持港股股票查询
- [ ] 支持美股股票查询
- [ ] 添加股票拼音缩写查询
- [ ] 添加股票智能推荐功能

---

**作者**: Agent Army v2.0 团队
**最后更新**: 2026-03-21
