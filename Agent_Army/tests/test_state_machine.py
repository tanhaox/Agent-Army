"""
状态机单元测试

测试Task类和StateMachineEngine类的所有功能。
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from src.core.state_machine import Task, StateMachineEngine, create_task


class TestTask:
    """测试Task类"""

    def test_create_task(self):
        """测试任务创建"""
        task = create_task("600519")

        assert task.task_id is not None
        assert task.stock_code == "600519"
        assert task.current_state == "Pending"
        assert task.stock_name is None
        assert len(task.state_history) == 0
        assert task.created_at is not None

    def test_task_transition(self):
        """测试状态转换"""
        task = create_task("600519")

        # Pending → Commander
        task.transition_to("Commander")
        assert task.current_state == "Commander"
        assert task.previous_state == "Pending"
        assert len(task.state_history) == 1
        assert "Commander" in task.state_transitions

        # Commander → Research
        task.transition_to("Research")
        assert task.current_state == "Research"
        assert task.previous_state == "Commander"
        assert len(task.state_history) == 2

    def test_is_complete(self):
        """测试完成检查"""
        task = create_task("600519")

        # 初始状态不是完成
        assert not task.is_complete()

        # 转换到Done状态
        task.transition_to("Commander")
        task.transition_to("Research")
        task.transition_to("Done")

        assert task.is_complete()

    def test_get_duration(self):
        """测试耗时计算"""
        task = create_task("600519")

        # 未开始的任务，耗时为0
        duration = task.get_duration()
        assert duration >= timedelta(0)

        # 开始任务
        task.started_at = datetime.now()
        duration = task.get_duration()
        assert duration >= timedelta(0)

    def test_add_error_warning(self):
        """测试错误和警告"""
        task = create_task("600519")

        task.add_error("测试错误")
        assert len(task.errors) == 1
        assert "测试错误" in task.errors[0]

        task.add_warning("测试警告")
        assert len(task.warnings) == 1
        assert "测试警告" in task.warnings[0]

    def test_to_dict(self):
        """测试转换为字典"""
        task = create_task("600519")
        task_dict = task.to_dict()

        assert task_dict['task_id'] == task.task_id
        assert task_dict['stock_code'] == "600519"
        assert task_dict['current_state'] == "Pending"

    def test_to_json(self):
        """测试转换为JSON"""
        task = create_task("600519")
        json_str = task.to_json()

        assert isinstance(json_str, str)
        assert "600519" in json_str
        assert "Pending" in json_str


class TestStateMachineEngine:
    """测试StateMachineEngine类"""

    @pytest.mark.asyncio
    async def test_create_task(self):
        """测试创建任务"""
        engine = StateMachineEngine()
        task_id = await engine.create_task("600519")

        assert task_id is not None
        assert "600519" in task_id
        assert task_id in engine.tasks
        assert task_id in engine.active_tasks

    @pytest.mark.asyncio
    async def test_get_task_status(self):
        """测试获取任务状态"""
        engine = StateMachineEngine()
        task_id = await engine.create_task("600519")

        status = engine.get_task_status(task_id)

        assert status is not None
        assert status['task_id'] == task_id
        assert status['stock_code'] == "600519"
        assert status['current_state'] == "Pending"
        assert status['progress'] == 0.0

    @pytest.mark.asyncio
    async def test_list_tasks(self):
        """测试列出任务"""
        engine = StateMachineEngine()

        # 创建多个任务
        task_id1 = await engine.create_task("600519")
        task_id2 = await engine.create_task("000001")

        tasks = engine.list_tasks()

        assert len(tasks) == 2
        assert tasks[0]['stock_code'] in ["600519", "000001"]

    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """测试取消任务"""
        engine = StateMachineEngine()
        task_id = await engine.create_task("600519")

        # 取消任务
        result = engine.cancel_task(task_id)

        assert result is True
        task = engine.tasks[task_id]
        assert task.is_complete()
        assert task_id not in engine.active_tasks

    @pytest.mark.asyncio
    async def test_get_active_count(self):
        """测试活跃任务计数"""
        engine = StateMachineEngine()

        # 初始为0
        assert engine.get_active_count() == 0

        # 创建任务
        task_id1 = await engine.create_task("600519")
        task_id2 = await engine.create_task("000001")

        assert engine.get_active_count() == 2

        # 完成一个任务
        engine.cancel_task(task_id1)

        assert engine.get_active_count() == 1

    @pytest.mark.asyncio
    async def test_clear_completed_tasks(self):
        """测试清理已完成任务"""
        engine = StateMachineEngine()

        # 创建任务
        task_id1 = await engine.create_task("600519")
        task_id2 = await engine.create_task("000001")

        # 完成一个
        engine.cancel_task(task_id1)

        # 清理
        cleared = engine.clear_completed_tasks()

        assert cleared == 1
        assert len(engine.tasks) == 1

    @pytest.mark.asyncio
    async def test_calculate_progress(self):
        """测试进度计算"""
        engine = StateMachineEngine()
        task_id = await engine.create_task("600519")

        task = engine.tasks[task_id]

        # Pending状态进度为0
        progress = engine._calculate_progress(task)
        assert progress == 0.0

        # 转换到中间状态
        task.transition_to("Commander")
        progress = engine._calculate_progress(task)
        assert 0 < progress < 100

        # 转换到Done状态
        task.transition_to("Done")
        progress = engine._calculate_progress(task)
        assert progress == 100.0

    @pytest.mark.asyncio
    async def test_run_task_simple(self):
        """测试简单任务运行（状态转换）"""
        engine = StateMachineEngine()
        task_id = await engine.create_task("600519")

        # 运行任务（会自动进行状态转换）
        success = await engine.run_task(task_id)

        assert success is True

        task = engine.tasks[task_id]
        assert task.is_complete()
        assert task.current_state == "Done"

    @pytest.mark.asyncio
    async def test_task_not_found(self):
        """测试任务不存在的情况"""
        engine = StateMachineEngine()

        with pytest.raises(ValueError, match="Task not found"):
            await engine.run_task("invalid-task-id")

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self):
        """测试获取不存在的任务状态"""
        engine = StateMachineEngine()

        status = engine.get_task_status("invalid-task-id")

        assert status is None


class TestTaskScenarios:
    """测试真实场景"""

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self):
        """测试完整分析流程"""
        engine = StateMachineEngine()
        task_id = await engine.create_task("600519")

        # 运行完整流程
        success = await engine.run_task(task_id)

        assert success is True

        status = engine.get_task_status(task_id)
        assert status['is_complete'] is True
        assert status['progress'] == 100.0

        task = engine.tasks[task_id]
        # 检查状态历史
        assert len(task.state_history) > 0

        # 检查状态转换顺序
        states = [h['to'] for h in task.state_history]
        assert states[-1] == "Done"

    @pytest.mark.asyncio
    async def test_concurrent_tasks(self):
        """测试并发任务"""
        engine = StateMachineEngine()

        # 创建多个任务
        task_ids = []
        for stock_code in ["600519", "000001", "002594"]:
            task_id = await engine.create_task(stock_code)
            task_ids.append(task_id)

        # 并发运行
        results = await asyncio.gather(
            *[engine.run_task(task_id) for task_id in task_ids]
        )

        # 所有任务都应成功
        assert all(results)

        # 检查所有任务都完成
        for task_id in task_ids:
            task = engine.tasks[task_id]
            assert task.is_complete()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
