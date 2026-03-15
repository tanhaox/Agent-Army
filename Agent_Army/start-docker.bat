@echo off
chcp 65001 > nul
REM ========================================
REM Agent Army v2.0 - Docker Desktop 启动脚本
REM ========================================

cd /d "%~dp0"

echo.
echo ========================================
echo   Agent Army v2.0 - Docker 启动
echo ========================================
echo.

REM 检查 Docker Desktop 是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop 未运行！
    echo.
    echo 请先启动 Docker Desktop，然后重试此脚本。
    echo.
    pause
    exit /b 1
)

echo [1/5] 检查环境变量文件...
if not exist ".env" (
    echo [WARN] 未找到 .env 文件
    echo.
    echo 正在从 .env.example 创建 .env 文件...
    copy .env.example .env >nul
    echo.
    echo [IMPORTANT] 请编辑 .env 文件，填入您的API密钥：
    echo   - ZHIPU_API_KEY（必需）
    echo   - TUSHARE_API_KEY（必需）
    echo.
    pause
)

echo [2/5] 检查数据目录...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "monitoring" mkdir monitoring
echo OK

echo [3/5] 检查监控配置...
if not exist "monitoring\prometheus.yml" (
    echo global: > monitoring\prometheus.yml
    echo   scrape_interval: 15s >> monitoring\prometheus.yml
    echo. >> monitoring\prometheus.yml
    echo scrape_configs: >> monitoring\prometheus.yml
    echo   - job_name: 'agent-army' >> monitoring\prometheus.yml
    echo     static_configs: >> monitoring\prometheus.yml
    echo       - targets: ['agent-army:8501'] >> monitoring\prometheus.yml
    echo     metrics_path: '/_stcore/health' >> monitoring\prometheus.yml
)
echo OK

echo [4/5] 启动 Docker 服务...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] 服务启动失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✓ 所有服务已成功启动！
echo ========================================
echo.
echo 服务访问地址：
echo   - Web界面: http://localhost:8501
echo   - Grafana: http://localhost:3000 (admin/admin)
echo   - Prometheus: http://localhost:9090
echo.
echo 常用命令：
echo   - 查看日志: docker-compose logs -f agent-army
echo   - 停止服务: stop-docker.bat
echo   - 重启服务: docker-compose restart
echo.
echo 按任意键打开 Web 界面...
pause >nul

REM 打开浏览器
start http://localhost:8501

echo.
echo 已在后台运行服务...
echo 如需查看完整日志，请运行：docker-compose logs -f
