@echo off
REM ============================================================
REM Zhiji - Create and Push to New Branch
REM ============================================================

cd /d "%~dp0"

echo ========================================
echo    Zhiji - Create New Branch
echo ========================================
echo.

REM Check git exists
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git not found!
    pause
    exit /b 1
)

echo Enter branch name (e.g., feature/login, fix/bug123):
set /p BRANCH_NAME=Branch name: 

if "%BRANCH_NAME%"=="" (
    echo ERROR: Branch name cannot be empty!
    pause
    exit /b 1
)

echo.
echo Creating branch: %BRANCH_NAME%
git checkout -b %BRANCH_NAME%
if errorlevel 1 (
    echo ERROR: Failed to create branch!
    pause
    exit /b 1
)
echo OK
echo.

echo Adding files...
git add .
echo OK
echo.

echo Committing...
git commit -m "Update branch %BRANCH_NAME%" 2>nul
echo OK
echo.

echo Pushing to remote...
git push -u origin %BRANCH_NAME%
if errorlevel 1 (
    echo.
    echo ERROR: Push failed!
) else (
    echo.
    echo ========================================
    echo    SUCCESS! Branch pushed!
    echo ========================================
    echo.
    echo Branch: %BRANCH_NAME%
    echo.
)

echo.
pause
