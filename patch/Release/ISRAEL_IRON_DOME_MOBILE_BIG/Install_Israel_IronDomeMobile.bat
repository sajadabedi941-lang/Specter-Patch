@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Install Israel Iron Dome Mobile (BIG)

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open the installer folder.
  pause
  exit /b 1
)
set "PATCH_DIR=%~dp0"

echo.
echo ============================================================
echo  Israel Iron Dome Mobile  -  BIG install
echo ============================================================
echo.

if not exist "%PATCH_DIR%_SPEC_DATA_ONE.big" (
  echo ERROR: Missing _SPEC_DATA_ONE.big
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%_SPEC_ART_TWO.big" (
  echo ERROR: Missing _SPEC_ART_TWO.big
  pause
  exit /b 1
)

set "GAME_ROOT="
if exist "%PATCH_DIR%generals.exe" set "GAME_ROOT=%PATCH_DIR%"
if not defined GAME_ROOT (
  for %%I in ("%PATCH_DIR%..") do (
    if exist "%%~fI\generals.exe" set "GAME_ROOT=%%~fI\"
  )
)
if not defined GAME_ROOT (
  echo ERROR: generals.exe not found in this folder or the parent folder.
  echo Put this pack inside SPECTER FINAL and run it again.
  pause
  exit /b 1
)
if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

echo Game folder:
echo   %GAME_ROOT%
echo.

if not exist "%GAME_ROOT%_SPEC_DATA_ONE.big" (
  echo ERROR: Game _SPEC_DATA_ONE.big not found.
  pause
  exit /b 1
)
if not exist "%GAME_ROOT%_SPEC_ART_TWO.big" (
  echo ERROR: Game _SPEC_ART_TWO.big not found.
  pause
  exit /b 1
)

set "BACKUP=%GAME_ROOT%SpecterBackup_IronDomeMobile\"
if not exist "%BACKUP%" mkdir "%BACKUP%"

echo [1/4] Backing up original BIGs to:
echo   %BACKUP%
if not exist "%BACKUP%_SPEC_DATA_ONE.big" copy /Y "%GAME_ROOT%_SPEC_DATA_ONE.big" "%BACKUP%_SPEC_DATA_ONE.big" >nul
if exist "%GAME_ROOT%_SPEC_ART_ONE.big" if not exist "%BACKUP%_SPEC_ART_ONE.big" copy /Y "%GAME_ROOT%_SPEC_ART_ONE.big" "%BACKUP%_SPEC_ART_ONE.big" >nul
if not exist "%BACKUP%_SPEC_ART_TWO.big" copy /Y "%GAME_ROOT%_SPEC_ART_TWO.big" "%BACKUP%_SPEC_ART_TWO.big" >nul
if exist "%GAME_ROOT%Data\INI\CommandSet.ini" if not exist "%BACKUP%Data_INI_CommandSet.ini" copy /Y "%GAME_ROOT%Data\INI\CommandSet.ini" "%BACKUP%Data_INI_CommandSet.ini" >nul
if exist "%GAME_ROOT%Data\English\generals.csf" if not exist "%BACKUP%Data_English_generals.csf" copy /Y "%GAME_ROOT%Data\English\generals.csf" "%BACKUP%Data_English_generals.csf" >nul
echo   Backup done.
echo.

echo [2/4] Installing patched BIGs...
copy /Y "%PATCH_DIR%_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
copy /Y "%PATCH_DIR%_SPEC_ART_TWO.big" "%GAME_ROOT%_SPEC_ART_TWO.big" >nul
echo   Installed _SPEC_DATA_ONE.big
echo   Installed _SPEC_ART_TWO.big
echo   _SPEC_ART_ONE.big was not replaced.
echo.

echo [3/4] Removing leftover files from Iron Dome Mobile v2 loose installer...
REM Unique files created by v2. They are not part of ss1.
if exist "%GAME_ROOT%Data\INI\CommandSet_SpecterPatch.ini" del /F /Q "%GAME_ROOT%Data\INI\CommandSet_SpecterPatch.ini"
if exist "%GAME_ROOT%Data\INI\CommandButton_Israel_VehicleIronDomeMobile.ini" del /F /Q "%GAME_ROOT%Data\INI\CommandButton_Israel_VehicleIronDomeMobile.ini"
if exist "%GAME_ROOT%Data\INI\CommandSet_Israel_VehicleIronDomeMobile.ini" del /F /Q "%GAME_ROOT%Data\INI\CommandSet_Israel_VehicleIronDomeMobile.ini"
if exist "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Israel_VehicleIronDomeMobile.ini" del /F /Q "%GAME_ROOT%Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Israel_VehicleIronDomeMobile.ini"
if exist "%GAME_ROOT%Data\English\generals.csf" del /F /Q "%GAME_ROOT%Data\English\generals.csf"
if exist "%GAME_ROOT%Art\W3D\BONDKS.W3D" del /F /Q "%GAME_ROOT%Art\W3D\BONDKS.W3D"
if exist "%GAME_ROOT%Art\Textures\T_M978_D01.tga" del /F /Q "%GAME_ROOT%Art\Textures\T_M978_D01.tga"
if exist "%GAME_ROOT%Art\Textures\T_M978_D02.tga" del /F /Q "%GAME_ROOT%Art\Textures\T_M978_D02.tga"
if exist "%GAME_ROOT%Art\Textures\T_M978_D03.tga" del /F /Q "%GAME_ROOT%Art\Textures\T_M978_D03.tga"
if exist "%GAME_ROOT%Art\Textures\concrete_wall_02_D.tga" del /F /Q "%GAME_ROOT%Art\Textures\concrete_wall_02_D.tga"
if exist "%GAME_ROOT%Art\Textures\texture_0006.tga" del /F /Q "%GAME_ROOT%Art\Textures\texture_0006.tga"
if exist "%GAME_ROOT%Art\Textures\texture_0007.tga" del /F /Q "%GAME_ROOT%Art\Textures\texture_0007.tga"
if exist "%GAME_ROOT%Art\Textures\texture_0008.tga" del /F /Q "%GAME_ROOT%Art\Textures\texture_0008.tga"

REM ss1 and v2 both keep a loose Data\INI\CommandSet.ini that WINS OVER the BIG.
REM Slot 11 lives in the patched BIG. The known duplicate must be removed or the BIG change is hidden.
if exist "%GAME_ROOT%Data\INI\CommandSet.ini" (
  for %%Z in ("%GAME_ROOT%Data\INI\CommandSet.ini") do set "CS_SIZE=%%~zZ"
  echo   Found loose Data\INI\CommandSet.ini size !CS_SIZE!
  if "!CS_SIZE!"=="450860" (
    echo   Removing ss1 duplicate CommandSet.ini so the patched BIG is used.
    del /F /Q "%GAME_ROOT%Data\INI\CommandSet.ini"
  ) else if "!CS_SIZE!"=="450912" (
    echo   Removing v2 CommandSet.ini so the patched BIG is used.
    del /F /Q "%GAME_ROOT%Data\INI\CommandSet.ini"
  ) else (
    echo   WARNING: Data\INI\CommandSet.ini size is not ss1 or v2.
    echo   Left in place. Slot 11 may not appear if this file wins over the BIG.
  )
)
echo.

echo [4/4] Done.
echo   Buy button: AirF Command Center slot 11
echo   Restore: Restore_Israel_IronDomeMobile.bat
echo.
pause
exit /b 0
