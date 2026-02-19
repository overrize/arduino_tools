param([Parameter(Position=0)][string]$Command="status")
$file = ".cursor/state/current-iteration.json"

switch($Command){
    "init" { 
        @{iteration=0;status="pending";current_agent=$null;context=@{
            vision="docs/vision.md";e2e_tests=@("docs/e2e-tests.md")
        }} | ConvertTo-Json | Out-File $file
        Write-Host "✅ 已初始化" -ForegroundColor Green
    }
    "status" { 
        $s = Get-Content $file | ConvertFrom-Json
        Write-Host "迭代: $($s.iteration), 状态: $($s.status), Agent: $($s.current_agent)"
    }
    "next" {
        $s = Get-Content $file | ConvertFrom-Json
        $s.iteration++; $s.status="pending"; $s.current_agent=$null
        $s | ConvertTo-Json | Out-File $file
        Write-Host "🔄 进入迭代 $($s.iteration)"
    }
    "reset" {
        $s = Get-Content $file | ConvertFrom-Json
        $s.status="pending"; $s.current_agent=$null
        $s | ConvertTo-Json | Out-File $file
        Write-Host "🔄 已重置"
    }
}