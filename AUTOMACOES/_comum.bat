@echo off
if not defined PROJECT_DIR call "%~dp0config.bat"

if /i "%~1"=="python" goto :python
if /i "%~1"=="venv" goto :venv
if /i "%~1"=="inno" goto :inno
if /i "%~1"=="git" goto :git
exit /b 2

:python
where py >nul 2>nul || (echo ERRO: Python Launcher nao encontrado. Instale Python 3.12 64-bit. & exit /b 1)
py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,12) else 1)" >nul 2>nul || (echo ERRO: Python 3.12 64-bit nao encontrado. & exit /b 1)
exit /b 0

:venv
call "%~f0" python || exit /b 1
if not exist "%PROJECT_DIR%\.venv\Scripts\python.exe" py -3.12 -m venv "%PROJECT_DIR%\.venv" || exit /b 1
"%PROJECT_DIR%\.venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r "%PROJECT_DIR%\requirements-dev.txt" || exit /b 1
exit /b 0

:inno
if defined ISCC_PATH if exist "%ISCC_PATH%" exit /b 0
set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ISCC_PATH%" exit /b 0
set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%ISCC_PATH%" exit /b 0
where ISCC.exe >nul 2>nul && (set "ISCC_PATH=ISCC.exe" & exit /b 0)
echo ERRO: Inno Setup 6 nao encontrado. Instale-o e tente novamente.
exit /b 1

:git
where git >nul 2>nul || (echo ERRO: Git nao instalado. & exit /b 1)
git -C "%RADAR_ROOT%" rev-parse --is-inside-work-tree >nul 2>nul || (echo ERRO: esta pasta nao e o repositorio do Radar. & exit /b 1)
exit /b 0

