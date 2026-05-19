@echo off
REM ============================================================
REM 智记 - 设置远程仓库
REM ============================================================

chcp 65001 >nul
title 智记 - 设置远程仓库

cd /d "%~dp0"

echo ========================================
echo    智记 - 设置Git远程仓库
echo ========================================
echo.

REM 使用PowerShell运行脚本
PowerShell -ExecutionPolicy Bypass -File "scripts\setup-remote.ps1"

if errorlevel 1 (
    echo.
    pause
) else (
    echo.
    echo 是否立即推送？
    choice /C YN /M "选择"
    if errorlevel 2 goto end
    if errorlevel 1 goto push
)
goto end

:push
PowerShell -ExecutionPolicy Bypass -File "scripts\push.ps1"

:end
echo.
pause
