@echo off
REM ============================================================
REM 智记 - Git仓库初始化脚本 (Windows)
REM ============================================================

chcp 65001 >nul
title 智记 - Git仓库初始化

echo ========================================
echo    智记 - Git仓库初始化
echo ========================================
echo.

cd /d "%~dp0.."

REM 检查是否已初始化Git
if exist ".git" (
    echo [警告] Git仓库已存在！
    echo.
    set /p CONFIRM="是否继续 (y/n)? "
    if /i not "%CONFIRM%"=="y" (
        echo 已取消。
        pause
        exit /b
    )
    echo.
)

REM 检查.gitignore
if not exist ".gitignore" (
    echo [错误] .gitignore 文件不存在！
    echo 请确保在项目根目录运行此脚本。
    pause
    exit /b 1
)

echo [1/5] 初始化Git仓库...
git init
if errorlevel 1 (
    echo [错误] Git初始化失败！
    pause
    exit /b 1
)
echo ✅ Git仓库已初始化
echo.

echo [2/5] 添加文件到暂存区...
git add .
echo ✅ 文件已添加
echo.

echo [3/5] 创建初始提交...
git commit -m "Initial commit: 智记iOS项目"
if errorlevel 1 (
    echo [提示] 需要配置Git用户信息
    echo.
    echo 请运行以下命令配置Git：
    echo   git config user.name "Your Name"
    echo   git config user.email "your.email@example.com"
    echo.
    pause
    exit /b 1
)
echo ✅ 初始提交已创建
echo.

echo [4/5] 显示状态...
git status
echo.

echo ========================================
echo    ✅ Git仓库初始化成功！
echo ========================================
echo.
echo 下一步：
echo 1. 创建远程仓库（GitHub/GitLab/Gitee等）
echo 2. 添加远程仓库地址：
echo    git remote add origin ^<your-repo-url^>
echo 3. 推送到远程：
echo    git push -u origin master
echo.
echo 提示：建议使用main分支
echo   git branch -M main
echo   git push -u origin main
echo.
pause
