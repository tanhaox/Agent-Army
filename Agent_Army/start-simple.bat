@echo off
cd /d "%~dp0"
python -m streamlit run web_app_v2.py --server.port 8501
pause
