@echo off
REM ============================================================
REM Zhiji - Git Push (Simple CMD Version)
REM ============================================================

cd /d "%~dp0"

echo ========================================
echo    Zhiji - Git Push
echo ========================================
echo.

REM Check if Git user is configured
echo Checking Git user configuration...
git config --global user.name >nul 2>&1
if errorlevel 1 (
    echo Git user not configured!
    echo.
    choice /C YN /M "Configure Git user now"
    if errorlevel 2 goto end
    if errorlevel 1 (
        echo.
        call git-config.bat
        echo.
    )
)

REM Check if .gitignore exists
if not exist ".gitignore" (
    echo [ERROR] Please run this script from project root!
    pause
    exit /b 1
)

echo [1/4] Checking Git status...
git status
echo.

REM Check if there are changes
git status --porcelain >nul 2>&1
if not errorlevel 1 (
    echo Changes detected!
    echo.
    choice /C YN /M "Commit changes now"
    if errorlevel 2 goto skip_commit
    if errorlevel 1 (
        echo.
        echo [2/4] Adding files...
        git add .
        
        echo.
        set /p COMMIT_MSG=Enter commit message: 
        if "%COMMIT_MSG%"=="" set COMMIT_MSG=Update
        
        echo.
        echo [3/4] Committing...
        git commit -m "%COMMIT_MSG%"
        
        if errorlevel 1 (
            echo [ERROR] Commit failed!
            pause
            exit /b 1
        )
        
        echo [OK] Changes committed!
    )
) else (
    echo [OK] No uncommitted changes.
)

:skip_commit
echo.
echo [4/4] Pushing to remote...

REM Get current branch
for /f %%i in ('git branch --show-current') do set BRANCH=%%i
echo Current branch: %BRANCH%

git push -u origin %BRANCH%

if errorlevel 1 (
    echo.
    echo [ERROR] Push failed!
    echo.
    echo Possible reasons:
    echo 1. Need to pull first: git pull
    echo 2. Network issue
    echo 3. Permission issue
    echo.
) else (
    echo.
    echo ========================================
    echo    Push SUCCESS!
    echo ========================================
    echo.
    echo Next steps (on Mac):
    echo 1. Pull code: git pull
    echo 2. Build: cd ios; ./scripts/build.sh development
    echo.
)

echo.
pause
