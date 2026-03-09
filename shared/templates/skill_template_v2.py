#!/usr/bin/env python3
"""
AI-Agent-Local 通用技能模板 v2.0
整合 mcp-builder 最佳实践的下一代技能框架

新特性 (v2.0)：
1. 脚本系统支持（SCRIPTS.md）
2. 渐进式文档披露
3. 评估驱动开发接口
4. 以智能体为中心的设计原则
5. 可操作错误消息
6. 工作流整合能力
7. 上下文优化支持

兼容原有 v1.0 所有功能
"""

import os
import sys
import json
import logging
import inspect
import functools
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import traceback

# 类型别名
T = TypeVar('T')
R = TypeVar('R')

# ==================== 配置类 ====================

@dataclass
class SkillConfig:
    """技能配置类 v2.0"""
    name: str = "未命名技能"
    version: str = "2.0.0"
    description: str = "技能描述"
    author: str = "匿名"

    # 执行设置
    require_confirmation: bool = True
    allow_local_execution: bool = True
    timeout_seconds: int = 30

    # 日志设置
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # AI 集成设置
    use_ai_assistant: bool = False
    ai_model: str = "local"
    ai_max_tokens: int = 1000

    # 生命周期设置
    announce_on_start: bool = True
    announce_on_complete: bool = True

    # 错误预防设置
    enable_error_prevention: bool = True
    require_tests_before_critical_ops: bool = False

    # 新增 v2.0：以智能体为中心的设计配置
    optimize_context: bool = True  # 优化上下文使用
    actionable_errors: bool = True  # 可操作错误消息
    workflow_integrated: bool = False  # 工作流整合模式
    progressive_disclosure: bool = True  # 渐进式文档披露

    # 评估驱动开发
    evaluation_driven: bool = False  # 启用评估驱动开发
    evaluation_scenarios: int = 10  # 评估场景数量

    # 脚本系统
    scripts_enabled: bool = False  # 启用脚本系统
    scripts_dir: Optional[str] = None  # 脚本目录

    # 自定义配置
    custom_config: Dict[str, Any] = field(default_factory=dict)

# ==================== 状态和结果类 ====================

class SkillStatus(Enum):
    """技能执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    CONFIRMATION_REQUIRED = "confirmation_required"

@dataclass
class SkillResult:
    """技能执行结果 v2.0"""
    status: SkillStatus
    data: Optional[Any] = None
    message: str = ""
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 新增 v2.0：上下文优化信息
    context_usage: Optional[Dict[str, int]] = None  # 上下文使用统计
    concise_mode: bool = False  # 是否使用精简模式

    # 新增 v2.0：评估信息
    evaluation_passed: bool = True  # 是否通过评估

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['status'] = self.status.value
        return result

    def is_success(self) -> bool:
        """是否成功"""
        return self.status == SkillStatus.SUCCESS

    @classmethod
    def success(cls, data: Any = None, message: str = "", **kwargs) -> 'SkillResult':
        """创建成功结果"""
        return cls(
            status=SkillStatus.SUCCESS,
            data=data,
            message=message or "执行成功",
            **kwargs
        )

    @classmethod
    def error_result(cls, error: str, message: str = "", **kwargs) -> 'SkillResult':
        """创建错误结果"""
        return cls(
            status=SkillStatus.FAILED,
            error=error,
            message=message or "执行失败",
            **kwargs
        )

# ==================== 异常类 ====================

class ConfirmationRequired(Exception):
    """需要确认的异常"""
    def __init__(self, message: str, action_description: str, context: Dict[str, Any] = None):
        super().__init__(message)
        self.action_description = action_description
        self.context = context or {}

class ActionableError(Exception):
    """可操作错误异常（v2.0 新增）"""
    def __init__(self, message: str, suggested_action: str, context: Dict[str, Any] = None):
        super().__init__(message)
        self.suggested_action = suggested_action
        self.context = context or {}

    def get_actionable_message(self) -> str:
        """获取可操作的错误消息"""
        return f"{self.message}\n建议操作：{self.suggested_action}"

# ==================== 装饰器 ====================

def confirm_action(description: str = None):
    """确认装饰器 - 在执行前要求用户确认"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            instance = args[0] if args else None
            description_text = description or func.__doc__ or func.__name__

            if isinstance(instance, SkillBase):
                if instance.config.require_confirmation:
                    context = {
                        'function': func.__name__,
                        'args': args[1:] if args else [],
                        'kwargs': kwargs,
                        'description': description_text
                    }
                    raise ConfirmationRequired(
                        f"需要确认: {description_text}",
                        description_text,
                        context
                    )

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_tests_pass(test_command: str = "pytest"):
    """测试验证装饰器 - 要求测试通过后才能执行"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(__name__)
            logger.info(f"[测试验证] 运行测试: {test_command}")

            result = subprocess.run(
                test_command.split(),
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                error_msg = f"测试失败，无法继续操作:\n{result.stdout}\n{result.stderr}"
                logger.error(f"[测试失败] {error_msg}")
                raise RuntimeError(error_msg)

            logger.info("[测试成功] 所有测试通过，继续执行")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def workflow_step(step_name: str, description: str = ""):
    """工作流步骤装饰器（v2.0 新增）"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            instance = args[0] if args else None
            if isinstance(instance, SkillBase):
                instance.logger.info(f"[工作流] 步骤: {step_name}")
                if description:
                    instance.logger.info(f"  描述: {description}")

            return func(*args, **kwargs)
        return wrapper
    return decorator

