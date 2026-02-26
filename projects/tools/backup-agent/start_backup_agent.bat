@echo off
REM Backup Agent 启动脚本（Windows 启动项）
REM 后台运行，不显示窗口

REM 进入项目目录
cd /d C:\AI-Agent-Local\projects\tools\backup-agent

REM 使用 VBScript 启动
wscript.exe "启动 Backup Agent.vbs"

REM 立即退出
exit
