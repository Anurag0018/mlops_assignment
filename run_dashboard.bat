@echo off
title Student Performance Dashboard
echo ========================================================
echo Launching Student Performance Analytics Dashboard...
echo ========================================================
echo.
python -m streamlit run dashboard/app.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo An error occurred launching the dashboard.
    pause
)
