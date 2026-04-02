@echo off
setlocal

set "ROOT=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%ROOT%run_normal.ps1"

endlocal
