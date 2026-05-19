@echo off
REM ============================================================
REM 智记 - 项目打包脚本 (Windows)
REM 用于将项目打包成ZIP文件，方便传输到Mac
REM ============================================================

chcp 65001 >nul
title 智记 - 项目打包

echo ========================================
echo    智记 iOS 项目打包
echo ========================================
echo.

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%
set OUTPUT_DIR=%PROJECT_DIR%..\output
set ZIP_NAME=ZhiJi_iOS_Project.zip
set ZIP_PATH=%OUTPUT_DIR%\%ZIP_NAME%

REM 创建输出目录
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo [INFO] 正在打包项目...
echo.

REM 删除旧的压缩包
if exist "%ZIP_PATH%" (
    echo [INFO] 删除旧的压缩包...
    del "%ZIP_PATH%"
)

REM 使用PowerShell进行压缩
echo [INFO] 正在创建压缩包...
powershell -Command "Compress-Archive -Path '%PROJECT_DIR%*' -DestinationPath '%ZIP_PATH%' -Force"

if exist "%ZIP_PATH%" (
    echo.
    echo ========================================
    echo    ^✅ 打包成功！
    echo ========================================
    echo.
    echo 📦 压缩包位置: %ZIP_PATH%
    echo.
    for %%A in ("%ZIP_PATH%") do (
        echo 📊 文件大小: %%~zA 字节
    )
    echo.
    echo 下一步:
    echo 1. 将 %ZIP_NAME% 传输到Mac
    echo 2. 在Mac上解压
    echo 3. 按照 BUILD_GUIDE.md 进行构建
    echo.
    
    REM 打开输出目录
    explorer "%OUTPUT_DIR%"
) else (
    echo.
    echo ========================================
    echo    ^❌ 打包失败！
    echo ========================================
    echo.
    pause
)

echo.
pause
