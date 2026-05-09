param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$installer = New-Object -ComObject WindowsInstaller.Installer
try {
    $resolvedPath = (Resolve-Path $Path).Path
    $database = $installer.GetType().InvokeMember(
        "OpenDatabase",
        "InvokeMethod",
        $null,
        $installer,
        @($resolvedPath, 0)
    )
}
catch {
    throw "Unable to open MSI database for ProductCode lookup: $Path. $($_.Exception.Message)"
}
$view = $database.GetType().InvokeMember(
    "OpenView",
    "InvokeMethod",
    $null,
    $database,
    @("SELECT `Value` FROM `Property` WHERE `Property`='ProductCode'")
)
$view.GetType().InvokeMember("Execute", "InvokeMethod", $null, $view, $null) | Out-Null
$record = $view.GetType().InvokeMember("Fetch", "InvokeMethod", $null, $view, $null)
if ($null -eq $record) {
    throw "ProductCode not found in MSI: $Path"
}
$value = $record.GetType().InvokeMember("StringData", "GetProperty", $null, $record, 1)
Write-Output $value

