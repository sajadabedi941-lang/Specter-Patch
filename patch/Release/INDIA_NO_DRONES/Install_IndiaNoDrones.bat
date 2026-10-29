@echo off
setlocal EnableExtensions
title SPECTER — remove India drones

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

findstr /C:"SPECTER_PATCH INDIA_NO_DRONES" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini in this pack is not the India-drone removal build.
  pause
  exit /b 1
)

findstr /C:"SPECTER_PATCH ISRAEL_GS" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is not the Israel Global Store lineage this pack needs.
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
  echo Unzip into the Zero Hour / SPECTER folder that has generals.exe,
  echo then run this script again.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

echo.
echo Copying ONLY _SPEC_DATA_ONE.big is not enough.
echo SPECTER already has Data\INI\CommandSet.ini as a loose file.
echo.

if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandButton.ini" "%GAME_ROOT%Data\INI\CommandButton.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0PlayerTemplate.ini" "%GAME_ROOT%Data\INI\PlayerTemplate.ini" >nul
if errorlevel 1 goto :copyfail

findstr /C:"SPECTER_PATCH INDIA_NO_DRONES" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Data\INI\CommandSet.ini was not replaced.
  pause
  exit /b 1
)

echo Installed:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%Data\INI\CommandSet.ini
echo   %GAME_ROOT%Data\INI\CommandButton.ini
echo   %GAME_ROOT%Data\INI\PlayerTemplate.ini
echo.
echo SHA-256:
echo   DATA  52b1186bc552b02237751f3faabd2b3c24c67f2a3ffe69d312db8dfd9a5bc58e
echo   CS    ba1c8175abc717aac5bb67d23abf249f24ebe24fe63ce00ffcbe250c40ae1e57
echo   CB    60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba
echo   PT    d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e
echo.
echo India CombatDrone / LoiteringDrone / HeavyUAV cannot be built.
echo Keep 0_ overlays and original ART. Do not replace ART.
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: Copy failed.
pause
exit /b 1
