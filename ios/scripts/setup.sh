#!/bin/bash

# ============================================================
# 智记 - iOS项目设置脚本
# ============================================================

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "========================================"
echo "  智记 iOS 项目设置"
echo "========================================"
echo

# 检查macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    log_error "此脚本需要在macOS上运行"
    exit 1
fi

# 检查Xcode
if ! command -v xcodebuild &> /dev/null; then
    log_error "Xcode未安装，请从App Store安装Xcode"
    exit 1
fi

log_info "Xcode版本:"
xcodebuild -version
echo

# 检查项目文件
PROJECT_FILE="$PROJECT_DIR/ZhiJi.xcodeproj"
if [[ ! -d "$PROJECT_FILE" ]]; then
    log_error "项目文件不存在: $PROJECT_FILE"
    exit 1
fi

log_info "✅ 项目文件检查通过"

# 设置脚本权限
chmod +x "$SCRIPT_DIR/build.sh"
log_info "✅ 构建脚本权限已设置"

# 检查讯飞SDK
LIB_DIR="$PROJECT_DIR/../lib"
if [[ -d "$LIB_DIR" && -d "$LIB_DIR/iflyMSC.framework" ]]; then
    log_info "✅ 讯飞SDK已找到"
else
    log_warning "讯飞SDK未找到，语音识别功能将无法使用"
fi

echo
echo "========================================"
echo "  ✅ 设置完成！"
echo "========================================"
echo
echo "下一步操作："
echo "1. 打开项目: open $PROJECT_FILE"
echo "2. 在Xcode中配置您的开发团队"
echo "3. 修改Bundle Identifier"
echo "4. 运行构建脚本: $SCRIPT_DIR/build.sh"
echo
echo "更多信息请查看 $PROJECT_DIR/README.md"
echo
