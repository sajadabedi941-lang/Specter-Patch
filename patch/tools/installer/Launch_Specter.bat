@echo off
setlocal EnableExtensions
title Specter Ultimate Expansion Launcher

REM ------------------------------------------------------------
REM  Specter Ultimate Expansion - Real Launcher
REM  Finds this folder, verifies files, loads SPEC BIGs into the
REM  game folder, then starts generals.exe from that folder.
REM ------------------------------------------------------------

cd /d "%~dp0"
if errorlevel 1 (
  echo ERROR: Cannot open launcher folder.
  echo.
  pause
  exit /b 1
)

set "PATCH_DIR=%~dp0"
echo.
echo ============================================================
echo  SPECTER ULTIMATE EXPANSION LAUNCHER
echo ============================================================
echo.
echo Launcher folder:
echo   %PATCH_DIR%
echo.

echo [1/4] Checking patch BIG files...
if not exist "%PATCH_DIR%_SPEC_DATA_ONE.big" (
  echo.
  echo ERROR: Missing _SPEC_DATA_ONE.big
  echo Put _SPEC_DATA_ONE.big next to Launch_Specter.bat
  echo.
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%_SPEC_ART_ONE.big" (
  echo.
  echo ERROR: Missing _SPEC_ART_ONE.big
  echo Put _SPEC_ART_ONE.big next to Launch_Specter.bat
  echo.
  pause
  exit /b 1
)
if not exist "%PATCH_DIR%0_SPECTER_NatoSpainDisplay.big" (
  echo.
  echo ERROR: Missing 0_SPECTER_NatoSpainDisplay.big
  echo Put 0_SPECTER_NatoSpainDisplay.big next to Launch_Specter.bat
  echo.
  pause
  exit /b 1
)
echo   OK: _SPEC_DATA_ONE.big
echo   OK: _SPEC_ART_ONE.big
echo   OK: 0_SPECTER_NatoSpainDisplay.big
if exist "%PATCH_DIR%_SPEC_ART_TWO.big" (
  echo   OK: _SPEC_ART_TWO.big
) else (
  echo   _SPEC_ART_TWO.big is not next to this launcher.
  echo   It must already sit beside generals.exe.
)
echo.

set "SZ_DATA="
set "SZ_ART1="
set "SZ_ART2="
set "SZ_SPAIN="
for %%A in ("%PATCH_DIR%_SPEC_DATA_ONE.big") do set "SZ_DATA=%%~zA"
for %%A in ("%PATCH_DIR%_SPEC_ART_ONE.big") do set "SZ_ART1=%%~zA"
for %%A in ("%PATCH_DIR%0_SPECTER_NatoSpainDisplay.big") do set "SZ_SPAIN=%%~zA"
if exist "%PATCH_DIR%_SPEC_ART_TWO.big" for %%A in ("%PATCH_DIR%_SPEC_ART_TWO.big") do set "SZ_ART2=%%~zA"
if not "%SZ_DATA%"=="373898957" (
  echo.
  echo ERROR: _SPEC_DATA_ONE.big is %SZ_DATA% bytes, expected 373898957.
  echo.
  pause
  exit /b 1
)
if not "%SZ_ART1%"=="2144972013" (
  echo.
  echo ERROR: _SPEC_ART_ONE.big is %SZ_ART1% bytes, expected 2144972013.
  echo A truncated ART_ONE copy leaves buildings black or magenta.
  echo.
  pause
  exit /b 1
)
if not "%SZ_SPAIN%"=="1608985" (
  echo.
  echo ERROR: 0_SPECTER_NatoSpainDisplay.big is %SZ_SPAIN% bytes, expected 1608985.
  echo.
  pause
  exit /b 1
)
if defined SZ_ART2 goto CHECK_ART2_SIZE
goto AFTER_ART2_SIZE
:CHECK_ART2_SIZE
if not "%SZ_ART2%"=="307254782" (
  echo.
  echo ERROR: _SPEC_ART_TWO.big is %SZ_ART2% bytes, expected 307254782.
  echo.
  pause
  exit /b 1
)
:AFTER_ART2_SIZE

