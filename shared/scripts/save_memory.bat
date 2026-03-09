@echo off
REM 记忆保存快捷脚本
REM 使用方式: save_memory [auto]

setlocal

set PYTHON_SCRIPT=c:\AI-Agent-Local\shared\scripts\save_memory.py

REM 检查参数
if "%1"=="auto" (
    python "%PYTHON_SCRIPT%" --auto --update-preload
) else (
    python "%PYTHON_SCRIPT%" --auto --update-preload
)

endlocal
