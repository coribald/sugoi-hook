@echo off
setlocal

set "ROOT=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$root = [System.IO.Path]::GetFullPath('%ROOT%'); $script = Join-Path $root 'run_debug.ps1'; Start-Process wt.exe -ArgumentList @('-w','0','nt','-p','PowerShell','-d',$root,'pwsh','-NoExit','-File',$script)"

endlocal
