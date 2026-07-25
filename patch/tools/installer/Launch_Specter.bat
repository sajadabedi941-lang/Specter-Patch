@echo off
setlocal EnableExtensions
title Specter Ultimate Expansion Launcher

REM ------------------------------------------------------------
REM  Specter Ultimate Expansion - Real Launcher
REM  Finds this folder, verifies files, loads SPEC BIGs into the
REM  game folder, then starts generals.exe from that folder.
REM ------------------------------------------------------------

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open launcher folder.
  echo.
  pause
  exit /b 1
)

set "PATCH_DIR=%~dp0"
echo.
echo ============================================================
echo  SPECTER ULTIMATE EXPANSION LAUNCHER
echo ============================================================
echo.
echo Launcher folder:
echo   %PATCH_DIR%
echo.

echo [1/4] Checking patch BIG files...
if not exist "%PATCH_DIR%_SPEC_DATA_ONE.big" (
  echo.
  echo ERROR: Missing _SPEC_DATA_ONE.big
  echo Put _SPEC_DATA_ONE.big next to Launch_Specter.bat
  echo.
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%_SPEC_ART_ONE.big" (
  echo.
  echo ERROR: Missing _SPEC_ART_ONE.big
  echo Put _SPEC_ART_ONE.big next to Launch_Specter.bat
  echo.
  pause
  exit /b 1
)
echo   OK: _SPEC_DATA_ONE.big
echo   OK: _SPEC_ART_ONE.big
echo.

echo [2/4] Checking generals.exe...
set "GAME_ROOT="
set "PARENT="
for %%I in ("%PATCH_DIR%..") do set "PARENT=%%~fI"

if exist "%PATCH_DIR%generals.exe" set "GAME_ROOT=%PATCH_DIR%"
if not defined GAME_ROOT if exist "%PATCH_DIR%Generals.exe" set "GAME_ROOT=%PATCH_DIR%"
if not defined GAME_ROOT if exist "%PARENT%\generals.exe" set "GAME_ROOT=%PARENT%\"
if not defined GAME_ROOT if exist "%PARENT%\Generals.exe" set "GAME_ROOT=%PARENT%\"

if not defined GAME_ROOT (
  echo.
  echo ERROR: generals.exe was not found.
  echo.
  echo Extract this ZIP into your Specter / Zero Hour game folder
  echo ^(the folder that already contains generals.exe^), then run
  echo Launch_Specter.bat again.
  echo.
  echo Checked:
  echo   %PATCH_DIR%
  echo   %PARENT%
  echo.
  pause
  exit /b 1
)

if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

set "GENEXE="
if exist "%GAME_ROOT%generals.exe" set "GENEXE=%GAME_ROOT%generals.exe"
if not defined GENEXE if exist "%GAME_ROOT%Generals.exe" set "GENEXE=%GAME_ROOT%Generals.exe"
if not defined GENEXE (
  echo.
  echo ERROR: generals.exe missing in game folder:
  echo   %GAME_ROOT%
  echo.
  pause
  exit /b 1
)

echo   OK: generals.exe
echo   Game folder:
echo   %GAME_ROOT%
echo.

echo [3/4] Loading Specter BIG files into game folder...
echo.
echo   Specter loads _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big from
echo   the game folder automatically when generals.exe starts.
echo.

set "SAME=0"
if /I "%PATCH_DIR%"=="%GAME_ROOT%" set "SAME=1"

if "%SAME%"=="1" (
  echo   Launcher is already inside the game folder.
  echo   BIG files are already in place - no copy needed.
) else (
  echo   Copying _SPEC_DATA_ONE.big ...
  copy /Y "%PATCH_DIR%_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
  if errorlevel 1 (
    echo.
    echo ERROR: Failed to copy _SPEC_DATA_ONE.big into game folder.
    echo.
    pause
    exit /b 1
  )
  echo   OK: copied _SPEC_DATA_ONE.big

  echo   Copying _SPEC_ART_ONE.big ...
  copy /Y "%PATCH_DIR%_SPEC_ART_ONE.big" "%GAME_ROOT%_SPEC_ART_ONE.big" >nul
  if errorlevel 1 (
    echo.
    echo ERROR: Failed to copy _SPEC_ART_ONE.big into game folder.
    echo.
    pause
    exit /b 1
  )
  echo   OK: copied _SPEC_ART_ONE.big
)

if not exist "%GAME_ROOT%_SPEC_DATA_ONE.big" (
  echo.
  echo ERROR: _SPEC_DATA_ONE.big is not in the game folder.
  echo.
  pause
  exit /b 1
)
if not exist "%GAME_ROOT%_SPEC_ART_ONE.big" (
  echo.
  echo ERROR: _SPEC_ART_ONE.big is not in the game folder.
  echo.
  pause
  exit /b 1
)
echo   Active BIGs ready in game folder.
echo.

echo [4/4] Launching generals.exe...
echo.
echo   %GENEXE%
echo.

pushd "%GAME_ROOT%"
if errorlevel 1 (
  echo.
  echo ERROR: Cannot enter game folder:
  echo   %GAME_ROOT%
  echo.
  pause
  exit /b 1
)

start "" "%GENEXE%"
if errorlevel 1 (
  echo.
  echo ERROR: Failed to start generals.exe
  echo Tried:
  echo   %GENEXE%
  echo.
  popd
  pause
  exit /b 1
)

popd

echo.
echo SUCCESS: Game launch requested with Specter patch BIGs loaded.
echo.
echo Active files:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%_SPEC_ART_ONE.big
echo.
echo You can close this window.
echo.
pause
endlocal
exit /b 0
