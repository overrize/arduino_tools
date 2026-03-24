# 检查并安装 Visual C++ Redistributable
$vcRedist = Get-WmiObject -Class Win32_Product | Where-Object { $_.Name -like "*Visual C++*Redistributable*" }

if (-not $vcRedist) {
    Write-Host "正在下载 Visual C++ Redistributable..."
    $url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    $output = "$env:TEMP\vc_redist.x64.exe"
    
    Invoke-WebRequest -Uri $url -OutFile $output
    
    Write-Host "正在安装 Visual C++ Redistributable..."
    Start-Process -FilePath $output -ArgumentList "/install", "/quiet", "/norestart" -Wait
    
    Write-Host "安装完成！"
} else {
    Write-Host "Visual C++ Redistributable 已安装"
}

# 检查 Rust
$rust = Get-Command rustc -ErrorAction SilentlyContinue
if (-not $rust) {
    Write-Host "未检测到 Rust，请先安装: https://rustup.rs/"
    exit 1
}

Write-Host "环境检查完成！"
