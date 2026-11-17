@echo off
setlocal EnableExtensions
title Install Global Store original button cameos

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open this folder.
  pause
  exit /b 1
)

if not exist "%~dp00_SPECTER_GlobalStoreCameos.big" (
  echo ERROR: 0_SPECTER_GlobalStoreCameos.big is not next to this script.
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

copy /Y "%~dp00_SPECTER_GlobalStoreCameos.big" "%GAME_ROOT%0_SPECTER_GlobalStoreCameos.big" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy 0_SPECTER_GlobalStoreCameos.big
  pause
  exit /b 1
)

echo Installed:
echo   %GAME_ROOT%0_SPECTER_GlobalStoreCameos.big
echo.
echo SHA-256 overlay ART:
echo   1ac22af21f78515b7a3eafdf72b2f8ecdb2c15f1ed196963ff9c3cc0706c59fc
echo.
echo Do NOT replace _SPEC_ART_ONE.big or _SPEC_ART_TWO.big.
echo Keep the cc-vt72b-nk-hwasong DATA / CommandSet.ini / CommandButton.ini.
echo The 0_ prefix must stay so this archive first-wins Art\Textures\specbtn_mic_*.tga
echo.
pause
endlocal
exit /b 0
