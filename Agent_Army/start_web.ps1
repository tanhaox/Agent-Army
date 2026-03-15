# Agent Army v2.0 - PowerShell 启动脚本
# 更可靠的启动方式

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Agent Army v2.0 - Web界面启动" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
Write-Host "[1/4] 检查 Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "      $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "      [错误] Python 未安装" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 检查 Streamlit
Write-Host "[2/4] 检查 Streamlit..." -ForegroundColor Yellow
try {
    $streamlitVersion = python -m streamlit --version 2>&1
    Write-Host "      $streamlitVersion" -ForegroundColor Green
} catch {
    Write-Host "      [错误] Streamlit 未安装，正在安装..." -ForegroundColor Red
    pip install streamlit
}

# 切换到脚本目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
Write-Host "[3/4] 当前目录: $scriptPath" -ForegroundColor Green

# 检查文件
Write-Host "[4/4] 检查文件..." -ForegroundColor Yellow
if (Test-Path "web_app_v2.py") {
    Write-Host "      [OK] web_app_v2.py" -ForegroundColor Green
} else {
    Write-Host "      [错误] 找不到 web_app_v2.py" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  正在启动服务" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址: http://localhost:8501" -ForegroundColor Yellow
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 启动 Streamlit
try {
    python -m streamlit run web_app_v2.py --server.port 8501 --server.address localhost
} catch {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  启动失败" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "错误: $_" -ForegroundColor Red
    Write-Host ""
}

Read-Host "按回车退出"
