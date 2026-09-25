@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Radar de Lotes - Ferramentas
for %%I in ("%~dp0..") do set "RADAR_ROOT=%%~fI"
set "PROJECT_DIR=%RADAR_ROOT%\PROJETO"
set "DELIVERY_DIR=%RADAR_ROOT%\ENTREGA_PARA_TESTE"
set "LOG_DIR=%~dp0logs"
set "EXE_FILE=%PROJECT_DIR%\dist\Radar de Lotes.exe"
set "INSTALLER_FILE=%PROJECT_DIR%\installer_output\Instalar Radar de Lotes.exe"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>nul
if not exist "%PROJECT_DIR%\VERSION" (echo ERRO: PROJETO\VERSION nao foi encontrado ao lado de AUTOMACOES. & pause & exit /b 1)

:menu
call :detectar
cls
echo ========================================
echo RADAR DE LOTES - FERRAMENTAS
echo ========================================
echo Versao detectada: !VERSION!
echo Branch atual: !BRANCH!
echo Git: !GIT_STATUS!
echo GitHub: !GH_STATUS!
echo.
echo 1 - Executar Radar
echo 2 - Rodar testes
echo 3 - Gerar EXE
echo 4 - Gerar instalador
echo 5 - Preparar versao para teste
echo 6 - Criar nova versao / branch
echo 7 - Ver status Git/GitHub
echo 8 - Criar backup da versao antiga
echo 9 - Publicar versao aprovada
echo 10 - Acompanhar/verificar Release
echo 11 - Abrir pasta de entrega
echo 12 - Abrir logs
echo 13 - Informacoes / O que cada opcao faz
echo 14 - Verificar ambiente
echo 15 - FAZER TUDO DE UMA VEZ
echo 0 - Sair
echo.
set "OP="
set /p "OP=Escolha: "
if "!OP!"=="0" exit /b 0
if "!OP!"=="1" call :executar
if "!OP!"=="2" call :testes
if "!OP!"=="3" call :gerar_exe
if "!OP!"=="4" call :gerar_instalador
if "!OP!"=="5" call :preparar_teste
if "!OP!"=="6" call :nova_versao
if "!OP!"=="7" call :status
if "!OP!"=="8" call :backup_main
if "!OP!"=="9" call :publicar_main
if "!OP!"=="10" call :acompanhar_release
if "!OP!"=="11" call :abrir_entrega
if "!OP!"=="12" call :abrir_logs
if "!OP!"=="13" call :ajuda
if "!OP!"=="14" call :ambiente
if "!OP!"=="15" call :tudo
echo.
pause
goto :menu

:detectar
set "VERSION=desconhecida"
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
set "BRANCH=sem Git"
set "GIT_STATUS=indisponivel"
set "GH_STATUS=indisponivel"
where git >nul 2>nul && (
  for /f "delims=" %%B in ('git -C "%RADAR_ROOT%" branch --show-current 2^>nul') do set "BRANCH=%%B"
  git -C "%RADAR_ROOT%" rev-parse --is-inside-work-tree >nul 2>nul && set "GIT_STATUS=com alteracoes"
  for /f %%C in ('git -C "%RADAR_ROOT%" status --porcelain 2^>nul ^| find /c /v ""') do if "%%C"=="0" set "GIT_STATUS=limpo"
)
where gh >nul 2>nul && (gh auth status >nul 2>nul && set "GH_STATUS=conectado")
exit /b 0

:log
>>"%LOG_DIR%\RADAR.log" echo [%date% %time%] %*
exit /b 0

:python
where py >nul 2>nul || (echo ERRO: Python Launcher nao encontrado. Instale Python 3.12 64-bit. & exit /b 1)
py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,12) else 1)" >nul 2>nul || (echo ERRO: Python 3.12 64-bit nao encontrado. & exit /b 1)
exit /b 0

:venv
call :python || exit /b 1
if not exist "%PROJECT_DIR%\.venv\Scripts\python.exe" py -3.12 -m venv "%PROJECT_DIR%\.venv" || exit /b 1
"%PROJECT_DIR%\.venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "%PROJECT_DIR%\requirements-dev.txt" || exit /b 1
exit /b 0

