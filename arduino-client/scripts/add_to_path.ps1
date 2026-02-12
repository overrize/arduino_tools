# Arduino Client - Add Scripts directory to PATH
# This script adds the arduino-client.exe directory to user PATH environment variable
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File add_to_path.ps1
#   or
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
#   .\add_to_path.ps1

Write-Host "Finding arduino-client.exe installation location..." -ForegroundColor Cyan

# Find arduino-client.exe
$arduinoClientPath = Get-Command arduino-client -ErrorAction SilentlyContinue

if (-not $arduinoClientPath) {
    # Try to get installation location from pip
    $pipShow = python -m pip show arduino-client 2>$null
    if ($pipShow) {
        $locationLine = $pipShow | Select-String -Pattern "Location:"
        if ($locationLine) {
            $packageLocation = ($locationLine -split "Location:")[1].Trim()
            $scriptsPath = Join-Path $packageLocation "..\Scripts"
            $scriptsPath = [System.IO.Path]::GetFullPath($scriptsPath)
        }
    }
    
    # If still not found, try common locations
    if (-not $scriptsPath) {
        $userProfile = $env:USERPROFILE
        $possiblePaths = @(
            "$userProfile\AppData\Local\Packages\PythonSoftwareFoundation.Python.*\LocalCache\local-packages\Python*\Scripts",
            "$userProfile\AppData\Local\Programs\Python\Python*\Scripts",
            "$userProfile\AppData\Roaming\Python\Python*\Scripts"
        )
        
        foreach ($pattern in $possiblePaths) {
            $found = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq "arduino-client.exe" } | Select-Object -First 1
            if ($found) {
                $scriptsPath = $found.DirectoryName
                break
            }
        }
    }
} else {
    $scriptsPath = Split-Path $arduinoClientPath.Source
}

if (-not $scriptsPath -or -not (Test-Path $scriptsPath)) {
    Write-Host "Error: Cannot find arduino-client.exe installation location" -ForegroundColor Red
    Write-Host "Please run manually: python -m arduino_client setup" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found Scripts directory: $scriptsPath" -ForegroundColor Green

# Check if already in PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathArray = $currentPath -split ';'
if ($pathArray -contains $scriptsPath) {
    Write-Host "Scripts directory is already in PATH" -ForegroundColor Green
    Write-Host "You can use: arduino-client setup" -ForegroundColor Cyan
    exit 0
}

# Add to PATH
Write-Host "Adding to user PATH..." -ForegroundColor Cyan
$newPath = $currentPath + ";" + $scriptsPath
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

Write-Host "Successfully added to user PATH" -ForegroundColor Green
Write-Host ""
Write-Host "Note: You need to reopen PowerShell window for changes to take effect" -ForegroundColor Yellow
Write-Host "Or run this command to refresh current session:" -ForegroundColor Yellow
Write-Host '  $env:Path = [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + [System.Environment]::GetEnvironmentVariable("Path","Machine")' -ForegroundColor Cyan
Write-Host ""
Write-Host "Then you can run: arduino-client setup" -ForegroundColor Cyan
