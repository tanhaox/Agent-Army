"""GPU 服务启停 + 看门狗 — 生命周期 mixin.

由 GPUServiceManager 混入, 持有 self.specs / self._states / self.startup_timeout_sec.
行为逐字迁移自原 gpu_service_manager.py (2026-08-08 包化重构).
"""
from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from app.services.gpu_service_manager._http import http_ok, pids_listening_on, port_of
from app.services.gpu_service_manager._specs import ServiceSpec

if TYPE_CHECKING:
    from app.services.gpu_service_manager._manager import _ServiceState

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOG_DIR = PROJECT_ROOT / "logs"

StatusCallback = Callable[[str], None]

__all__ = ["ServiceLifecycleMixin"]


class ServiceLifecycleMixin:
    """服务启停: 确保在线 / 启动 / 停止 / 强杀端口 / 看门狗空闲回收."""

    def _ensure_running(self, key: str, notify: StatusCallback) -> None:
        spec = self.specs[key]
        state = self._states[key]

        if http_ok(spec.health_url):
            if state.proc is None:
                logger.info("[gpu_svc] %s 已由外部启动, 直接复用", spec.display_name)
            return

        # 进程还在但健康检查失败 (启动中途/僵死) → 先杀干净
        if state.proc is not None and state.proc.poll() is None:
            self._kill_proc_tree(state.proc, spec)
            state.proc = None

        # 腾显存: 停掉本管理器启动的其他服务
        for other_key, other_state in self._states.items():
            if other_key != key and other_state.proc is not None:
                notify(f"正在关闭 {self.specs[other_key].display_name} 以腾出显存…")
                self._stop_service(other_key)

        # 霸道清场 (2026-08-07): 强杀占用目标端口的外部进程。
        # 场景: 手动启动的 api_server (PID 由外部拉起, managed=False, 管理器不认) 或残留僵尸进程
        # 占着 7862 → 若不杀, 启动会 bind 失败或直接复用旧进程。按端口杀精确且安全:
        # 人工网页端在 7861 (webui.py), 与托管 7862 不同端口, 不会误杀。
        self._force_free_port(spec)

        notify(f"正在启动 {spec.display_name} 服务 (首次加载模型约 1-2 分钟)…")
        self._await_ready(key, spec, state, notify)

    def _await_ready(
        self,
        key: str,
        spec: ServiceSpec,
        state: _ServiceState,
        notify: StatusCallback,
    ) -> None:
        """启动进程后轮询健康直到就绪; 失败抛 RuntimeError, 超时抛 TimeoutError."""
        state.proc = self._launch(spec)
        state.starting = True
        try:
            deadline = time.time() + self.startup_timeout_sec
            while time.time() < deadline:
                if state.proc.poll() is not None:
                    raise RuntimeError(
                        f"{spec.display_name} 进程启动即退出 (exit={state.proc.returncode}), "
                        f"日志: logs/gpu_svc_{key}.log"
                    )
                if http_ok(spec.health_url):
                    notify(f"{spec.display_name} 服务就绪")
                    logger.info("[gpu_svc] %s ready at %s", key, spec.base_url)
                    return
                time.sleep(2.0)
            # 超时: 杀掉半启动进程, 避免残留占显存
            self._kill_proc_tree(state.proc, spec)
            state.proc = None
            raise TimeoutError(
                f"{spec.display_name} 启动超时 ({self.startup_timeout_sec:.0f}s), "
                f"日志: logs/gpu_svc_{key}.log"
            )
        finally:
            state.starting = False

    def _launch(self, spec: ServiceSpec) -> subprocess.Popen:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = LOG_DIR / f"gpu_svc_{spec.key}.log"
        log_fh = open(log_path, "ab")
        env = dict(os.environ)
        env.update(spec.env)
        # 子进程 UTF-8 输出, 避免 fish 的 GBK UnicodeEncodeError
        env.setdefault("PYTHONIOENCODING", "utf-8")
        cmd = list(spec.command)
        # 相对命令基于服务 cwd 解析
        exe = Path(cmd[0])
        if not exe.is_absolute():
            cmd[0] = str(spec.cwd / exe)
        logger.info("[gpu_svc] launching %s: %s", spec.key, cmd)
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        return subprocess.Popen(
            cmd,
            cwd=str(spec.cwd),
            env=env,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )

    def _stop_service(self, key: str) -> None:
        state = self._states[key]
        if state.proc is None:
            return
        self._kill_proc_tree(state.proc, self.specs[key])
        state.proc = None
        self._force_free_port(self.specs[key])
        logger.info("[gpu_svc] %s stopped, VRAM released", key)

    @staticmethod
    def _force_free_port(spec: ServiceSpec) -> None:
        """兜底: 进程树杀完后端口仍被占用 → 按端口找 PID 强杀.

        场景: 服务派生的孙进程脱离了进程树 (taskkill /T 覆盖不到),
        或前次残留的僵尸进程占着端口导致下次启动 bind 失败.

        安全红线 (2026-08-07): 本项目自用端口永不强杀, 避免"霸道清场"
        误杀正在跑的 web 服务 / 人工网页端 / ComfyUI:
          - 54321  run_web.py (本项目 uvicorn, 承载页面+导演台)
          - 7861   人工网页端 webui.py (index-tts-windows 一键启动)
          - 8188   ComfyUI (LTX 渲染, 显存大户但属本项目管线)
        托管 TTS 端口 (7860/7862/7861-f5) 才是清场目标。
        """
        port = port_of(spec.base_url)
        if not port or os.name != "nt":
            return
        # 本项目/人工网页/ComfyUI 端口永不强杀
        if port in (54321, 7861, 8188):
            return
        for _ in range(5):
            pids = pids_listening_on(port)
            pids = [p for p in pids if p not in (0, os.getpid())]
            if not pids:
                return
            for pid in pids:
                logger.warning(
                    "[gpu_svc] port %s still held by PID %s after kill, force taskkill",
                    port, pid,
                )
                try:
                    subprocess.run(
                        ["taskkill", "/PID", str(pid), "/T", "/F"],
                        capture_output=True, timeout=30,
                    )
                except Exception as exc:
                    logger.warning("[gpu_svc] force kill PID %s failed: %s", pid, exc)
            time.sleep(1.0)
        if pids_listening_on(port):
            logger.error("[gpu_svc] port %s STILL occupied after force kill", port)

    @staticmethod
    def _kill_proc_tree(proc: subprocess.Popen, spec: ServiceSpec) -> None:
        """Windows 下用 taskkill /T 杀整棵进程树 (uv/venv 会派生子进程)."""
        if proc.poll() is not None:
            return
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    capture_output=True, timeout=30,
                )
            else:
                proc.terminate()
            proc.wait(timeout=30)
        except Exception as exc:
            logger.warning("[gpu_svc] kill %s failed: %s", spec.key, exc)

    # ── 看门狗 ───────────────────────────────────────────────

    def _stop_if_idle(self, key: str, force: bool = False) -> None:
        state = self._states[key]
        if state.proc is None:
            return
        idle = time.time() - state.last_used
        if force or idle >= self.idle_timeout_sec:
            # 有任务在跑/排队时不关
            if self._gpu_lock.locked() or self._waiting > 0:
                return
            self._stop_service(key)

    def _start_watchdog(self) -> None:
        if self._watchdog is not None and self._watchdog.is_alive():
            return

        def _loop():
            while True:
                time.sleep(15.0)
                try:
                    for key in list(self._states):
                        self._stop_if_idle(key)
                except Exception as exc:
                    logger.warning("[gpu_svc] watchdog error: %s", exc)
                # 全部服务已停且无任务 → 线程退出
                with self._state_lock:
                    if (
                        all(s.proc is None for s in self._states.values())
                        and self._waiting == 0
                    ):
                        return

        self._watchdog = threading.Thread(
            target=_loop, daemon=True, name="gpu-svc-watchdog"
        )
        self._watchdog.start()
