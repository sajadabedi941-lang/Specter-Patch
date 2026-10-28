@echo off
setlocal EnableExtensions
title Install Command Center VT72B / NK Hwasong15BB

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
echo   52baa018c53015e90bf55b1451a33d22cad9de0951b4924168287129eeb2144a
echo SHA-256 CommandSet.ini:
echo   a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87
echo SHA-256 CommandButton.ini:
echo   5df320b6ce032225be66518eccfaaa0b52498ff01550c008008c8d22085b67dd
echo.
echo JP/VN/SK Command Center: VT72B only. NK: VT72B + Hwasong15BB.
echo War Factory / Missile Factory / radar unchanged. Do not replace ART.
echo.
pause
endlocal
exit /b 0
