#!/bin/bash

# ============================================================
# 智记 - Git仓库初始化脚本 (macOS/Linux)
# ============================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "========================================"
echo "   智记 - Git仓库初始化"
echo "========================================"
echo

# 检查是否已初始化Git
if [ -d ".git" ]; then
    echo "[警告] Git仓库已存在！"
    echo
    read -p "是否继续 (y/n)? " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消。"
        exit 1
    fi
    echo
fi

# 检查.gitignore
if [ ! -f ".gitignore" ]; then
    echo "[错误] .gitignore 文件不存在！"
    echo "请确保在项目根目录运行此脚本。"
    exit 1
fi

echo "[1/5] 初始化Git仓库..."
git init
echo "✅ Git仓库已初始化"
echo

echo "[2/5] 添加文件到暂存区..."
git add .
echo "✅ 文件已添加"
echo

echo "[3/5] 创建初始提交..."
if ! git commit -m "Initial commit: 智记iOS项目" 2>/dev/null; then
    echo "[提示] 需要配置Git用户信息"
    echo
    echo "请运行以下命令配置Git："
    echo "  git config user.name \"Your Name\""
    echo "  git config user.email \"your.email@example.com\""
    echo
    exit 1
fi
echo "✅ 初始提交已创建"
echo

echo "[4/5] 显示状态..."
git status
echo

echo "========================================"
echo "   ✅ Git仓库初始化成功！"
echo "========================================"
echo
echo "下一步："
echo "1. 创建远程仓库（GitHub/GitLab/Gitee等）"
echo "2. 添加远程仓库地址："
echo "   git remote add origin <your-repo-url>"
echo "3. 推送到远程："
echo "   git branch -M main"
echo "   git push -u origin main"
echo
