"""
Agent Army - 日志系统
使用structlog提供专业的日志功能
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import structlog
from structlog.types import Processor


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "./logs",
    enable_console: bool = True,
    enable_file: bool = True
) -> None:
    """
    配置日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件目录
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件输出
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 共享的处理器
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
    ]

    # 控制台输出处理器
    console_processors = shared_processors + [
        structlog.dev.ConsoleRenderer(colors=True)
    ]

    # 文件输出处理器
    file_processors = shared_processors + [
        structlog.processors.JSONRenderer()
    ]

    # 配置structlog
    structlog.configure(
        processors=console_processors if enable_console else file_processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level)
        ),
        cache_logger_on_first_use=True,
    )

    # 配置标准logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(log_level),
    )

    # 如果启用文件输出,添加文件处理器
    if enable_file:
        file_handler = logging.FileHandler(
            log_path / "agent-army.log",
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.root.addHandler(file_handler)

        # 错误日志单独记录
        error_handler = logging.FileHandler(
            log_path / "error.log",
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter("%(message)s"))
        logging.root.addHandler(error_handler)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    获取日志器

    Args:
        name: 日志器名称

    Returns:
        配置好的日志器
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    日志器混入类,为类提供日志功能
    """

    _logger: Optional[structlog.stdlib.BoundLogger] = None

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """
        获取日志器

        Returns:
            配置好的日志器
        """
        if self._logger is None:
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
