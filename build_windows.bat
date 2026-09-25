@echo off
setlocal
cd /d "%~dp0"
for /f "usebackq delims=" %%V in ("VERSION") do set "RADAR_VERSION=%%V"
if not defined RADAR_VERSION exit /b 1

where py >nul 2>nul || (echo Python Launcher nao encontrado no computador de desenvolvimento. & exit /b 1)
py -3.12 -c "import sys; assert sys.version_info[:2] == (3, 12)" || exit /b 1
if exist .venv rmdir /s /q .venv
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist installer_output rmdir /s /q installer_output
py -3.12 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip || exit /b 1
python -m pip install -r requirements-dev.txt || exit /b 1
python -m pytest -q || exit /b 1
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "Radar de Lotes" --add-data "VERSION;." --collect-all winotify --collect-submodules bs4 --collect-submodules requests main.py || exit /b 1
dist\Radar de Lotes.exe --self-test || exit /b 1

>build_version.iss echo #define AppVersion "%RADAR_VERSION%"
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (echo Inno Setup 6 nao encontrado. & exit /b 1)
"%ISCC%" installer.iss || exit /b 1
echo.
echo Instalador criado em: installer_output\Instalar Radar de Lotes.exe
exit /b 0
