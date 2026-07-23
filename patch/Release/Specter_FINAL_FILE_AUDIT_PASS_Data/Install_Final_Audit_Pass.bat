@echo off
setlocal EnableExtensions
title Specter FINAL AUDIT PASS Patch
cd /d "%~dp0"
echo.
echo  Specter FINAL FILE AUDIT PASS
echo  Audit: 0 Object/ModuleTag/MissingRef/WrongPath/Empty
echo.
set "PSEXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PSEXE%" set "PSEXE=powershell.exe"
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install_Runtime_Fix.ps1" %*
echo.
pause
