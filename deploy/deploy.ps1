# Upload tracked files using OpenSSH keys; no passwords in command arguments.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9.-]*$')][string]$ServerHost,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z_][A-Za-z0-9_-]*$')][string]$SshUser
)
$ErrorActionPreference = 'Stop'
$projectPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$target = "${SshUser}@${ServerHost}"
$sshOptions = @('-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes')
$archivePath = Join-Path ([System.IO.Path]::GetTempPath()) ("msi-hbp-" + [guid]::NewGuid().ToString('N') + '.tar')
try {
    & git -C $projectPath archive --format=tar --output=$archivePath HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the tracked-file archive.' }
    & ssh @sshOptions $target 'mkdir -p /opt/msi-hbp'
    if ($LASTEXITCODE -ne 0) { throw 'SSH connection or directory creation failed.' }
    & scp @sshOptions $archivePath "${target}:/opt/msi-hbp/upload.tar"
    if ($LASTEXITCODE -ne 0) { throw 'Upload failed.' }
    & ssh @sshOptions $target 'tar -xf /opt/msi-hbp/upload.tar -C /opt/msi-hbp && rm /opt/msi-hbp/upload.tar'
    if ($LASTEXITCODE -ne 0) { throw 'Archive extraction failed.' }
    Write-Host 'Tracked files uploaded. Configure the server-local .env, then run deploy/deploy.sh on the server.'
} finally {
    if (Test-Path -LiteralPath $archivePath) { Remove-Item -LiteralPath $archivePath }
}
