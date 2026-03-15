@echo off
REM Agent Army Web v2.0 启动脚本
REM Phase 1 + Phase 2 完整版

echo ====================================
echo Agent Army Web v2.0
echo 24个Agent | 6大军团 | 100%完成
echo Phase 1 + Phase 2 完整版
echo ====================================
echo.

REM 检查Python环境


echo.
echo [INFO] 正在启动Web界面...
echo [INFO] 访问地址: http://localhost:8501
echo [INFO] 按 Ctrl+C 停止服务
echo.

REM 启动Streamlit（使用最终版主程序）
streamlit run web_app_v2_final.py --server.port=8501 --server.address=localhost

pause
