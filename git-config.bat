@echo off
REM ============================================================
REM Zhiji - Configure Git User Identity
REM ============================================================

cd /d "%~dp0"

echo ========================================
echo    Zhiji - Git User Setup
echo ========================================
echo.

REM Check if git exists
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found! Please install Git first.
    pause
    exit /b 1
)

echo [OK] Git is installed
echo.

REM Ask for user name
echo Please enter your name:
echo (This will be shown in Git commits)
set /p GIT_NAME=Name: 

if "%GIT_NAME%"=="" (
    echo Using default name: Zhiji User
    set GIT_NAME=Zhiji User
)

REM Ask for email
echo.
echo Please enter your email:
echo (This will be shown in Git commits)
echo Example: yourname@example.com
set /p GIT_EMAIL=Email: 

if "%GIT_EMAIL%"=="" (
    echo Using default email: zhiji@example.com
    set GIT_EMAIL=zhiji@example.com
)

echo.
echo Setting Git user identity...
echo.

REM Set global config
git config --global user.name "%GIT_NAME%"
git config --global user.email "%GIT_EMAIL%"

echo [OK] Git user configured!
echo.

REM Verify
echo Configuration saved:
git config --global user.name
git config --global user.email
echo.

echo ========================================
echo    Setup complete!
echo ========================================
echo.
echo Now you can:
echo 1. Run git-push.bat to commit and push
echo 2. Or continue with your work
echo.
pause
