@echo off
setlocal
call "%~dp0config.bat"
call "%~dp0_comum.bat" venv || (pause & exit /b 1)
cd /d "%PROJECT_DIR%"
".venv\Scripts\python.exe" main.py
exit /b %errorlevel%

