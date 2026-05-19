@echo off
REM ============================================================
REM Zhiji - Simple Git Push (No Chinese Issues)
REM ============================================================

cd /d "%~dp0"

echo ========================================
echo    Zhiji - Simple Git Push
echo ========================================
echo.

REM Check git exists
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git not found!
    pause
    exit /b 1
)

echo Step 1: Adding files...
git add .
echo OK
echo.

echo Step 2: Committing...
git commit -m "Update project"
if errorlevel 1 (
    echo No changes to commit, or commit failed.
    echo Continuing anyway...
)
echo OK
echo.

echo Step 3: Pushing...
git push -u origin main
if errorlevel 1 (
    echo.
    echo ERROR: Push failed!
    echo.
    echo Common fixes:
    echo 1. git pull first, then push
    echo 2. Check your internet
    echo 3. Check repository permissions
    echo.
) else (
    echo.
    echo ========================================
    echo    SUCCESS! Push complete!
    echo ========================================
    echo.
    echo Now verify on GitHub:
    echo https://github.com/HY1866/zhiji-ios
    echo.
)

echo.
pause
