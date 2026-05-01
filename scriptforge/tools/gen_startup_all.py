"""Generate combined ScriptForge startup .bat (backend + frontend)."""
import os

LINES = [
    "@echo off",
    "chcp 65001 1>nul",
    "title ScriptForge 启动中...",
    "",
    "echo ============================================",
    "echo   ScriptForge 全栈服务启动脚本",
    "echo ============================================",
    "echo.",
    "",
    "REM === 清除历史进程 ===",
    "echo [1/4] 正在清除旧进程...",
    "",
    'for /f "tokens=5" %%a in (\'netstat -ano ^| findstr ":8002.*LISTENING" 2^>nul\') do (',
    "    echo   终止 PID %%a (占用端口 8002)",
    "    taskkill /F /PID %%a 1>nul 2>&1",
    ")",
    "",
    'for /f "tokens=5" %%a in (\'netstat -ano ^| findstr ":5173.*LISTENING" 2^>nul\') do (',
    "    echo   终止 PID %%a (占用端口 5173)",
    "    taskkill /F /PID %%a 1>nul 2>&1",
    ")",
    "",
    'taskkill /F /IM python.exe /FI "WINDOWTITLE eq ScriptForge*" 1>nul 2>&1',
    "timeout /t 2 /nobreak 1>nul",
    "echo   旧进程清除完毕",
    "echo.",
    "",
    "REM === 启动后端 ===",
    "echo [2/4] 正在启动后端服务...",
    r"cd /d C:\AI-Agent-Local\scriptforge\backend",
    "",
    r'if exist ".venv-py312\Scripts\activate.bat" (',
    "    echo   检测到虚拟环境: .venv-py312",
    r"    call .venv-py312\Scripts\activate.bat",
    "    echo   虚拟环境已激活",
    ") else (",
    "    echo   使用系统 Python",
    ")",
    "",
    'start "ScriptForge-后端" /MIN cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload"',
    "echo   后端服务已在新窗口启动 (端口 8002)",
    "echo.",
    "",
    "REM === 等待后端就绪 ===",
    "echo [3/4] 等待后端就绪...",
    ":wait_backend",
    "timeout /t 2 /nobreak 1>nul",
    "curl -s http://localhost:8002/api/health 1>nul 2>&1",
    "if errorlevel 1 goto wait_backend",
    "echo   后端已就绪",
    "echo.",
    "",
    "REM === 启动前端 ===",
    "echo [4/4] 正在启动前端服务...",
    r"cd /d C:\AI-Agent-Local\scriptforge\frontend",
    "",
    "echo.",
    "echo ============================================",
    "echo   ScriptForge 全部启动完成！",
    "echo.",
    "echo   前端页面  : http://localhost:5173",
    "echo   后端 API  : http://localhost:8002",
    "echo   API 文档  : http://localhost:8002/docs",
    "echo   健康检查  : http://localhost:8002/api/health",
    "echo ============================================",
    "echo.",
    "echo 按 Ctrl+C 停止前端，后端窗口请手动关闭",
    "echo ============================================",
    "echo.",
    "",
    "pnpm dev",
    "",
    "pause",
]


def generate(dest: str | None = None):
    if dest is None:
        dest = os.path.join(os.environ.get("USERPROFILE", "."), "Desktop", "ScriptForge-启动服务.bat")

    raw = "\r\n".join(LINES) + "\r\n"

    with open(dest, "w", encoding="utf-8-sig") as f:
        f.write(raw)

    print(f"OK: {dest}")
    print(f"  Encoding: UTF-8 with BOM")
    print(f"  Line endings: CRLF")
    print(f"  Lines: {len(LINES)}")


if __name__ == "__main__":
    generate()
