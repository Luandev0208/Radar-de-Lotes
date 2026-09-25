@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Radar de Lotes - Ferramentas locais

for %%I in ("%~dp0..") do set "RADAR_ROOT=%%~fI"
set "PROJECT_DIR=%RADAR_ROOT%\PROJETO"
set "DELIVERY_DIR=%RADAR_ROOT%\ENTREGA_PARA_TESTE"
set "LOG_DIR=%~dp0logs"
set "EXE_FILE=%PROJECT_DIR%\dist\Radar de Lotes.exe"
set "INSTALLER_FILE=%PROJECT_DIR%\installer_output\Instalar Radar de Lotes.exe"
set "COMPAT_FILE=%PROJECT_DIR%\installer_output\Radar-de-Lotes-Instalador-Compatibilidade.zip"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>nul
if not exist "%PROJECT_DIR%\VERSION" goto erro_version

:menu
call :detectar
cls
echo ========================================
echo RADAR DE LOTES - FERRAMENTAS LOCAIS
echo ========================================
echo Versao detectada: !VERSION!
echo Branch atual: !BRANCH!
echo Git: !GIT_STATUS!
echo GitHub: !GH_STATUS!
echo.
echo 1 - Executar Radar
echo 2 - Rodar testes
echo 3 - Gerar EXE
echo 4 - Gerar instaladores
echo 5 - Preparar versao para teste
echo 6 - Criar nova versao / branch
echo 7 - Ver status Git/GitHub
echo 8 - Criar backup da versao antiga
echo 9 - Publicar versao aprovada
echo 10 - Acompanhar/verificar Release
echo 11 - Abrir pasta de entrega
echo 12 - Abrir logs
echo 13 - Informacoes / Ajuda
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
where git >nul 2>nul
if errorlevel 1 goto detectar_gh
for /f "delims=" %%B in ('git -C "%RADAR_ROOT%" branch --show-current 2^>nul') do set "BRANCH=%%B"
for /f %%C in ('git -C "%RADAR_ROOT%" status --porcelain 2^>nul ^| find /c /v ""') do set "CHANGED=%%C"
set "GIT_STATUS=com alteracoes"
if "!CHANGED!"=="0" set "GIT_STATUS=limpo"
:detectar_gh
where gh >nul 2>nul
if errorlevel 1 exit /b 0
gh auth status >nul 2>nul
if not errorlevel 1 set "GH_STATUS=conectado"
exit /b 0

:log
>>"%LOG_DIR%\RADAR.log" echo [%date% %time%] %*
exit /b 0

:python
where py >nul 2>nul
if errorlevel 1 goto erro_python
py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,12) else 1)" >nul 2>nul
if errorlevel 1 goto erro_python
exit /b 0

:venv
call :python
if errorlevel 1 exit /b 1
if not exist "%PROJECT_DIR%\.venv\Scripts\python.exe" py -3.12 -m venv "%PROJECT_DIR%\.venv"
if errorlevel 1 exit /b 1
"%PROJECT_DIR%\.venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "%PROJECT_DIR%\requirements-dev.txt"
if errorlevel 1 exit /b 1
exit /b 0

:git
where git >nul 2>nul
if errorlevel 1 goto erro_git
git -C "%RADAR_ROOT%" rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 goto erro_repo
exit /b 0

:github
call :git
if errorlevel 1 exit /b 1
where gh >nul 2>nul
if errorlevel 1 goto erro_gh
gh auth status >nul 2>nul
if errorlevel 1 goto erro_gh_auth
for /f "delims=" %%U in ('git -C "%RADAR_ROOT%" remote get-url origin 2^>nul') do set "ORIGIN_URL=%%U"
if not defined ORIGIN_URL goto erro_origin
set "REPO_NAME=!ORIGIN_URL:https://github.com/=!"
set "REPO_NAME=!REPO_NAME:git@github.com:=!"
set "REPO_NAME=!REPO_NAME:.git=!"
set "REPO_NAME=!REPO_NAME:\=/!"
exit /b 0

:inno
set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "!ISCC_PATH!" exit /b 0
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
if "!CHANGED!"=="0" exit /b 0
echo ERRO: Git possui !CHANGED! arquivos alterados. Faca commit antes de continuar.
exit /b 1

:executar
call :venv
if errorlevel 1 exit /b 1
call :log Executar Radar em desenvolvimento
cd /d "%PROJECT_DIR%"
".venv\Scripts\python.exe" main.py
exit /b !errorlevel!

