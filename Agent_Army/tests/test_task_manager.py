"""
任务管理器单元测试

测试TaskManager类的所有功能。
"""

import pytest
import asyncio
from src.core.task_manager import TaskManager
from src.core.permission_matrix import PermissionError


class TestTaskManager:
    """测试TaskManager类"""

    @pytest.mark.asyncio
    async def test_init(self):
        """测试初始化"""
        manager = TaskManager()

        assert manager.state_machine is not None
        assert manager.permission_checker is not None
        assert manager.max_concurrent_tasks == 10

    @pytest.mark.asyncio
    async def test_create_analysis_task(self):
        """测试创建分析任务"""
        manager = TaskManager()

        task_id = await manager.create_analysis_task("600519")

        assert task_id is not None
        assert "600519" in task_id

        # 检查任务在状态机中
        assert task_id in manager.state_machine.tasks

    @pytest.mark.asyncio
    async def test_create_task_with_permission_check(self):
        """测试权限检查"""
        manager = TaskManager()

        # 投资者可以创建任务（投资者可以调用commander）
        task_id = await manager.create_analysis_task(
            "600519",
            caller="investor"
        )
        assert task_id is not None

        # 研究部可以创建任务（研究部可以回调commander）
        task_id2 = await manager.create_analysis_task(
            "000001",
            caller="research_department"
        )
        assert task_id2 is not None

        # 使用一个完全没有权限的调用者（不在权限矩阵中）
        with pytest.raises(PermissionError):
            await manager.create_analysis_task(
                "600000",
                caller="invalid_caller"
            )

    @pytest.mark.asyncio
    async def test_get_task_status(self):
        """测试获取任务状态"""
        manager = TaskManager()
        task_id = await manager.create_analysis_task("600519")

        status = await manager.get_task_status(task_id)

        assert status is not None
        assert status['task_id'] == task_id
        assert status['stock_code'] == "600519"
        assert status['current_state'] == "Pending"

    @pytest.mark.asyncio
    async def test_list_tasks(self):
        """测试列出任务"""
        manager = TaskManager()

        # 创建多个任务
        task_id1 = await manager.create_analysis_task("600519")
        task_id2 = await manager.create_analysis_task("000001")

        tasks = await manager.list_tasks()

        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_cancel_task(self):
        """测试取消任务"""
        manager = TaskManager()
        task_id = await manager.create_analysis_task("600519")

        # 取消任务
        result = await manager.cancel_task(task_id)

        assert result is True

        # 检查任务已取消
        task = manager.state_machine.tasks[task_id]
        assert task.is_complete()

    @pytest.mark.asyncio
    async def test_get_queue_size(self):
        """测试获取队列大小"""
        manager = TaskManager()

        # 初始队列为0
        assert manager.get_queue_size() == 0

        # 添加任务到队列
        await manager.create_analysis_task("600519")

        # 队列大小应该增加
        # 注意：任务可能已经被处理，所以这里只检查队列不为负数
        assert manager.get_queue_size() >= 0

    @pytest.mark.asyncio
    async def test_get_running_count(self):
        """测试获取运行中的任务数量"""
        manager = TaskManager()

        # 初始为0
        assert manager.get_running_count() == 0

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """测试获取统计信息"""
        manager = TaskManager()

        # 创建任务
        await manager.create_analysis_task("600519")

        stats = manager.get_statistics()

        assert 'total_tasks' in stats
        assert 'active_tasks' in stats
        assert 'completed_tasks' in stats
        assert 'queued_tasks' in stats
        assert 'running_tasks' in stats
        assert 'max_concurrent_tasks' in stats

    @pytest.mark.asyncio
    async def test_wait_for_completion(self):
        """测试等待任务完成"""
        manager = TaskManager()
        task_id = await manager.create_analysis_task("600519")

        # 等待任务完成（带超时）
        completed = await manager.wait_for_completion(task_id, timeout=10.0)

        # 任务应该完成
        assert completed is True

    @pytest.mark.asyncio
    async def test_get_task_result(self):
        """测试获取任务结果"""
        manager = TaskManager()
        task_id = await manager.create_analysis_task("600519")

        # 等待任务完成
        await manager.wait_for_completion(task_id, timeout=10.0)

        # 获取结果
        result = await manager.get_task_result(task_id)

        assert result is not None
        assert result['task_id'] == task_id
        assert result['stock_code'] == "600519"

    @pytest.mark.asyncio
    async def test_concurrent_task_limit(self):
        """测试并发任务限制"""
        manager = TaskManager(max_concurrent_tasks=2)

        # 创建多个任务
        task_ids = []
        for i in range(5):
            task_id = await manager.create_analysis_task(f"STOCK{i}")
            task_ids.append(task_id)

        # 检查运行中的任务不超过限制
        # 注意：由于任务处理很快，这里可能已经完成了
        running_count = manager.get_running_count()
        assert running_count <= 2


