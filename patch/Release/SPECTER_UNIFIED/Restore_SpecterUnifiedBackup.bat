@echo off
setlocal EnableExtensions
title Restore SPECTER Unified backup

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open this folder.
  pause
  exit /b 1
)

set "GAME_ROOT="
set "PARENT="
for %%I in ("%~dp0..") do set "PARENT=%%~fI"
if exist "%PARENT%\generals.exe" set "GAME_ROOT=%PARENT%\"
if not defined GAME_ROOT if exist "%PARENT%\Generals.exe" set "GAME_ROOT=%PARENT%\"
if not defined GAME_ROOT if exist "%~dp0..\generals.exe" set "GAME_ROOT=%~dp0..\"

if not defined GAME_ROOT (
  echo ERROR: generals.exe not found next to this backup folder.
  echo Run this script from Backup_SPECTER_UNIFIED_* inside the game folder.
  pause
  exit /b 1
)

if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"
if not exist "%GAME_ROOT%Data\INI\" mkdir "%GAME_ROOT%Data\INI"

echo Restoring from:
echo   %~dp0
echo Into:
echo   %GAME_ROOT%

if exist "%~dp0_SPEC_DATA_ONE.big" copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if exist "%~dp0Data\INI\CommandSet.ini" copy /Y "%~dp0Data\INI\CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if exist "%~dp0Data\INI\CommandButton.ini" copy /Y "%~dp0Data\INI\CommandButton.ini" "%GAME_ROOT%Data\INI\CommandButton.ini" >nul
if exist "%~dp00_SPECTER_GlobalStoreCameos.big" (
  copy /Y "%~dp00_SPECTER_GlobalStoreCameos.big" "%GAME_ROOT%0_SPECTER_GlobalStoreCameos.big" >nul
) else (
  if exist "%GAME_ROOT%0_SPECTER_GlobalStoreCameos.big" del /F /Q "%GAME_ROOT%0_SPECTER_GlobalStoreCameos.big"
)
if exist "%~dp00_SPECTER_MissileJLMNCameos.big" (
  copy /Y "%~dp00_SPECTER_MissileJLMNCameos.big" "%GAME_ROOT%0_SPECTER_MissileJLMNCameos.big" >nul
) else (
  if exist "%GAME_ROOT%0_SPECTER_MissileJLMNCameos.big" del /F /Q "%GAME_ROOT%0_SPECTER_MissileJLMNCameos.big"
)

echo Restore finished. ART ONE/TWO were not changed.
pause
endlocal
exit /b 0
