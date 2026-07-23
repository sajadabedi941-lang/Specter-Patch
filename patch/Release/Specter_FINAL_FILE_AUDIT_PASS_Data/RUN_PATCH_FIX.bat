@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter FINAL FILE AUDIT PASS - Auto Installer
cd /d "%~dp0"

echo.
echo ============================================================
echo  Specter FINAL FILE AUDIT PASS
echo  Automatic launcher - RUN_PATCH_FIX.bat
echo ============================================================
echo.

REM --- Require installer files next to this launcher ---
if not exist "%~dp0Install_Final_Audit_Pass.bat" (
  echo [ERROR] Install_Final_Audit_Pass.bat not found.
  echo Place RUN_PATCH_FIX.bat inside the extracted Specter_FINAL_FILE_AUDIT_PASS folder.
  echo.
  pause
  exit /b 1
)
if not exist "%~dp0Install_Runtime_Fix.ps1" (
  echo [ERROR] Install_Runtime_Fix.ps1 not found next to this launcher.
  echo.
  pause
  exit /b 1
)

set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"

REM --- Auto-detect GameRoot (handles spaces via PowerShell) ---
echo [1/5] Detecting game folder...
for /f "usebackq delims=" %%I in (`"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Detect_GameRoot.ps1" "%~dp0"`) do (
  set "GAMEROOT=%%I"
)

if /I "!GAMEROOT!"=="CANCEL" (
  echo [ERROR] Game folder selection cancelled.
  echo.
  pause
  exit /b 1
)
if /I "!GAMEROOT!"=="INVALID" (
  echo [ERROR] Wrong folder selected.
  echo The folder must contain both:
  echo   - Data\
  echo   - generals.exe  ^(or GeneralsZH.exe^)
  echo.
  pause
  exit /b 1
)
if not defined GAMEROOT (
  echo [ERROR] Could not detect game folder.
  echo.
  pause
  exit /b 1
)

REM --- Validate GameRoot ---
echo.
echo [2/5] Game detected:
echo       !GAMEROOT!
if not exist "!GAMEROOT!\Data\" (
  echo [ERROR] Data\ folder not found in selected game folder.
  echo.
  pause
  exit /b 1
)
set "EXE_OK=0"
if exist "!GAMEROOT!\generals.exe" set "EXE_OK=1"
if exist "!GAMEROOT!\Generals.exe" set "EXE_OK=1"
if exist "!GAMEROOT!\GeneralsZH.exe" set "EXE_OK=1"
if exist "!GAMEROOT!\generalszh.exe" set "EXE_OK=1"
if "!EXE_OK!"=="0" (
  echo [ERROR] generals.exe / GeneralsZH.exe not found in:
  echo       !GAMEROOT!
  echo Wrong folder selected.
  echo.
  pause
  exit /b 1
)
echo       Data\ OK
echo       generals.exe OK
echo.

echo [3/5] Backup will be created automatically under:
echo       SpecterPatch_Backup\RuntimeCrashFixV2_^<timestamp^>
echo.
echo [4/5] Patch installing...
echo.

REM Pass GameRoot quoted so spaces work; skip nested pause in child by env flag
set "SPECTER_LAUNCHER=1"
call "%~dp0Install_Final_Audit_Pass.bat" "!GAMEROOT!"
set "ERR=!ERRORLEVEL!"

echo.
if not "!ERR!"=="0" (
  echo [ERROR] Installation failed ^(exit code !ERR!^).
  echo Check messages above. Backup is kept if created.
  echo.
  pause
  exit /b !ERR!
)

echo [5/5] Installation completed successfully.
echo       Launch Generals Zero Hour / Specter now.
echo.
pause
endlocal
exit /b 0
