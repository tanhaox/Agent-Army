# Handoff: team-plan → team-exec

**任务**: Phase 3任务3.1 - Agent状态页面扁平化
**日期**: 2026-03-15

## Decided (已决定)

1. **设计文档**: 严格遵循 `docs/PHASE2_DASHBOARD_DESIGN_TASK.md` 的设计规范
2. **设计系统**: 100%使用Phase 1设计系统（Design Tokens、全局样式、UI组件）
3. **重构方向**:
   - 移除7个深层嵌套的标签页
   - 使用展开/折叠替代标签页
   - 扁平化信息架构，一屏展示更多内容
4. **军团主题色**: 使用 `DesignTokens.Colors.ARMY_*` 统一各军团颜色
5. **卡片设计**: 统一卡片样式（阴影、圆角、边框）

## Rejected (已拒绝)

1. **保留标签页结构** - 信息层级过深，不符合扁平化要求
2. **混用原生组件** - 不使用 `st.info()` 等原生组件，改用Design Tokens
3. **硬编码颜色** - 所有颜色必须从 `DesignTokens.Colors` 获取

## Risks (风险识别)

1. **现有代码结构复杂** - agent_status.py有310行，需要仔细重构
2. **Design Tokens应用不完整** - 需要确保100%覆盖所有颜色、字体、间距
3. **响应式设计挑战** - 扁平化后需要确保移动端适配正常
4. **性能问题** - 展开所有内容可能影响首屏加载时间

## Files (关键文件)

1. **目标文件**: `src/core/pages_v2/agent_status.py` (310行) - 需要重构
2. **设计系统**: `src/core/design_tokens.py` - Colors、Typography、Spacing、Radius等
3. **UI组件**: `src/core/ui_components.py` - 可复用组件（状态徽章、指标卡片等）
4. **全局样式**: `src/core/global_styles.py` - apply_global_styles()
5. **反馈组件**: `src/core/feedback.py` - toast_success, toast_error
6. **加载状态**: `src/core/loading_states.py` - show_skeleton_card

## Remaining (待执行阶段处理)

### team-exec阶段任务

**执行者**: designer agent

**任务列表**:
1. **子任务1**: 阅读设计文档
   - 阅读 `docs/PHASE2_DASHBOARD_DESIGN_TASK.md`
   - 阅读 `docs/PHASE3_PLAN.md`
   - 理解设计要求和验收标准

2. **子任务2**: 重构页面结构
   - 移除7个标签页（lines 24-32）
   - 实现展开/折叠交互
   - 扁平化信息架构

3. **子任务3**: 应用Design Tokens
   - 导入设计系统
   - 替换所有硬编码颜色
   - 使用Typography和Spacing

4. **子任务4**: 优化卡片设计
   - 军团卡片：使用ARMY_*主题色
   - Agent卡片：统一样式
   - 添加悬停效果

5. **子任务5**: 添加交互功能
   - 实时刷新按钮
   - 快速筛选功能
   - 性能监控（可选）

6. **子任务6**: 测试验证
   - 验证设计一致性100%
   - 测试页面加载时间 < 1秒
   - 测试移动端适配

**关键要求**:
- 所有颜色使用 `DesignTokens.Colors`
- 所有字体使用 `DesignTokens.Typography`
- 所有间距使用 `DesignTokens.Spacing`
- 军团主题色使用 `DesignTokens.Colors.ARMY_*`

**验收标准**:
- [ ] 信息扁平化，无深层嵌套
- [ ] 设计一致性100%
- [ ] 页面加载时间 < 1秒
- [ ] 移动端适配正常

---

**Handoff创建时间**: 2026-03-15
**下一个阶段**: team-exec (启动designer agent)
