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

# Verify arduino-client.exe actually exists
$arduinoClientExe = Join-Path $scriptsPath "arduino-client.exe"
if (-not (Test-Path $arduinoClientExe)) {
    Write-Host "Warning: arduino-client.exe not found in Scripts directory" -ForegroundColor Yellow
    Write-Host "Scripts directory: $scriptsPath" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Please reinstall arduino-client:" -ForegroundColor Yellow
    Write-Host "  pip install -e arduino-client/ --force-reinstall" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or use: python -m arduino_client setup" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found Scripts directory: $scriptsPath" -ForegroundColor Green
Write-Host "Found arduino-client.exe: $arduinoClientExe" -ForegroundColor Green

# Check if already in PATH (user environment variable)
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathArray = $currentPath -split ';'
if ($pathArray -contains $scriptsPath) {
    Write-Host "Scripts directory is already in user PATH" -ForegroundColor Green
    
    # Even if in user PATH, refresh current session PATH
    Write-Host "Refreshing current session PATH..." -ForegroundColor Cyan
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + [System.Environment]::GetEnvironmentVariable("Path","Machine")
    
    # Verify arduino-client is now available
    $arduinoClientCheck = Get-Command arduino-client -ErrorAction SilentlyContinue
    if ($arduinoClientCheck) {
        Write-Host "✓ arduino-client is now available!" -ForegroundColor Green
        Write-Host ""
        Write-Host "You can now run:" -ForegroundColor Cyan
        Write-Host "  arduino-client setup" -ForegroundColor Yellow
        Write-Host "  arduino-client --version" -ForegroundColor Yellow
    } else {
        Write-Host "⚠ Warning: arduino-client still not found after refreshing PATH" -ForegroundColor Yellow
        Write-Host "Please verify the Scripts directory contains arduino-client.exe:" -ForegroundColor Yellow
        Write-Host "  $scriptsPath" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "If the file exists, try closing and reopening PowerShell window" -ForegroundColor Yellow
    }
    exit 0
}

# Add to PATH
Write-Host "Adding to user PATH..." -ForegroundColor Cyan
$newPath = $currentPath + ";" + $scriptsPath
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

Write-Host "Successfully added to user PATH" -ForegroundColor Green
Write-Host ""

# Refresh current session PATH
Write-Host "Refreshing current session PATH..." -ForegroundColor Cyan
$userPath = [System.Environment]::GetEnvironmentVariable("Path","User")
$machinePath = [System.Environment]::GetEnvironmentVariable("Path","Machine")
$env:Path = $userPath + ";" + $machinePath

# Also explicitly add scriptsPath to current session if not already there
$currentSessionPath = $env:Path -split ';'
if ($currentSessionPath -notcontains $scriptsPath) {
    $env:Path = $env:Path + ";" + $scriptsPath
    Write-Host "Added to current session PATH: $scriptsPath" -ForegroundColor Cyan
}

# Verify arduino-client is now available
# Clear command cache and wait
$null = Get-Command arduino-client -ErrorAction SilentlyContinue  # Force cache refresh
Start-Sleep -Milliseconds 1000  # Give PowerShell time to refresh command cache

# Try Get-Command first
$arduinoClientCheck = Get-Command arduino-client -ErrorAction SilentlyContinue
if ($arduinoClientCheck) {
    Write-Host "✓ arduino-client is now available!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now run:" -ForegroundColor Cyan
    Write-Host "  arduino-client setup" -ForegroundColor Yellow
    Write-Host "  arduino-client --version" -ForegroundColor Yellow
    Write-Host ""
    # Test the command directly
    Write-Host "Testing command..." -ForegroundColor Cyan
    try {
        $version = & arduino-client --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $version) {
            Write-Host "Command test successful: $version" -ForegroundColor Green
        } else {
            Write-Host "Command test: Command found but execution may have issues" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Command test failed: $_" -ForegroundColor Yellow
        Write-Host "Try using direct path: & '$arduinoClientExe' --version" -ForegroundColor Cyan
    }
} else {
    # If Get-Command fails, try direct execution
    Write-Host "Get-Command failed, trying direct execution..." -ForegroundColor Yellow
    try {
        $testResult = & $arduinoClientExe --version 2>&1
        if ($LASTEXITCODE -eq 0 -or $testResult) {
            Write-Host "✓ Direct execution works! Command is available at:" -ForegroundColor Green
            Write-Host "  $arduinoClientExe" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Note: PowerShell command cache may need a new session to refresh." -ForegroundColor Yellow
            Write-Host "You can use the direct path or close/reopen PowerShell window." -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Or use: python -m arduino_client setup" -ForegroundColor Cyan
        } else {
            throw "Direct execution also failed"
        }
    } catch {
        Write-Host "⚠ Warning: arduino-client still not found after refreshing PATH" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "  1. Verify file exists: Test-Path '$arduinoClientExe'" -ForegroundColor Cyan
        Write-Host "  2. Current PATH contains Scripts: `$env:Path -split ';' | Select-String '$scriptsPath'" -ForegroundColor Cyan
        Write-Host "  3. Try direct path: & '$arduinoClientExe' --version" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Recommended: Close and reopen PowerShell window, or use:" -ForegroundColor Yellow
        Write-Host "  python -m arduino_client setup" -ForegroundColor Cyan
    }
}
