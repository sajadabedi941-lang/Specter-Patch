@echo off
setlocal EnableExtensions
title Specter FULL INI Repair - Installer
cd /d "%~dp0"

REM ============================================================
REM  GameRoot = this BAT's folder only (%~dp0). No GameRoot prompt.
REM  Supports spaces, parentheses, Unicode/Persian paths.
REM  Copy package INTO the game folder, then run this BAT.
REM ============================================================

chcp 65001 >nul 2>&1

set "GAMEROOT=%~dp0"
if "%GAMEROOT:~-1%"=="\" set "GAMEROOT=%GAMEROOT:~0,-1%"
set "SCRIPTDIR=%GAMEROOT%"

echo.
echo ============================================================
echo  Specter FULL INI Repair
echo ============================================================
echo.
echo Detected game path:
echo "%GAMEROOT%"
echo.

if not exist "%GAMEROOT%\Data\" (
  echo [ERROR] Data folder not found.
  echo Place this package inside the main game folder that contains:
  echo   Data\
  echo   Generals.exe
  echo Example: D:\New folder ^(5^)\SPECTER FINAL ^(GeneralsMode.com^)
  echo.
  pause
  exit /b 1
)

if not exist "%SCRIPTDIR%\Specter_FULL_REPAIR_Data\" (
  echo [ERROR] Patch payload folder not found next to this BAT.
  echo Expected: "%SCRIPTDIR%\Specter_FULL_REPAIR_Data\"
  echo.
  pause
  exit /b 1
)

if not exist "%SCRIPTDIR%\Install_Specter_Full_Repair.ps1" (
  echo [ERROR] Install_Specter_Full_Repair.ps1 missing next to this BAT.
  echo.
  pause
  exit /b 1
)

if not exist "%SCRIPTDIR%\RepairManifest.txt" (
  echo [ERROR] RepairManifest.txt missing next to this BAT.
  echo.
  pause
  exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

echo Creating backup...
echo Installing repaired files...
echo.

REM Pass game folder as -LiteralPath (required by Install_Specter_Full_Repair.ps1)
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPTDIR%\Install_Specter_Full_Repair.ps1" -LiteralPath "%GAMEROOT%" -ScriptDir "%SCRIPTDIR%"
set "ERR=%ERRORLEVEL%"

if not "%ERR%"=="0" (
  echo.
  echo [ERROR] Installation failed.
  echo.
  pause
  exit /b %ERR%
)

echo.
echo ============================================================
echo INSTALL SUCCESSFUL
echo Specter FULL INI Repair activated.
echo ============================================================
echo.
echo Game path: "%GAMEROOT%"
echo Backup:    "%GAMEROOT%\SpecterPatch_Backup\"
echo.
echo You can now launch Generals / Specter.
echo To rollback, run UNINSTALL_SPECTER_FULL_REPAIR.bat
echo.
pause
endlocal
exit /b 0
