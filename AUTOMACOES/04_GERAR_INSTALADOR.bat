@echo off
setlocal
call "%~dp0config.bat"
if not exist "%EXE_FILE%" (echo ERRO: gere o EXE primeiro pela opcao 3. & exit /b 1)
call "%~dp0_comum.bat" inno || exit /b 1
cd /d "%PROJECT_DIR%"
for /f "usebackq delims=" %%V in ("VERSION") do set "VERSION=%%V"
>build_version.iss echo #define AppVersion "%VERSION%"
if exist installer_output rmdir /s /q installer_output
"%ISCC_PATH%" installer.iss || exit /b 1
if not exist "%INSTALLER_FILE%" (echo ERRO: instalador nao criado. & exit /b 1)
echo OK: "%INSTALLER_FILE%"
exit /b 0