# ==================== 技能基类 ====================

class SkillBase(ABC):
    """技能基类 v2.0"""

    def __init__(self, config: Optional[SkillConfig] = None):
        """
        初始化技能

        Args:
            config: 技能配置，如果为None则使用默认配置
        """
        self.config = config or SkillConfig(name=self.__class__.__name__)
        self._setup_logging()
        self.logger = logging.getLogger(f"skill.{self.config.name}")
        self._execution_context: Dict[str, Any] = {}

        # 脚本系统初始化
        self._scripts: Dict[str, Callable] = {}
        if self.config.scripts_enabled and self.config.scripts_dir:
            self._load_scripts()

    def _setup_logging(self):
        """设置日志（双输出模式）"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        # 清除现有处理器
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # 配置控制台日志
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(console_handler)

        # 设置日志级别
        root_logger.setLevel(getattr(logging, self.config.log_level.upper()))

        # 文件日志
        if self.config.log_file:
            log_path = Path(self.config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.config.log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(log_format))
            root_logger.addHandler(file_handler)

    def _load_scripts(self):
        """加载脚本（v2.0 新增）"""
        scripts_dir = Path(self.config.scripts_dir)
        if not scripts_dir.exists():
            self.logger.warning(f"脚本目录不存在: {scripts_dir}")
            return

        # 动态加载脚本
        import importlib.util
        for script_file in scripts_dir.glob("*.py"):
            if script_file.name.startswith("_"):
                continue

            spec = importlib.util.spec_from_file_location(
                script_file.stem,
                script_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 注册脚本中的函数
                for name, obj in inspect.getmembers(module, inspect.isfunction):
                    if not name.startswith("_"):
                        self._scripts[name] = obj
                        self.logger.info(f"加载脚本: {name} from {script_file.name}")

    # ==================== 上下文管理 ====================

    def set_context(self, key: str, value: Any):
        """设置执行上下文"""
        self._execution_context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取执行上下文"""
        return self._execution_context.get(key, default)

    # ==================== 生命周期方法 ====================

    def _announce_start(self):
        """开始声明"""
        if self.config.announce_on_start:
            message = f"[开始] 正在使用 {self.config.name} 技能 v{self.config.version}"
            self.logger.info(message)
            print(message)

    def _announce_complete(self, result: SkillResult):
        """完成声明"""
        if self.config.announce_on_complete:
            status_icon = "✅" if result.is_success() else "❌"
            message = f"[完成] {self.config.name} 技能执行 {status_icon}"
            if not result.is_success() and result.error:
                message += f": {result.error}"
            self.logger.info(message)
            print(message)

    # ==================== 抽象方法 ====================

    @abstractmethod
    def execute(self, **kwargs) -> SkillResult:
        """
        执行技能 - 子类必须实现此方法

        Returns:
            SkillResult: 执行结果
        """
        pass

    # ==================== 可选覆盖方法 ====================

    def validate(self, **kwargs) -> Optional[str]:
        """
        验证输入参数 - 可选覆盖

        Returns:
            Optional[str]: 错误消息，如果验证通过则返回None
        """
        return None

    def pre_execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行前的准备工作 - 可选覆盖

        Returns:
            Dict[str, Any]: 传递给execute的额外参数
        """
        return {}

    def post_execute(self, result: SkillResult, **kwargs) -> SkillResult:
        """
        执行后的处理工作 - 可选覆盖

        Args:
            result: 执行结果
            **kwargs: 执行参数

        Returns:
            处理后的结果
        """
        return result

    def handle_confirmation(self, confirmation: ConfirmationRequired) -> bool:
        """
        处理确认请求 - 默认实现

        Args:
            confirmation: 确认异常

        Returns:
            bool: 是否确认执行
        """
        self.logger.info(f"需要确认: {confirmation.action_description}")
        self.logger.info(f"上下文: {confirmation.context}")
        return True

    # ==================== 新增 v2.0 方法 ====================

    def optimize_result_for_context(
        self,
        result: SkillResult,
        concise: bool = False
    ) -> SkillResult:
        """
        优化结果以节省上下文（v2.0 新增）

        Args:
            result: 原始结果
            concise: 是否使用精简模式

        Returns:
            优化后的结果
        """
        if not self.config.optimize_context:
            return result

        result.concise_mode = concise

        # 如果是精简模式，压缩数据
        if concise and isinstance(result.data, dict):
            # 保留关键字段
            optimized_data = {
                k: v for k, v in result.data.items()
                if k in ['id', 'name', 'status', 'result']
            }
            result.data = optimized_data

        return result

    def create_actionable_error(
        self,
        error_message: str,
        suggested_action: str,
        context: Dict[str, Any] = None
    ) -> ActionableError:
        """
        创建可操作错误（v2.0 新增）

        Args:
            error_message: 错误消息
            suggested_action: 建议操作
            context: 上下文信息

        Returns:
            ActionableError 实例
        """
        return ActionableError(error_message, suggested_action, context)

    # ==================== 主执行流程 ====================

    def run(self, **kwargs) -> SkillResult:
        """
        运行技能的完整流程

        Returns:
            SkillResult: 最终结果
        """
        import time

        start_time = time.time()
        result = None

        # 开始声明
        self._announce_start()

        try:
            self.logger.info(f"开始执行技能: {self.config.name}")
            self.logger.info(f"参数: {kwargs}")

            # 1. 验证
            validation_error = self.validate(**kwargs)
            if validation_error:
                return SkillResult.error_result(
                    f"验证失败: {validation_error}",
                    "参数验证失败"
                )

            # 2. 预处理
            extra_kwargs = self.pre_execute(**kwargs)
            all_kwargs = {**kwargs, **extra_kwargs}

            # 3. 执行
            result = self.execute(**all_kwargs)

            # 4. 优化上下文
            if self.config.optimize_context:
                concise = kwargs.get('concise', False)
                result = self.optimize_result_for_context(result, concise)

            # 5. 后处理
            if result and result.is_success():
                result = self.post_execute(result, **all_kwargs)

        except ConfirmationRequired as e:
            # 需要确认
            if self.handle_confirmation(e):
                self.config.require_confirmation = False
                return self.run(**kwargs)
            else:
                result = SkillResult(
                    status=SkillStatus.CANCELLED,
                    message="用户取消执行",
                    error="Cancelled by user"
                )

        except ActionableError as e:
            # 可操作错误
            self.logger.error(e.get_actionable_message())
            result = SkillResult.error_result(
                e.get_actionable_message(),
                "执行失败（可操作错误）"
            )

        except Exception as e:
            # 执行异常
            error_msg = str(e)
            self.logger.error(f"技能执行异常: {error_msg}")
            self.logger.error(traceback.format_exc())

            result = SkillResult.error_result(
                error_msg,
                f"执行异常: {error_msg}",
                metadata={"exception_type": type(e).__name__}
            )

        finally:
            # 计算执行时间
            execution_time = time.time() - start_time
            if result:
                result.execution_time = execution_time

            self.logger.info(f"技能执行完成: {self.config.name}")
            self.logger.info(f"执行时间: {execution_time:.2f}秒")
            if result:
                self.logger.info(f"结果状态: {result.status.value}")

            # 完成声明
            if result:
                self._announce_complete(result)

        return result or SkillResult.error_result("未知错误", "执行过程未返回结果")

# ==================== 辅助类 ====================

class AIAssistant:
    """AI助手集成"""

    def __init__(self, config: SkillConfig):
        self.config = config
        self.logger = logging.getLogger("ai.assistant")

    def analyze_action(self, action_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析动作"""
        if not self.config.use_ai_assistant:
            return {"recommendation": "proceed", "reason": "AI助手未启用"}

        return {
            "recommendation": "proceed",
            "reason": "基于AI分析的建议",
            "risk_level": "low",
            "suggestions": []
        }

