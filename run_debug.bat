@echo off
setlocal

set "ROOT=%~dp0"
set "EXTRA_ARG="
if /I "%~1"=="--debug" set "EXTRA_ARG=--debug"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$root = [System.IO.Path]::GetFullPath('%ROOT%'); $script = Join-Path $root 'run_debug.ps1'; $argsList = @('-w','0','nt','-p','PowerShell','-d',$root,'pwsh','-NoExit','-File',$script); if ('%EXTRA_ARG%' -ne '') { $argsList += '%EXTRA_ARG%' }; Start-Process wt.exe -ArgumentList $argsList"

endlocal
