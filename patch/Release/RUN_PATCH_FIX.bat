@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Specter FULL INI REPAIR PASS - Auto Installer
cd /d "%~dp0"

echo.
echo ============================================================
echo  Specter FULL INI REPAIR PASS
echo  Automatic launcher - RUN_PATCH_FIX.bat
echo ============================================================
echo.

if not exist "%~dp0Install_Final_Audit_Pass.bat" (
  echo [ERROR] Install_Final_Audit_Pass.bat not found.
  echo Place RUN_PATCH_FIX.bat inside the extracted Specter_FULL_INI_REPAIR_PASS folder.
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

echo [1/5] Detecting game folder...
set "GAMEROOT="

if exist "%~dp0Detect_GameRoot.ps1" (
  for /f "usebackq delims=" %%I in (`"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Detect_GameRoot.ps1" "%~dp0"`) do set "GAMEROOT=%%I"
) else (
  REM Inline PowerShell fallback (spaces-safe) if Detect_GameRoot.ps1 is missing
  for /f "usebackq delims=" %%I in (`"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -Command "$p='%~dp0'.TrimEnd('\'); function T([string]$x){ if(-not $x){return $false}; if(-not (Test-Path -LiteralPath $x)){return $false}; if(-not (Test-Path -LiteralPath (Join-Path $x 'Data'))){return $false}; foreach($e in @('generals.exe','Generals.exe','GeneralsZH.exe','generalszh.exe')){ if(Test-Path -LiteralPath (Join-Path $x $e)){ return $true } }; return $false }; if(T $p){ $p; exit 0 }; $c=$p; 1..4 | ForEach-Object { $c=Split-Path -Parent $c; if(T $c){ $c; exit 0 } }; Add-Type -AssemblyName System.Windows.Forms | Out-Null; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Select Generals Zero Hour / Specter game folder (Data + generals.exe)'; $d.ShowNewFolderButton=$false; if($d.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){ 'CANCEL'; exit 0 }; if(T $d.SelectedPath){ $d.SelectedPath } else { 'INVALID' }"`) do set "GAMEROOT=%%I"
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

echo.
echo [2/5] Game detected:
echo       !GAMEROOT!

if not exist "!GAMEROOT!\Data\" (
  echo [ERROR] Data\ folder not found. Wrong folder selected.
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
  echo [ERROR] generals.exe / GeneralsZH.exe not found.
  echo Wrong folder selected: !GAMEROOT!
  echo.
  pause
  exit /b 1
)
echo       Data\ OK
echo       generals.exe OK
echo.

echo [3/5] Backup created automatically under SpecterPatch_Backup\...
echo.
echo [4/5] Patch installing...
echo.

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
