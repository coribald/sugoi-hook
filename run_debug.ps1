$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root

Write-Host 'Starting Sugoi Hook in debug mode...'

& "$root\Python39\python.exe" "$root\SugoiHook_gui.py"
