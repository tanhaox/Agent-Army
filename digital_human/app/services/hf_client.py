"""HyperFrames (HF) CLI subprocess wrapper.

Single responsibility: invoke ``npx hyperframes render <project_dir> -o <output>``
with ``cwd=project_dir``, 300s hard timeout, capture stdout/stderr to ``render.log``.

Validation (output exists / ffprobe) is the orchestrator's job, not ours.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


class HFRenderError(RuntimeError):
    """Raised when the HF subprocess fails (non-zero exit or timeout)."""


def render_visual(
    project_dir: Path,
    output_path: Path,
    hyperframes_bin: str = "npx",
    timeout_sec: int = 300,
) -> dict:
    """Run ``npx hyperframes render . -o <name>`` inside ``project_dir``.

    Args:
        project_dir: HF project root (must contain ``index.html``).
        output_path: Target mp4 path (absolute or relative to ``project_dir``).
        hyperframes_bin: Executable to invoke (default ``npx``).
        timeout_sec: Hard timeout in seconds (default 300).

    Returns:
        Dict ``{returncode, stdout, stderr, log_path, cmd}``.

    Raises:
        HFRenderError: When exit != 0 or subprocess times out.
    """
    project_dir = Path(project_dir).resolve()
    output_path = Path(output_path)
    log_path = project_dir / "render.log"

    # HF expects `-o <name>` (the basename) and writes inside cwd.
    output_basename = output_path.name

    # Windows note: bare ``npx`` resolves to ``npx.exe`` (Node 21+) but the
    # legacy batch shim ``npx.cmd`` is the reliable Windows entry — without
    # ``.cmd`` CreateProcess raises FileNotFoundError on some setups.
    import platform
    bin_name = hyperframes_bin
    if platform.system() == "Windows" and bin_name == "npx" and not bin_name.lower().endswith((".cmd", ".exe", ".bat")):
        bin_name = "npx.cmd"
    # `-y` 关键: 首次运行时 npx 弹出 "Ok to proceed? (y)" 交互确认会卡死到
    # 300s 超时 (2026-08-07 hf_title 全超时根因)。`-y` 跳过下载确认。
    # `--low-memory-mode` 关键 (2026-08-08): 本机 (Intel UHD 集显 + 32-core
    # auto-workers) 默认 calibration 阶段 Chrome 初始化会卡死到 300s 超时
    # (Runtime.evaluate timed out, 150 帧 0 完成)。该参数固定 1 worker + 截图
    # 捕获 + 跳过 auto-worker calibration, 实测 39s 稳定出片。
    cmd = [
        bin_name,
        "-y",
        "hyperframes",
        "render",
        ".",
        "-o",
        output_basename,
        "--low-memory-mode",
    ]

    # NOTE: 不能用 subprocess.run(timeout=...) — Windows 上 timeout 只杀主进程，
    # npx 的子进程 (node/chromium) 继承 stdout/stderr 管道导致 communicate() 死锁。
    # 改用 Popen + 手动超时 + taskkill /F /T 杀进程树。
    import platform
    is_win = platform.system() == "Windows"
    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if is_win else 0

    proc = subprocess.Popen(
        cmd,
        cwd=str(project_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=creation_flags,
    )
    # 2026-08-08: 登记到 proc_registry, 供 force-stop 按 job_id 杀整棵进程树.
    # 非 director 上下文 (visual_render 管线) 时线程无 job_id → 自动 no-op.
    from app.services.proc_registry import register_subprocess, unregister_subprocess
    register_subprocess(proc)

    timed_out = False
    try:
        try:
            stdout, stderr = proc.communicate(timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            timed_out = True
            # Windows: taskkill /F /T 杀整棵进程树 (npx → node → chromium)
            if is_win:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    capture_output=True, timeout=10,
                )
            else:
                proc.kill()
            try:
                stdout, stderr = proc.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                stdout, stderr = "", ""
                proc.kill()

        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            f"$ {' '.join(cmd)}\n"
            f"[cwd={project_dir}]\n"
            f"[exit={proc.returncode}]\n"
            f"[timed_out={timed_out}]\n"
            f"--- stdout ---\n{stdout}\n"
            f"--- stderr ---\n{stderr}\n",
            encoding="utf-8",
        )

        result = {
            "returncode": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "log_path": str(log_path),
            "cmd": cmd,
        }

        if timed_out:
            raise HFRenderError(
                f"HyperFrames timed out after {timeout_sec}s (see {log_path})"
            )

        if proc.returncode != 0:
            raise HFRenderError(
                f"HyperFrames exited with code {proc.returncode} (see {log_path})"
            )

        return result
    finally:
        unregister_subprocess(proc)