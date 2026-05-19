@echo off
REM ============================================================
REM 智记 - 推送到远程仓库
REM ============================================================

chcp 65001 >nul
title 智记 - 推送到远程

cd /d "%~dp0"

echo ========================================
echo    智记 - 推送到远程仓库
echo ========================================
echo.

REM 使用PowerShell运行脚本
PowerShell -ExecutionPolicy Bypass -File "scripts\push.ps1"

echo.
pause