echo [2/4] Checking generals.exe...
set "GAME_ROOT="
set "PARENT="
for %%I in ("%PATCH_DIR%..") do set "PARENT=%%~fI"

if exist "%PATCH_DIR%generals.exe" set "GAME_ROOT=%PATCH_DIR%"
if not defined GAME_ROOT if exist "%PATCH_DIR%Generals.exe" set "GAME_ROOT=%PATCH_DIR%"
if not defined GAME_ROOT if exist "%PARENT%\generals.exe" set "GAME_ROOT=%PARENT%\"
if not defined GAME_ROOT if exist "%PARENT%\Generals.exe" set "GAME_ROOT=%PARENT%\"

if not defined GAME_ROOT (
  echo.
  echo ERROR: generals.exe was not found.
  echo.
  echo Extract this ZIP into your Specter / Zero Hour game folder
  echo ^(the folder that already contains generals.exe^), then run
  echo Launch_Specter.bat again.
  echo.
  echo Checked:
  echo   %PATCH_DIR%
  echo   %PARENT%
  echo.
  pause
  exit /b 1
)

if not "%GAME_ROOT:~-1%"=="\" set "GAME_ROOT=%GAME_ROOT%\"

set "GENEXE="
if exist "%GAME_ROOT%generals.exe" set "GENEXE=%GAME_ROOT%generals.exe"
if not defined GENEXE if exist "%GAME_ROOT%Generals.exe" set "GENEXE=%GAME_ROOT%Generals.exe"
if not defined GENEXE (
  echo.
  echo ERROR: generals.exe missing in game folder:
  echo   %GAME_ROOT%
  echo.
  pause
  exit /b 1
)

echo   OK: generals.exe
echo   Game folder:
echo   %GAME_ROOT%
echo.

echo [3/4] Loading Specter BIG files into game folder...
echo.
echo   Specter loads 0_SPECTER_NatoSpainDisplay.big, _SPEC_DATA_ONE.big,
echo   _SPEC_ART_ONE.big, and _SPEC_ART_TWO.big from the game folder.
echo   ART_TWO holds W3D models including US_Command. The 0_ overlay wins
echo   Data\English\generals.csf so FactionNato shows as Spanish Armed Forces.
echo.

set "SAME=0"
if /I "%PATCH_DIR%"=="%GAME_ROOT%" set "SAME=1"

if "%SAME%"=="1" (
  echo   Launcher is already inside the game folder.
  echo   BIG files are already in place - no copy needed.
) else (
  echo   Copying _SPEC_DATA_ONE.big ...
  copy /Y "%PATCH_DIR%_SPEC_DATA_ONE.big" "%GAME_ROOT%_SPEC_DATA_ONE.big" >nul
  if errorlevel 1 (
    echo.
    echo ERROR: Failed to copy _SPEC_DATA_ONE.big into game folder.
    echo.
    pause
    exit /b 1
  )
  echo   OK: copied _SPEC_DATA_ONE.big

  echo   Copying _SPEC_ART_ONE.big ...
  copy /Y "%PATCH_DIR%_SPEC_ART_ONE.big" "%GAME_ROOT%_SPEC_ART_ONE.big" >nul
  if errorlevel 1 (
    echo.
    echo ERROR: Failed to copy _SPEC_ART_ONE.big into game folder.
    echo.
    pause
    exit /b 1
  )
  echo   OK: copied _SPEC_ART_ONE.big

  if exist "%PATCH_DIR%_SPEC_ART_TWO.big" (
    echo   Copying _SPEC_ART_TWO.big ...
    copy /Y "%PATCH_DIR%_SPEC_ART_TWO.big" "%GAME_ROOT%_SPEC_ART_TWO.big" >nul
    if errorlevel 1 (
      echo.
      echo ERROR: Failed to copy _SPEC_ART_TWO.big into game folder.
      echo.
      pause
      exit /b 1
    )
    echo   OK: copied _SPEC_ART_TWO.big
  )

  echo   Copying 0_SPECTER_NatoSpainDisplay.big ...
  copy /Y "%PATCH_DIR%0_SPECTER_NatoSpainDisplay.big" "%GAME_ROOT%0_SPECTER_NatoSpainDisplay.big" >nul
  if errorlevel 1 (
    echo.
    echo ERROR: Failed to copy 0_SPECTER_NatoSpainDisplay.big into game folder.
    echo.
    pause
    exit /b 1
  )
  echo   OK: copied 0_SPECTER_NatoSpainDisplay.big
)

