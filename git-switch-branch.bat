@echo off
REM ============================================================
REM Zhiji - Switch Branch
REM ============================================================

cd /d "%~dp0"

echo ========================================
echo    Zhiji - Switch Branch
echo ========================================
echo.

REM Check git exists
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git not found!
    pause
    exit /b 1
)

echo Current branches:
echo.
git branch
echo.

echo Enter branch name to switch to:
set /p BRANCH_NAME=Branch name: 

if "%BRANCH_NAME%"=="" (
    echo ERROR: Branch name cannot be empty!
    pause
    exit /b 1
)

echo.
echo Switching to: %BRANCH_NAME%
git checkout %BRANCH_NAME%
if errorlevel 1 (
    echo.
    echo ERROR: Failed to switch branch!
    echo Branch may not exist.
) else (
    echo.
    echo ========================================
    echo    Switched to: %BRANCH_NAME%
    echo ========================================
)

echo.
pause
