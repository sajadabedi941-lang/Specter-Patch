@echo off
setlocal EnableExtensions
title Install WF remove RS-24 / DF-41 / Khorramshahr

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
if not exist "%~dp0CommandSet.ini" (
  echo ERROR: CommandSet.ini is not next to this script.
  pause
  exit /b 1
)
if not exist "%~dp0CommandButton.ini" (
  echo ERROR: CommandButton.ini is not next to this script.
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

copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy _SPEC_DATA_ONE.big
  pause
  exit /b 1
)

if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
copy /Y "%~dp0CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy CommandSet.ini
  pause
  exit /b 1
)
copy /Y "%~dp0CommandButton.ini" "%GAME_ROOT%Data\INI\CommandButton.ini" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy CommandButton.ini
  pause
  exit /b 1
)

echo Installed:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%Data\INI\CommandSet.ini
echo   %GAME_ROOT%Data\INI\CommandButton.ini
echo.
echo SHA-256 DATA BIG:
echo   a41168def32528d84d28879e077adcc1eb27ff3a02cc96b20fa15da05b3b465f
echo SHA-256 CommandSet.ini:
echo   32bf182ad2f701b86eba5b95d9a2a1ebc4ae8472fcd59bc01e949bbacbd628d9
echo SHA-256 CommandButton.ini:
echo   5df320b6ce032225be66518eccfaaa0b52498ff01550c008008c8d22085b67dd
echo.
echo Removed RS-24 / DF-41 / Khorramshahr from RU/CN/IR War Factory menus only.
echo Missile Factory K/L/M/N unchanged. Do not replace ART.
echo.
pause
endlocal
exit /b 0
