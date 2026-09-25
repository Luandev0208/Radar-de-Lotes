@echo off
setlocal
call "%~dp0config.bat"
call "%~dp0_comum.bat" venv || (pause & exit /b 1)
cd /d "%PROJECT_DIR%"
echo Rodando todos os testes...
".venv\Scripts\python.exe" -m pytest -q
set "RC=%errorlevel%"
if not "%RC%"=="0" (echo FALHA: existem testes com erro. & exit /b %RC%)
echo OK: todos os testes foram aprovados.
exit /b 0

