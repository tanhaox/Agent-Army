@echo off
chcp 65001 >nul

echo ============================================================
echo   Agent Army v2.0
echo ============================================================
echo.
echo 正在启动服务...
echo.
echo 新窗口将打开，请勿关闭它
echo.

REM 在新窗口中启动 Streamlit
start "Agent Army v2.0 - Web服务" cmd /k "cd /d %~dp0 && echo 正在启动 Streamlit... && echo. && python -m streamlit run web_app_v2.py --server.port 8501 --server.address localhost && echo. && echo 服务已停止 && pause"

echo.
echo ============================================================
echo   服务已在新窗口中启动
echo ============================================================
echo.
echo 访问地址: http://localhost:8501
echo.
echo 提示:
echo   - 服务运行在名为 "Agent Army v2.0 - Web服务" 的窗口中
echo   - 关闭该窗口将停止服务
echo   - 如果浏览器没有自动打开，请手动访问上面的地址
echo.

timeout /t 5 /nobreak >nul

REM 尝试打开浏览器
start http://localhost:8501

echo.
echo 按任意键关闭此窗口...
pause >nul
