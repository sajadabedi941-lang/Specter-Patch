@echo off
setlocal EnableExtensions
title Specter Ultimate Expansion Launcher

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open launcher folder.
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
echo   Found _SPEC_DATA_ONE.big
echo   Found _SPEC_ART_ONE.big
echo.

echo [2/4] Detecting game folder with generals.exe...
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
  echo Put this launcher folder INSIDE your Command and Conquer
  echo Generals Zero Hour / Specter folder, then run again.
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
  echo ERROR: generals.exe missing in game folder.
  echo   %GAME_ROOT%
  pause
  exit /b 1
)

echo   Game folder:
echo   %GAME_ROOT%
echo   Executable:
echo   %GENEXE%
echo.

echo [3/4] Loading Specter BIG patch into game folder...
echo.
echo   Zero Hour loads .big archives from the game folder automatically.
echo   Specter Ultimate Expansion needs BOTH files active:
echo     _SPEC_DATA_ONE.big
echo     _SPEC_ART_ONE.big
echo.
echo   Note: ZH "-mod file.big" supports only ONE mod archive, so it cannot
echo   enable both Specter BIGs. The correct method is placing both BIGs
echo   next to generals.exe, then starting the game from that folder.
echo.

copy /Y "%PATCH_DIR%_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 (
  echo ERROR: Failed to load _SPEC_DATA_ONE.big into game folder.
  pause
  exit /b 1
)
echo   Loaded _SPEC_DATA_ONE.big into game folder

copy /Y "%PATCH_DIR%_SPEC_ART_ONE.big" "%GAME_ROOT%_SPEC_ART_ONE.big" >nul
if errorlevel 1 (
  echo ERROR: Failed to load _SPEC_ART_ONE.big into game folder.
  pause
  exit /b 1
)
echo   Loaded _SPEC_ART_ONE.big into game folder
echo.

if not exist "%GAME_ROOT%_SPEC_DATA_ONE.big" (
  echo ERROR: _SPEC_DATA_ONE.big not present in game folder after load.
  pause
  exit /b 1
)
if not exist "%GAME_ROOT%_SPEC_ART_ONE.big" (
  echo ERROR: _SPEC_ART_ONE.big not present in game folder after load.
  pause
  exit /b 1
)

echo [4/4] Starting Command and Conquer Generals Zero Hour...
echo.
echo   Working directory: %GAME_ROOT%
echo   Command: generals.exe
echo   Active patch BIGs:
echo     %GAME_ROOT%_SPEC_DATA_ONE.big
echo     %GAME_ROOT%_SPEC_ART_ONE.big
echo.

REM Enter game folder so ArchiveFileSystem finds the SPEC BIGs, then launch.
pushd "%GAME_ROOT%"
if errorlevel 1 (
  echo ERROR: Cannot enter game folder.
  pause
  exit /b 1
)

REM Use relative exe name from GameRoot working directory.
start "" "generals.exe"
if errorlevel 1 (
  start "" "Generals.exe"
)

popd

echo.
echo Launch requested.
echo The game should now open with Specter Ultimate Expansion BIGs loaded.
echo You can close this window.
echo.
pause
endlocal
exit /b 0
