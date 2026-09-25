@echo off
setlocal
call "%~dp0config.bat"
:menu
cls
set "VERSION=desconhecida"
if exist "%PROJECT_DIR%\VERSION" set /p VERSION=<"%PROJECT_DIR%\VERSION"
set "BRANCH=sem Git"
for /f "delims=" %%B in ('git -C "%RADAR_ROOT%" branch --show-current 2^>nul') do set "BRANCH=%%B"
set "GITSTATE=indisponivel"
git -C "%RADAR_ROOT%" diff --quiet >nul 2>nul && git -C "%RADAR_ROOT%" diff --cached --quiet >nul 2>nul && set "GITSTATE=limpo"
echo =================================
echo RADAR DE LOTES - FERRAMENTAS
echo =================================
echo Versao atual: %VERSION%
echo Branch atual: %BRANCH%
echo Status Git: %GITSTATE%
echo.
echo 1 - Executar Radar
echo 2 - Rodar testes
echo 3 - Gerar EXE
echo 4 - Gerar instalador
echo 5 - Preparar versao completa para teste
echo 6 - Criar nova branch de desenvolvimento
echo 7 - Ver status do Git/GitHub
echo 8 - Criar backup da versao antiga
echo 9 - Publicar versao aprovada
echo 10 - Acompanhar GitHub Actions e abrir Release
echo 11 - Abrir pasta ENTREGA_PARA_TESTE
echo 12 - Abrir logs
echo 13 - Ver tutorial rapido
echo 14 - Verificar ambiente
echo 15 - Fluxo completo apos aprovacao
echo 0 - Sair
echo.
set /p "OP=Escolha: "
if "%OP%"=="0" exit /b 0
if "%OP%"=="1" call "%~dp001_EXECUTAR_RADAR.bat"
if "%OP%"=="2" call "%~dp002_RODAR_TESTES.bat"
if "%OP%"=="3" call "%~dp003_GERAR_EXE.bat"
if "%OP%"=="4" call "%~dp004_GERAR_INSTALADOR.bat"
if "%OP%"=="5" call "%~dp005_PREPARAR_TESTE_COMPLETO.bat"
if "%OP%"=="6" call "%~dp006_CRIAR_BRANCH_NOVA_VERSAO.bat"
if "%OP%"=="7" call "%~dp007_VER_STATUS_GIT.bat"
if "%OP%"=="8" call "%~dp008_CRIAR_BACKUP_MAIN_ANTIGA.bat"
if "%OP%"=="9" call "%~dp009_PUBLICAR_VERSAO_APROVADA.bat"
if "%OP%"=="10" call "%~dp010_PUBLICAR_RELEASE.bat"
if "%OP%"=="11" call "%~dp011_ABRIR_ENTREGA.bat"
if "%OP%"=="12" call "%~dp012_ABRIR_LOGS.bat"
if "%OP%"=="13" start "" notepad "%~dp0README_AUTOMACOES.txt"
if "%OP%"=="14" call "%~dp014_VERIFICAR_AMBIENTE.bat"
if "%OP%"=="15" call "%~dp0TUDO_EM_UM_APOS_APROVACAO.bat"
echo.
pause
goto menu