:git
where git >nul 2>nul || (echo ERRO: Git nao instalado. & exit /b 1)
git -C "%RADAR_ROOT%" rev-parse --is-inside-work-tree >nul 2>nul || (echo ERRO: a pasta pai nao e o repositorio do Radar. & exit /b 1)
exit /b 0

:github
call :git || exit /b 1
where gh >nul 2>nul || (echo ERRO: GitHub CLI nao instalado. & exit /b 1)
gh auth status >nul 2>nul || (echo ERRO: execute gh auth login uma unica vez. & exit /b 1)
set "ORIGIN_URL="
for /f "delims=" %%U in ('git -C "%RADAR_ROOT%" remote get-url origin 2^>nul') do set "ORIGIN_URL=%%U"
if not defined ORIGIN_URL (echo ERRO: origin nao configurado. & exit /b 1)
set "REPO_NAME=!ORIGIN_URL:https://github.com/=!"
set "REPO_NAME=!REPO_NAME:git@github.com:=!"
set "REPO_NAME=!REPO_NAME:.git=!"
set "REPO_NAME=!REPO_NAME:\=/!"
exit /b 0

:inno
set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "!ISCC_PATH!" exit /b 0
set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "!ISCC_PATH!" exit /b 0
set "ISCC_PATH="
for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do if not defined ISCC_PATH set "ISCC_PATH=%%I"
if defined ISCC_PATH exit /b 0
echo ERRO: Inno Setup 6 nao encontrado.
exit /b 1

:git_limpo
for /f %%C in ('git -C "%RADAR_ROOT%" status --porcelain ^| find /c /v ""') do set "CHANGED=%%C"
if not "!CHANGED!"=="0" (echo ERRO: Git possui !CHANGED! arquivo(s) alterado(s). Faça commit antes de continuar. & exit /b 1)
exit /b 0

:executar
call :venv || exit /b 1
call :log Executar Radar em desenvolvimento
cd /d "%PROJECT_DIR%"
".venv\Scripts\python.exe" main.py
exit /b !errorlevel!

:testes
call :venv || exit /b 1
call :log Inicio dos testes
cd /d "%PROJECT_DIR%"
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 (call :log FALHA nos testes & echo FALHA: existem testes com erro. & exit /b 1)
call :log Testes aprovados
echo OK: todos os testes foram aprovados.
exit /b 0

:gerar_exe
call :venv || exit /b 1
call :log Inicio da geracao do EXE
cd /d "%PROJECT_DIR%"
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name "Radar de Lotes" --add-data "VERSION;." --collect-all winotify --collect-submodules bs4 --collect-submodules requests main.py || exit /b 1
if not exist "%EXE_FILE%" (echo ERRO: o EXE nao foi criado. & exit /b 1)
"%EXE_FILE%" --self-test || (echo ERRO: o autoteste do EXE falhou. & exit /b 1)
call :log EXE e autoteste concluidos
echo OK: "%EXE_FILE%"
exit /b 0

:gerar_instalador
if not exist "%EXE_FILE%" (echo ERRO: gere o EXE primeiro pela opcao 3. & exit /b 1)
call :inno || exit /b 1
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
cd /d "%PROJECT_DIR%"
>build_version.iss echo #define AppVersion "!VERSION!"
if exist installer_output rmdir /s /q installer_output
"!ISCC_PATH!" installer.iss || exit /b 1
if not exist "%INSTALLER_FILE%" (echo ERRO: instalador nao criado. & exit /b 1)
call :log Instalador !VERSION! concluido
echo OK: "%INSTALLER_FILE%"
exit /b 0

:preparar_teste
call :testes || exit /b 1
call :gerar_exe || exit /b 1
call :gerar_instalador || exit /b 1
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
if exist "%DELIVERY_DIR%" rmdir /s /q "%DELIVERY_DIR%"
mkdir "%DELIVERY_DIR%" || exit /b 1
copy /y "%INSTALLER_FILE%" "%DELIVERY_DIR%\Instalar Radar de Lotes !VERSION!.exe" >nul || exit /b 1
copy /y "%PROJECT_DIR%\VERSION" "%DELIVERY_DIR%\VERSION.txt" >nul || exit /b 1
>"%DELIVERY_DIR%\LEIA-ME-TESTE.txt" echo Instalador de teste v!VERSION!. Main, tag e Release nao foram alterados.
call :log Pacote de teste !VERSION! preparado sem publicacao
echo BUILD DE TESTE CONCLUIDO. Main, tag e Release nao foram alterados.
start "" explorer "%DELIVERY_DIR%"
exit /b 0

