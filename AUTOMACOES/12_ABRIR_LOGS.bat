@echo off
setlocal
call "%~dp0config.bat"
start "" explorer "%LOG_DIR%"

