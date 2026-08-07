"""GPU 服务生命周期管理器 — 按需启动 / 排队执行 / 空闲自动关闭.

背景:
  本地单卡 4090 要轮流跑 Fish/F5/IndexTTS2 + ComfyUI(LTX) 多个显存大户.
  TTS 服务不能常驻 — 音频生成结束后必须腾出显存给后续视频渲染.

策略:
  - session(backend): 全局 GPU 锁(排队) + 确保目标服务健康(不在线则拉起)
  - 拉起某服务前, 先停掉本管理器启动的其他 TTS 服务(腾显存)
  - 外部手动启动的服务只用不杀(managed=False), 避免误杀
  - 看门狗线程: 空闲 > idle_timeout_sec 自动 kill 进程树
  - idle_timeout_sec = 0 → session 结束立即关闭

部署事实(内置默认, 可被 config/app.yaml `tts_services.<key>` 覆盖):
  fish     E:/AI/tts/fish-speech       tools/api_server.py  :7860  /v1/health
  f5       E:/AI/tts/F5-TTS            f5-tts_infer-gradio  :7861  /
  indextts E:/AI/tts/index-tts-windows api_server.py        :7862  /health
  comfyui  E:/AI/ComfyUI_windows_portable main.py           :8188  /system_stats
"""
from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"

StatusCallback = Callable[[str], None]

# ── 内置部署事实 ──────────────────────────────────────────────
_BUILTIN_SPECS: dict[str, dict[str, Any]] = {
    "fish": {
        "display_name": "Fish Speech",
        "base_url": "http://127.0.0.1:7860",
        "health_path": "/v1/health",
        "cwd": "E:/AI/tts/fish-speech",
        "command": [
            ".venv/Scripts/python.exe", "tools/api_server.py",
            "--listen", "127.0.0.1:7860",
            "--llama-checkpoint-path", "E:/AI/tts/models/s2-pro",
            "--decoder-checkpoint-path", "E:/AI/tts/models/s2-pro/codec.pth",
            "--decoder-config-name", "modded_dac_vq",
            "--device", "cuda",
        ],
        "env": {},
    },
    "f5": {
        "display_name": "F5-TTS",
        "base_url": "http://127.0.0.1:7861",
        "health_path": "/",
        "cwd": "E:/AI/tts/F5-TTS",
        "command": [
            ".venv/Scripts/f5-tts_infer-gradio.exe",
            "--host", "127.0.0.1", "--port", "7861",
        ],
        "env": {},
    },
    "indextts": {
        "display_name": "IndexTTS2",
        "base_url": "http://127.0.0.1:7862",
        "health_path": "/health",
        "cwd": "E:/AI/tts/index-tts-windows",
        "command": [
            ".venv/Scripts/python.exe", "api_server.py",
            "--port", "7862", "--host", "127.0.0.1",
        ],
        # 与 启动_api_server.bat 一致: 清 PYTHONPATH + HF 镜像
        "env": {
            "PYTHONPATH": "",
            "HF_ENDPOINT": "https://hf-mirror.com",
            "HF_HOME": "E:/AI/tts/index-tts-windows/.huggingface",
        },
    },
    "comfyui": {
        "display_name": "ComfyUI",
        "base_url": "http://127.0.0.1:8188",
        "health_path": "/system_stats",
        "cwd": "E:/AI/ComfyUI_windows_portable",
        "command": [
            "python_embeded/python.exe", "-s", "ComfyUI/main.py",
            "--windows-standalone-build", "--listen", "127.0.0.1",
        ],
        # 与 run_nvidia_gpu.bat 一致: CUDA_VISIBLE_DEVICES=0 锚定 4090
        # (本机 CUDA 视角 CUDA0=4090 / CUDA1=4060, 不设会落 4060 8GB OOM)
        "env": {"CUDA_VISIBLE_DEVICES": "0"},
    },
}

# elevenlabs 等云端后端不占本地 GPU, session 直接放行
_NO_LOCAL_SERVICE = {"elevenlabs"}


