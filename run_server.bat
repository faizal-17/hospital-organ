@echo off
title OrganSync - Hospital Organ Request & Government Approval Management System
echo ======================================================================
echo Starting OrganSync Web Application Server...
echo ======================================================================
echo.

cd /d "%~dp0"

REM Try python from PATH or direct installation path
set "PYTHON_CMD=python"
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    set "PYTHON_CMD=C:\Users\divya\AppData\Local\Programs\Python\Python312\python.exe"
)

echo Using Python: %PYTHON_CMD%
echo.
echo Application will be available at: http://127.0.0.1:8000/
echo Press Ctrl+C in this terminal window to stop the server.
echo.

"%PYTHON_CMD%" manage.py runserver 127.0.0.1:8000
pause
