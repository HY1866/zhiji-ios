# ============================================================
# 智记 - 设置Git远程仓库脚本 (PowerShell)
# ============================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   智记 - 设置Git远程仓库" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在项目根目录
if (-not (Test-Path ".gitignore")) {
    Write-Host "[错误] 请在项目根目录运行此脚本！" -ForegroundColor Red
    Write-Host "当前目录: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# 检查Git是否安装
try {
    $gitVersion = git --version 2>&1
    Write-Host "[OK] Git已安装: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未找到Git，请先安装Git！" -ForegroundColor Red
    exit 1
}

# 检查是否已初始化Git
if (-not (Test-Path ".git")) {
    Write-Host "[提示] Git仓库未初始化" -ForegroundColor Yellow
    $init = Read-Host "是否初始化Git仓库? (y/n)"
    if ($init -eq "y" -or $init -eq "Y") {
        Write-Host ""
        Write-Host "[1/4] 初始化Git仓库..." -ForegroundColor Cyan
        git init
        Write-Host "[OK] Git仓库已初始化" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "[2/4] 添加文件..." -ForegroundColor Cyan
        git add .
        Write-Host "[OK] 文件已添加" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "[3/4] 创建提交..." -ForegroundColor Cyan
        git commit -m "Initial commit: 智记iOS项目"
        Write-Host "[OK] 初始提交已创建" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "[4/4] 切换到main分支..." -ForegroundColor Cyan
        git branch -M main
        Write-Host "[OK] 已切换到main分支" -ForegroundColor Green
    } else {
        Write-Host "已取消。" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "请输入Git远程仓库URL" -ForegroundColor Cyan
Write-Host "例如: https://github.com/你的用户名/zhiji-ios.git" -ForegroundColor Gray
$remoteUrl = Read-Host "远程仓库URL"

if ([string]::IsNullOrWhiteSpace($remoteUrl)) {
    Write-Host "[错误] URL不能为空！" -ForegroundColor Red
    exit 1
}

# 检查是否已存在远程仓库
try {
    $existingRemotes = git remote
    if ($existingRemotes -contains "origin") {
        Write-Host ""
        Write-Host "[提示] 远程仓库 'origin' 已存在" -ForegroundColor Yellow
        $override = Read-Host "是否覆盖? (y/n)"
        if ($override -eq "y" -or $override -eq "Y") {
            git remote remove origin
            Write-Host "[OK] 已删除旧的远程仓库" -ForegroundColor Green
        } else {
            Write-Host "已取消。" -ForegroundColor Yellow
            exit 0
        }
    }
} catch {
    # 忽略错误
}

Write-Host ""
Write-Host "正在添加远程仓库..." -ForegroundColor Cyan
git remote add origin $remoteUrl

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] 远程仓库已添加" -ForegroundColor Green
    Write-Host ""
    Write-Host "远程仓库信息:" -ForegroundColor Cyan
    git remote -v
} else {
    Write-Host "[错误] 添加远程仓库失败！" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ✅ 远程仓库设置成功！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步操作：" -ForegroundColor Yellow
Write-Host "1. 推送到远程仓库:" -ForegroundColor White
Write-Host "   git push -u origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 或者运行推送脚本:" -ForegroundColor White
Write-Host "   .\scripts\push.ps1" -ForegroundColor Gray
Write-Host ""
