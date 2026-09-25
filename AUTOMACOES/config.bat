@echo off
set "RADAR_ROOT=%~dp0.."
for %%I in ("%RADAR_ROOT%") do set "RADAR_ROOT=%%~fI"
set "PROJECT_DIR=%RADAR_ROOT%\PROJETO"
set "AUTOMATION_DIR=%RADAR_ROOT%\AUTOMACOES"
set "DELIVERY_DIR=%RADAR_ROOT%\ENTREGA_PARA_TESTE"
set "REPO_NAME=Luandev0208/Radar-de-Lotes"
set "EXE_FILE=%PROJECT_DIR%\dist\Radar de Lotes.exe"
set "INSTALLER_FILE=%PROJECT_DIR%\installer_output\Instalar Radar de Lotes.exe"
set "LOG_DIR=%AUTOMATION_DIR%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

