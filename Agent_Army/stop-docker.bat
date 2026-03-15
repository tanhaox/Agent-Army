@echo off
REM ========================================
REM Agent Army - Docker Desktop 停止脚本
REM ========================================

echo.
echo ========================================
echo   Agent Army - 停止服务
echo ========================================
echo.

echo [1/3] 停止所有服务...
docker-compose down

echo [2/3] 清理未使用的资源...
docker system prune -f

echo [3/3] 清理未使用的镜像...
docker image prune -a -f

echo.
echo ========================================
echo   ✓ 所有服务已停止
echo ========================================
echo.
echo 如需重新启动，请运行：start-docker.bat
echo.
pause
