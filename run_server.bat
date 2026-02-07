@echo off
REM Windows batch script to run the server with correct PYTHONPATH
cd /d "%~dp0"
set PYTHONPATH=%CD%
python -m uvicorn app.main:app --reload
pause
