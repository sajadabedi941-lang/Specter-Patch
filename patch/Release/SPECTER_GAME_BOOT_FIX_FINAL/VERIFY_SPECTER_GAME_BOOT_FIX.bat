@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SPECTER GAME BOOT FIX - VERIFY
cd /d "%~dp0"

echo.
echo SPECTER GAME BOOT FIX - VERIFY
echo.

set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

if not exist "%SCRIPTDIR%\Fixed" (
  echo [ERROR] Fixed folder missing.
  echo VERIFY FAIL
  echo.
  pause
  exit /b 1
)

echo Detecting game folder...
set "GAMEROOT="
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
  echo VERIFY FAIL
  echo.
  pause
  exit /b 1
)

echo GameRoot: "%GAMEROOT%"
echo.

set "MISSING=0"
set "CHECKED=0"
for /R "%SCRIPTDIR%\Fixed" %%F in (*.ini) do (
  set "FULL=%%~fF"
  set "REL=!FULL:%SCRIPTDIR%\Fixed\=!"
  set "DEST=%GAMEROOT%\Data\INI\Object\Specter\!REL!"
  set /a CHECKED+=1
  if not exist "!DEST!" (
    echo MISSING: !REL!
    set /a MISSING+=1
  )
)

echo Checked: !CHECKED!
echo Missing: !MISSING!
echo.

if not !MISSING! EQU 0 (
  echo VERIFY FAIL
  echo.
  pause
  exit /b 1
)

echo VERIFY PASS - all Fixed files are present in Specter.
echo.
pause
endlocal
exit /b 0
