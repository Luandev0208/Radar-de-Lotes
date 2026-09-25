@echo off
setlocal enabledelayedexpansion
call "%~dp0config.bat"
call "%~dp0_comum.bat" git || exit /b 1
git -C "%RADAR_ROOT%" diff --quiet && git -C "%RADAR_ROOT%" diff --cached --quiet || (echo ERRO: ha alteracoes nao commitadas. & exit /b 1)
git -C "%RADAR_ROOT%" fetch origin || exit /b 1
git -C "%RADAR_ROOT%" switch main || exit /b 1
git -C "%RADAR_ROOT%" pull --ff-only origin main || exit /b 1
set /p "NEW_VERSION=Nova versao, por exemplo 1.5.0: "
echo !NEW_VERSION!| findstr /r "^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*$" >nul || (echo ERRO: use o formato X.Y.Z. & exit /b 1)
git -C "%RADAR_ROOT%" show-ref --verify --quiet "refs/heads/dev-v!NEW_VERSION!" && (echo ERRO: a branch ja existe. & exit /b 1)
git -C "%RADAR_ROOT%" switch -c "dev-v!NEW_VERSION!" || exit /b 1
>"%PROJECT_DIR%\VERSION" echo !NEW_VERSION!-dev
git -C "%RADAR_ROOT%" add PROJETO/VERSION
git -C "%RADAR_ROOT%" commit -m "chore: iniciar desenvolvimento v!NEW_VERSION!" || exit /b 1
echo Branch criada: dev-v!NEW_VERSION!
echo Main permanece aprovada. Faca as alteracoes somente nesta branch.
exit /b 0

