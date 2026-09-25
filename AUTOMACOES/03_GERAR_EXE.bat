@echo off
setlocal
call "%~dp0config.bat"
call "%~dp0_comum.bat" venv || exit /b 1
cd /d "%PROJECT_DIR%"
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name "Radar de Lotes" --add-data "VERSION;." --collect-all winotify --collect-submodules bs4 --collect-submodules requests main.py || exit /b 1
if not exist "%EXE_FILE%" (echo ERRO: o EXE nao foi criado. & exit /b 1)
"%EXE_FILE%" --self-test || (echo ERRO: o autoteste do EXE falhou. & exit /b 1)
echo OK: "%EXE_FILE%"
exit /b 0

