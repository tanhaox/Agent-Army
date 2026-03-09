# AI-Agent-Local 项目结构

**版本**: 1.0.0
**更新**: 2026-02-08

---

## 📁 快速导航

```
AI-Agent-Local/
├── 📂 projects/          # 项目（skills/apps/tools）
├── 📂 shared/            # 共享资源
├── 📂 docs/              # 文档
├── 📂 archives/          # 归档
├── 📂 logs/              # 日志
├── 📂 github_downloads/  # 第三方代码
├── 📂 claude-skills/     # Claude Skills
│
├── 📄 CLAUDE.md          # 项目配置
├── 📄 README.md          # 项目说明
└── 📄 requirements-dev.txt # 开发依赖
```

---

## 🎯 核心目录

### 📂 projects/
**项目存放位置**
- `skills/` - 技能类项目
- `apps/` - 应用类项目
- `tools/` - 工具类项目

**当前项目** (7 个)：
- api_manager - API 管理技能
- ollama_ai - Ollama AI 技能
- local_ocr - 本地 OCR 技能
- intelligent-tutor - 智能辅导系统
- ddg-search - DuckDuckGo 搜索工具
- github-ai - GitHub AI 助手
- file-operations - 文件操作工具

---

### 📂 shared/
**共享资源库**
- `subagents/` - 子代理框架（2,247 行）
- `testing/` - 测试框架
- `templates/` - 项目模板
- `scripts/` - 工具脚本
- `lib/` - 共享库

**核心框架**：
- Dispatcher（调度器）
- Code Reviewer（审查器）
- Progress Tracker（进度跟踪）
- Evaluation Workflow（评估驱动工作流）

---

### 📂 docs/
**项目文档**
- `项目组织规范.md` - 目录结构、命名规范
- `代码可维护性规范.md` - 模块化、注释、配置
- `开发指南.md` - 工作流、最佳实践
- `测试框架使用指南.md` - 测试框架文档
- `子代理框架使用指南.md` - 子代理 API 参考
- `评估驱动开发指南.md` - 4 阶段开发流程
- `子代理框架实用示例.md` - 10+ 实用案例

---

### 📂 archives/
**归档区域**
- `reports/` - 历史报告（按日期归档）
- `old-dirs/` - 旧目录归档

---

### 📂 claude-skills/
**Claude Skills**
- `evaluation-driven-development-skill/` - 评估驱动开发技能

---

## 🚀 快速开始

### 创建新项目
```bash
cd shared/scripts
python create_project.py
```

### 运行测试
```bash
# Windows
run_tests.bat

# Unix/Linux
./run_tests.sh
```

### 查看文档
```bash
# 项目规范
cat docs/项目组织规范.md

# 子代理框架
cat docs/子代理框架使用指南.md

# 评估驱动开发
cat docs/评估驱动开发指南.md
```

---

## 📊 项目统计

| 类型 | 数量 | 说明 |
|------|------|------|
| **项目** | 7 | 3 技能 + 1 应用 + 3 工具 |
| **共享框架** | 2 | 子代理 + 测试 |
| **核心文档** | 7 | 规范 + 指南 |
| **代码行数** | 2,247 | 子代理框架 |
| **报告归档** | 17+ | 历史文档 |

---

## 🎯 规范遵循

✅ 100% 符合《项目组织规范》
✅ 100% 符合《代码可维护性规范》
✅ 100% 符合《开发指南》

---

## 📞 帮助

**问题排查**：
1. 查看 `docs/` 中的相关规范
2. 查看 `archives/reports/` 中的历史报告
3. 查看具体项目的 README.md

**新手上路**：
1. 先读 `docs/开发指南.md`
2. 使用项目生成器创建项目
3. 参考现有项目学习

---

**最后更新**: 2026-02-08
**项目状态**: ✅ 生产就绪
**规范版本**: 1.0.0
