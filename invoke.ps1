param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "src\mail_triage_cli\cli.py"

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

& $pythonCmd $pythonScript @Arguments
