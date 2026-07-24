@echo off
setlocal EnableExtensions EnableDelayedExpansion
title SPECTER GAME BOOT FIX - UNINSTALL
cd /d "%~dp0"

echo.
echo SPECTER GAME BOOT FIX - UNINSTALL / restore backup
echo.

set "SCRIPTDIR=%~dp0"
if "%SCRIPTDIR:~-1%"=="\" set "SCRIPTDIR=%SCRIPTDIR:~0,-1%"

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
  echo UNINSTALL FAILED
  echo.
  pause
  exit /b 1
)

set "BAKROOT=%GAMEROOT%\Specter_GAME_BOOT_FIX_BACKUP"
if not exist "%BAKROOT%" (
  echo [ERROR] No Specter_GAME_BOOT_FIX_BACKUP folder found.
  echo         Run INSTALL first.
  echo UNINSTALL FAILED
  echo.
  pause
  exit /b 1
)

set "LATEST="
for /f "delims=" %%D in ('dir /b /ad /o-n "%BAKROOT%"') do (
  if not defined LATEST set "LATEST=%%D"
)

if not defined LATEST (
  echo [ERROR] Backup folder is empty.
  echo UNINSTALL FAILED
  echo.
  pause
  exit /b 1
)

set "SRC=%BAKROOT%\%LATEST%"
echo Restoring from: "%SRC%"
echo.

set "RESTORED=0"
for /R "%SRC%" %%F in (*.ini) do (
  set "FULL=%%~fF"
  set "REL=!FULL:%SRC%\=!"
  set "DEST=%GAMEROOT%\Data\INI\Object\Specter\!REL!"
  for %%D in ("!DEST!") do (
    if not exist "%%~dpD" mkdir "%%~dpD" >nul 2>&1
  )
  copy /Y "!FULL!" "!DEST!" >nul
  if errorlevel 1 (
    echo [ERROR] Failed to restore: !REL!
    echo UNINSTALL FAILED
    echo.
    pause
    exit /b 1
  )
  set /a RESTORED+=1
  echo   RESTORED: !REL!
)

echo.
echo UNINSTALL SUCCESSFUL - restored !RESTORED! files.
echo.
pause
endlocal
exit /b 0
