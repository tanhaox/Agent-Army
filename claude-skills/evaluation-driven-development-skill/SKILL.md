# Evaluation-Driven Development Skill

## Purpose

Teaches Claude to use the **4-phase evaluation-driven development workflow** with automatic quality gates and iteration optimization.

**Core Workflow**: Research → Implementation → Review → Evaluation

---

## When to Use

**Activation Phrases** (Claude will automatically use this skill when you say):
- "使用评估驱动开发"
- "实现高质量代码"
- "使用4阶段开发流程"
- "执行评估驱动开发工作流"
- "需要质量保证的开发"
- "evaluation-driven development"
- "apply quality gates"

**Use Cases**:
- Developing production-ready features
- Implementing critical functionality
- Code requiring high quality standards
- Projects with automatic iteration optimization
- Team development workflows

---

## What It Does

### Phase 1: Research（研究）
- Analyzes requirements and task complexity
- Identifies potential risks and issues
- Generates implementation recommendations

### Phase 2: Implementation（实现）
- Executes tasks using subagent framework
- Supports both sequential and parallel execution
- Intelligent model selection (Opus/Sonnet/Haiku)
- Real-time progress tracking

### Phase 3: Review（审查）
- Automatic code quality review
- 5 categories of checks: Security, Performance, Style, Documentation, Testing
- Issue severity classification: Critical, Important, Minor
- Code strength analysis

### Phase 4: Evaluation（评估）
- Comprehensive quality scoring (0.0-10.0)
- Quality gate assessment:
  - **Excellent** (9.0-10.0): Ready for deployment
  - **Good** (7.0-8.9): Minor optimization needed
  - **Acceptable** (5.0-6.9): Fix important issues
  - **Needs Work** (0.0-4.9): Reimplement required
- Automatic iteration if below threshold
- Final workflow report generation

---

## How to Use

### Basic Usage

```python
import asyncio
from shared.subagents.workflow import create_workflow
from shared.subagents.dispatcher import create_task

async def main():
    # Step 1: Define tasks
    tasks = [
        create_task(
            task_id="feature-1",
            name="实现用户认证",
            requirements="""
            1. POST /auth/login
            2. POST /auth/register
            3. JWT token verification
            4. Password encryption
            """,
            task_type="development",
            complexity="high",
            priority=1
        ),
    ]

    # Step 2: Create workflow with quality threshold
    workflow = create_workflow(
        quality_threshold=7.0,  # Minimum acceptable quality
        max_iterations=3,       # Maximum optimization iterations
        enable_review=True,     # Enable code review
        enable_progress_tracking=True
    )

    # Step 3: Execute workflow
    results = await workflow.execute(tasks, mode="sequential")

    # Step 4: Review results
    print(workflow.generate_report())

asyncio.run(main())
```

### Advanced Configuration

```python
# High-quality production development
workflow = create_workflow(
    quality_threshold=9.0,  # Strict standard
    max_iterations=5        # More iterations
)

# Rapid prototyping
workflow = create_workflow(
    quality_threshold=5.0,  # Relaxed standard
    max_iterations=1        # Single iteration
)

# Standard development
workflow = create_workflow(
    quality_threshold=7.0,  # Balanced standard
    max_iterations=3        # Normal iterations
)
```

---

## Instructions for Claude

When this skill is activated, follow this workflow:

### 1. Understand the Request
- Parse user requirements
- Identify task complexity (low/medium/high)
- Determine task type (development/testing/documentation/review)

### 2. Create Tasks
Use `create_task()` to define structured tasks:
- `task_id`: Unique identifier
- `name`: Task name
- `description`: Brief description
- `requirements`: Detailed requirements (numbered list)
- `task_type`: development/testing/documentation/review
- `complexity`: low/medium/high
- `priority`: 0-4 (0=critical, 4=backlog)
- `dependencies`: List of task IDs this depends on

### 3. Initialize Workflow
```python
from shared.subagents.workflow import create_workflow

workflow = create_workflow(
    quality_threshold=7.0,
    max_iterations=3,
    enable_review=True,
    enable_progress_tracking=True
)
```

