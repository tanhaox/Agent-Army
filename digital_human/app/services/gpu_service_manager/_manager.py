"""GPU 服务管理器主类 — 对外 API + 状态持有.

行为逐字迁移自原 gpu_service_manager.py (2026-08-08 包化重构).
"""
from __future__ import annotations

import subprocess
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable

from app.services.gpu_service_manager._http import http_ok
from app.services.gpu_service_manager._lifecycle import ServiceLifecycleMixin
from app.services.gpu_service_manager._specs import NO_LOCAL_SERVICE, ServiceSpec

logger = __import__("logging").getLogger(__name__)

StatusCallback = Callable[[str], None]

__all__ = ["GPUServiceManager", "_ServiceState"]


@dataclass
class _ServiceState:
    proc: subprocess.Popen | None = None  # 本管理器拉起的进程 (None=未管理)
    last_used: float = 0.0
    starting: bool = False


class GPUServiceManager(ServiceLifecycleMixin):
    """单 GPU 串行调度: 排队 → 确保服务在线 → 执行 → 空闲自动关停."""

    def __init__(
        self,
        specs: dict[str, ServiceSpec],
        idle_timeout_sec: float = 300.0,
        startup_timeout_sec: float = 300.0,
        auto_manage: bool = True,
    ):
        self.specs = specs
        self.idle_timeout_sec = idle_timeout_sec
        self.startup_timeout_sec = startup_timeout_sec
        self.auto_manage = auto_manage

        self._gpu_lock = threading.Lock()  # 全局串行锁 (排队)
        self._state_lock = threading.Lock()  # 保护 _states/_waiting
        self._states: dict[str, _ServiceState] = {k: _ServiceState() for k in specs}
        self._waiting = 0  # 当前排队任务数
        self._active_key: str | None = None  # 正在执行任务的服务
        self._watchdog: threading.Thread | None = None

    # ── 对外主入口 ────────────────────────────────────────────

    @contextmanager
    def session(self, backend: str, status_callback: StatusCallback | None = None):
        """排队获取 GPU → 确保 backend 服务在线 → 执行 → 释放.

        backend 不是本地 GPU 服务 (如 elevenlabs) 时直接放行.
        服务启动失败抛 RuntimeError, 超时抛 TimeoutError.
        """
        if backend in NO_LOCAL_SERVICE or backend not in self.specs:
            yield
            return
        if not self.auto_manage:
            # 未启用托管: 保持旧行为 (直接调用, 服务不在线由调用方报错)
            yield
            return

        notify = status_callback or (lambda msg: None)

        with self._state_lock:
            self._waiting += 1
            queue_pos = self._waiting
        if queue_pos > 1 or self._gpu_lock.locked():
            notify("GPU 排队中 (前面还有任务)…")

        self._gpu_lock.acquire()
        try:
            with self._state_lock:
                self._waiting -= 1
                self._active_key = backend
            self._ensure_running(backend, notify)
            self._touch(backend)
            yield
        finally:
            self._touch(backend)
            with self._state_lock:
                self._active_key = None
            self._gpu_lock.release()
            if self.idle_timeout_sec <= 0:
                # 立即释放显存模式
                self._stop_if_idle(backend, force=True)
            else:
                self._start_watchdog()

    # ── 看门狗 ───────────────────────────────────────────────

    def _touch(self, key: str) -> None:
        self._states[key].last_used = time.time()

    # ── 状态与手动控制 ────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        with self._state_lock:
            services = {}
            for key, spec in self.specs.items():
                state = self._states[key]
                healthy = http_ok(spec.health_url, timeout=1.5)
                services[key] = {
                    "display_name": spec.display_name,
                    "base_url": spec.base_url,
                    "healthy": healthy,
                    "managed": state.proc is not None and state.proc.poll() is None,
                    "starting": state.starting,
                    "idle_sec": round(time.time() - state.last_used, 1) if state.last_used else None,
                }
            return {
                "auto_manage": self.auto_manage,
                "idle_timeout_sec": self.idle_timeout_sec,
                "busy": self._gpu_lock.locked(),
                "active_backend": self._active_key,
                "queue_length": self._waiting,
                "services": services,
            }

    def stop_all(self) -> list[str]:
        """手动停止所有托管服务 (外部启动的不动)."""
        stopped = []
        for key in list(self._states):
            if self._states[key].proc is not None:
                self._stop_service(key)
                stopped.append(key)
        return stopped

    def shutdown(self) -> None:
        """应用退出钩子: 杀掉所有托管进程, 不留孤儿占显存."""
        self.stop_all()
