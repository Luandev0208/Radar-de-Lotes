@echo off
setlocal
call "%~dp0config.bat"
call "%~dp0_comum.bat" git || exit /b 1
git -C "%RADAR_ROOT%" fetch origin --quiet
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
for /f "delims=" %%B in ('git -C "%RADAR_ROOT%" branch --show-current') do set "BRANCH=%%B"
for /f "delims=" %%C in ('git -C "%RADAR_ROOT%" log -1 --oneline') do set "LAST=%%C"
for /f %%C in ('git -C "%RADAR_ROOT%" status --porcelain ^| find /c /v ""') do set "CHANGED=%%C"
for /f %%C in ('git -C "%RADAR_ROOT%" rev-list --count origin/%BRANCH%..%BRANCH% 2^>nul') do set "AHEAD=%%C"
for /f %%C in ('git -C "%RADAR_ROOT%" rev-list --count %BRANCH%..origin/%BRANCH% 2^>nul') do set "BEHIND=%%C"
echo Branch atual: %BRANCH%
echo Versao: %VERSION%
echo Arquivos alterados: %CHANGED%
echo Commits locais nao enviados: %AHEAD%
echo Commits remotos nao puxados: %BEHIND%
echo Ultimo commit: %LAST%
git -C "%RADAR_ROOT%" describe --tags --abbrev=0 2>nul
git -C "%RADAR_ROOT%" remote -v
where gh >nul 2>nul && gh auth status || echo GitHub CLI ausente ou nao autenticado.
exit /b 0

