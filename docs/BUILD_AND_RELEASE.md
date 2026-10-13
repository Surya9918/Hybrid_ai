# AURA Companion — Build and Release Guide

**Target Architecture:** Windows on ARM64 (`win-arm64`)  
**Target Hardware:** Microsoft Surface Laptop 7th Edition  

---

## 1. Prerequisites

### Windows on ARM64 Build Machine
- Windows 11 Build 22621 or newer (ARM64 native or x64 cross-compilation host).
- .NET 8.0 SDK (version 8.0.204 or newer).
- Visual Studio 2022 (version 17.10+) with the following workloads:
  - *.NET Desktop Development*
  - *Windows App SDK C# Templates*
  - *MSVC v143 - VS 2022 C++ ARM64 build tools*
- Windows App SDK 1.5 runtime (`Microsoft.WindowsAppRuntime.1.5`).
- Windows 10/11 SDK (10.0.22621.0).

---

## 2. Compilation and Build Commands

### Step 1: Restore Dependencies
From the repository root:
```powershell
dotnet restore src\AuraCompanion\AuraCompanion.csproj -r win-arm64
```

### Step 2: Compile Native ARM64 Release Build
Compile with tiered JIT compilation and ReadyToRun native optimization for Qualcomm Snapdragon X:
```powershell
dotnet publish src\AuraCompanion\AuraCompanion.csproj `
    -c Release `
    -r win-arm64 `
    --self-contained false `
    -p:PlatformTarget=ARM64 `
    -p:PublishReadyToRun=true `
    -o dist\ARM64\AppX
```

---

## 3. Packaging and MSIX Creation

Run the automated packaging script:
```powershell
.\packaging\msix\build_arm64_package.ps1 -Configuration Release -Platform ARM64
```

Under the hood, this executes MakeAppx:
```cmd
makeappx.exe pack /d dist\ARM64\AppX /p dist\ARM64\AuraCompanion_v1.0.0_arm64.msix /o
```

---

## 4. Code Signing Requirements

To sideload or distribute the MSIX package on Windows 11:
1. **Developer / Internal Testing Certificate:**
   ```powershell
   New-SelfSignedCertificate -Type Custom `
       -Subject "CN=AuraOSFoundation, O=AURA, C=US" `
       -KeyUsage DigitalSignature `
       -FriendlyName "AURA Companion ARM64 Dev Cert" `
       -CertStoreLocation "Cert:\CurrentUser\My"
   ```
2. **Sign MSIX Package:**
   ```cmd
   signtool.exe sign /fd SHA256 /a /f AuraDevCert.pfx /p <password> dist\ARM64\AuraCompanion_v1.0.0_arm64.msix
   ```
3. *Production Note:* Enterprise deployments should sign using a trusted commercial code-signing certificate (EV Authenticode).

---

## 5. Upgrade and Rollback Procedures

### Clean Upgrade
1. Run `packaging\scripts\upgrade.ps1 -NewPackagePath "dist\ARM64\AuraCompanion_v1.1.0_arm64.msix"`.
2. The upgrade script backs up the local SQLite database from `%LocalAppData%\Packages\AuraCompanion.Desktop_...\LocalState\aura_companion.db`.
3. Upgrades the MSIX package in place via `Add-AppxPackage -Path ...`.
4. On first launch, automatic database migrations (`schema_migrations`) apply schema changes without data loss.

### Rollback Procedure
1. If a regression occurs, execute:
   ```powershell
   Remove-AppxPackage -Package AuraCompanion.Desktop_1.1.0.0_arm64__...
   Add-AppxPackage -Path "dist\ARM64\AuraCompanion_v1.0.0_arm64.msix"
   ```
2. Restore the backed-up database file to `%LocalAppData%\Packages\AuraCompanion.Desktop_...\LocalState\`.
