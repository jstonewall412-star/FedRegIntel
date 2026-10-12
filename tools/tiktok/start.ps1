$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$pythonRuntime = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
if ($pythonCommand) { & $pythonCommand.Source uploader.py }
elseif (Test-Path -LiteralPath $pythonRuntime) { & $pythonRuntime uploader.py }
else { throw 'Python 3.12 or newer is required. Install Python, then run this launcher again.' }
