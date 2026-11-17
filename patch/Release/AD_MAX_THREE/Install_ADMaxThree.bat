@echo off
setlocal EnableExtensions
title Install SPECTER Air Defence max-3 cap

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
echo   8728a24c3856850ff4d958b0b4d15dd443da13f299306fd16e57ea10f6432628
echo SHA-256 CommandSet.ini:
echo   405e587998a3eaf6deb8e3495c30dd267a3c888e43f6ce9f6a95cf8ad62ad858
echo SHA-256 CommandButton.ini:
echo   5df320b6ce032225be66518eccfaaa0b52498ff01550c008008c8d22085b67dd
echo.
echo Air Defence cap: MaxSimultaneousOfType = 3 per type per player.
echo Patch_AirDefense shared pool removed. Do not replace ART.
echo.
pause
endlocal
exit /b 0
