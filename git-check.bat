@echo off
REM ============================================================
REM Zhiji - Check Git Status
REM ============================================================

cd /d "%~dp0"

echo ========================================
echo    Zhiji - Git Status Check
echo ========================================
echo.

REM Check if git exists
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found! Please install Git first.
    pause
    exit /b 1
)

echo [1/5] Checking Git installation...
git --version
echo [OK] Git is installed
echo.

echo [2/5] Checking Git repository...
if not exist ".git" (
    echo [ERROR] Git repository not initialized!
    echo Please run git-setup.bat first.
    pause
    exit /b 1
)
echo [OK] Git repository exists
echo.

echo [3/5] Checking remote repository...
git remote >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No remote repository configured!
    echo Please run git-setup.bat first.
) else (
    echo [OK] Remote configured:
    git remote -v
)
echo.

echo [4/5] Checking branch...
for /f %%i in ('git branch --show-current') do set BRANCH=%%i
echo Current branch: %BRANCH%
echo.

echo [5/5] Checking status...
git status
echo.

echo ========================================
echo    Summary
echo ========================================
echo.
git log --oneline -5
echo.
echo ========================================
echo.
echo To verify push success:
echo 1. Visit your repository on GitHub/GitLab
echo 2. Check if commits appear
echo 3. Or run: git log origin/%BRANCH%
echo.
pause