### 4. Execute and Monitor
- Execute workflow: `results = await workflow.execute(tasks, mode="sequential")`
- Monitor progress reports
- Review stage results

### 5. Generate Report
- Display workflow.generate_report()
- Highlight quality score
- List any issues found
- Provide recommendations

### 6. Explain Results
- Interpret quality score for user
- Explain each phase outcome
- Summarize strengths and issues
- Suggest next steps

---

## Success Criteria

✅ **Quality Score ≥ Threshold**: Final score meets or exceeds quality_threshold
✅ **All Critical Issues Resolved**: No critical security or bug issues
✅ **Workflow Report Generated**: Complete report with all phases
✅ **User Understands Results**: Clear explanation of outcomes

---

## Output Format

### Workflow Report

```
======================================================================
📋 评估驱动开发工作流报告
======================================================================
总迭代次数: 1
质量阈值: 7.0

各阶段结果:
----------------------------------------------------------------------
✅ RESEARCH         - 分数: 0.0/10.0
✅ IMPLEMENTATION   - 分数: 10.0/10.0
✅ REVIEW           - 分数: 8.5/10.0
✅ EVALUATION       - 分数: 8.8/10.0
✅ COMPLETE         - 分数: 8.8/10.0
======================================================================

优点 (5):
  ✓ 良好的文档注释
  ✓ 使用类型注解
  ✓ 适当的异常处理
  ✓ 使用日志系统
  ✓ 包含测试代码

问题 (2):
  [CRITICAL] security: eval() 可能导致代码注入漏洞
  [IMPORTANT] performance: 嵌套循环可能导致性能问题

建议:
  • 优先修复 1 个关键问题
  • 优化 2 个重要问题以提升代码质量
  • 代码质量良好，继续保持
```

---

## Tools and Dependencies

**Required Files** (located in `shared/subagents/`):
- `workflow.py` - EvaluationDrivenWorkflow class
- `dispatcher.py` - Dispatcher and task management
- `reviewer.py` - CodeReviewer and rules
- `progress_tracker.py` - ProgressTracker

**No External Dependencies**: All functionality is self-contained

---

## Best Practices

### For Users
1. **Provide Clear Requirements**: Detailed, numbered requirements yield better results
2. **Set Appropriate Quality Threshold**: 9.0 for production, 7.0 for standard, 5.0 for prototyping
3. **Review Progress Reports**: Check progress after each iteration
4. **Understand Quality Gates**: Know what each score range means

### For Claude
1. **Always Use Quality Thresholds**: Never skip quality evaluation
2. **Explain Each Phase**: Keep user informed throughout the workflow
3. **Highlight Issues**: Clearly communicate any problems found
4. **Suggest Improvements**: Provide actionable recommendations
5. **Respect Iteration Limits**: Don't exceed max_iterations without user consent

---

## Troubleshooting

### Quality Score Below Threshold
- **Cause**: Code has critical or multiple important issues
- **Solution**: Automatic iteration will attempt to fix issues
- **User Action**: Review issues and adjust requirements if needed

### Workflow Fails
- **Cause**: Missing dependencies or file access issues
- **Solution**: Check that shared/subagents/ files exist
- **User Action**: Verify project structure is correct

### No Progress Shown
- **Cause**: Progress tracking disabled
- **Solution**: Enable with `enable_progress_tracking=True`
- **User Action**: Recreate workflow with tracking enabled

---

## Examples

See `examples/` directory for complete working examples:
- `basic_usage.md` - Simple single-task workflow
- `advanced_usage.md` - Multi-task with dependencies
- `quality_tuning.md` - Different quality thresholds
- `iteration_example.md` - Multi-iteration optimization

---

## Related Skills

- **Subagent Dispatcher Skill**: For task parallelization
- **Code Reviewer Skill**: For standalone code review
- **Progress Tracker Skill**: For project management

---

## Version History

- **1.0.0** (2026-02-08): Initial release with 4-phase workflow

---

## Support

For issues or questions:
- Documentation: `docs/评估驱动开发指南.md`
- Examples: `docs/子代理框架实用示例.md`
- API Reference: `docs/子代理框架使用指南.md`

---

**Author**: AI-Agent-Local
**License**: MIT
**Status**: Production Ready ✅
