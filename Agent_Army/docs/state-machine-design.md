# Agent Army 状态机设计

> **版本**: v2.0（8部门制）
> **日期**: 2026-03-20
> **方案**: Plan B - 自己实现，不依赖OpenClaw

---

## 一、状态机概述

### 1.1 核心概念

状态机管理投资分析任务的整个生命周期，从创建到完成。

```
任务生命周期：
Pending（待处理）→ Commander（总司令识别）→
Research（研究部分析）→ Analysis（分析部分析）→
Review（质量审核）→ Prediction（预测部计算）→
Strategy（策略部分析）→ Validation（验证部验证）→
Report（生成报告）→ Done（完成）
```

### 1.2 状态流转图

```
                    ┌─────────────┐
                    │  Pending    │ 投资者输入
                    │  (待处理)    │
                    └──────┬──────┘
                           ↓ 意图识别
                    ┌─────────────┐
                    │ Commander   │ 总司令识别
                    │ (总司令)     │ 股票代码
                    └──────┬──────┘
                           ↓ 派发研究部
                    ┌─────────────┐
                    │  Research   │ 研究部分析
                    │  (研究部)    │ (2个AI并行)
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │  Analysis   │ 分析部分析
                    │  (分析部)    │ (3个AI并行)
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │   Review    │ 质量审核
                    │  (质量审核)  │ 总司令审核
                    └──────┬──────┘
                           ↓ 通过
                    ┌─────────────┐
                    │ Prediction  │ 预测部计算
                    │  (预测部)    │ (3个AI并行)
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │  Strategy   │ 策略部分析
                    │  (策略部)    │ (4个AI并行)
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │ Validation  │ 验证部验证
                    │  (验证部)    │ (2个AI并行)
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │   Report    │ 生成报告
                    │  (生成报告)  │ 总司令汇总
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │    Done     │ 完成归档
                    │   (完成)     │
                    └─────────────┘
```

---

## 二、状态定义

### 2.1 完整状态列表

```python
STATE_MACHINE = {
    # 初始状态
    'Pending': {
        'name': '待处理',
        'description': '投资者输入，等待总司令识别',
        'next_state': 'Commander',
        'actor': '投资者',
        'timeout': None
    },

    # 总司令识别
    'Commander': {
        'name': '总司令识别',
        'description': '总司令识别意图，提取股票代码',
        'next_state': 'Research',
        'actor': '总司令',
        'timeout': 10  # 10秒内完成识别
    },

    # 研究部分析
    'Research': {
        'name': '研究部分析',
        'description': '研究部分析产业链和宏观环境（2个AI并行）',
        'next_state': 'Analysis',
        'actor': '研究部',
        'timeout': 60  # 60秒内完成
    },

    # 分析部分析
    'Analysis': {
        'name': '分析部分析',
        'description': '分析部分析基本面和估值（3个AI并行）',
        'next_state': 'Review',
        'actor': '分析部',
        'timeout': 90  # 90秒内完成
    },

    # 质量审核
    'Review': {
        'name': '质量审核',
        'description': '总司令审核分析方案质量',
        'next_state': 'Prediction',  # 通过
        'next_state_reject': 'Research',  # 驳回
        'actor': '总司令',
        'timeout': 15  # 15秒内完成审核
    },

    # 预测部计算
    'Prediction': {
        'name': '预测部计算',
        'description': '预测部计算目标价和评分（3个AI并行）',
        'next_state': 'Strategy',
        'actor': '预测部',
        'timeout': 60  # 60秒内完成
    },

    # 策略部分析
    'Strategy': {
        'name': '策略部分析',
        'description': '策略部分析买卖时机和仓位（4个AI并行）',
        'next_state': 'Validation',
        'actor': '策略部',
        'timeout': 60  # 60秒内完成
    },

    # 验证部验证
    'Validation': {
        'name': '验证部验证',
        'description': '验证部进行预测验证和回测（2个AI并行）',
        'next_state': 'Report',
        'actor': '验证部',
        'timeout': 45  # 45秒内完成
    },

    # 生成报告
    'Report': {
        'name': '生成报告',
        'description': '总司令汇总所有结果，生成投资报告',
        'next_state': 'Done',
        'actor': '总司令',
        'timeout': 20  # 20秒内完成
    },

    # 完成
    'Done': {
        'name': '完成',
        'description': '任务完成，报告归档到报告库',
        'next_state': None,
        'actor': '报告库',
        'timeout': None
    }
}
```

