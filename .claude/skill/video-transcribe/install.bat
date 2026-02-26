@echo off
REM Video Transcribe 安装脚本
REM 用于自动安装所有依赖

echo ========================================
echo Video Transcribe 安装程序
echo ========================================
echo.

echo [1/4] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python，请先安装 Python 3.8 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo Python 已安装
echo.

echo [2/4] 检查 pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 pip
    pause
    exit /b 1
)
echo pip 已安装
echo.

echo [3/4] 安装 Python 依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)
echo 依赖安装成功
echo.

echo [4/4] 检查 FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 警告: 未找到 FFmpeg
    echo FFmpeg 是必需的，请按以下步骤安装:
    echo.
    echo 1. 下载 FFmpeg: https://www.gyan.dev/ffmpeg/builds/
    echo 2. 下载 ffmpeg-git-full.7z
    echo 3. 解压到 C:\ffmpeg
    echo 4. 添加 C:\ffmpeg\bin 到系统 PATH 环境变量
    echo.
    set /p continue="按 Enter 继续安装其他组件，或按 Ctrl+C 取消..."
) else (
    echo FFmpeg 已安装
)
echo.

echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 下一步:
echo 1. 配置 AI 翻译服务（可选，但推荐）
echo 2. 复制 .env.example 为 .env 并填入 API Key
echo.
echo 使用方法:
echo   python scripts\main.py ^<视频链接^>
echo.
pause
