@echo off
echo 正在杀死僵尸 claude.exe 进程...
taskkill /PID 115920 /F
taskkill /PID 12000 /F
taskkill /PID 53768 /F
echo.
echo 完成！按任意键退出...
pause
