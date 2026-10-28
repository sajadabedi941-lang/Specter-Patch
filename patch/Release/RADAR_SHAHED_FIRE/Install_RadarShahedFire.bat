@echo off
setlocal EnableExtensions
title Install radar Shahed-136 Fire path

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open this folder.
  pause
  exit /b 1
)

if not exist "%~dp0_SPEC_DATA_ONE.big" (
  echo ERROR: _SPEC_DATA_ONE.big is not next to this script.
  pause
  exit /b 1
)
if not exist "%~dp0CommandSet.ini" (
  echo ERROR: CommandSet.ini is not next to this script.
  pause
  exit /b 1
)
if not exist "%~dp0CommandButton.ini" (
  echo ERROR: CommandButton.ini is not next to this script.
  pause
  exit /b 1
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

echo Installed:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%Data\INI\CommandSet.ini
echo   %GAME_ROOT%Data\INI\CommandButton.ini
echo.
echo SHA-256:
echo   DATA  71559b012715a8336cb8b79cefef29cf4e00465825969b500184d95401cc7346
echo   CS    a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87
echo   CB    60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba
echo.
echo Radar Shahed_136 Mobile Launcher now uses the Iran Fire path.
echo Iran original cost 1500 is unchanged. Other-country cost stays 8000.
echo Keep 0_ overlays and original ART. Do not replace ART.
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: Copy failed.
pause
exit /b 1
