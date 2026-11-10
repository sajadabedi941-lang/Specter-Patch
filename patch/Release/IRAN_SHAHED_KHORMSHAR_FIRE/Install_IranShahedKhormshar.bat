@echo off
setlocal EnableExtensions
title Install Iran Shahed-136 / Khormshar DATA BIG

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open this folder.
  pause
  exit /b 1
)

if not exist "%~dp0_SPEC_DATA_ONE.big" (
  echo ERROR: _SPEC_DATA_ONE.big is not next to this script.
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

copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy _SPEC_DATA_ONE.big
  pause
  exit /b 1
)

echo Installed:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo.
echo SHA-256 must be:
echo   1cf73a202d68a9008dfc6bc2925d26b31da53f622ad5881e400f5ce74c3c7937
echo.
echo KEEP Data\INI\CommandSet.ini from PR #710 / iran-commandset-live-path.
echo Do not delete it or replace it with an older copy.
echo SHA-256 of that CommandSet.ini must stay:
echo   5be1f652563e52c6ae89d903a1e64ac3f4e21946e06fde4ef8df165d399d3aac
echo.
echo Do not replace ART files.
echo.
pause
endlocal
exit /b 0
