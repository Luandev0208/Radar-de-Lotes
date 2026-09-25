@echo off
setlocal EnableExtensions
for %%I in ("%~dp0..") do set "RADAR_ROOT=%%~fI"
set "TARGET=%RADAR_ROOT%\AUTOMACOES"
if not exist "%TARGET%" mkdir "%TARGET%"
copy /y "%~dp0RADAR_LOCAL_TEMPLATE.bat" "%TARGET%\RADAR.bat" >nul
if errorlevel 1 (
  echo ERRO: nao foi possivel criar AUTOMACOES\RADAR.bat
  pause
  exit /b 1
)
echo Ferramenta local instalada em:
echo %TARGET%\RADAR.bat
echo.
echo Essa pasta e ignorada pelo Git e nao sera trocada ao mudar de branch.
start "" "%TARGET%\RADAR.bat"
exit /b 0
