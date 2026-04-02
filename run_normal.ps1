$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root

$pythonExe = Join-Path $root 'Python39\pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    $pythonExe = Join-Path $root 'Python39\python.exe'
}

$env:SUGOIHOOK_SKIP_ELEVATION = '1'
Start-Process -FilePath $pythonExe -WorkingDirectory $root -ArgumentList @("$root\SugoiHook_gui.py")
