"""Generate ScriptForge backend startup .bat file with UTF-8 BOM + CRLF."""

import sys
import os

CONTENT_LINES = [
    "@echo off",
    "chcp 65001 >nul",
    "title ScriptForge Backend Server",
    "",
    "echo ============================================",
    "echo   ScriptForge 后端服务启动脚本",
    "echo ============================================",
    "echo.",
    "",
    "REM ============================================================",
    "REM 清除历史进程",
    "REM ============================================================",
    "echo [1/3] 正在清除旧进程...",
    "",
    "REM 按端口 8000 终止占用进程",
    "for /f \"tokens=5\" %%a in ('netstat -ano ^| findstr \":8002.*LISTENING\" 2^>nul') do (",
    "    echo   终止 PID %%a (占用端口 8002)",
    "    taskkill /F /PID %%a >nul 2>&1",
    ")",
    "",
    "REM 按窗口标题终止残留 Python 进程",
    "taskkill /F /IM python.exe /FI \"WINDOWTITLE eq ScriptForge*\" >nul 2>&1",
    "",
    "REM 等待端口彻底释放",
    "timeout /t 2 /nobreak >nul",
    "",
    "REM 二次确认端口已释放",
    "for /f \"tokens=5\" %%a in ('netstat -ano ^| findstr \":8000.*LISTENING\" 2^>nul') do (",
    "    echo   [警告] 端口 8000 仍被 PID %%a 占用，强制终止...",
    "    taskkill /F /PID %%a >nul 2>&1",
    "    timeout /t 1 /nobreak >nul",
    ")",
    "",
    "echo   旧进程清除完毕",
    "echo.",
    "",
    "REM ============================================================",
    "REM 启动服务",
    "REM ============================================================",
    "echo [2/3] 正在切换到项目目录...",
    r"cd /d C:\AI-Agent-Local\scriptforge\backend",
    "",
    "REM 检查并激活虚拟环境",
    r'if exist ".venv-py312\Scripts\activate.bat" (',
    "    echo   检测到虚拟环境: .venv-py312",
    r"    call .venv-py312\Scripts\activate.bat",
    "    echo   虚拟环境已激活",
    ") else (",
    "    echo   未检测到虚拟环境，使用系统 Python",
    ")",
    "",
    "echo.",
    "echo [3/3] 启动 Uvicorn 服务 (端口 8000)...",
    "echo.",
    "echo ============================================",
    "echo   后端地址  : http://localhost:8002",
    "echo   API 文档  : http://localhost:8002/docs",
    "echo   健康检查  : http://localhost:8002/api/health",
    "echo   前端页面  : http://localhost:5173",
    "echo ============================================",
    "echo.",
    "echo 按 Ctrl+C 停止服务",
    "echo ============================================",
    "echo.",
    "",
    "python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload",
    "",
    "pause",
]


def generate(dest: str | None = None):
    if dest is None:
        dest = os.path.join(os.environ.get("USERPROFILE", "."), "Desktop", "ScriptForge-启动后端.bat")

    # CRLF line endings (required for .bat for-loop body parsing)
    raw = "\r\n".join(CONTENT_LINES) + "\r\n"

    # UTF-8 BOM — BOM tells cmd.exe to parse as UTF-8; CRLF fixes @echo off
    with open(dest, "w", encoding="utf-8-sig") as f:
        f.write(raw)

    print(f"OK: {dest}")
    print(f"  Encoding: UTF-8 with BOM")
    print(f"  Line endings: CRLF")
    print(f"  Lines: {len(CONTENT_LINES)}")
    return dest
