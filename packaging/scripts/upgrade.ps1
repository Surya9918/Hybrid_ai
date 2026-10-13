<#
.SYNOPSIS
    Automated upgrade and migration script for AURA Companion on Windows on ARM64.
.DESCRIPTION
    Safely backs up local SQLite database state, deploys new MSIX package,
    and supports automated rollback in the event of an upgrade failure.
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$NewPackagePath,
    [string]$BackupDir = "$env:TEMP\AuraCompanion_Backup"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Upgrading AURA Companion (Hitodama Replica) on ARM64" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path $NewPackagePath)) {
    Write-Error "Package not found at: $NewPackagePath"
}

# 1. Locate local state and back up database
$localStateDir = "$env:LOCALAPPDATA\Packages\AuraCompanion.Desktop_8wekyb3d8bbwe\LocalState"
$dbFile = Join-Path $localStateDir "aura_companion.db"

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$backupFile = Join-Path $BackupDir "aura_companion_backup_$timestamp.db"

if (Test-Path $dbFile) {
    Write-Host "[1/3] Backing up SQLite database to $backupFile..." -ForegroundColor Yellow
    Copy-Item -Path $dbFile -Destination $backupFile -Force
    Write-Host "Backup completed successfully." -ForegroundColor Green
} else {
    Write-Host "[1/3] No existing database found at $dbFile (fresh install)." -ForegroundColor Yellow
}

# 2. Deploy updated package
Write-Host "[2/3] Installing updated MSIX package: $NewPackagePath..." -ForegroundColor Yellow
try {
    Add-AppxPackage -Path $NewPackagePath -ForceUpdateFromAnyVersion
    Write-Host "MSIX package upgraded successfully." -ForegroundColor Green
} catch {
    Write-Warning "Upgrade deployment failed: $_"
    if (Test-Path $backupFile) {
        Write-Host "Initiating rollback: restoring database from $backupFile..." -ForegroundColor Yellow
        Copy-Item -Path $backupFile -Destination $dbFile -Force
    }
    throw $_
}

# 3. Final verification
Write-Host "[3/3] Upgrade complete! Launch AURA Companion from Start or Win+Space." -ForegroundColor Cyan
