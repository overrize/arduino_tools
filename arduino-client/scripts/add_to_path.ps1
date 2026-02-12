# Arduino Client - 添加 Scripts 目录到 PATH
# 此脚本会将 arduino-client.exe 所在目录添加到用户 PATH 环境变量

Write-Host "正在查找 arduino-client.exe 安装位置..." -ForegroundColor Cyan

# 查找 arduino-client.exe
$arduinoClientPath = Get-Command arduino-client -ErrorAction SilentlyContinue

if (-not $arduinoClientPath) {
    # 尝试从 pip 获取安装位置
    $pipShow = python -m pip show arduino-client 2>$null
    if ($pipShow) {
        $locationLine = $pipShow | Select-String -Pattern "Location:"
        if ($locationLine) {
            $packageLocation = ($locationLine -split "Location:")[1].Trim()
            $scriptsPath = Join-Path $packageLocation "..\Scripts"
            $scriptsPath = [System.IO.Path]::GetFullPath($scriptsPath)
        }
    }
    
    # 如果还是找不到，尝试常见位置
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
    Write-Host "错误：无法找到 arduino-client.exe 安装位置" -ForegroundColor Red
    Write-Host "请手动运行: python -m arduino_client setup" -ForegroundColor Yellow
    exit 1
}

Write-Host "找到 Scripts 目录: $scriptsPath" -ForegroundColor Green

# 检查是否已在 PATH 中
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -split ';' -contains $scriptsPath) {
    Write-Host "Scripts 目录已在 PATH 中" -ForegroundColor Green
    Write-Host "可以直接使用: arduino-client setup" -ForegroundColor Cyan
    exit 0
}

# 添加到 PATH
Write-Host "正在添加到用户 PATH..." -ForegroundColor Cyan
$newPath = $currentPath + ";" + $scriptsPath
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

Write-Host "✓ 已添加到用户 PATH" -ForegroundColor Green
Write-Host ""
Write-Host "注意：需要重新打开 PowerShell 窗口才能生效" -ForegroundColor Yellow
Write-Host "或者运行以下命令刷新当前会话：" -ForegroundColor Yellow
Write-Host "  `$env:Path = [System.Environment]::GetEnvironmentVariable('Path','User') + ';' + [System.Environment]::GetEnvironmentVariable('Path','Machine')" -ForegroundColor Cyan
Write-Host ""
Write-Host "然后可以运行: arduino-client setup" -ForegroundColor Cyan