@dataclass
class ServiceSpec:
    key: str
    display_name: str
    base_url: str
    health_path: str
    cwd: Path
    command: list[str]
    env: dict[str, str]

    @property
    def health_url(self) -> str:
        return self.base_url.rstrip("/") + self.health_path


@dataclass
class _ServiceState:
    proc: subprocess.Popen | None = None  # 本管理器拉起的进程 (None=未管理)
    last_used: float = 0.0
    starting: bool = False


def _http_ok(url: str, timeout: float = 3.0) -> bool:
    """GET url, 2xx/3xx 视为健康."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False


def _port_of(base_url: str) -> int | None:
    from urllib.parse import urlparse

    return urlparse(base_url).port


def _pids_listening_on(port: int) -> list[int]:
    """Windows: netstat -ano 找出 LISTENING 在该端口上的 PID."""
    if os.name != "nt":
        return []
    try:
        out = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True, text=True, timeout=15,
        ).stdout
    except Exception:
        return []
    pids: set[int] = set()
    suffix = f":{port}"
    for line in out.splitlines():
        parts = line.split()
        # TCP  本地地址:端口  远程地址  LISTENING  PID
        if len(parts) >= 5 and parts[0] == "TCP" and parts[1].endswith(suffix):
            if "LISTEN" in parts[3].upper():
                try:
                    pids.add(int(parts[4]))
                except ValueError:
                    pass
    return sorted(pids)


class GPUServiceManager:
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
        if backend in _NO_LOCAL_SERVICE or backend not in self.specs:
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

    # ── 服务启停 ─────────────────────────────────────────────

    def _ensure_running(self, key: str, notify: StatusCallback) -> None:
        spec = self.specs[key]
        state = self._states[key]

        if _http_ok(spec.health_url):
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
                if _http_ok(spec.health_url):
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
        port = _port_of(spec.base_url)
        if not port or os.name != "nt":
            return
        # 本项目/人工网页/ComfyUI 端口永不强杀
        if port in (54321, 7861, 8188):
            return
        for _ in range(5):
            pids = _pids_listening_on(port)
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
        if _pids_listening_on(port):
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

    def _touch(self, key: str) -> None:
        self._states[key].last_used = time.time()

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
        self._watchdog = threading.Thread(target=_loop, daemon=True, name="gpu-svc-watchdog")
        self._watchdog.start()

    # ── 状态与手动控制 ────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        with self._state_lock:
            services = {}
            for key, spec in self.specs.items():
                state = self._states[key]
                healthy = _http_ok(spec.health_url, timeout=1.5)
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


# ── 模块级单例 ────────────────────────────────────────────────
_manager: GPUServiceManager | None = None
_manager_lock = threading.Lock()


def _build_specs(raw_cfg: dict[str, Any]) -> tuple[dict[str, ServiceSpec], dict[str, Any]]:
    """内置默认 + app.yaml `tts_services` 覆盖 → ServiceSpec 表."""
    svc_cfg = raw_cfg.get("tts_services") or {}
    specs: dict[str, ServiceSpec] = {}
    for key, builtin in _BUILTIN_SPECS.items():
        override = svc_cfg.get(key) or {}
        merged = {**builtin, **override}
        specs[key] = ServiceSpec(
            key=key,
            display_name=merged["display_name"],
            base_url=merged["base_url"],
            health_path=merged["health_path"],
            cwd=Path(merged["cwd"]),
            command=list(merged["command"]),
            env=dict(merged.get("env") or {}),
        )
    return specs, svc_cfg


def get_gpu_service_manager() -> GPUServiceManager:
    """惰性单例; 配置读 config/app.yaml `tts_services` 节 (可缺省)."""
    global _manager
    with _manager_lock:
        if _manager is None:
            from ..config import get_config

            raw = get_config().raw
            specs, svc_cfg = _build_specs(raw)
            _manager = GPUServiceManager(
                specs=specs,
                idle_timeout_sec=float(svc_cfg.get("idle_timeout_sec", 300)),
                startup_timeout_sec=float(svc_cfg.get("startup_timeout_sec", 300)),
                auto_manage=bool(svc_cfg.get("auto_manage", True)),
            )
        return _manager