### 2.2 快速流程状态（精简版）

```python
QUICK_STATE_MACHINE = {
    'Pending': {
        'name': '待处理',
        'next_state': 'QuickCommander',
        'timeout': None
    },

    'QuickCommander': {
        'name': '快速识别',
        'next_state': 'QuickAnalysis',
        'timeout': 5
    },

    'QuickAnalysis': {
        'name': '快速分析',
        'description': '核心部门快速分析（5个AI并行）',
        'next_state': 'QuickReport',
        'timeout': 30
    },

    'QuickReport': {
        'name': '快速报告',
        'next_state': 'Done',
        'timeout': 10
    },

    'Done': {
        'name': '完成',
        'next_state': None,
        'timeout': None
    }
}
```

---

## 三、状态转换规则

### 3.1 正常转换

```python
STATE_TRANSITIONS = {
    'Pending': {
        'trigger': 'user_input',
        'next': 'Commander',
        'action': '识别意图'
    },

    'Commander': {
        'trigger': 'intent_identified',
        'next': 'Research',
        'action': '派发研究部'
    },

    'Research': {
        'trigger': 'research_completed',
        'next': 'Analysis',
        'action': '派发分析部'
    },

    'Analysis': {
        'trigger': 'analysis_completed',
        'next': 'Review',
        'action': '提交审核'
    },

    'Review': {
        'trigger': 'quality_approved',
        'next': 'Prediction',
        'action': '派发预测部'
    },

    'Review': {
        'trigger': 'quality_rejected',
        'next': 'Research',
        'action': '驳回重做'
    },

    'Prediction': {
        'trigger': 'prediction_completed',
        'next': 'Strategy',
        'action': '派发策略部'
    },

    'Strategy': {
        'trigger': 'strategy_completed',
        'next': 'Validation',
        'action': '派发验证部'
    },

    'Validation': {
        'trigger': 'validation_completed',
        'next': 'Report',
        'action': '生成报告'
    },

    'Report': {
        'trigger': 'report_generated',
        'next': 'Done',
        'action': '归档'
    }
}
```

### 3.2 异常转换

```python
ERROR_TRANSITIONS = {
    # 超时处理
    'timeout': {
        'from': ['Research', 'Analysis', 'Prediction', 'Strategy', 'Validation'],
        'action': '记录警告，继续执行或标记失败'
    },

    # 失败处理
    'failed': {
        'from': ['Research', 'Analysis', 'Prediction', 'Strategy', 'Validation'],
        'action': '记录错误，决定是否重试或跳过'
    },

    # 紧急停止
    'emergency_stop': {
        'from': ['*'],  # 任何状态
        'action': '立即停止，生成部分报告'
    }
}
```

---

## 四、状态数据结构

### 4.1 任务对象

```python
class Task:
    """投资分析任务"""

    def __init__(self, task_id: str, stock_code: str):
        self.task_id = task_id
        self.stock_code = stock_code
        self.stock_name = None

        # 状态信息
        self.current_state = 'Pending'
        self.previous_state = None
        self.state_history = []

        # 时间信息
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.state_transitions = {}  # {state: transition_time}

        # 部门执行结果
        self.department_results = {
            'Research': None,
            'Analysis': None,
            'Prediction': None,
            'Strategy': None,
            'Validation': None
        }

        # 质量评分
        self.quality_scores = {
            'Research': 0,
            'Analysis': 0
        }

        # 最终报告
        self.final_report = None

        # 错误信息
        self.errors = []
        self.warnings = []

    def transition_to(self, new_state: str):
        """状态转换"""
        self.previous_state = self.current_state
        self.current_state = new_state

        self.state_history.append({
            'from': self.previous_state,
            'to': new_state,
            'timestamp': datetime.now()
        })

        self.state_transitions[new_state] = datetime.now()

    def is_complete(self) -> bool:
        """是否完成"""
        return self.current_state == 'Done'

    def get_duration(self) -> timedelta:
        """获取耗时"""
        if self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            return datetime.now() - self.started_at
        else:
            return timedelta(0)
```

