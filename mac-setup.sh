#!/bin/bash
# ============================================================
# Zhiji - Mac Quick Setup Script
# ============================================================

echo "========================================"
echo "   Zhiji - Mac Quick Setup"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "ios" ]; then
    echo "ERROR: Please run this script from the project root directory!"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "[1/5] Checking for Xcode..."
if ! command -v xcodebuild &> /dev/null; then
    echo "ERROR: Xcode not found!"
    echo "Please install Xcode from the Mac App Store."
    exit 1
fi
XCODE_VERSION=$(xcodebuild -version | head -n 1)
echo "OK: $XCODE_VERSION"
echo ""

echo "[2/5] Checking git..."
if ! command -v git &> /dev/null; then
    echo "ERROR: Git not found!"
    exit 1
fi
GIT_VERSION=$(git --version)
echo "OK: $GIT_VERSION"
echo ""

echo "[3/5] Entering ios directory..."
cd ios || exit 1
echo "OK"
echo ""

echo "[4/5] Checking Xcode project..."
if [ ! -f "ZhiJi.xcodeproj/project.pbxproj" ]; then
    echo "ERROR: Xcode project not found!"
    exit 1
fi
echo "OK: ZhiJi.xcodeproj found"
echo ""

echo "[5/5] Making scripts executable..."
chmod +x scripts/*.sh
echo "OK"
echo ""

echo "========================================"
echo "   Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Open Xcode project:"
echo "   open ZhiJi.xcodeproj"
echo ""
echo "2. Or in Xcode:"
echo "   - Open ios/ZhiJi.xcodeproj"
echo "   - Configure signing (select Team)"
echo "   - Connect your iOS device"
echo "   - Click Run (Cmd+R)"
echo ""
echo "3. Or use build script:"
echo "   ./scripts/build.sh development"
echo ""
echo "4. For detailed instructions:"
echo "   See ../iOS部署到设备指南.md"
echo ""

# Ask if user wants to open Xcode
read -p "Open Xcode project now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open ZhiJi.xcodeproj
fi
