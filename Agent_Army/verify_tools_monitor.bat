@echo off
chcp 65001 >nul 2>&1
cd /d C:\AI-Agent-Local\Agent_Army

echo.
echo ========================================
echo    验证工具库监控功能
echo ========================================
echo.

echo [1/3] 检查工具导入...
python -c "from src.core.tools import NewsTool, FinancialTool, LLMTool, NLPTool, FormulaTool; print('✅ 所有工具导入成功')" 2>nul
if %errorlevel% equ 0 (
    echo ✅ 工具库正常
) else (
    echo ❌ 工具库异常
    pause
    exit /b 1
)

echo.
echo [2/3] 检查Web界面...
python -c "import streamlit; print('✅ Streamlit可用')" 2>nul
if %errorlevel% equ 0 (
    echo ✅ Web框架正常
) else (
    echo ❌ Web框架异常
    pause
    exit /b 1
)

echo.
echo [3/3] 启动Web界面...
echo.
echo ========================================
echo   工具库监控功能已就绪
echo ========================================
echo.
echo 功能位置:
echo   - 主页: 工具库状态监控
echo   - Agent状态: 工具库详细信息
echo   - 系统配置: API配置检查
echo.
echo 访问地址: http://localhost:8501
echo.
echo ========================================
echo.

streamlit run web_app.py --server.port 8501
