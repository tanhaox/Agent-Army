# -*- coding: utf-8 -*-
"""tools.vpn — 变色龙加速器托管 (2026-08-27, 素材层外网管线配套).

实测链路 (2026-08-27 定稿):
  启动 Main.exe → 弹一次确认框(需人工点一次) → 点窗口内开关(相对坐标 210,360)
  → 本地 HTTP 代理口 127.0.0.1:9876 激活 → youtube 200 @1.2s

⚠ GPU 互斥铁律 (用户令, 不可违): VPN 与 4090 计算不能同时 — 虚拟网卡与显卡
驱动冲突会死机/重启。connect() 前必须 ensure_gpu_idle(); GPU 任务前 disconnect()。
llama-server(8080)/ComfyUI(8188)/数字人后端都可能占卡, 按端口探测逐 PID 杀。

⚠ 2026-08-27 实测状态: connect 已验证可用 (启动+点开关(断开态 210,360)+代理口 9876+youtube 200)。
disconnect 未自动化: ①连接态 UI 布局变了, 断开钮坐标未知(存档 _cham_connected.png 待视觉定位)
②进程 admin 权限杀不掉(Access denied) ③WM_CLOSE 被托盘模式无视。
临时手段: 人工点断开 / 或连"断开"坐标定位后补 disconnect()。

用法 (CLI):
  python -m tools.vpn status
  python -m tools.vpn connect [--force-kill-gpu]
  python -m tools.vpn disconnect
用法 (代码):
  from tools.vpn import connect, disconnect, PROXY, proxy_env
  requests.get(url, proxies=proxy_env())
  yt-dlp --proxy http://127.0.0.1:9876 ...
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

EXE = r"C:\Program Files\Cham\Main.exe"
PROXY = "http://127.0.0.1:9876"
PROBE_URL = "https://www.youtube.com/generate_204"  # 轻量连通探针
TOGGLE_X, TOGGLE_Y = 210, 360  # 窗口内相对坐标 (视觉模型实测, 窗口 420x720)

# 占用 4090 的服务端口 → 互斥检查用 (与 gpu_service_manager specs 对齐)
GPU_PORTS = {8080: "llama-server", 8188: "comfyui", 7862: "indextts",
             7860: "fish-speech", 7861: "f5-tts"}


def proxy_env() -> dict:
    return {"http": PROXY, "https": PROXY}


def _ps(script: str) -> str:
    r = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                       capture_output=True, text=True, timeout=60)
    return (r.stdout or "") + (r.stderr or "")


def _proc() -> tuple[int, str] | None:
    """返回 (pid, 窗口标题) — 主进程带窗口才算可操作."""
    out = _ps(
        "Get-Process | Where-Object {$_.Name -eq 'Main'} | "
        "Where-Object {$_.MainWindowTitle -ne ''} | "
        "ForEach-Object { \"$($_.Id)|$($_.MainWindowTitle)\" }")
    for line in out.splitlines():
        line = line.strip()
        if "|" in line:
            pid, title = line.split("|", 1)
            try:
                return int(pid), title
            except ValueError:
                continue
    return None


def _listening(port: int) -> int | None:
    r = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=30)
    for line in (r.stdout or "").splitlines():
        if f"127.0.0.1:{port}" in line and "LISTEN" in line:
            try:
                return int(line.split()[-1])
            except (ValueError, IndexError):
                return None
    return None


def gpu_busy() -> list[str]:
    """在跑的 GPU 服务清单 (互斥检查)."""
    return [f"{name}(:{port},pid={_listening(port)})"
            for port, name in GPU_PORTS.items() if _listening(port)]


def ensure_gpu_idle(force: bool = False) -> list[str]:
    """杀掉在跑的 GPU 服务 (按端口→PID 精确, 不批量杀 python)."""
    killed: list[str] = []
    for port, name in GPU_PORTS.items():
        pid = _listening(port)
        if not pid:
            continue
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        killed.append(f"{name}(:{port},pid={pid})")
    return killed


def probe(timeout: int = 8) -> bool:
    """代理口→外网探针 (generate_204 最轻)."""
    handler = urllib.request.ProxyHandler(proxy_env())
    opener = urllib.request.build_opener(handler)
    try:
        with opener.open(PROBE_URL, timeout=timeout) as resp:
            return resp.status in (200, 204)
    except Exception:
        return False


def status() -> dict:
    proc = _proc()
    port_up = _listening(9876) is not None
    ok = probe(6) if port_up else False
    return {"process": proc[0] if proc else None,
            "proxy_port_up": port_up, "proxy_ok": ok,
            "gpu_busy": gpu_busy()}


def _click_toggle(pid: int) -> None:
    """置前后台 + 按窗口相对坐标点开关."""
    _ps(r"""
$p = Get-Process -Id %d
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class V {
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out R r);
  public struct R { public int L, T, Rt, B; }
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint data, UIntPtr extra);
}
'@
$r = New-Object 'V+R'
[V]::GetWindowRect($p.MainWindowHandle, [ref]$r) | Out-Null
[V]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
Start-Sleep -Milliseconds 600
[V]::SetCursorPos($r.L + %d, $r.T + %d) | Out-Null
Start-Sleep -Milliseconds 300
[V]::mouse_event(2, 0, 0, 0, [UIntPtr]::Zero)
Start-Sleep -Milliseconds 120
[V]::mouse_event(4, 0, 0, 0, [UIntPtr]::Zero)
Write-Host ("clicked window+" + %d + "," + %d)
""" % (pid, TOGGLE_X, TOGGLE_Y, TOGGLE_X, TOGGLE_Y))


def connect(force_kill_gpu: bool = False, wait_sec: int = 25) -> dict:
    """确保 VPN 连通: GPU清场 → 拉起/复用进程 → 点开关 → 等代理口 → 探针."""
    busy = gpu_busy()
    if busy and not force_kill_gpu:
        return {"ok": False, "error": f"GPU 服务在跑, 互斥铁律拒绝连接: {busy} (用 --force-kill-gpu)"}
    if busy:
        ensure_gpu_idle()

    if probe(4):  # 已连通
        return {"ok": True, "already": True, **{k: v for k, v in status().items()}}

    proc = _proc()
    if not proc:
        subprocess.Popen([EXE], cwd=str(Path(EXE).parent))
        print("[vpn] Main.exe 已拉起 (首次启动若弹确认框需人工点一次)")
        for _ in range(wait_sec):
            time.sleep(2)
            proc = _proc()
            if proc:
                break
    if not proc:
        return {"ok": False, "error": "进程未起来 (确认框未点?)"}

    time.sleep(2)
    _click_toggle(proc[0])
    for _ in range(wait_sec):
        time.sleep(2)
        if _listening(9876) and probe(6):
            return {"ok": True, "pid": proc[0], **{k: v for k, v in status().items()}}
    return {"ok": False, "error": "点了开关但代理口未就绪/探针失败", **status()}


def disconnect() -> dict:
    proc = _proc()
    pid = proc[0] if proc else _listening(9876)
    if pid:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
        time.sleep(2)
    return {"ok": not _listening(9876), "killed_pid": pid}


def main() -> int:
    ap = argparse.ArgumentParser(description="变色龙 VPN 托管 (GPU 互斥)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p_c = sub.add_parser("connect")
    p_c.add_argument("--force-kill-gpu", action="store_true")
    sub.add_parser("disconnect")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.cmd == "status":
        print(status())
    elif args.cmd == "connect":
        r = connect(force_kill_gpu=args.force_kill_gpu)
        print(r)
        return 0 if r.get("ok") else 1
    else:
        print(disconnect())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
