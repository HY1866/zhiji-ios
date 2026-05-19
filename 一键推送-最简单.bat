@echo off
REM ============================================================
REM Zhiji - ONE-CLICK PUSH (Simplest)
REM ============================================================

cd /d "%~dp0"

echo ========================================
echo    Zhiji - ONE-CLICK PUSH
echo ========================================
echo.

git add .
git commit -m "Update" 2>nul
git push -u origin main

echo.
echo ========================================
echo    Done!
echo ========================================
echo.
echo Check GitHub: https://github.com/HY1866/zhiji-ios
echo.
pause
