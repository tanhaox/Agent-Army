# dashboard.md — 进度 / 完成度子系统

> **决策依据**：B3（横纵向研判补遗）
> **重要性**：🟡 **重要**（统一"书进度"概念；`dashboard.html` 的实现依据）
> **状态**：✅ 完整版
> **关联**：MVP_AUTHORITY §五 / web_spec_sync.md / kickoff_meeting / write

---

## 🎯 系统职责

为每本书维护一个**统一进度口径**——解决"dashboard 算完成度用什么数据"的问题。

**核心承诺**：

- ✅ 单一定义：`completion` = `已填设定维度数 / 6`
- ✅ Dashboard、命令、提示都基于这个数据
- ✅ 没有"进度条百分比"的争议

---

## 📐 完成度维度

每本书有 6 维度可填：

| # | 设定维度 | 文件 | 必填字段数 |
|---|---------|------|-----------|
| 1 | 世界观 | `settings/01-world.md` | 5 |
| 2 | 人物 | `settings/02-characters.md` | N（角色数） |
| 3 | 框架 | `settings/03-framework.md` | 3 |
| 4 | 基调 | `settings/04-tone.md` | 4 |
| 5 | 伏笔（设定阶段的伏笔预埋）| `settings/05-foreshadow.md` | ≥1 |
| 6 | 受众 | `settings/06-audience.md` | 3 |

**完成度算法**：

```python
def calc_completion(book_name):
    """返回每维度完成度 + 总分"""
    dimensions = ["01-world", "02-characters", "03-framework", "04-tone", "05-foreshadow", "06-audience"]
    completed = []
    for dim in dimensions:
        path = f"books/{book_name}/settings/{dim}.md"
        if file_exists(path) and len(parse_frontmatter(path)) > MIN_FIELDS[dim]:
            completed.append(dim)
    return {
        "completed": len(completed),
        "total": 6,
        "percent": round(len(completed) / 6 * 100, 1),
        "missing": [dim for dim in dimensions if dim not in completed],
        "kickoff_passed": parse_meta(book_name).get("kickoff_passed", False),
    }
```

---

## 📊 Dashboard 多口径数据

虽然"进度"主口径是设定完成度，但 dashboard 还需要其他数据：

```yaml
dashboard_data:
  # 主进度（设定完成度）
  settings_completion:
    completed: 4
    total: 6
    percent: 66.7
    missing: [05-foreshadow, 06-audience]
  
  # 阶段状态
  stage_state:
    step1_setup: ✅      # 6 维度已填
    step2_kickoff: 🚧    # 立项会进行中 / 未通过
    step3_writing: ⏸️   # 未开始
    step4_audit: ⏸️     # 未开始
  
  kickoff_state:
    last_run: 2026-07-10T15:00:00
    decision: must_fix
    attempts: 3
    can_advance_to_writing: false
  
  # 章节进度
  chapter_stats:
    written: 0
    target_total: 200
    last_chapter: null
    last_chapter_word_count: 0
  
  # 设定派生
  voice_print_state:
    generated: false
    reason: kickoff_meeting 未通过
  
  # 警告（连锁）
  warnings:
    - "立项会仍未通过"
    - "声纹未派生"
```

---

## 🔌 CLI 命令

```bash
# 查询书的进度
python -m ai_coauthor dashboard --book <name>

# 输出 JSON 给 web / 其他命令
python -m ai_coauthor dashboard --book <name> --format json
```

## 输出 schema

```yaml
book_name: str
settings_completion: object
stage_state: object
kickoff_state: object
chapter_stats: object
voice_print_state: object
warnings: array of str
computed_at: ISO 8601
```

---

## 🔗 与其他子系统的接口

### 写入点

- **kickoff_meeting** 通过时 → 更新 `kickoff_state` + 可能派生 voice_print
- **write** 保存章节时 → 更新 `chapter_stats` (written += 1)
- **setup_consult** 完成设定后 → 更新 `settings_completion`
- **factual extraction** 成功时 → 更新 `settings_completion` 部分字段

### 读出点

- **dashboard.html** 渲染数据
- **写章节时** 提示"剩余 X 个设定待补"
- **cumulative_audit** 触发时验证 "kickoff_passed=true"

### 数据落地位置

- **不单独建文件** —— dashboard 数据 = 派生数据
- 所有数据从 `books/<name>/` 现有文件 + `meta.yaml` 计算
- 命令不写中间状态文件

---

## 🧪 测试用例（MVP 必过）

1. **空书**：6 维度全缺 → completion=0% + missing=所有 6
2. **半填**：4 个维度有内容 → completion=66.7%
3. **完成设定**：6 个维度都有 → completion=100% + step1_setup=✅
4. **kickoff 通过**：completion=100% + kickoff_passed=true → step2_kickoff=✅
5. **写一章**：chapter_stats.written += 1 + last_chapter 更新
6. **派生声纹**：kickoff 通过后 voice_print_state.generated=true

---

## 📋 MVP vs Phase 2

| 项 | MVP | Phase 2 |
|---|-----|---------|
| completion 算法（设定完成度） | ✅ | ✅ |
| dashboard 命令 | ✅ | ✅ |
| kickoff_state 跟踪 | ✅ | ✅ |
| chapter_stats | ✅ | ✅ |
| voice_print_state | ✅ | ✅ |
| Phase 4: dashboard.html 可视化 | ❌ | ❌（Phase 4 Web）|
| Phase 2: 完成度权重（每维度不等权）| ❌ | ✅ |
| Phase 2: 完成度估算（每个字段必填/选填）| ❌ | ✅ |

---

## 🔗 关联

- 子系统：所有其他子系统（这是中枢数据视图）
- Web spec：`dashboard.html`
- 决策：B3（横纵向研判补遗）

---

## 📌 元信息

- **创建日期**：2026-07-10
- **重要性**：🟡 重要（统一进度概念）
- **关联决策**：B3（研判补遗）
- **关联子系统**：所有其他子系统 / 命令
- **关联命令**：`dashboard`（MVP 9 命令之外，**轻量工具命令**）
