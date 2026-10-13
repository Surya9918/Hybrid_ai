<#
.SYNOPSIS
    Automated installation script for AURA Companion on Windows on ARM64.
#>

param(
    [string]$PackagePath = "$PSScriptRoot\..\..\dist\ARM64\AuraCompanion_v1.0.0_arm64.msix",
    [switch]$SkipPrereqCheck = $false
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Installing AURA Companion (Hitodama Replica) on ARM64" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not $SkipPrereqCheck) {
    Write-Host "[1/3] Verifying Target Architecture..." -ForegroundColor Yellow
    $arch = $env:PROCESSOR_ARCHITECTURE
    if ($arch -ne "ARM64") {
        Write-Warning "Detected architecture: $arch. AURA Companion is optimized natively for ARM64 Snapdragon X. Execution on x64/x86 will utilize emulation."
    } else {
        Write-Host "Confirmed native ARM64 Qualcomm Snapdragon host." -ForegroundColor Green
    }

    Write-Host "[2/3] Checking Windows App Runtime 1.5..." -ForegroundColor Yellow
    $appRuntime = Get-AppxPackage -Name "Microsoft.WindowsAppRuntime.1.5*" -ErrorAction SilentlyContinue
    if (-not $appRuntime) {
        Write-Host "Windows App Runtime 1.5 not found. Installing via winget..." -ForegroundColor Yellow
        winget install Microsoft.WindowsAppRuntime.1.5 --accept-package-agreements --accept-source-agreements
    } else {
        Write-Host "Windows App Runtime 1.5 verified." -ForegroundColor Green
    }
}

Write-Host "[3/3] Deploying MSIX Package..." -ForegroundColor Yellow
if (Test-Path $PackagePath) {
    Add-AppxPackage -Path $PackagePath
    Write-Host "AURA Companion installed successfully! Launch from Start Menu or press Win+Space." -ForegroundColor Green
} else {
    Write-Warning "Package not found at $PackagePath. Please ensure the build output is present."
}
