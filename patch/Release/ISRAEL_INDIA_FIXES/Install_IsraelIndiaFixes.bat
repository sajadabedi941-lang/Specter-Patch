@echo off
setlocal EnableExtensions
title SPECTER — Israel Global Store + India drone removal

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

findstr /C:"SPECTER_PATCH ISRAEL_GS" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is missing the Israel Global Store patch.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH INDIA_NO_DRONES" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is missing the India drone-removal patch.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH AA_COMBO_HIDE" "%~dp0PlayerTemplate.ini" >nul
if errorlevel 1 (
  echo ERROR: PlayerTemplate.ini is not the combo-hide lineage this pack needs.
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
  echo Unzip SPECTER_ISRAEL_INDIA_FIXES_INSTALL.zip into the Zero Hour
  echo / SPECTER folder that has generals.exe, then run this script again.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

echo.
echo This installer copies ONLY:
echo   _SPEC_DATA_ONE.big
echo   Data\INI\CommandSet.ini
echo   Data\INI\CommandButton.ini
echo   Data\INI\PlayerTemplate.ini
echo It does NOT copy or replace _SPEC_ART_ONE.big, _SPEC_ART_TWO.big,
echo or any 0_*.big overlay.
echo.

if exist "%~dp0_SPEC_ART_ONE.big" (
  echo ERROR: ART file found next to this script. This pack must not ship ART.
  pause
  exit /b 1
)
if exist "%~dp00_SPECTER_GlobalStoreCameos.big" (
  echo NOTE: A 0_ overlay is next to this script and will NOT be copied.
)

if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandButton.ini" "%GAME_ROOT%Data\INI\CommandButton.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0PlayerTemplate.ini" "%GAME_ROOT%Data\INI\PlayerTemplate.ini" >nul
if errorlevel 1 goto :copyfail

findstr /C:"SPECTER_PATCH ISRAEL_GS" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Data\INI\CommandSet.ini was not replaced (Israel marker missing).
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH INDIA_NO_DRONES" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Data\INI\CommandSet.ini was not replaced (India marker missing).
  pause
  exit /b 1
)

echo Installed both fixes:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%Data\INI\CommandSet.ini
echo   %GAME_ROOT%Data\INI\CommandButton.ini
echo   %GAME_ROOT%Data\INI\PlayerTemplate.ini
echo.
echo ART and 0_ overlays were not copied.
echo.
echo SHA-256:
echo   DATA  52b1186bc552b02237751f3faabd2b3c24c67f2a3ffe69d312db8dfd9a5bc58e
echo   CS    ba1c8175abc717aac5bb67d23abf249f24ebe24fe63ce00ffcbe250c40ae1e57
echo   CB    60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba
echo   PT    d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e
echo.
echo Zero Hour was not run on this pack. Static INI/BIG checks only.
echo Keep original ART and 0_SPECTER_GlobalStoreCameos.big.
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: Copy failed.
pause
exit /b 1
