[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$ServiceAccount = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
)

$ErrorActionPreference = 'Stop'
$principal = [System.Security.Principal.WindowsPrincipal]::new(
    [System.Security.Principal.WindowsIdentity]::GetCurrent()
)
if (-not $principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script from an elevated PowerShell window.'
}

$repoRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$targets = @(
    (Join-Path $repoRoot 'backend\.env'),
    (Join-Path $repoRoot 'backend\data'),
    (Join-Path $repoRoot 'backend\outputs'),
    (Join-Path $repoRoot '.phase1-artifacts'),
    (Join-Path $repoRoot 'backups')
)
$accounts = @($ServiceAccount, 'NT AUTHORITY\SYSTEM', 'BUILTIN\Administrators') |
    Select-Object -Unique

function Assert-WorkspaceTarget([string]$Path) {
    $resolved = [System.IO.Path]::GetFullPath($Path)
    $rootPrefix = $repoRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $resolved.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing path outside workspace: $resolved"
    }
    return $resolved
}

function Set-PrivateAcl([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing reparse point: $Path"
    }
    $isDirectory = $item.PSIsContainer
    $acl = New-Object System.Security.AccessControl.DirectorySecurity
    if (-not $isDirectory) {
        $acl = New-Object System.Security.AccessControl.FileSecurity
    }
    $acl.SetAccessRuleProtection($true, $false)
    $acl.SetOwner([System.Security.Principal.NTAccount]::new($ServiceAccount))
    foreach ($account in $accounts) {
        $inheritance = if ($isDirectory) {
            [System.Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
        } else {
            [System.Security.AccessControl.InheritanceFlags]::None
        }
        $rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
            $account,
            [System.Security.AccessControl.FileSystemRights]::FullControl,
            $inheritance,
            [System.Security.AccessControl.PropagationFlags]::None,
            [System.Security.AccessControl.AccessControlType]::Allow
        )
        [void]$acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $Path -AclObject $acl
}

foreach ($candidate in $targets) {
    $target = Assert-WorkspaceTarget $candidate
    if (-not (Test-Path -LiteralPath $target)) {
        Write-Verbose "Skipping absent target: $target"
        continue
    }
    if ($PSCmdlet.ShouldProcess($target, 'Restrict ACL to service account, SYSTEM and Administrators')) {
        $rootItem = Get-Item -LiteralPath $target -Force
        if ($rootItem.PSIsContainer) {
            Get-ChildItem -LiteralPath $target -Force -Recurse |
                Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0 } |
                Sort-Object { $_.FullName.Length } -Descending |
                ForEach-Object { Set-PrivateAcl $_.FullName }
        }
        Set-PrivateAcl $target
    }
}

Write-Output "ACL hardening complete for $ServiceAccount."