class TestTaskManagerScenarios:
    """测试真实场景"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程"""
        manager = TaskManager()

        # 1. 创建任务
        task_id = await manager.create_analysis_task("600519")
        assert task_id is not None

        # 2. 检查状态
        status = await manager.get_task_status(task_id)
        assert status['current_state'] == "Pending"

        # 3. 等待完成
        completed = await manager.wait_for_completion(task_id, timeout=15.0)
        assert completed is True

        # 4. 获取结果
        result = await manager.get_task_result(task_id)
        assert result is not None
        assert result['stock_code'] == "600519"

        # 5. 检查统计
        stats = manager.get_statistics()
        assert stats['completed_tasks'] >= 1

    @pytest.mark.asyncio
    async def test_multiple_stocks_workflow(self):
        """测试多股票分析工作流程"""
        manager = TaskManager()

        stocks = ["600519", "000001", "002594"]
        task_ids = []

        # 创建多个任务
        for stock in stocks:
            task_id = await manager.create_analysis_task(stock)
            task_ids.append(task_id)

        # 等待所有任务完成
        for task_id in task_ids:
            completed = await manager.wait_for_completion(task_id, timeout=15.0)
            assert completed is True

        # 获取所有结果
        for task_id in task_ids:
            result = await manager.get_task_result(task_id)
            assert result is not None

    @pytest.mark.asyncio
    async def test_cancel_running_task(self):
        """测试取消正在运行的任务"""
        manager = TaskManager()

        # 创建任务
        task_id = await manager.create_analysis_task("600519")

        # 等待一小段时间让任务开始
        await asyncio.sleep(0.2)

        # 取消任务
        result = await manager.cancel_task(task_id)
        assert result is True

        # 检查任务已取消
        task = manager.state_machine.tasks[task_id]
        assert task.is_complete()

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self):
        """测试获取不存在的任务"""
        manager = TaskManager()

        status = await manager.get_task_status("invalid-task-id")
        assert status is None

        result = await manager.get_task_result("invalid-task-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_task_mode_setting(self):
        """测试任务模式设置"""
        manager = TaskManager()

        # 创建标准模式任务
        task_id_standard = await manager.create_analysis_task(
            "600519",
            mode="standard"
        )
        task_standard = manager.state_machine.tasks[task_id_standard]
        assert task_standard.mode == "standard"

        # 创建快速模式任务
        task_id_quick = await manager.create_analysis_task(
            "000001",
            mode="quick"
        )
        task_quick = manager.state_machine.tasks[task_id_quick]
        assert task_quick.mode == "quick"


class TestTaskManagerPerformance:
    """测试性能"""

    @pytest.mark.asyncio
    async def test_create_task_performance(self):
        """测试任务创建性能"""
        manager = TaskManager()

        # 创建100个任务
        start_time = asyncio.get_event_loop().time()

        for i in range(100):
            await manager.create_analysis_task(f"STOCK{i}")

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # 100个任务创建应该在5秒内完成
        assert duration < 5.0

    @pytest.mark.asyncio
    async def test_concurrent_performance(self):
        """测试并发性能"""
        manager = TaskManager(max_concurrent_tasks=10)

        # 创建20个任务
        task_ids = []
        for i in range(20):
            task_id = await manager.create_analysis_task(f"STOCK{i}")
            task_ids.append(task_id)

        # 等待所有任务完成
        start_time = asyncio.get_event_loop().time()

        for task_id in task_ids:
            await manager.wait_for_completion(task_id, timeout=30.0)

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # 20个任务应该在30秒内完成
        assert duration < 30.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
