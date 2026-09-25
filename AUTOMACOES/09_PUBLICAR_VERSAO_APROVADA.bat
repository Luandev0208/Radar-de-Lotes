@echo off
setlocal enabledelayedexpansion
call "%~dp0config.bat"
call "%~dp0_comum.bat" git || exit /b 1
for /f "delims=" %%B in ('git -C "%RADAR_ROOT%" branch --show-current') do set "BRANCH=%%B"
echo !BRANCH!| findstr /b /c:"dev-v" >nul || (echo ERRO: publique somente de uma branch dev-vX.Y.Z. & exit /b 1)
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
set "FINAL_VERSION=!VERSION:-dev=!"
echo =================================
echo PUBLICAR VERSAO APROVADA
echo =================================
echo Branch a publicar: !BRANCH!
echo Nova versao: v!FINAL_VERSION!
if not defined RADAR_CONFIRMADO set /p "CONFIRM=Digite exatamente PUBLICAR: "
if defined RADAR_CONFIRMADO set "CONFIRM=PUBLICAR"
if not "!CONFIRM!"=="PUBLICAR" (echo Publicacao cancelada. & exit /b 2)
call "%~dp002_RODAR_TESTES.bat" || exit /b 1
git -C "%RADAR_ROOT%" diff --quiet && git -C "%RADAR_ROOT%" diff --cached --quiet || (echo ERRO: Git nao esta limpo. & exit /b 1)
if not "!VERSION!"=="!FINAL_VERSION!" (
  >"%PROJECT_DIR%\VERSION" echo !FINAL_VERSION!
  git -C "%RADAR_ROOT%" add PROJETO/VERSION
  git -C "%RADAR_ROOT%" commit -m "release: Radar de Lotes v!FINAL_VERSION!" || exit /b 1
)
call "%~dp008_CRIAR_BACKUP_MAIN_ANTIGA.bat" || exit /b 1
git -C "%RADAR_ROOT%" fetch origin || exit /b 1
git -C "%RADAR_ROOT%" switch main || exit /b 1
git -C "%RADAR_ROOT%" pull --ff-only origin main || exit /b 1
git -C "%RADAR_ROOT%" merge --ff-only "!BRANCH!" || (echo ERRO: main divergiu; resolva manualmente. & exit /b 1)
git -C "%RADAR_ROOT%" push origin main || exit /b 1
echo Main atualizada com seguranca. A branch dev foi preservada.
exit /b 0
