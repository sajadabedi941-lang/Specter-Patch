@echo off
setlocal EnableExtensions
title SPECTER — Radar Sarab_3 + Lamina (19 countries)

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open this folder.
  pause
  exit /b 1
)

set "NEED=_SPEC_DATA_ONE.big CommandSet.ini CommandButton.ini PlayerTemplate.ini"
for %%F in (%NEED%) do (
  if not exist "%~dp0%%F" (
    echo ERROR: %%F is not next to this script.
    pause
    exit /b 1
  )
)

findstr /C:"SPECTER_PATCH RADAR_SARAB_LAMINA_19" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is not the 19-country Sarab3/Lamina radar build.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH ISRAEL_GS" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Israel Global Store patch missing from CommandSet.ini.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH INDIA_NO_DRONES" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: India drone-removal patch missing from CommandSet.ini.
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
  echo Unzip into the folder that has generals.exe, then run this again.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

echo.
echo Copies ONLY DATA + CommandSet.ini + CommandButton.ini + PlayerTemplate.ini
echo Does NOT copy ART or 0_ overlays.
echo.

if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandButton.ini" "%GAME_ROOT%Data\INI\CommandButton.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0PlayerTemplate.ini" "%GAME_ROOT%Data\INI\PlayerTemplate.ini" >nul
if errorlevel 1 goto :copyfail

findstr /C:"SPECTER_PATCH RADAR_SARAB_LAMINA_19" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Data\INI\CommandSet.ini was not replaced.
  pause
  exit /b 1
)

echo Installed:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%Data\INI\CommandSet.ini
echo   %GAME_ROOT%Data\INI\CommandButton.ini
echo   %GAME_ROOT%Data\INI\PlayerTemplate.ini
echo.
echo SHA-256:
echo   DATA  bb42e2c1e96c7c41660540cb8cfd93f1633a41557dde1af349984ac9242b787e
echo   CS    4a280015eea96b167426268616b51f761a2ec67ecd90213121e979b0d0309680
echo   CB    4e987da75ee4ce1a2079aa4a2da1b514b0ccbb43f987d51c67d2d122dd50c54b
echo   PT    d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e
echo.
echo Keep original ART and 0_ overlays. Zero Hour was not run.
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: Copy failed.
pause
exit /b 1
