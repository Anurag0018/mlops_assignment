@echo off
title Student Performance Pipeline
echo ========================================================
echo Executing Student Performance Data Engineering Pipeline
echo ========================================================
echo.
python dags/student_pipeline.py
if %ERRORLEVEL% equ 0 (
    echo.
    echo Pipeline execution completed successfully!
) else (
    echo.
    echo Pipeline execution encountered an error.
)
pause
