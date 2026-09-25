@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Uso: PUBLICAR_ATUALIZACAO.bat 1.4.0
  exit /b 1
)
echo %~1| findstr /r "^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*$" >nul || (echo Versao invalida. Use X.Y.Z & exit /b 1)
git diff --quiet || (echo Existem alteracoes nao commitadas. Revise antes de publicar. & exit /b 1)
>VERSION echo %~1
notepad RELEASE_NOTES.md
call build_windows.bat || exit /b 1
git add VERSION RELEASE_NOTES.md
git commit -m "release: Radar de Lotes v%~1" || exit /b 1
git push origin main || exit /b 1
echo O GitHub Actions esta gerando e publicando a Release v%~1.