if not exist "%GAME_ROOT%_SPEC_DATA_ONE.big" (
  echo.
  echo ERROR: _SPEC_DATA_ONE.big is not in the game folder.
  echo.
  pause
  exit /b 1
)
if not exist "%GAME_ROOT%_SPEC_ART_ONE.big" (
  echo.
  echo ERROR: _SPEC_ART_ONE.big is not in the game folder.
  echo.
  pause
  exit /b 1
)
if not exist "%GAME_ROOT%_SPEC_ART_TWO.big" (
  echo.
  echo ERROR: _SPEC_ART_TWO.big is not in the game folder.
  echo US_Command.W3D is only in this archive. Copy it beside generals.exe.
  echo Official SPEC size 307254782 bytes,
  echo SHA-256 a5a20d959d2835f12a4bf5431e011c4d45047f24ea3d88841c2281fc0a6c19af
  echo.
  pause
  exit /b 1
)
if not exist "%GAME_ROOT%0_SPECTER_NatoSpainDisplay.big" (
  echo.
  echo ERROR: 0_SPECTER_NatoSpainDisplay.big is not in the game folder.
  echo.
  pause
  exit /b 1
)
set "DST_DATA="
set "DST_ART1="
set "DST_ART2="
set "DST_SPAIN="
for %%A in ("%GAME_ROOT%_SPEC_DATA_ONE.big") do set "DST_DATA=%%~zA"
for %%A in ("%GAME_ROOT%_SPEC_ART_ONE.big") do set "DST_ART1=%%~zA"
for %%A in ("%GAME_ROOT%_SPEC_ART_TWO.big") do set "DST_ART2=%%~zA"
for %%A in ("%GAME_ROOT%0_SPECTER_NatoSpainDisplay.big") do set "DST_SPAIN=%%~zA"
if not "%DST_DATA%"=="373898957" (
  echo ERROR: game-folder _SPEC_DATA_ONE.big is %DST_DATA% bytes, expected 373898957.
  pause
  exit /b 1
)
if not "%DST_ART1%"=="2144972013" (
  echo ERROR: game-folder _SPEC_ART_ONE.big is %DST_ART1% bytes, expected 2144972013.
  pause
  exit /b 1
)
if not "%DST_ART2%"=="307254782" (
  echo ERROR: game-folder _SPEC_ART_TWO.big is %DST_ART2% bytes, expected 307254782.
  pause
  exit /b 1
)
if not "%DST_SPAIN%"=="1608985" (
  echo ERROR: game-folder 0_SPECTER_NatoSpainDisplay.big is %DST_SPAIN% bytes, expected 1608985.
  pause
  exit /b 1
)
echo   Active BIGs ready in game folder. Destination byte sizes match.
echo.

echo [4/4] Launching generals.exe...
echo.
echo   %GENEXE%
echo.

pushd "%GAME_ROOT%"
if errorlevel 1 (
  echo.
  echo ERROR: Cannot enter game folder:
  echo   %GAME_ROOT%
  echo.
  pause
  exit /b 1
)

start "" "%GENEXE%"
if errorlevel 1 (
  echo.
  echo ERROR: Failed to start generals.exe
  echo Tried:
  echo   %GENEXE%
  echo.
  popd
  pause
  exit /b 1
)

popd

echo.
echo SUCCESS: Game launch requested with Specter patch BIGs loaded.
echo.
echo Active files:
echo   %GAME_ROOT%0_SPECTER_NatoSpainDisplay.big
echo   %GAME_ROOT%_SPEC_DATA_ONE.big
echo   %GAME_ROOT%_SPEC_ART_ONE.big
echo   %GAME_ROOT%_SPEC_ART_TWO.big
echo.
echo You can close this window.
echo.
pause
endlocal
exit /b 0