# ==================== 示例技能类 ====================

class ExampleSkill(SkillBase):
    """示例技能 v2.0 - 演示新功能"""

    def __init__(self):
        config = SkillConfig(
            name="示例技能",
            version="2.0.0",
            description="演示 v2.0 新功能的示例技能",
            author="技能模板",
            require_confirmation=True,
            optimize_context=True,  # 启用上下文优化
            actionable_errors=True,  # 启用可操作错误
            evaluation_driven=False,  # 演示用，不启用评估
        )
        super().__init__(config)

    def validate(self, **kwargs) -> Optional[str]:
        """验证参数"""
        if 'message' not in kwargs:
            return self.create_actionable_error(
                "缺少必要参数: message",
                "请添加 message 参数到调用中",
                {"required": "message"}
            ).get_actionable_message()

        message = kwargs['message']
        if not isinstance(message, str):
            return "参数 message 必须是字符串"

        if len(message) < 3:
            return self.create_actionable_error(
                "消息长度不足",
                "请确保消息长度至少3个字符",
                {"current_length": len(message), "required": 3}
            ).get_actionable_message()

        return None

    @confirm_action("发送消息到控制台")
    @workflow_step("打印消息", "将消息输出到控制台")
    def execute(self, **kwargs) -> SkillResult:
        """执行技能"""
        message = kwargs.get('message', '')
        repeat = kwargs.get('repeat', 1)

        self.logger.info(f"开始执行示例技能 v2.0")

        for i in range(repeat):
            print(f"[{i+1}/{repeat}] 消息: {message}")

        result_data = {
            "original_message": message,
            "repeat_count": repeat,
            "processed_at": "2026-02-08T00:00:00Z",
            "characters": len(message)
        }

        return SkillResult.success(
            data=result_data,
            message=f"成功处理消息: {message}",
            metadata={"version": "2.0", "optimized": self.config.optimize_context}
        )

