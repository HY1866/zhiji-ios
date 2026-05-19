@echo off
REM ============================================================
REM Zhiji - Initial Push (One-Click)
REM ============================================================

cd /d "%~dp0"

echo ========================================
echo    Zhiji - Initial Push
echo ========================================
echo.

REM Check git exists
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git not found!
    pause
    exit /b 1
)

echo [1/4] Initializing repository (if needed)...
if not exist ".git" (
    git init
)
echo OK
echo.

echo [2/4] Adding files...
git add .
echo OK
echo.

echo [3/4] Creating commit...
git commit -m "Initial commit: Zhiji iOS Project"
if errorlevel 1 (
    echo Commit may already exist, continuing...
)
echo OK
echo.

echo [4/4] Pushing to remote...
git push -u origin main
if errorlevel 1 (
    echo.
    echo ERROR: Push failed!
    echo.
    echo Please check:
    echo 1. Is remote repository set?
    echo    Run: git remote -v
    echo 2. Is repository URL correct?
    echo 3. Do you have internet access?
    echo.
    echo If remote not set, run:
    echo git remote add origin https://github.com/HY1866/zhiji-ios.git
    echo.
) else (
    echo.
    echo ========================================
    echo    SUCCESS! PUSH COMPLETE!
    echo ========================================
    echo.
    echo Now check GitHub:
    echo https://github.com/HY1866/zhiji-ios
    echo.
    echo Then run:
    echo 快速验证.bat
    echo.
)

echo.
pause
