@echo off
REM ============================================================
REM Zhiji - Quick Verify Push Success
REM ============================================================

cd /d "%~dp0"

cls
echo ========================================
echo    Zhiji - Quick Verification
echo ========================================
echo.

REM Check 1: Git installation
echo [Check 1/5] Git installation...
git --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Git not found!
    echo Please install Git from https://git-scm.com/
    goto end
)
git --version
echo [OK] Git is installed
echo.

REM Check 2: Repository exists
echo [Check 2/5] Git repository...
if not exist ".git" (
    echo [FAIL] Repository not initialized!
    echo Please run git-setup.bat first.
    goto end
)
echo [OK] Repository exists
echo.

REM Check 3: Remote configured
echo [Check 3/5] Remote repository...
git remote >nul 2>&1
if errorlevel 1 (
    echo [FAIL] No remote configured!
    echo Please run git-setup.bat first.
    goto end
)
echo [OK] Remote configured:
git remote -v
echo.

REM Check 4: Commits exist
echo [Check 4/5] Commits...
git log --oneline >nul 2>&1
if errorlevel 1 (
    echo [FAIL] No commits found!
    echo Please run git-push.bat first.
    goto end
)
echo [OK] Commits found:
git log --oneline -3
echo.

REM Check 5: Remote has commits
echo [Check 5/5] Checking remote...
echo.
echo ========================================
echo    VERIFICATION METHODS
echo ========================================
echo.
echo Method 1 (Recommended):
echo   Visit: https://github.com/HY1866/zhiji-ios
echo   Check if files appear on GitHub
echo.
echo Method 2 (Git Command):
echo   git log origin/main --oneline
echo.
echo Method 3 (Full Check):
echo   Run: git-check.bat
echo.
echo Method 4 (Verify on Mac):
echo   git clone https://github.com/HY1866/zhiji-ios.git
echo.
echo ========================================
echo.
echo Press any key to test fetching from remote...
pause >nul

echo.
echo Testing connection to remote...
git fetch origin
if errorlevel 1 (
    echo [FAIL] Could not fetch from remote!
    echo Check your internet connection and repository URL.
) else (
    echo [OK] Connection successful!
    echo.
    git log origin/main --oneline -3
    echo.
    echo ========================================
    echo    If you see commits above, PUSH SUCCESS!
    echo ========================================
)

:end
echo.
echo For more details, see: 验证推送成功.md
echo.
pause
