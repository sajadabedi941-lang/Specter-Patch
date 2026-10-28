@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SPECTER Unified Install

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open this folder.
  pause
  exit /b 1
)

set "NEED=_SPEC_DATA_ONE.big CommandSet.ini CommandButton.ini 0_SPECTER_GlobalStoreCameos.big 0_SPECTER_MissileJLMNCameos.big"
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
  echo ERROR: generals.exe not found. Unzip this pack and run the installer from the game folder, or from a folder next to it.
  pause
  exit /b 1
)

if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

if not exist "%GAME_ROOT%Data\INI\" mkdir "%GAME_ROOT%Data\INI"
if errorlevel 1 (
  echo ERROR: Cannot create Data\INI
  pause
  exit /b 1
)

for /f "tokens=1-3 delims=/ " %%A in ("%DATE%") do set "D=%%C%%A%%B"
for /f "tokens=1-3 delims=:." %%A in ("%TIME%") do set "T=%%A%%B%%C"
set "T=%T: =0%"
set "BACKUP=%GAME_ROOT%Backup_SPECTER_UNIFIED_%D%_%T%"
mkdir "%BACKUP%" 2>nul
mkdir "%BACKUP%\Data\INI" 2>nul

echo Backing up existing files to:
echo   %BACKUP%
if exist "%GAME_ROOT%_SPEC_DATA_ONE.big" copy /Y "%GAME_ROOT%_SPEC_DATA_ONE.big" "%BACKUP%\_SPEC_DATA_ONE.big" >nul
if exist "%GAME_ROOT%Data\INI\CommandSet.ini" copy /Y "%GAME_ROOT%Data\INI\CommandSet.ini" "%BACKUP%\Data\INI\CommandSet.ini" >nul
if exist "%GAME_ROOT%Data\INI\CommandButton.ini" copy /Y "%GAME_ROOT%Data\INI\CommandButton.ini" "%BACKUP%\Data\INI\CommandButton.ini" >nul
if exist "%GAME_ROOT%0_SPECTER_GlobalStoreCameos.big" copy /Y "%GAME_ROOT%0_SPECTER_GlobalStoreCameos.big" "%BACKUP%\0_SPECTER_GlobalStoreCameos.big" >nul
if exist "%GAME_ROOT%0_SPECTER_MissileJLMNCameos.big" copy /Y "%GAME_ROOT%0_SPECTER_MissileJLMNCameos.big" "%BACKUP%\0_SPECTER_MissileJLMNCameos.big" >nul
copy /Y "%~dp0Restore_SpecterUnifiedBackup.bat" "%BACKUP%\Restore_SpecterUnifiedBackup.bat" >nul 2>nul
echo %BACKUP%> "%GAME_ROOT%Backup_SPECTER_UNIFIED_LAST.txt"

echo Installing...
copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandButton.ini" "%GAME_ROOT%Data\INI\CommandButton.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp00_SPECTER_GlobalStoreCameos.big" "%GAME_ROOT%0_SPECTER_GlobalStoreCameos.big" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp00_SPECTER_MissileJLMNCameos.big" "%GAME_ROOT%0_SPECTER_MissileJLMNCameos.big" >nul
if errorlevel 1 goto :copyfail

echo.
echo Installed:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%Data\INI\CommandSet.ini
echo   %GAME_ROOT%Data\INI\CommandButton.ini
echo   %GAME_ROOT%0_SPECTER_GlobalStoreCameos.big
echo   %GAME_ROOT%0_SPECTER_MissileJLMNCameos.big
echo.
echo SHA-256:
echo   DATA  c775c5cc5ae7ca1a4cb717b061c387ad044a737a19989b15496b88f6172da8ac
echo   CS    a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87
echo   CB    60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba
echo   GS    1ac22af21f78515b7a3eafdf72b2f8ecdb2c15f1ed196963ff9c3cc0706c59fc
echo   JLMN  618c6dabb192b8033f074a005e5141af2a756182be746d71f2c2fdda125fbfae
echo.
echo ART files _SPEC_ART_ONE.big and _SPEC_ART_TWO.big were NOT replaced.
echo Keep the 0_ prefix on both overlay BIG files.
echo To undo, run Restore_SpecterUnifiedBackup.bat from:
echo   %BACKUP%
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: Copy failed. Restore from %BACKUP% if needed.
pause
exit /b 1
