@echo off
setlocal EnableExtensions
title Install Iran live CommandSet.ini

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open this folder.
  pause
  exit /b 1
)

if not exist "%~dp0CommandSet.ini" (
  echo ERROR: CommandSet.ini is not next to this script.
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
  echo Put this folder inside the Zero Hour game folder, or next to it.
  pause
  exit /b 1
)

if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
if errorlevel 1 (
  echo ERROR: Cannot create Data\INI
  pause
  exit /b 1
)

copy /Y "%~dp0CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy CommandSet.ini
  pause
  exit /b 1
)

echo Installed:
echo   %GAME_ROOT%Data\INI\CommandSet.ini
echo.
echo Keep the existing _SPEC_DATA_ONE.big. Do not replace it with this folder.
echo SHA-256 must be:
echo   5be1f652563e52c6ae89d903a1e64ac3f4e21946e06fde4ef8df165d399d3aac
echo.
pause
endlocal
exit /b 0
