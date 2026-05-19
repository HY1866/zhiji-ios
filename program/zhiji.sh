#!/bin/bash
# 智记 (ZhiJi) 启动脚本
# 版本: v1.5 (2026-05-18)

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 执行主程序
echo "正在启动智记..."
exec python3 zhiji.py "$@"
