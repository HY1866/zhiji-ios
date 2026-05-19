@echo off
REM ============================================================
REM Zhiji - Setup Git Remote (Simple CMD Version)
REM ============================================================

cd /d "%~dp0"

echo ========================================
echo    Zhiji - Setup Git Remote
echo ========================================
echo.

REM Check if .gitignore exists
if not exist ".gitignore" (
    echo [ERROR] Please run this script from project root!
    pause
    exit /b 1
)

REM Check if git exists
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found! Please install Git first.
    pause
    exit /b 1
)

echo [OK] Git is installed
echo.

REM Check if Git user is configured
echo Checking Git user configuration...
git config --global user.name >nul 2>&1
if errorlevel 1 (
    echo Git user not configured!
    echo.
    choice /C YN /M "Configure Git user now"
    if errorlevel 2 goto skip_config
    if errorlevel 1 (
        echo.
        call git-config.bat
        echo.
    )
)
:skip_config

REM Check if .git exists
if not exist ".git" (
    echo Git repository not initialized.
    echo Initializing Git repository...
    echo.
    
    git init
    echo.
    
    echo Adding files...
    git add .
    echo.
    
    echo Creating initial commit...
    git commit -m "Initial commit: Zhiji iOS Project"
    echo.
    
    echo Switching to main branch...
    git branch -M main
    echo.
    
    echo [OK] Git initialized!
    echo.
)

REM Ask for remote URL
echo Please enter your Git repository URL:
echo Example: https://github.com/yourusername/zhiji-ios.git
set /p REMOTE_URL=URL: 

if "%REMOTE_URL%"=="" (
    echo [ERROR] URL cannot be empty!
    pause
    exit /b 1
)

echo.

REM Check if origin already exists
git remote >nul 2>&1
for /f %%i in ('git remote') do (
    if "%%i"=="origin" (
        echo Remote 'origin' already exists.
        choice /C YN /M "Overwrite it"
        if errorlevel 2 goto end
        if errorlevel 1 (
            git remote remove origin
            echo.
        )
    )
)

echo Adding remote repository...
git remote add origin "%REMOTE_URL%"

if errorlevel 1 (
    echo [ERROR] Failed to add remote!
    pause
    exit /b 1
)

echo [OK] Remote added!
echo.
git remote -v
echo.

echo ========================================
echo    Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Push to remote: git push -u origin main
echo 2. Or run git-push.bat
echo.

choice /C YN /M "Push now"
if errorlevel 2 goto end
if errorlevel 1 goto push

:push
echo.
call git-push.bat

:end
echo.
pause
