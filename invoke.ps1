param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path $scriptDir
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$sharedSrc = "C:\Users\ThomasBray\src\midtown-org-scan\microsoft-auth\src"
$toolSrc = Join-Path $projectRoot "src"

if (Test-Path $venvPython) {
    $env:PYTHONPATH = "$toolSrc;$sharedSrc;$env:PYTHONPATH"
    & $venvPython $toolSrc\mail_triage_cli\cli.py @Arguments
    exit $LASTEXITCODE
}

if ($env:VIRTUAL_ENV) {
    $pythonCmd = "python"
} else {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
    }
    if (-not $pythonCmd) {
        Write-Error "Python not found. Please install Python 3.10 or later."
        exit 1
    }
    $pythonCmd = $pythonCmd.Source
}

$env:PYTHONPATH = "$toolSrc;$sharedSrc;$env:PYTHONPATH"
& $pythonCmd $toolSrc\mail_triage_cli\cli.py @Arguments
exit $LASTEXITCODE