:testes
call :venv
if errorlevel 1 exit /b 1
call :log Inicio dos testes
set "PYTEST_TMP=%LOCALAPPDATA%\RadarDeLotesDev\pytest-!RANDOM!-!RANDOM!"
if not exist "%LOCALAPPDATA%\RadarDeLotesDev" mkdir "%LOCALAPPDATA%\RadarDeLotesDev" >nul 2>nul
cd /d "%PROJECT_DIR%"
".venv\Scripts\python.exe" -m pytest -q --basetemp "!PYTEST_TMP!"
set "TEST_RC=!ERRORLEVEL!"
rmdir /s /q "!PYTEST_TMP!" >nul 2>nul
if not "!TEST_RC!"=="0" goto erro_testes
call :log Testes aprovados
echo OK: todos os testes foram aprovados.
exit /b 0

:gerar_exe
call :venv
if errorlevel 1 exit /b 1
call :log Inicio da geracao do EXE
cd /d "%PROJECT_DIR%"
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name "Radar de Lotes" --add-data "VERSION;." --collect-all winotify --collect-submodules bs4 --collect-submodules requests main.py
if errorlevel 1 exit /b 1
if not exist "%EXE_FILE%" goto erro_exe
"%EXE_FILE%" --self-test
if errorlevel 1 goto erro_selftest
call :log EXE e autoteste concluidos
echo OK: "%EXE_FILE%"
exit /b 0

:gerar_instalador
if not exist "%EXE_FILE%" goto erro_sem_exe
call :inno
if errorlevel 1 exit /b 1
cd /d "%PROJECT_DIR%"
set /p "VERSION="<"VERSION"
>build_version.iss echo #define AppVersion "!VERSION!"
if exist installer_output rmdir /s /q installer_output
if exist installer_compatible_output rmdir /s /q installer_compatible_output
"!ISCC_PATH!" installer.iss
if errorlevel 1 exit /b 1
"!ISCC_PATH!" installer_compatible.iss
if errorlevel 1 exit /b 1
powershell -NoProfile -ExecutionPolicy Bypass -Command "$files=Get-ChildItem -LiteralPath 'installer_compatible_output' -File|%% FullName; Compress-Archive -LiteralPath $files -DestinationPath 'installer_output\Radar-de-Lotes-Instalador-Compatibilidade.zip' -Force"
if errorlevel 1 exit /b 1
if not exist "%INSTALLER_FILE%" goto erro_instalador
if not exist "%COMPAT_FILE%" goto erro_compat
call :log Instaladores !VERSION! concluidos
echo OK: instalador normal e pacote de compatibilidade criados.
exit /b 0

:preparar_teste
call :testes
if errorlevel 1 exit /b 1
call :gerar_exe
if errorlevel 1 exit /b 1
call :gerar_instalador
if errorlevel 1 exit /b 1
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
if exist "%DELIVERY_DIR%" rmdir /s /q "%DELIVERY_DIR%"
mkdir "%DELIVERY_DIR%"
copy /y "%INSTALLER_FILE%" "%DELIVERY_DIR%\Instalar Radar de Lotes !VERSION!.exe" >nul
copy /y "%COMPAT_FILE%" "%DELIVERY_DIR%\Radar-de-Lotes-Instalador-Compatibilidade-!VERSION!.zip" >nul
copy /y "%PROJECT_DIR%\VERSION" "%DELIVERY_DIR%\VERSION.txt" >nul
>"%DELIVERY_DIR%\LEIA-ME-TESTE.txt" echo Build de teste v!VERSION!. Main, tag e Release nao foram alterados.
call :log Pacote de teste !VERSION! preparado
start "" explorer "%DELIVERY_DIR%"
exit /b 0

:nova_versao
call :github
if errorlevel 1 exit /b 1
call :git_limpo
if errorlevel 1 exit /b 1
git -C "%RADAR_ROOT%" fetch origin
if errorlevel 1 exit /b 1
git -C "%RADAR_ROOT%" switch main
if errorlevel 1 exit /b 1
git -C "%RADAR_ROOT%" pull --ff-only origin main
if errorlevel 1 exit /b 1
set "NEW_VERSION="
set /p "NEW_VERSION=Nova versao no formato X.Y.Z: "
echo !NEW_VERSION!| findstr /r "^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*$" >nul
if errorlevel 1 goto erro_formato
git -C "%RADAR_ROOT%" switch -c "dev-v!NEW_VERSION!"
if errorlevel 1 exit /b 1
>"%PROJECT_DIR%\VERSION" echo !NEW_VERSION!
git -C "%RADAR_ROOT%" add PROJETO/VERSION
git -C "%RADAR_ROOT%" commit -m "chore: iniciar desenvolvimento v!NEW_VERSION!"
if errorlevel 1 exit /b 1
echo Branch dev-v!NEW_VERSION! criada. Main continua inalterada.
exit /b 0

:status
call :github
if errorlevel 1 exit /b 1
git -C "%RADAR_ROOT%" fetch origin --quiet
call :detectar
for /f "delims=" %%C in ('git -C "%RADAR_ROOT%" log -1 --oneline') do set "LAST=%%C"
echo Branch: !BRANCH!
echo Versao: !VERSION!
echo Git: !GIT_STATUS!
echo Ultimo commit: !LAST!
echo Origin: !ORIGIN_URL!
exit /b 0

