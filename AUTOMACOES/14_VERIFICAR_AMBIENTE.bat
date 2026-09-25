@echo off
setlocal enabledelayedexpansion
call "%~dp0config.bat"
echo === VERIFICACAO DO AMBIENTE ===
call "%~dp0_comum.bat" python && echo OK - Python 3.12 || echo FALTA - Python 3.12
where git >nul 2>nul && git --version || echo FALTA - Git
where gh >nul 2>nul && (gh --version & gh auth status) || echo FALTA - GitHub CLI
call "%~dp0_comum.bat" inno && echo OK - Inno Setup: !ISCC_PATH! || echo FALTA - Inno Setup 6
git -C "%RADAR_ROOT%" remote get-url origin 2>nul
echo PC do usuario final: nenhum desses programas e necessario.
exit /b 0
