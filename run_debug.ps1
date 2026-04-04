$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $root

$debugEnabled = $args -contains '--debug'
if ($debugEnabled) {
    $env:SUGOIHOOK_DEBUG_LOGGING = '1'
    Write-Host 'Starting Sugoi Hook in debug mode with verbose runtime logging...'
} else {
    Remove-Item Env:SUGOIHOOK_DEBUG_LOGGING -ErrorAction SilentlyContinue
    Write-Host 'Starting Sugoi Hook in debug mode with quiet runtime logging...'
}

& "$root\Python39\python.exe" "$root\SugoiHook_gui.py"
