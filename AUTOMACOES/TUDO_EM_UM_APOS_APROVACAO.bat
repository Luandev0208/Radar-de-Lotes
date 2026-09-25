@echo off
setlocal
call "%~dp0config.bat"
echo ESTE FLUXO SO PODE SER USADO DEPOIS DO TESTE E DA APROVACAO.
set /p "CONFIRM=Digite exatamente PUBLICAR: "
if not "%CONFIRM%"=="PUBLICAR" (echo Cancelado. & exit /b 2)
call "%~dp014_VERIFICAR_AMBIENTE.bat" || exit /b 1
call "%~dp007_VER_STATUS_GIT.bat" || exit /b 1
call "%~dp002_RODAR_TESTES.bat" || exit /b 1
call "%~dp003_GERAR_EXE.bat" || exit /b 1
call "%~dp004_GERAR_INSTALADOR.bat" || exit /b 1
set "RADAR_CONFIRMADO=1"
call "%~dp009_PUBLICAR_VERSAO_APROVADA.bat" || exit /b 1
call "%~dp010_PUBLICAR_RELEASE.bat" || exit /b 1
echo ======================================
echo PUBLICACAO CONCLUIDA COM SEGURANCA
echo Backup, main, tag, Release e SHA-256: OK
echo ======================================
exit /b 0

