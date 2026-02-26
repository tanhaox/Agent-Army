@echo off
REM 快速备份脚本 - AI 主动触发
REM
REM 使用方法：
REM   quick_backup.bat [备份原因]
REM
REM 示例：
REM   quick_backup.bat 检测到bug关键词
REM   quick_backup.bat 修复订单匹配问题

chcp 65001 >nul
cd /d "%~dp0"

if "%~1"=="" (
    python quick_backup.py "AI 检测到关键词"
) else (
    python quick_backup.py %*
)