### 4.2 状态上下文

```python
class StateContext:
    """状态上下文，传递给每个状态处理器"""

    def __init__(self, task: Task):
        self.task = task

        # 部门Agent引用
        self.departments = {
            'Research': ResearchDepartment(),
            'Analysis': AnalysisDepartment(),
            'Prediction': PredictionDepartment(),
            'Strategy': StrategyDepartment(),
            'Validation': ValidationDepartment()
        }

        # 总司令
        self.commander = CommanderAgent()

        # 配置
        self.config = {
            'timeout': 300,  # 总超时时间（秒）
            'parallel': True,  # 是否并行执行
            'mode': 'standard'  # standard | quick
        }

    async def execute_state(self, state: str) -> bool:
        """执行指定状态"""
        if state == 'Commander':
            return await self._execute_commander()
        elif state == 'Research':
            return await self._execute_research()
        elif state == 'Analysis':
            return await self._execute_analysis()
        elif state == 'Review':
            return await self._execute_review()
        # ... 其他状态
        else:
            raise ValueError(f"Unknown state: {state}")
```

---

## 五、状态处理器实现

### 5.1 总司令识别状态

```python
async def _execute_commander(self) -> bool:
    """执行总司令识别"""
    try:
        # 1. 识别意图
        intent = await self.commander.identify_intent(
            self.task.stock_code
        )

        if not intent['is_stock_analysis']:
            raise ValueError("不是股票分析请求")

        # 2. 提取股票代码
        stock_code = intent['stock_code']
        self.task.stock_code = stock_code
        self.task.stock_name = intent['stock_name']

        # 3. 转换到下一状态
        self.task.transition_to('Research')

        return True

    except Exception as e:
        self.task.errors.append(f"总司令识别失败: {e}")
        return False
```

### 5.2 研究部分析状态

```python
async def _execute_research(self) -> bool:
    """执行研究部分析"""
    try:
        # 1. 并行派发2个AI
        results = await asyncio.gather(
            self.departments['Research'].agents[0].analyze(
                self.task.stock_code
            ),  # 产业链研究AI
            self.departments['Research'].agents[1].analyze(
                self.task.stock_code
            ),  # 宏观政策研究AI
            return_exceptions=True
        )

        # 2. 合并结果
        research_result = {
            'industry_chain': results[0],
            'macro_policy': results[1]
        }

        self.task.department_results['Research'] = research_result

        # 3. 转换到下一状态
        self.task.transition_to('Analysis')

        return True

    except Exception as e:
        self.task.errors.append(f"研究部分析失败: {e}")
        return False
```

### 5.3 质量审核状态

```python
async def _execute_review(self) -> bool:
    """执行质量审核"""
    try:
        # 1. 总司令审核质量
        research_score = self.commander.assess_quality(
            self.task.department_results['Research']
        )

        analysis_score = self.commander.assess_quality(
            self.task.department_results['Analysis']
        )

        self.task.quality_scores = {
            'Research': research_score,
            'Analysis': analysis_score
        }

        # 2. 决策
        if research_score >= 80 and analysis_score >= 80:
            # 通过
            self.task.transition_to('Prediction')
            return True
        else:
            # 驳回
            self.task.warnings.append(
                f"质量不达标（研究部: {research_score}, "
                f"分析部: {analysis_score}），驳回重做"
            )
            self.task.transition_to('Research')
            return False

    except Exception as e:
        self.task.errors.append(f"质量审核失败: {e}")
        return False
```

---

## 六、状态机引擎

### 6.1 引擎实现

