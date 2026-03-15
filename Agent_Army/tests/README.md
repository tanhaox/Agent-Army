# Agent Army 测试目录

**版本**: v1.0
**最后更新**: 2026-03-15

---

## 📋 目录结构

```
tests/
├── README.md                          # 本文件 - 测试目录说明
├── SMOKE_TEST_GUIDE.md                # 冒烟测试完整指南
├── SMOKE_TEST_COMPLETION_REPORT.md    # 冒烟测试完成报告
├── MANUAL_TEST_CHECKLIST.md           # 手动测试清单
├── smoke_test.py                      # 自动化冒烟测试脚本
├── test_all_pages.py                  # 页面导入测试
├── test_pages_import.py               # 快速导入测试
├── test_imports.py                    # 模块导入测试
└── [其他测试文件...]
```

---

## 🚀 快速开始

### 运行冒烟测试（推荐）

```bash
# 方式1：使用批处理脚本（最简单）
run_smoke_test.bat

# 方式2：直接运行Python脚本
python tests/smoke_test.py

# 方式3：运行特定套件
python tests/smoke_test.py --suite import
python tests/smoke_test.py --suite design-tokens
python tests/smoke_test.py --suite agents
```

### 生成测试报告

```bash
# 生成JSON报告
python tests/smoke_test.py --report --output report.json

# 详细输出
python tests/smoke_test.py --verbose
```

---

## 📊 测试类型

### 1. 冒烟测试 (Smoke Test) ⭐
**目的**: 快速验证核心功能
**执行时间**: ~1秒（自动化）+ 5分钟（手动）
**时机**: 每次更新、升级、bug修复后

**文件**:
- `smoke_test.py` - 自动化测试脚本
- `SMOKE_TEST_GUIDE.md` - 完整测试指南
- `MANUAL_TEST_CHECKLIST.md` - 手动测试清单

**测试套件**:
- ✅ 模块导入测试（14个）
- ✅ Design Tokens系统测试（21个）
- ✅ Agent初始化测试（3个）
- ✅ 页面渲染测试（8个）
- ✅ 配置管理测试（5个）
- ✅ 基本工作流测试（2个）

---

### 2. 页面测试 (Page Tests)
**目的**: 验证所有页面可以正常导入
**执行时间**: ~1秒

**文件**:
- `test_all_pages.py` - 所有页面测试
- `test_pages_import.py` - 页面导入测试
- `test_imports.py` - 模块导入测试

---

### 3. 单元测试 (Unit Tests)
**目的**: 测试单个函数和类
**执行时间**: 不定

**文件**:
- `test_agent_status_v3.py` - Agent状态页面测试
- `test_task_management_v3.py` - 任务管理页面测试
- `test_analysis_reports_v3.py` - 分析报告页面测试
- `test_system_config_v3.py` - 系统配置页面测试
- `test_*_v3.py` - 其他v3版本测试
- `test_*.py` - 其他单元测试

---

## 🎯 测试结果

### 最新测试结果（2026-03-15）

```
✅ 冒烟测试通过
总计: 53/53 (100%)
耗时: 0.8秒

详情见: SMOKE_TEST_COMPLETION_REPORT.md
```

---

## 📝 测试最佳实践

### 1. 测试时机
- ✅ **代码提交前**: 运行冒烟测试
- ✅ **功能升级后**: 运行完整测试+手动测试
- ✅ **Bug修复后**: 运行相关测试
- ✅ **发布前**: 运行所有测试

### 2. 测试流程
1. **快速验证**: `run_smoke_test.bat` (1秒)
2. **如测试失败**: 修复问题
3. **重新测试**: 直到通过
4. **手动测试**: 核心功能验证（5分钟）
5. **发布**: 测试通过后可以发布

### 3. 失败处理
- 查看错误信息
- 修复问题
- 重新测试
- 确保通过

---

## 🔄 持续集成

### GitHub Actions
测试系统支持CI/CD集成，示例配置见 `SMOKE_TEST_GUIDE.md`。

### 本地Hook
可以在git commit前自动运行测试：

```bash
# .git/hooks/pre-commit
#!/bin/bash
python tests/smoke_test.py
if [ $? -ne 0 ]; then
    echo "测试失败，提交被拒绝"
    exit 1
fi
```

---

## 📚 相关文档

### 测试文档
- [冒烟测试指南](SMOKE_TEST_GUIDE.md) - 完整测试文档
- [手动测试清单](MANUAL_TEST_CHECKLIST.md) - 手动测试步骤
- [完成报告](SMOKE_TEST_COMPLETION_REPORT.md) - 测试系统总结

### 项目文档
- [用户指南](../docs/USER_GUIDE_V2.md)
- [设计规范](../docs/WEB_DESIGN_V2.md)
- [快速开始](../docs/QUICK_START_V2.md)

---

## 🛠️ 维护指南

### 添加新测试
1. 在相应的测试文件中添加测试函数
2. 更新测试文档
3. 运行测试验证
4. 提交代码

### 更新测试
1. 根据新功能更新测试用例
2. 移除过时的测试
3. 优化测试性能
4. 更新文档

### 测试调试
```bash
# 详细输出
python tests/smoke_test.py --verbose

# 单个套件
python tests/smoke_test.py --suite import

# 生成报告
python tests/smoke_test.py --report
```

---

## 🎯 快速参考

### 常用命令

```bash
# 运行所有测试
python tests/smoke_test.py

# 快速测试
run_smoke_test.bat

# 详细输出
python tests/smoke_test.py --verbose

# 生成报告
python tests/smoke_test.py --report

# 特定套件
python tests/smoke_test.py --suite import
python tests/smoke_test.py --suite design-tokens
python tests/smoke_test.py --suite agents
```

### 测试通过标准
- ✅ 所有自动化测试100%通过
- ✅ 关键手动测试项100%通过
- ✅ 无P0/P1级别问题

---

## 📞 支持

如有问题或建议，请：
1. 查看测试文档
2. 运行详细测试模式
3. 记录问题到Issue
4. 联系开发团队

---

**测试系统版本**: v1.0
**最后更新**: 2026-03-15
**维护者**: Agent Army开发团队

---

**🎖️ Agent Army - 让AI价值投资更智能、更透明、更高效！**
