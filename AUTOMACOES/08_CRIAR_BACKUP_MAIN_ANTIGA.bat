@echo off
setlocal
call "%~dp0config.bat"
call "%~dp0_comum.bat" git || exit /b 1
git -C "%RADAR_ROOT%" fetch origin || exit /b 1
for /f "delims=" %%V in ('git -C "%RADAR_ROOT%" show origin/main:PROJETO/VERSION') do set "OLD_VERSION=%%V"
set "OLD_VERSION=%OLD_VERSION:-dev=%"
set "BACKUP=backup-v%OLD_VERSION%"
git -C "%RADAR_ROOT%" show-ref --verify --quiet "refs/remotes/origin/%BACKUP%" && (echo ERRO: %BACKUP% ja existe; nada foi sobrescrito. & exit /b 2)
git -C "%RADAR_ROOT%" branch "%BACKUP%" origin/main || exit /b 1
git -C "%RADAR_ROOT%" push -u origin "%BACKUP%" || exit /b 1
echo Backup criado e enviado: %BACKUP%
exit /b 0

