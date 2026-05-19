# ============================================================
# 智记 - Git推送脚本 (PowerShell)
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   智记 - Git推送" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在项目根目录
if (-not (Test-Path ".gitignore")) {
    Write-Host "[错误] 请在项目根目录运行此脚本！" -ForegroundColor Red
    exit 1
}

# 检查Git状态
Write-Host "[1/4] 检查Git状态..." -ForegroundColor Cyan
git status
Write-Host ""

# 检查是否有变更
$status = git status --porcelain
if ($status) {
    Write-Host "[提示] 检测到未提交的变更" -ForegroundColor Yellow
    
    $commitNow = Read-Host "是否提交变更? (y/n)"
    if ($commitNow -eq "y" -or $commitNow -eq "Y") {
        Write-Host ""
        Write-Host "[2/4] 添加文件..." -ForegroundColor Cyan
        git add .
        
        Write-Host ""
        $commitMsg = Read-Host "请输入提交信息"
        if ([string]::IsNullOrWhiteSpace($commitMsg)) {
            $commitMsg = "Update"
        }
        
        Write-Host ""
        Write-Host "[3/4] 提交变更..." -ForegroundColor Cyan
        git commit -m $commitMsg
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[错误] 提交失败！" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "[OK] 变更已提交" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] 没有未提交的变更" -ForegroundColor Green
}

Write-Host ""
Write-Host "[4/4] 推送到远程仓库..." -ForegroundColor Cyan

# 获取当前分支
$branch = git branch --show-current
Write-Host "当前分支: $branch" -ForegroundColor Gray

git push -u origin $branch

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   ✅ 推送成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "下一步（在Mac上）:" -ForegroundColor Yellow
    Write-Host "1. 拉取代码: git pull" -ForegroundColor White
    Write-Host "2. 构建: cd ios; ./scripts/build.sh development" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "[错误] 推送失败！" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的原因:" -ForegroundColor Yellow
    Write-Host "1. 需要先拉取: git pull" -ForegroundColor White
    Write-Host "2. 网络连接问题" -ForegroundColor White
    Write-Host "3. 仓库权限问题" -ForegroundColor White
    Write-Host ""
}
