@echo off
setlocal enabledelayedexpansion
call "%~dp0config.bat"
call "%~dp0_comum.bat" git || exit /b 1
where gh >nul 2>nul || (echo ERRO: GitHub CLI nao instalado. & exit /b 1)
gh auth status || (echo ERRO: execute gh auth login. & exit /b 1)
for /f "delims=" %%B in ('git -C "%RADAR_ROOT%" branch --show-current') do set "BRANCH=%%B"
if not "!BRANCH!"=="main" (echo ERRO: acompanhe a Release somente depois que a main for atualizada. & exit /b 1)
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
echo !VERSION!| findstr /c:"-dev" >nul && (echo ERRO: versao de desenvolvimento nao pode virar Release. & exit /b 1)
for /f "delims=" %%S in ('git -C "%RADAR_ROOT%" rev-parse HEAD') do set "MAIN_SHA=%%S"
echo Aguardando o GitHub Actions assumir a publicacao oficial de v!VERSION!...
set "RUN_ID="
for /l %%I in (1,1,24) do (
  for /f "delims=" %%R in ('gh run list --repo "%REPO_NAME%" --workflow release.yml --branch main --limit 5 --json databaseId^,headSha --jq ".[] ^| select(.headSha==\"!MAIN_SHA!\") ^| .databaseId" 2^>nul') do if not defined RUN_ID set "RUN_ID=%%R"
  if defined RUN_ID goto :acompanhar
  timeout /t 5 /nobreak >nul
)
echo ERRO: o workflow da main nao apareceu no prazo esperado.
exit /b 1

:acompanhar
echo Workflow encontrado: !RUN_ID!
gh run watch !RUN_ID! --repo "%REPO_NAME%" --exit-status || (echo ERRO: GitHub Actions falhou; nenhuma segunda Release foi criada localmente. & exit /b 1)
gh release view "v!VERSION!" --repo "%REPO_NAME%" --json url^,tagName^,assets --jq ".tagName + \" pronta: \" + .url" || exit /b 1
for /f "delims=" %%U in ('gh release view "v!VERSION!" --repo "%REPO_NAME%" --json url --jq ".url"') do set "RELEASE_URL=%%U"
if defined RELEASE_URL start "" "!RELEASE_URL!"
echo Release v!VERSION! foi publicada exclusivamente pelo GitHub Actions.
exit /b 0