:nova_versao
call :github || exit /b 1
call :git_limpo || exit /b 1
git -C "%RADAR_ROOT%" fetch origin || exit /b 1
git -C "%RADAR_ROOT%" switch main || exit /b 1
git -C "%RADAR_ROOT%" pull --ff-only origin main || exit /b 1
set "NEW_VERSION="
set /p "NEW_VERSION=Nova versao no formato X.Y.Z: "
echo !NEW_VERSION!| findstr /r "^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*$" >nul || (echo ERRO: use o formato X.Y.Z. & exit /b 1)
git -C "%RADAR_ROOT%" show-ref --verify --quiet "refs/heads/dev-v!NEW_VERSION!" && (echo ERRO: a branch local ja existe. & exit /b 1)
git -C "%RADAR_ROOT%" ls-remote --exit-code --heads origin "refs/heads/dev-v!NEW_VERSION!" >nul 2>nul && (echo ERRO: a branch remota ja existe. & exit /b 1)
git -C "%RADAR_ROOT%" switch -c "dev-v!NEW_VERSION!" || exit /b 1
>"%PROJECT_DIR%\VERSION" echo !NEW_VERSION!
git -C "%RADAR_ROOT%" add PROJETO/VERSION
git -C "%RADAR_ROOT%" commit -m "chore: iniciar desenvolvimento v!NEW_VERSION!" || exit /b 1
echo Branch dev-v!NEW_VERSION! criada. Main continua inalterada.
exit /b 0

:status
call :github || exit /b 1
git -C "%RADAR_ROOT%" fetch origin --quiet || exit /b 1
call :detectar
for /f "delims=" %%C in ('git -C "%RADAR_ROOT%" log -1 --oneline') do set "LAST=%%C"
for /f %%C in ('git -C "%RADAR_ROOT%" status --porcelain ^| find /c /v ""') do set "CHANGED=%%C"
echo Branch: !BRANCH!
echo Versao: !VERSION!
echo Arquivos alterados: !CHANGED!
echo Ultimo commit: !LAST!
echo Origin: !ORIGIN_URL!
gh auth status
exit /b 0

:backup_main
call :github || exit /b 1
git -C "%RADAR_ROOT%" fetch origin || exit /b 1
for /f "delims=" %%V in ('git -C "%RADAR_ROOT%" show origin/main:PROJETO/VERSION') do set "OLD_VERSION=%%V"
for /f "delims=" %%S in ('git -C "%RADAR_ROOT%" rev-parse origin/main') do set "OLD_SHA=%%S"
set "BACKUP=backup-v!OLD_VERSION!"
set "BACKUP_SHA="
for /f "tokens=1" %%S in ('git -C "%RADAR_ROOT%" ls-remote --heads origin "refs/heads/!BACKUP!"') do set "BACKUP_SHA=%%S"
if defined BACKUP_SHA (
  if /i "!BACKUP_SHA!"=="!OLD_SHA!" (echo Backup !BACKUP! ja existe e esta correto. & exit /b 0)
  echo ERRO: !BACKUP! existe, mas nao aponta para a main atual. Nada foi sobrescrito.
  exit /b 1
)
git -C "%RADAR_ROOT%" push origin "!OLD_SHA!:refs/heads/!BACKUP!" || exit /b 1
for /f "tokens=1" %%S in ('git -C "%RADAR_ROOT%" ls-remote --heads origin "refs/heads/!BACKUP!"') do set "BACKUP_SHA=%%S"
if /i not "!BACKUP_SHA!"=="!OLD_SHA!" (echo ERRO: nao foi possivel confirmar o backup remoto. & exit /b 1)
call :log Backup !BACKUP! criado em !OLD_SHA!
echo Backup confirmado: !BACKUP!
exit /b 0

