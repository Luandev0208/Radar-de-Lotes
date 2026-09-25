@echo off
setlocal enabledelayedexpansion
call "%~dp0config.bat"
call "%~dp0_comum.bat" git || exit /b 1
where gh >nul 2>nul || (echo ERRO: GitHub CLI nao instalado. & exit /b 1)
gh auth status || (echo ERRO: execute gh auth login. & exit /b 1)
for /f "delims=" %%B in ('git -C "%RADAR_ROOT%" branch --show-current') do set "BRANCH=%%B"
if not "!BRANCH!"=="main" (echo ERRO: a Release final so pode sair da main. & exit /b 1)
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
echo !VERSION!| findstr /c:"-dev" >nul && (echo ERRO: versao de desenvolvimento nao pode virar Release. & exit /b 1)
git -C "%RADAR_ROOT%" rev-parse "v!VERSION!" >nul 2>nul && (echo ERRO: tag v!VERSION! ja existe. & exit /b 2)
call "%~dp002_RODAR_TESTES.bat" || exit /b 1
call "%~dp003_GERAR_EXE.bat" || exit /b 1
call "%~dp004_GERAR_INSTALADOR.bat" || exit /b 1
for /f "tokens=*" %%H in ('certutil -hashfile "%INSTALLER_FILE%" SHA256 ^| findstr /r /v "hash CertUtil"') do set "HASH=%%H"
set "HASH=!HASH: =!"
>"%PROJECT_DIR%\installer_output\SHA256SUMS.txt" echo !HASH!  Instalar Radar de Lotes.exe
git -C "%RADAR_ROOT%" tag -a "v!VERSION!" -m "Radar de Lotes v!VERSION!" || exit /b 1
git -C "%RADAR_ROOT%" push origin "v!VERSION!" || exit /b 1
gh release create "v!VERSION!" "%INSTALLER_FILE%#Instalar Radar de Lotes.exe" "%PROJECT_DIR%\installer_output\SHA256SUMS.txt" --repo "%REPO_NAME%" --title "Radar de Lotes v!VERSION!" --notes-file "%PROJECT_DIR%\RELEASE_NOTES.md" --latest || exit /b 1
echo Release v!VERSION! publicada com instalador e SHA-256.
exit /b 0

