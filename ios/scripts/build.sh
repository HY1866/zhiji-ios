#!/bin/bash

# ============================================================
# 智记 - iOS应用构建脚本
# 使用方法: ./build.sh [development|app-store|ad-hoc|enterprise]
# ============================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_NAME="ZhiJi"
SCHEME_NAME="ZhiJi"
BUILD_DIR="$PROJECT_DIR/build"
ARCHIVE_PATH="$BUILD_DIR/$PROJECT_NAME.xcarchive"
EXPORT_PATH="$BUILD_DIR/export"
EXPORT_PLIST="$SCRIPT_DIR/ExportOptions.plist"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否在macOS上
if [[ "$OSTYPE" != "darwin"* ]]; then
    log_error "此脚本需要在macOS上运行"
    exit 1
fi

# 检查Xcode是否安装
if ! command -v xcodebuild &> /dev/null; then
    log_error "Xcode未安装，请先安装Xcode"
    exit 1
fi

# 获取导出方式
EXPORT_METHOD="${1:-development}"
case "$EXPORT_METHOD" in
    development|app-store|ad-hoc|enterprise)
        log_info "使用导出方式: $EXPORT_METHOD"
        ;;
    *)
        log_error "无效的导出方式: $EXPORT_METHOD"
        echo "可用选项: development, app-store, ad-hoc, enterprise"
        exit 1
        ;;
esac

# 更新ExportOptions.plist中的method
if [[ -f "$EXPORT_PLIST" ]]; then
    if command -v plutil &> /dev/null; then
        plutil -replace method -string "$EXPORT_METHOD" "$EXPORT_PLIST"
        log_info "已更新导出方式为: $EXPORT_METHOD"
    fi
fi

# 创建构建目录
mkdir -p "$BUILD_DIR"
mkdir -p "$EXPORT_PATH"

cd "$PROJECT_DIR"

# 清理旧的构建
log_info "清理旧的构建文件..."
xcodebuild clean -project "$PROJECT_NAME.xcodeproj" -scheme "$SCHEME_NAME" -configuration Release

# 归档项目
log_info "开始归档项目..."
xcodebuild archive \
    -project "$PROJECT_NAME.xcodeproj" \
    -scheme "$SCHEME_NAME" \
    -configuration Release \
    -archivePath "$ARCHIVE_PATH"

if [ $? -eq 0 ]; then
    log_info "归档成功！"
else
    log_error "归档失败"
    exit 1
fi

# 导出.ipa
log_info "开始导出.ipa文件..."
xcodebuild -exportArchive \
    -archivePath "$ARCHIVE_PATH" \
    -exportOptionsPlist "$EXPORT_PLIST" \
    -exportPath "$EXPORT_PATH"

if [ $? -eq 0 ]; then
    log_info "导出成功！"
    
    IPA_FILE=$(find "$EXPORT_PATH" -name "*.ipa" | head -1)
    if [ -f "$IPA_FILE" ]; then
        log_info ".ipa文件位置: $IPA_FILE"
        echo
        echo "========================================"
        echo "  ✅ 构建成功！"
        echo "  📦 .ipa文件: $IPA_FILE"
        echo "  📦 归档文件: $ARCHIVE_PATH"
        echo "========================================"
        echo
        # 在Finder中显示
        open -R "$IPA_FILE" 2>/dev/null || true
    fi
else
    log_error "导出失败"
    exit 1
fi
