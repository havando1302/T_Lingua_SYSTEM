# Restrict local secrets/runtime to the current operator, existing owner and SYSTEM.
$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$privatePaths = @('.phase1-artifacts', 'backend\.env', 'backend\data', 'backend\outputs', 'backend\temp')
$operatorSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
foreach ($relativePath in $privatePaths) {
    $targetPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $relativePath))
    if (-not $targetPath.StartsWith($repoRoot + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Private path must remain inside the workspace.'
    }
    if (-not (Test-Path -LiteralPath $targetPath)) { continue }
    $targetItem = Get-Item -LiteralPath $targetPath -Force
    $ancestor = $targetItem
    while ($null -ne $ancestor -and $ancestor.FullName.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        if (($ancestor.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw 'Private paths must not traverse links or junctions.'
        }
        $ancestor = if ($ancestor.PSIsContainer) { $ancestor.Parent } else { $ancestor.Directory }
    }
    $existingAcl = Get-Acl -LiteralPath $targetPath
    $ownerSid = $existingAcl.GetOwner([System.Security.Principal.SecurityIdentifier])
    $newAcl = if ($targetItem.PSIsContainer) { New-Object System.Security.AccessControl.DirectorySecurity } else { New-Object System.Security.AccessControl.FileSecurity }
    $newAcl.SetOwner($ownerSid)
    $newAcl.SetAccessRuleProtection($true, $false)
    $inheritance = if ($targetItem.PSIsContainer) { [System.Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit' } else { [System.Security.AccessControl.InheritanceFlags]::None }
    foreach ($sid in @($operatorSid, $ownerSid, [System.Security.Principal.SecurityIdentifier]'S-1-5-18')) {
        $rule = [System.Security.AccessControl.FileSystemAccessRule]::new($sid, [System.Security.AccessControl.FileSystemRights]::FullControl, $inheritance, [System.Security.AccessControl.PropagationFlags]::None, [System.Security.AccessControl.AccessControlType]::Allow)
        $newAcl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $targetPath -AclObject $newAcl
}
Write-Output 'Private configuration and runtime ACLs applied; no contents were displayed.'
