<#
.SYNOPSIS
    Builds native ARM64 release package and MSIX bundle for Microsoft Surface Laptop 7.
.DESCRIPTION
    Compiles AuraCompanion in Release ARM64 configuration, packages with MakeAppx,
    and prepares deployable assets.
#>

param(
    [string]$Configuration = "Release",
    [string]$Platform = "ARM64",
    [string]$OutputDir = "$PSScriptRoot\..\..\dist\ARM64"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Building AURA Companion - Windows on ARM64 Release Build" -ForegroundColor Cyan
Write-Host " Target Architecture: ARM64 (Qualcomm Snapdragon X Elite)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Ensure Output Directories
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$ProjectDir = "$PSScriptRoot\..\..\src\AuraCompanion"

Write-Host "[1/4] Restoring NuGet dependencies for ARM64..." -ForegroundColor Yellow
dotnet restore "$ProjectDir\AuraCompanion.csproj" -r win-arm64

Write-Host "[2/4] Publishing Native ARM64 Binaries with Tiered Compilation & ReadyToRun..." -ForegroundColor Yellow
dotnet publish "$ProjectDir\AuraCompanion.csproj" `
    -c $Configuration `
    -r win-arm64 `
    --self-contained false `
    -p:PlatformTarget=$Platform `
    -p:PublishReadyToRun=true `
    -o "$OutputDir\AppX"

Write-Host "[3/4] Packaging with MakeAppx into MSIX container..." -ForegroundColor Yellow
$MakeAppxCandidates = @(
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\arm64\makeappx.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\makeappx.exe",
    "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x86\makeappx.exe"
)
$MakeAppxPath = $MakeAppxCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $MakeAppxPath) {
    $cmd = Get-Command makeappx.exe -ErrorAction SilentlyContinue
    $MakeAppxPath = if ($cmd) { $cmd.Source } else { "makeappx.exe" }
}

$MsixOutput = "$OutputDir\AuraCompanion_v1.0.0_arm64.msix"
& $MakeAppxPath pack /d "$OutputDir\AppX" /p $MsixOutput /o

Write-Host "[4/4] Release Package created successfully: $MsixOutput" -ForegroundColor Green
Write-Host "Note: To sign for sideloading on Surface Laptop 7, use SignTool with developer certificate or trusted enterprise root." -ForegroundColor Gray
