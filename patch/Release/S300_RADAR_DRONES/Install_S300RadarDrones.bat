@echo off
setlocal EnableExtensions
title SPECTER — Global Store S-300 + Radar Sarab_3/Lamina

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open this folder.
  pause
  exit /b 1
)

set "NEED=_SPEC_DATA_ONE.big CommandSet.ini CommandButton.ini PlayerTemplate.ini"
for %%F in (%NEED%) do (
  if not exist "%~dp0%%F" (
    echo ERROR: %%F is not next to this script. Unzip the full pack.
    pause
    exit /b 1
  )
)

findstr /C:"SPECTER_PATCH GS_S300" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is missing the Global Store S-300 patch.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH RADAR_SARAB_LAMINA_19" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: CommandSet.ini is missing the 19-country Radar drone patch.
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
findstr /C:"5 = Command_ConstructIraq_MIC_S300" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Global Store slot 5 is not S-300.
  pause
  exit /b 1
)
findstr /C:"5 = Command_ConstructIraq_MIC_PantsirS1M" "%~dp0CommandSet.ini" >nul
if not errorlevel 1 (
  echo ERROR: Pantsir is still on Global Store slot 5. Incomplete pack.
  pause
  exit /b 1
)
findstr /C:"CommandSet Spain_RadarCommandSet" "%~dp0CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: Spain Radar CommandSet missing.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH AA_COMBO_HIDE" "%~dp0PlayerTemplate.ini" >nul
if errorlevel 1 (
  echo ERROR: PlayerTemplate.ini is not the expected lineage.
  pause
  exit /b 1
)

if exist "%~dp0_SPEC_ART_ONE.big" (
  echo ERROR: ART file found next to this script. This pack must not ship ART.
  pause
  exit /b 1
)
if exist "%~dp0_SPEC_ART_TWO.big" (
  echo ERROR: ART file found next to this script. This pack must not ship ART.
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
  echo Unzip SPECTER_S300_RADAR_DRONES_INSTALL.zip into the folder that
  echo has generals.exe, then run this script again.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

echo.
echo Copies ONLY DATA + CommandSet.ini + CommandButton.ini + PlayerTemplate.ini
echo Does NOT copy _SPEC_ART_ONE.big, _SPEC_ART_TWO.big, or 0_ overlays.
echo.

if exist "%GAME_ROOT%0_SPECTER_GlobalStoreCameos.big" (
  echo NOTE: existing 0_SPECTER_GlobalStoreCameos.big will NOT be replaced.
)
if exist "%GAME_ROOT%_SPEC_ART_ONE.big" (
  echo NOTE: existing _SPEC_ART_ONE.big will NOT be replaced.
)

if not exist "%GAME_ROOT%Data\INI" mkdir "%GAME_ROOT%Data\INI"
copy /Y "%~dp0_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandSet.ini" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0CommandButton.ini" "%GAME_ROOT%Data\INI\CommandButton.ini" >nul
if errorlevel 1 goto :copyfail
copy /Y "%~dp0PlayerTemplate.ini" "%GAME_ROOT%Data\INI\PlayerTemplate.ini" >nul
if errorlevel 1 goto :copyfail

findstr /C:"SPECTER_PATCH GS_S300" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: installed CommandSet.ini missing GS S-300. Incomplete install.
  pause
  exit /b 1
)
findstr /C:"SPECTER_PATCH RADAR_SARAB_LAMINA_19" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: installed CommandSet.ini missing Radar drones. Incomplete install.
  pause
  exit /b 1
)
findstr /C:"5 = Command_ConstructIraq_MIC_S300" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: installed Global Store slot 5 is not S-300.
  pause
  exit /b 1
)
findstr /C:"5 = Command_ConstructIraq_MIC_PantsirS1M" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if not errorlevel 1 (
  echo ERROR: installed CommandSet.ini still has Pantsir on GS slot 5.
  pause
  exit /b 1
)
findstr /C:"CommandSet Spain_RadarCommandSet" "%GAME_ROOT%Data\INI\CommandSet.ini" >nul
if errorlevel 1 (
  echo ERROR: installed CommandSet.ini missing Spain Radar.
  pause
  exit /b 1
)

echo Installed both packs:
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%Data\INI\CommandSet.ini
echo   %GAME_ROOT%Data\INI\CommandButton.ini
echo   %GAME_ROOT%Data\INI\PlayerTemplate.ini
echo.
echo ART and 0_ overlays were not copied.
echo.
echo SHA-256:
echo   DATA  aa40e6d1e68058becbe8d197a94c9ba05a5ef1af6bda25a14f5e82e9ea4ece53
echo   CS    13264095c91e610458e92bbc324aaa4d82d11bfdba597cd26cdf31d42e771213
echo   CB    1264aef1606ca9e6d1d68db0c211a793403d385417bc66238175c757f7350250
echo   PT    d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e
echo.
echo Zero Hour was not run. Static INI/BIG checks only.
echo.
pause
endlocal
exit /b 0

:copyfail
echo ERROR: Copy failed. Previous files were not fully replaced.
pause
exit /b 1