:backup_main
call :github
if errorlevel 1 exit /b 1
git -C "%RADAR_ROOT%" fetch origin
if errorlevel 1 exit /b 1
for /f "delims=" %%V in ('git -C "%RADAR_ROOT%" show origin/main:PROJETO/VERSION') do set "OLD_VERSION=%%V"
for /f "delims=" %%S in ('git -C "%RADAR_ROOT%" rev-parse origin/main') do set "OLD_SHA=%%S"
set "BACKUP=backup-v!OLD_VERSION!"
set "BACKUP_SHA="
for /f "tokens=1" %%S in ('git -C "%RADAR_ROOT%" ls-remote --heads origin "refs/heads/!BACKUP!"') do set "BACKUP_SHA=%%S"
if not defined BACKUP_SHA goto criar_backup
if /i "!BACKUP_SHA!"=="!OLD_SHA!" echo Backup !BACKUP! ja existe e esta correto.
if /i "!BACKUP_SHA!"=="!OLD_SHA!" exit /b 0
echo ERRO: !BACKUP! existe mas aponta para outro commit. Nada foi sobrescrito.
exit /b 1
:criar_backup
git -C "%RADAR_ROOT%" push origin "!OLD_SHA!:refs/heads/!BACKUP!"
if errorlevel 1 exit /b 1
call :log Backup !BACKUP! criado em !OLD_SHA!
echo Backup confirmado: !BACKUP!
exit /b 0

:publicar_main
call :github
if errorlevel 1 exit /b 1
call :detectar
echo !BRANCH!| findstr /r /b "dev-v[0-9]" >nul
if errorlevel 1 goto erro_branch_dev
set "DEV_BRANCH=!BRANCH!"
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
if /i not "!DEV_BRANCH!"=="dev-v!VERSION!" goto erro_branch_version
if defined RADAR_CONFIRMADO goto publicar_core
set "CONFIRM="
set /p "CONFIRM=Digite exatamente PUBLICAR: "
if not "!CONFIRM!"=="PUBLICAR" goto publicacao_cancelada
call :testes
if errorlevel 1 exit /b 1
call :gerar_exe
if errorlevel 1 exit /b 1
call :gerar_instalador
if errorlevel 1 exit /b 1
call :backup_main
if errorlevel 1 exit /b 1
:publicar_core
call :git_limpo
if errorlevel 1 exit /b 1
git -C "%RADAR_ROOT%" push -u origin "!DEV_BRANCH!"
if errorlevel 1 exit /b 1
git -C "%RADAR_ROOT%" fetch origin
if errorlevel 1 exit /b 1
git -C "%RADAR_ROOT%" merge-base --is-ancestor origin/main "origin/!DEV_BRANCH!"
if errorlevel 1 goto erro_divergiu
git -C "%RADAR_ROOT%" switch main
if errorlevel 1 exit /b 1
git -C "%RADAR_ROOT%" pull --ff-only origin main
if errorlevel 1 exit /b 1
git -C "%RADAR_ROOT%" merge --ff-only "origin/!DEV_BRANCH!"
if errorlevel 1 exit /b 1
git -C "%RADAR_ROOT%" push origin main
if errorlevel 1 exit /b 1
call :log Main atualizada para !VERSION!
echo Main atualizada. GitHub Actions assumira tag e Release.
exit /b 0

:acompanhar_release
call :github
if errorlevel 1 exit /b 1
call :detectar
if /i not "!BRANCH!"=="main" goto erro_release_main
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
for /f "delims=" %%S in ('git -C "%RADAR_ROOT%" rev-parse HEAD') do set "MAIN_SHA=%%S"
set "RUN_ID="
echo Procurando workflow da main para v!VERSION!...
for /l %%I in (1,1,60) do (
  for /f "delims=" %%R in ('gh run list --repo "!REPO_NAME!" --workflow release.yml --branch main --limit 10 --json databaseId^,headSha --jq ".[] ^| select(.headSha==\"!MAIN_SHA!\") ^| .databaseId" 2^>nul') do if not defined RUN_ID set "RUN_ID=%%R"
  if defined RUN_ID goto workflow_encontrado
  timeout /t 5 /nobreak >nul
)
echo ERRO: workflow nao encontrado no prazo esperado.
exit /b 1

