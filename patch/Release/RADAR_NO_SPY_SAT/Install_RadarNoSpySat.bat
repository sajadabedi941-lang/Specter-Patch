@echo off
setlocal EnableExtensions
title Install radar no Spy Satellite

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

copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy _SPEC_DATA_ONE.big
  pause
  exit /b 1
)

if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
copy /Y "%~dp0CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy CommandSet.ini
  pause
  exit /b 1
)
copy /Y "%~dp0CommandButton.ini" "%GAME_ROOT%Data\INI\CommandButton.ini" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy CommandButton.ini
  pause
  exit /b 1
)

echo Installed:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%Data\INI\CommandSet.ini
echo   %GAME_ROOT%Data\INI\CommandButton.ini
echo.
echo SHA-256 DATA BIG:
echo   64835645cb60fe726b59d8033574823d5de4443aa9dff0f74c1f7978d3d67465
echo SHA-256 CommandSet.ini:
echo   2af068adeb95042efb665dfcd9f65d9898e8333ded25f49687535586dcaece84
echo SHA-256 CommandButton.ini:
echo   5df320b6ce032225be66518eccfaaa0b52498ff01550c008008c8d22085b67dd
echo.
echo Removed Command_SpySatelliteScan from 12 unauthorized live radar menus.
echo NK/SK/JP/VN RadarSearch kept. Iran/Iraq already clean. Do not replace ART.
echo.
pause
endlocal
exit /b 0
