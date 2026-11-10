@echo off
setlocal EnableExtensions
title Remove Arabic Alliance from country lists

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open this folder.
  pause
  exit /b 1
)

set "NEED=_SPEC_DATA_ONE.big CommandSet.ini CommandButton.ini PlayerTemplate.ini"
for %%F in (%NEED%) do (
  if not exist "%~dp0%%F" (
    echo ERROR: %%F is not next to this script.
    pause
    exit /b 1
  )
)

set "GAME_ROOT="
set "PARENT="
for %%I in ("%~dp0..") do set "PARENT=%%~fI"
if exist "%~dp0generals.exe" set "GAME_ROOT=%~dp0"
if not defined GAME_ROOT if exist "%~dp0Generals.exe" set "GAME_ROOT=%~dp0"
if not defined GAME_ROOT if exist "%PARENT%\generals.exe" set "GAME_ROOT=%PARENT%\"
if not defined GAME_ROOT if exist "%PARENT%\Generals.exe" set "GAME_ROOT=%PARENT%\"
if not defined GAME_ROOT (
  echo ERROR: generals.exe not found.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandButton.ini" "%GAME_ROOT%Data\INI\CommandButton.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0PlayerTemplate.ini" "%GAME_ROOT%Data\INI\PlayerTemplate.ini" >nul
if errorlevel 1 goto :copyfail

echo Installed:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%Data\INI\CommandSet.ini
echo   %GAME_ROOT%Data\INI\CommandButton.ini
echo   %GAME_ROOT%Data\INI\PlayerTemplate.ini
echo.
echo SHA-256:
echo   DATA  751550a6aee5d3bd9ad475b6625744d7b7a4a26e0a9551fd845e313c0f87b6b4
echo   CS    a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87
echo   CB    60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba
echo   PT    7245baec02a5a8c7af9792fa2c1e451282c0c1ddba87506ae5398cdfbaec9a20
echo.
echo Arabic Alliance / FactionGLA is not playable. Iraq/Saudi/UAE/Syria/Libya remain.
echo Keep 0_ overlays and original ART. Do not replace ART.
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: Copy failed.
pause
exit /b 1