:workflow_encontrado
gh run watch !RUN_ID! --repo "!REPO_NAME!" --exit-status
if errorlevel 1 goto erro_actions
gh release view "v!VERSION!" --repo "!REPO_NAME!" --json assets --jq ".assets[].name" | findstr /i "SHA256SUMS.txt" >nul
if errorlevel 1 goto erro_assets
gh release view "v!VERSION!" --repo "!REPO_NAME!" --json assets --jq ".assets[].name" | findstr /i "Radar-de-Lotes-Instalador-Compatibilidade.zip" >nul
if errorlevel 1 goto erro_assets
echo Release v!VERSION! confirmada com instalador e SHA-256.
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
echo === VERIFICACAO DO AMBIENTE ===
call :python
if errorlevel 1 exit /b 1
call :git
if errorlevel 1 exit /b 1
call :github
if errorlevel 1 exit /b 1
call :inno
if errorlevel 1 exit /b 1
echo OK - Python 3.12, Git, GitHub CLI e Inno Setup encontrados.
echo O computador do usuario final nao precisa dessas ferramentas.
exit /b 0

:ajuda
cls
echo ================= INFORMACOES =================
echo Este RADAR.bat e local e ignorado pelo Git.
echo Trocar de branch nao substitui este arquivo.
echo 1 a 5 servem para executar, testar e gerar builds sem publicar.
echo 6 cria uma nova branch dev-vX.Y.Z.
echo 8 cria backup idempotente da main remota.
echo 9 publica uma branch aprovada com uma confirmacao PUBLICAR.
echo 10 acompanha o GitHub Actions e valida a Release.
echo 15 faz ambiente, testes, EXE, instaladores, backup, main e Release.
echo A opcao 15 pede PUBLICAR apenas uma vez e nao repete testes/builds.
exit /b 0

:tudo
call :detectar
call :github
if errorlevel 1 exit /b 1
echo !BRANCH!| findstr /r /b "dev-v[0-9]" >nul
if errorlevel 1 goto erro_branch_dev
set "DEV_BRANCH=!BRANCH!"
set /p "VERSION="<"%PROJECT_DIR%\VERSION"
if /i not "!DEV_BRANCH!"=="dev-v!VERSION!" goto erro_branch_version
set "CONFIRM="
set /p "CONFIRM=Voce TESTOU e APROVOU? Digite exatamente PUBLICAR: "
if not "!CONFIRM!"=="PUBLICAR" goto publicacao_cancelada
call :ambiente
if errorlevel 1 exit /b 1
call :git_limpo
if errorlevel 1 exit /b 1
call :testes
if errorlevel 1 exit /b 1
call :gerar_exe
if errorlevel 1 exit /b 1
call :gerar_instalador
if errorlevel 1 exit /b 1
call :backup_main
if errorlevel 1 exit /b 1
set "RADAR_CONFIRMADO=1"
call :publicar_main
if errorlevel 1 exit /b 1
call :acompanhar_release
if errorlevel 1 exit /b 1
echo ========================================
echo PUBLICACAO CONCLUIDA COM SEGURANCA
echo ========================================
exit /b 0

:erro_version
echo ERRO: PROJETO\VERSION nao foi encontrado ao lado da pasta AUTOMACOES.
pause
exit /b 1
:erro_python
echo ERRO: Python 3.12 64-bit nao encontrado.
exit /b 1
:erro_git
echo ERRO: Git nao instalado.
exit /b 1
:erro_repo
echo ERRO: a pasta pai nao e o repositorio do Radar.
exit /b 1
:erro_gh
echo ERRO: GitHub CLI nao instalado.
exit /b 1
:erro_gh_auth
echo ERRO: execute gh auth login uma unica vez.
exit /b 1
:erro_origin
echo ERRO: origin nao configurado.
exit /b 1
:erro_testes
call :log FALHA nos testes
echo FALHA: existem testes com erro.
exit /b 1
:erro_exe
echo ERRO: o EXE nao foi criado.
exit /b 1
:erro_selftest
echo ERRO: o autoteste do EXE falhou.
exit /b 1
:erro_sem_exe
echo ERRO: gere o EXE primeiro pela opcao 3.
exit /b 1
:erro_instalador
echo ERRO: o instalador normal nao foi criado.
exit /b 1
:erro_compat
echo ERRO: o pacote de compatibilidade nao foi criado.
exit /b 1
:erro_formato
echo ERRO: use o formato X.Y.Z.
exit /b 1
:erro_branch_dev
echo ERRO: publique somente de uma branch dev-vX.Y.Z.
exit /b 1
:erro_branch_version
echo ERRO: branch e VERSION nao correspondem.
exit /b 1
:erro_divergiu
echo ERRO: a branch divergiu da main. Nada foi publicado.
exit /b 1
:erro_release_main
echo ERRO: acompanhe a Release depois que a main for atualizada.
exit /b 1
:erro_actions
echo ERRO: GitHub Actions falhou.
exit /b 1
:erro_assets
echo ERRO: a Release nao contem todos os arquivos esperados.
exit /b 1
:publicacao_cancelada
echo Publicacao cancelada sem alterar a main.
exit /b 2
