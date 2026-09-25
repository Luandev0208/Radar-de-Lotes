@echo off
setlocal
call "%~dp0config.bat"
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do set "STAMP=%%c-%%b-%%a"
set "LOG=%LOG_DIR%\%STAMP%_preparar_teste.log"
echo [%date% %time%] Inicio do build de teste>"%LOG%"
call "%~dp002_RODAR_TESTES.bat" || (echo Testes falharam>>"%LOG%" & exit /b 1)
call "%~dp003_GERAR_EXE.bat" || (echo EXE falhou>>"%LOG%" & exit /b 1)
call "%~dp004_GERAR_INSTALADOR.bat" || (echo Instalador falhou>>"%LOG%" & exit /b 1)
if exist "%DELIVERY_DIR%" rmdir /s /q "%DELIVERY_DIR%"
mkdir "%DELIVERY_DIR%" || exit /b 1
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
copy /y "%INSTALLER_FILE%" "%DELIVERY_DIR%\Instalar Radar de Lotes %VERSION%.exe" >nul || exit /b 1
copy /y "%PROJECT_DIR%\VERSION" "%DELIVERY_DIR%\VERSION.txt" >nul
if exist "%PROJECT_DIR%\RELEASE_NOTES.md" copy /y "%PROJECT_DIR%\RELEASE_NOTES.md" "%DELIVERY_DIR%\CHANGELOG_TESTE.txt" >nul
>"%DELIVERY_DIR%\LEIA-ME-TESTE.txt" echo Instale e teste esta versao. O main e a Release nao foram alterados.
echo [%date% %time%] Build %VERSION% concluido>>"%LOG%"
echo BUILD DE TESTE CONCLUIDO. Main e Release nao foram alterados.
start "" explorer "%DELIVERY_DIR%"
exit /b 0

