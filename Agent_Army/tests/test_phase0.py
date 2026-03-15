"""
Agent Army - Phase 0 验证测试
验证管理层Agent是否能正常运行
"""

import sys
import io
from pathlib import Path

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import setup_logging, get_logger
from src.core.config import get_config_manager
from src.agents.management.corps_coordinator import CorpsCoordinator
from src.agents.management.capability_manager import AgentCapabilityManager


def test_environment_setup():
    """测试环境设置"""
    print("=" * 60)
    print("  Phase 0 环境验证测试")
    print("=" * 60)

    # 1. 设置日志
    print("\n[1/5] 设置日志系统...")
    setup_logging(log_level="INFO", log_dir="./logs", enable_console=True)
    logger = get_logger("test")
    logger.info("日志系统设置成功")
    print("✅ 日志系统设置成功")

    # 2. 加载配置
    print("\n[2/5] 加载配置...")
    config_manager = get_config_manager("./config")
    logger.info("配置加载成功", config_keys=list(config_manager._configs.keys()))
    print("✅ 配置加载成功")
    print(f"   - 配置文件: {list(config_manager._configs.keys())}")

    # 3. 初始化军团协调官
    print("\n[3/5] 初始化军团协调官...")
    coordinator = CorpsCoordinator(config=config_manager.get_agent_config("corps_coordinator"))
    print(f"✅ 军团协调官初始化成功")
    print(f"   - 名称: {coordinator.name}")
    print(f"   - 角色: {coordinator.role}")
    print(f"   - 能力: {len(coordinator.get_capabilities())}个")
    print(f"   - 工具: {len(coordinator.get_tools())}个")

    # 4. 初始化Agent能力管理官
    print("\n[4/5] 初始化Agent能力管理官...")
    capability_manager = AgentCapabilityManager(
        config=config_manager.get_agent_config("capability_manager")
    )
    print(f"✅ Agent能力管理官初始化成功")
    print(f"   - 名称: {capability_manager.name}")
    print(f"   - 角色: {capability_manager.role}")
    print(f"   - 能力: {len(capability_manager.get_capabilities())}个")
    print(f"   - 工具: {len(capability_manager.get_tools())}个")

    # 5. 验证状态
    print("\n[5/5] 验证Agent状态...")
    coordinator_state = coordinator.get_state()
    capability_manager_state = capability_manager.get_state()

    print(f"✅ 军团协调官状态: {coordinator_state.status}")
    print(f"✅ Agent能力管理官状态: {capability_manager_state.status}")

    # 测试总结
    print("\n" + "=" * 60)
    print("  Phase 0 验证测试完成")
    print("=" * 60)
    print("\n✅ 所有测试通过!")
    print("\n验证项目:")
    print("  ✅ 日志系统正常工作")
    print("  ✅ 配置管理正常工作")
    print("  ✅ 军团协调官正常初始化")
    print("  ✅ Agent能力管理官正常初始化")
    print("  ✅ Agent状态管理正常工作")
    print("\n🎉 Phase 0 平台搭建成功!")

    return True


if __name__ == "__main__":
    try:
        test_environment_setup()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
