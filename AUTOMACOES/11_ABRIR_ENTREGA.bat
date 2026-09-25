@echo off
setlocal
call "%~dp0config.bat"
if not exist "%DELIVERY_DIR%" mkdir "%DELIVERY_DIR%"
start "" explorer "%DELIVERY_DIR%"