:publicar_main
call :github || exit /b 1
call :detectar
echo !BRANCH!| findstr /r /b "dev-v[0-9]" >nul || (echo ERRO: publique somente de uma branch dev-vX.Y.Z. & exit /b 1)
set "DEV_BRANCH=!BRANCH!"
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
if /i not "!DEV_BRANCH!"=="dev-v!VERSION!" (echo ERRO: branch !DEV_BRANCH! nao corresponde a VERSION !VERSION!. & exit /b 1)
if not defined RADAR_CONFIRMADO (
  echo Branch aprovada: !DEV_BRANCH!
  echo Nova versao: !VERSION!
  set "CONFIRM="
  set /p "CONFIRM=Digite exatamente PUBLICAR: "
  if not "!CONFIRM!"=="PUBLICAR" (echo Publicacao cancelada. & exit /b 2)
)
call :git_limpo || exit /b 1
git -C "%RADAR_ROOT%" fetch origin || exit /b 1
git -C "%RADAR_ROOT%" merge-base --is-ancestor origin/main "!DEV_BRANCH!" || (echo ERRO: a branch divergiu da main. Resolva manualmente. & exit /b 1)
call :testes || exit /b 1
call :backup_main || exit /b 1
git -C "%RADAR_ROOT%" switch main || exit /b 1
git -C "%RADAR_ROOT%" pull --ff-only origin main || exit /b 1
git -C "%RADAR_ROOT%" merge --ff-only "!DEV_BRANCH!" || (echo ERRO: main nao pode avançar por fast-forward. & exit /b 1)
git -C "%RADAR_ROOT%" push origin main || exit /b 1
call :log Main atualizada para !VERSION! apos backup confirmado
echo Main atualizada. GitHub Actions assumira tag e Release.
exit /b 0

:acompanhar_release
call :github || exit /b 1
call :detectar
if /i not "!BRANCH!"=="main" (echo ERRO: acompanhe a Release depois que a main for atualizada. & exit /b 1)
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
for /f "delims=" %%S in ('git -C "%RADAR_ROOT%" rev-parse HEAD') do set "MAIN_SHA=%%S"
set "RUN_ID="
echo Procurando workflow da main para v!VERSION!...
for /l %%I in (1,1,36) do (
  for /f "delims=" %%R in ('gh run list --repo "!REPO_NAME!" --workflow release.yml --branch main --limit 10 --json databaseId^,headSha --jq ".[] ^| select(.headSha==\"!MAIN_SHA!\") ^| .databaseId" 2^>nul') do if not defined RUN_ID set "RUN_ID=%%R"
  if defined RUN_ID goto :workflow_encontrado
  timeout /t 5 /nobreak >nul
)
echo ERRO: workflow nao encontrado no prazo esperado.
exit /b 1

:workflow_encontrado
echo Workflow !RUN_ID! encontrado.
gh run watch !RUN_ID! --repo "!REPO_NAME!" --exit-status || (echo ERRO: GitHub Actions falhou. & exit /b 1)
gh release view "v!VERSION!" --repo "!REPO_NAME!" --json tagName --jq ".tagName" | findstr /x "v!VERSION!" >nul || (echo ERRO: tag/Release nao confirmada. & exit /b 1)
gh release view "v!VERSION!" --repo "!REPO_NAME!" --json assets --jq ".assets[].name" | findstr /i /r "Instalar.*Radar.*Lotes.*exe" >nul || (echo ERRO: instalador ausente na Release. & exit /b 1)
gh release view "v!VERSION!" --repo "!REPO_NAME!" --json assets --jq ".assets[].name" | findstr /x "SHA256SUMS.txt" >nul || (echo ERRO: SHA256SUMS.txt ausente. & exit /b 1)
for /f "delims=" %%U in ('gh release view "v!VERSION!" --repo "!REPO_NAME!" --json url --jq ".url"') do set "RELEASE_URL=%%U"
call :log Release v!VERSION! confirmada pelo GitHub Actions
echo Release v!VERSION!, instalador e SHA-256 confirmados.
if defined RELEASE_URL start "" "!RELEASE_URL!"
exit /b 0

:abrir_entrega
if not exist "%DELIVERY_DIR%" mkdir "%DELIVERY_DIR%"
start "" explorer "%DELIVERY_DIR%"
exit /b 0

:abrir_logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
start "" explorer "%LOG_DIR%"
exit /b 0