# ==================== 技能工厂类 ====================

class SkillFactory:
    """技能工厂 - 管理和创建技能实例"""

    _skills: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, skill_class: type):
        """注册技能类"""
        if not issubclass(skill_class, SkillBase):
            raise TypeError(f"技能类必须继承自 SkillBase: {skill_class}")

        cls._skills[name] = skill_class
        logging.getLogger("skill.factory").info(f"注册技能: {name} -> {skill_class.__name__}")

    @classmethod
    def create(cls, name: str, config: Optional[SkillConfig] = None, **kwargs) -> SkillBase:
        """创建技能实例"""
        if name not in cls._skills:
            available = list(cls._skills.keys())
            raise ValueError(f"未找到技能: {name}，可用的技能: {available}")

        skill_class = cls._skills[name]
        instance = skill_class(config, **kwargs)
        return instance

    @classmethod
    def list_skills(cls) -> List[str]:
        """列出所有已注册的技能"""
        return list(cls._skills.keys())

# ==================== 工具函数 ====================

def create_skill_from_function(
    func: Callable,
    name: str = None,
    description: str = None,
    require_confirmation: bool = True
) -> type:
    """从函数创建技能类"""
    skill_name = name or func.__name__
    skill_description = description or func.__doc__ or f"基于函数 {func.__name__} 的技能"

    class DynamicSkill(SkillBase):
        def __init__(self, config: Optional[SkillConfig] = None):
            if config is None:
                config = SkillConfig(
                    name=skill_name,
                    description=skill_description,
                    require_confirmation=require_confirmation
                )
            super().__init__(config)

        def execute(self, **kwargs) -> SkillResult:
            try:
                result = func(**kwargs)
                return SkillResult.success(data=result, message=f"{skill_name} 执行成功")
            except Exception as e:
                return SkillResult.error_result(str(e), f"{skill_name} 执行失败")

    DynamicSkill.__name__ = f"DynamicSkill_{skill_name}"
    DynamicSkill.__doc__ = skill_description

    return DynamicSkill

# ==================== 注册示例技能 ====================

SkillFactory.register("example", ExampleSkill)

# ==================== 命令行接口 ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="通用技能模板 v2.0 - 命令行接口")
    parser.add_argument("skill", nargs="?", help="要执行的技能名称")
    parser.add_argument("--list", action="store_true", help="列出所有可用技能")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--message", help="示例技能的消息参数")
    parser.add_argument("--repeat", type=int, default=1, help="重复次数")
    parser.add_argument("--no-confirm", action="store_true", help="跳过确认")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="输出格式")
    parser.add_argument("--concise", action="store_true", help="精简模式（上下文优化）")

    args = parser.parse_args()

    if args.list:
        skills = SkillFactory.list_skills()
        print("可用技能:")
        for skill in skills:
            print(f"  - {skill}")
        sys.exit(0)

    if not args.skill:
        parser.print_help()
        sys.exit(1)

    try:
        config = SkillConfig(require_confirmation=not args.no_confirm)
        skill = SkillFactory.create(args.skill, config)

        kwargs = {}
        if args.skill == "example":
            if args.message:
                kwargs["message"] = args.message
            kwargs["repeat"] = args.repeat
            kwargs["concise"] = args.concise

        result = skill.run(**kwargs)

        if args.output == "json":
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(f"技能: {args.skill}")
            print(f"状态: {result.status.value}")
            print(f"消息: {result.message}")
            print(f"执行时间: {result.execution_time:.2f}秒")

            if result.error:
                print(f"错误: {result.error}")

            if result.data:
                print(f"数据: {json.dumps(result.data, indent=2, ensure_ascii=False)}")

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
