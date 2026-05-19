@echo off
REM ============================================================
REM Zhiji - Push to Specific Branch
REM ============================================================

cd /d "%~dp0"

echo ========================================
echo    Zhiji - Push to Branch
echo ========================================
echo.

REM Check git exists
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git not found!
    pause
    exit /b 1
)

echo Current branch:
git branch --show-current
echo.

echo Enter branch name to push to (or press Enter for current branch):
set /p BRANCH_NAME=Branch name: 

if "%BRANCH_NAME%"=="" (
    for /f %%i in ('git branch --show-current') do set BRANCH_NAME=%%i
    echo Using current branch: %BRANCH_NAME%
)

echo.
echo Adding files...
git add .
echo OK
echo.

echo Committing...
git commit -m "Update %BRANCH_NAME%" 2>nul
echo OK
echo.

echo Pushing to %BRANCH_NAME%...
git push -u origin %BRANCH_NAME%
if errorlevel 1 (
    echo.
    echo ERROR: Push failed!
) else (
    echo.
    echo ========================================
    echo    SUCCESS! Pushed to %BRANCH_NAME%
    echo ========================================
    echo.
)

echo.
pause