:ambiente
echo === VERIFICACAO DO AMBIENTE DE DESENVOLVIMENTO ===
set "ENV_ERROR=0"
call :python && (echo OK - Python 3.12) || (echo FALTA - Python 3.12 & set "ENV_ERROR=1")
where git >nul 2>nul && (git --version) || (echo FALTA - Git & set "ENV_ERROR=1")
where gh >nul 2>nul && (gh --version & gh auth status) || (echo FALTA - GitHub CLI/autenticacao & set "ENV_ERROR=1")
call :inno && (echo OK - Inno Setup: !ISCC_PATH!) || (echo FALTA - Inno Setup 6 & set "ENV_ERROR=1")
if exist "%PROJECT_DIR%\VERSION" (echo OK - PROJETO e VERSION encontrados) else (echo FALTA - PROJETO\VERSION & set "ENV_ERROR=1")
echo O computador do usuario final nao precisa desses programas.
if "!ENV_ERROR!"=="1" (echo ERRO: corrija o ambiente antes de continuar. & exit /b 1)
exit /b 0

:ajuda
cls
echo ================= INFORMACOES =================
echo 1 EXECUTAR - abre em desenvolvimento. Nao altera Git, main ou GitHub.
echo 2 TESTES - prepara .venv e roda pytest. Seguro antes da aprovacao.
echo 3 EXE - gera EXE e roda o autoteste. Nao publica nada.
echo 4 INSTALADOR - usa EXE e Inno Setup. Nao publica nada.
echo 5 PREPARAR TESTE - testa, gera EXE e instalador local. Nao altera main,
echo   nao cria tag e nao publica Release. Use antes de aprovar.
echo 6 NOVA VERSAO - atualiza main local e cria dev-vX.Y.Z. Nao publica main.
echo 7 STATUS - consulta Git/GitHub. Somente leitura.
echo 8 BACKUP - cria backup da main remota no GitHub. Nao altera main.
echo 9 PUBLICAR - exige PUBLICAR, testes, Git limpo e backup; atualiza main
echo   por fast-forward. GitHub Actions cria tag e Release.
echo 10 RELEASE - nao publica; acompanha Actions e confirma assets.
echo 11 ENTREGA - abre a pasta local de teste. 12 LOGS - abre logs locais.
echo 13 AJUDA - mostra esta tela. 14 AMBIENTE - verifica as ferramentas.
echo 15 FAZER TUDO - SOMENTE apos testar e aprovar. Exige PUBLICAR; verifica,
echo   testa, gera, cria backup, atualiza main, acompanha e confirma a Release.
echo.
echo Seguras antes da aprovacao: 1, 2, 3, 4, 5, 7, 11, 12, 13 e 14.
echo Enviam ao GitHub: 8, 9 e 15. Alteram main: 9 e 15.
exit /b 0

:tudo
call :detectar
call :github || exit /b 1
git -C "%RADAR_ROOT%" fetch origin || exit /b 1
for /f "delims=" %%V in ('git -C "%RADAR_ROOT%" show origin/main:PROJETO/VERSION') do set "MAIN_VERSION=%%V"
echo ========================================
echo PUBLICACAO COMPLETA APOS APROVACAO
echo ========================================
echo Versao atual da main: !MAIN_VERSION!
echo Nova versao: !VERSION!
echo Branch atual: !BRANCH!
echo Serao feitos ambiente, testes, EXE, autoteste, instalador, backup,
echo main, push, GitHub Actions e validacao da Release.
set "CONFIRM="
set /p "CONFIRM=Voce TESTOU e APROVOU? Digite exatamente PUBLICAR: "
if not "!CONFIRM!"=="PUBLICAR" (echo Cancelado sem alteracoes. & exit /b 2)
call :ambiente || exit /b 1
call :git_limpo || exit /b 1
echo !BRANCH!| findstr /r /b "dev-v[0-9]" >nul || (echo ERRO: branch atual nao e dev-vX.Y.Z. & exit /b 1)
if /i not "!BRANCH!"=="dev-v!VERSION!" (echo ERRO: branch e VERSION nao correspondem. & exit /b 1)
call :testes || exit /b 1
call :gerar_exe || exit /b 1
call :gerar_instalador || exit /b 1
call :backup_main || exit /b 1
set "RADAR_CONFIRMADO=1"
call :publicar_main || exit /b 1
call :acompanhar_release || exit /b 1
echo ========================================
echo PUBLICACAO CONCLUIDA COM SEGURANCA
echo Backup, main, workflow, tag, Release, instalador e SHA-256: OK
echo ========================================
exit /b 0