```python
class StateMachineEngine:
    """状态机引擎"""

    def __init__(self):
        self.tasks = {}  # {task_id: Task}
        self.active_tasks = set()

    async def create_task(self, stock_code: str) -> str:
        """创建新任务"""
        task_id = f"ANALYSIS-{stock_code}-{int(time.time())}"
        task = Task(task_id, stock_code)

        self.tasks[task_id] = task
        self.active_tasks.add(task_id)

        return task_id

    async def run_task(self, task_id: str) -> bool:
        """运行任务"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        context = StateContext(task)
        task.started_at = datetime.now()

        try:
            # 状态循环
            while not task.is_complete():
                current_state = task.current_state

                # 检查超时
                if self._is_timeout(task, current_state):
                    raise TimeoutError(
                        f"State {current_state} timeout"
                    )

                # 执行当前状态
                success = await context.execute_state(current_state)

                if not success:
                    # 处理失败
                    if not await self._handle_failure(task, current_state):
                        break

            # 完成
            task.completed_at = datetime.now()
            self.active_tasks.remove(task_id)

            return True

        except Exception as e:
            task.errors.append(f"任务执行失败: {e}")
            task.completed_at = datetime.now()
            self.active_tasks.remove(task_id)
            return False

    def _is_timeout(self, task: Task, state: str) -> bool:
        """检查是否超时"""
        state_timeout = STATE_MACHINE[state]['timeout']
        if state_timeout is None:
            return False

        state_enter_time = task.state_transitions.get(state)
        if not state_enter_time:
            return False

        duration = (datetime.now() - state_enter_time).total_seconds()
        return duration > state_timeout

    async def _handle_failure(self, task: Task, failed_state: str) -> bool:
        """处理失败"""
        # 检查是否可以重试
        if failed_state in ['Research', 'Analysis']:
            # 可以重试
            task.warnings.append(f"{failed_state}失败，重试中...")
            return True

        # 不能重试，标记失败
        return False

    def get_task_status(self, task_id: str) -> dict:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        return {
            'task_id': task.task_id,
            'stock_code': task.stock_code,
            'stock_name': task.stock_name,
            'current_state': task.current_state,
            'progress': self._calculate_progress(task),
            'duration': str(task.get_duration()),
            'errors': task.errors,
            'warnings': task.warnings
        }

    def _calculate_progress(self, task: Task) -> float:
        """计算进度百分比"""
        total_states = len(STATE_MACHINE) - 1  # 排除Done
        current_index = list(STATE_MACHINE.keys()).index(task.current_state)

        return (current_index / total_states) * 100
```

---

## 七、WebSocket实时推送

### 7.1 状态变更事件

```python
class StateChangeEvent:
    """状态变更事件"""

    def __init__(self, task_id: str, from_state: str, to_state: str):
        self.task_id = task_id
        self.from_state = from_state
        self.to_state = to_state
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            'event_type': 'state_change',
            'task_id': self.task_id,
            'from_state': self.from_state,
            'to_state': self.to_state,
            'timestamp': self.timestamp.isoformat(),
            'state_name': STATE_MACHINE[self.to_state]['name']
        }
```

### 7.2 进度更新事件

```python
class ProgressUpdateEvent:
    """进度更新事件"""

    def __init__(self, task_id: str, message: str, progress: float):
        self.task_id = task_id
        self.message = message
        self.progress = progress
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        return {
            'event_type': 'progress_update',
            'task_id': self.task_id,
            'message': self.message,
            'progress': self.progress,
            'timestamp': self.timestamp.isoformat()
        }
```

---

## 八、使用示例

### 8.1 创建和运行任务

```python
# 创建状态机引擎
engine = StateMachineEngine()

# 创建任务
task_id = await engine.create_task("600519")
print(f"Task created: {task_id}")

# 运行任务
success = await engine.run_task(task_id)

if success:
    print("任务完成")
    task = engine.tasks[task_id]
    print(f"报告: {task.final_report}")
else:
    print("任务失败")
```

### 8.2 监控任务进度

```python
# 获取任务状态
status = engine.get_task_status(task_id)

print(f"当前状态: {status['current_state']}")
print(f"进度: {status['progress']:.1f}%")
print(f"耗时: {status['duration']}")
```

---

**创建时间**: 2026-03-20
**设计师**: Claude
**版本**: v2.0（8部门制）
**状态**: 已完成
