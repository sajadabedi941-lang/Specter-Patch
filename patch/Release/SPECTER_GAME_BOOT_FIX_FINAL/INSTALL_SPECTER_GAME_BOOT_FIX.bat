@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SPECTER GAME BOOT FIX - INSTALL
cd /d "%~dp0"

echo.
echo ============================================================
echo  SPECTER GAME BOOT FIX FINAL
echo  Pure batch installer - cmd.exe only
echo ============================================================
echo.

set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

if not exist "%SCRIPTDIR%\Fixed" (
  echo [ERROR] Fixed folder missing next to this BAT.
  echo INSTALL FAILED
  echo.
  pause
  exit /b 1
)

echo [1/4] Detecting game folder...
set "GAMEROOT="

REM Check this folder and parents for Data\INI\Object\Specter
set "CAND=%SCRIPTDIR%"
for /L %%N in (1,1,7) do (
  if not defined GAMEROOT (
    if exist "!CAND!\Data\INI\Object\Specter" (
      set "GAMEROOT=!CAND!"
    ) else (
      for %%P in ("!CAND!\..") do set "CAND=%%~fP"
    )
  )
)

if not defined GAMEROOT (
  echo [ERROR] Could not find Data\INI\Object\Specter
  echo         Copy this folder into your game root and run again.
  echo         Game root must contain: Data\INI\Object\Specter
  echo INSTALL FAILED
  echo.
  pause
  exit /b 1
)

echo         GameRoot: "%GAMEROOT%"
echo         Specter : "%GAMEROOT%\Data\INI\Object\Specter"
echo.

echo [2/4] Creating backup...
set "STAMP=%DATE:~-4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
set "STAMP=%STAMP: =0%"
set "STAMP=%STAMP:/=-%"
set "STAMP=%STAMP::=-%"
set "BACKUP=%GAMEROOT%\Specter_GAME_BOOT_FIX_BACKUP\%STAMP%"
mkdir "%BACKUP%" >nul 2>&1

set "COPIED=0"
set "BACKED=0"
for /R "%SCRIPTDIR%\Fixed" %%F in (*.ini) do (
  set "FULL=%%~fF"
  set "REL=!FULL:%SCRIPTDIR%\Fixed\=!"
  set "DEST=%GAMEROOT%\Data\INI\Object\Specter\!REL!"
  set "BAK=%BACKUP%\!REL!"

  for %%D in ("!DEST!") do (
    if not exist "%%~dpD" mkdir "%%~dpD" >nul 2>&1
  )
  for %%D in ("!BAK!") do (
    if not exist "%%~dpD" mkdir "%%~dpD" >nul 2>&1
  )

  if exist "!DEST!" (
    copy /Y "!DEST!" "!BAK!" >nul
    if not errorlevel 1 set /a BACKED+=1
  )
)

echo         Backup folder: "%BACKUP%"
echo         Files backed up: !BACKED!
echo.

echo [3/4] Copying Fixed INI files into Specter...
for /R "%SCRIPTDIR%\Fixed" %%F in (*.ini) do (
  set "FULL=%%~fF"
  set "REL=!FULL:%SCRIPTDIR%\Fixed\=!"
  set "DEST=%GAMEROOT%\Data\INI\Object\Specter\!REL!"

  for %%D in ("!DEST!") do (
    if not exist "%%~dpD" mkdir "%%~dpD" >nul 2>&1
  )

  copy /Y "!FULL!" "!DEST!" >nul
  if errorlevel 1 (
    echo [ERROR] Failed to copy: !REL!
    echo INSTALL FAILED
    echo.
    pause
    exit /b 1
  )
  set /a COPIED+=1
  echo         Copied: !REL!
)

echo         Total copied: !COPIED!
echo.

if !COPIED! LSS 1 (
  echo [ERROR] No INI files found under Fixed\
  echo INSTALL FAILED
  echo.
  pause
  exit /b 1
)

echo [4/4] Verifying copied files...
set "MISSING=0"
for /R "%SCRIPTDIR%\Fixed" %%F in (*.ini) do (
  set "FULL=%%~fF"
  set "REL=!FULL:%SCRIPTDIR%\Fixed\=!"
  set "DEST=%GAMEROOT%\Data\INI\Object\Specter\!REL!"
  if not exist "!DEST!" (
    echo         MISSING: !REL!
    set /a MISSING+=1
  )
)

if not !MISSING! EQU 0 (
  echo [ERROR] Verification failed. Missing files: !MISSING!
  echo INSTALL FAILED
  echo.
  pause
  exit /b 1
)

REM Spot-check known crash targets
set "FAILKNOWN=0"
if not exist "%GAMEROOT%\Data\INI\Object\Specter\British Armed Forces\Airforce\Britain_F35B.ini" (
  echo         MISSING known target: Britain_F35B.ini
  set "FAILKNOWN=1"
)
if not exist "%GAMEROOT%\Data\INI\Object\Specter\British Armed Forces\Drones\Britain_CombatDrone.ini" (
  echo         MISSING known target: Britain_CombatDrone.ini
  set "FAILKNOWN=1"
)
if not exist "%GAMEROOT%\Data\INI\Object\Specter\Turkey Armed Forces\Turkey_WeaponObjects.ini" (
  echo         MISSING known target: Turkey_WeaponObjects.ini
  set "FAILKNOWN=1"
)

if not "!FAILKNOWN!"=="0" (
  echo [ERROR] Known crash-target files missing after copy.
  echo INSTALL FAILED
  echo.
  pause
  exit /b 1
)

echo         Verification OK
echo.

echo ============================================================
echo INSTALL SUCCESSFUL
echo Deployed !COPIED! INI files into Data\INI\Object\Specter
echo Backup: Specter_GAME_BOOT_FIX_BACKUP\%STAMP%\
echo Launch Specter and confirm main menu / Skirmish.
echo ============================================================
echo.
pause
endlocal
exit /b 0
