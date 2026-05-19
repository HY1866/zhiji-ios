#!/bin/bash
# 智记 (ZhiJi) 一键安装脚本 — 拿到即用，无需手动操作
# 版本: v1.5 (2026-05-18)

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK] $1${NC}"; }
info() { echo -e "${YELLOW}[..] $1${NC}"; }
warn() { echo -e "${YELLOW}[!!] $1${NC}"; }
fail() { echo -e "${RED}[ERR] $1${NC}"; }

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════╗"
echo "║   智记 (ZhiJi) Time Recorder - Installer ║"
echo "║                 v1.5                     ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIP_MIRROR="-i https://pypi.tuna.tsinghua.edu.cn/simple"
ERRORS=0

# ============================================================
# 1. 系统依赖（不卡住，失败只警告）
# ============================================================
info "安装系统依赖..."

SYS_PKGS=""
if command -v apt-get >/dev/null 2>&1; then
    PKGS="python3 python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 ffmpeg alsa-utils"
    NEED=""
    for pkg in $PKGS; do
        if ! dpkg -s "$pkg" >/dev/null 2>&1; then
            NEED="$NEED $pkg"
        fi
    done
    if [ -z "$NEED" ]; then
        ok "系统依赖已全部安装"
    else
        info "需要安装:$NEED"
        sudo apt-get install -y $NEED 2>&1 | while read -r line; do
            case "$line" in
                *Unpacking*|*Setting*|*Processing*) echo -e "${YELLOW}  $line${NC}" ;;
            esac
        done
        ok "系统依赖完成"
    fi
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3 python3-pip python3-gobject gtk3 ffmpeg alsa-utils 2>/dev/null
    ok "系统依赖完成"
elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --noconfirm --needed python python-pip python-gobject gtk3 ffmpeg alsa-utils 2>/dev/null
    ok "系统依赖完成"
else
    warn "未检测到包管理器，跳过系统依赖"
fi

# ============================================================
# 2. Python 依赖（讯飞 WebSocket + Whisper 备选）
# ============================================================
info "安装 Python 依赖..."

for pkg_info in \
    "numpy:import numpy:科学计算基础库(faster-whisper依赖)" \
    "websocket-client:import websocket:讯飞在线识别" \
    "faster-whisper:from faster_whisper import WhisperModel:离线备选识别" \
    "pypinyin:import pypinyin:拼音转换用于匹配" \
    "cffi:import cffi:faster-whisper依赖" \
    "pycparser:import pycparser:cffi依赖"; do
    pkg_name="${pkg_info%%:*}"
    rest="${pkg_info#*:}"
    pkg_check="${rest%%:*}"
    pkg_desc="${rest#*:}"
    if python3 -c "$pkg_check" 2>/dev/null; then
        ok "$pkg_name 已就绪（$pkg_desc）"
    else
        info "安装 $pkg_name ($pkg_desc)..."
        pip3 install --user $PIP_MIRROR --progress-bar on "$pkg_name" 2>&1 | tail -5
        if python3 -c "$pkg_check" 2>/dev/null; then
            ok "$pkg_name 安装成功"
        else
            warn "$pkg_name 安装失败（$pkg_desc 不可用）"
        fi
    fi
done

# ============================================================
# 3. 离线模型下载/更新（可选，跳过不影响讯飞在线识别）
# ============================================================
info "检查离线语音模型..."

WHISPER_MODELS_DIR="${SCRIPT_DIR}/Offline data/whisper-models"
mkdir -p "${WHISPER_MODELS_DIR}"
HAS_MODEL=0
MODEL_NAME=""
MODEL_PATH=""

# 检查现有模型（包括modelscope下载的结构）
for name in small medium base; do
    # 直接目录格式
    model_path="${WHISPER_MODELS_DIR}/${name}"
    if [ -d "$model_path" ] && [ -f "${model_path}/model.bin" ]; then
        MODEL_NAME="${name}"
        MODEL_PATH="${model_path}"
        ok "离线模型已存在: ${name}"
        HAS_MODEL=1
        break
    fi
    # modelscope下载的格式
    modelscope_path="${WHISPER_MODELS_DIR}/Systran/faster-whisper-${name}"
    if [ -d "$modelscope_path" ] && [ -f "${modelscope_path}/model.bin" ]; then
        MODEL_NAME="${name}"
        MODEL_PATH="${modelscope_path}"
        ok "离线模型已存在: ${name} (ModelScope)"
        HAS_MODEL=1
        break
    fi
    # 新格式（huggingface下载）
    hf_path="${WHISPER_MODELS_DIR}/models--Systran--faster-whisper-${name}"
    if [ -d "$hf_path" ]; then
        MODEL_NAME="${name}"
        MODEL_PATH="${hf_path}"
        ok "离线模型已存在: ${name} (HuggingFace)"
        HAS_MODEL=1
        break
    fi
done

# 获取模型修改时间
if [ "$HAS_MODEL" -eq 1 ]; then
    # 尝试查找 model.bin 文件
    if [ -f "${MODEL_PATH}/model.bin" ]; then
        MODEL_BIN="${MODEL_PATH}/model.bin"
    else
        # 在子目录中查找
        MODEL_BIN=$(find "${MODEL_PATH}" -name "model.bin" -type f 2>/dev/null | head -1)
    fi
    
    if [ -n "$MODEL_BIN" ]; then
        MODEL_MTIME=$(stat -c %Y "$MODEL_BIN" 2>/dev/null || stat -f %m "$MODEL_BIN" 2>/dev/null)
        if [ -n "$MODEL_MTIME" ]; then
            MODEL_DATE=$(date -d "@$MODEL_MTIME" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || date -r "$MODEL_MTIME" "+%Y-%m-%d %H:%M:%S" 2>/dev/null)
            if [ -n "$MODEL_DATE" ]; then
                info "模型最后更新: ${MODEL_DATE}"
            fi
        fi
    fi
fi

if [ "$HAS_MODEL" -eq 0 ]; then
    warn "无离线模型（不影响使用，讯飞在线识别为主引擎）"
    info "如需离线备选，可选择以下方式："
    echo -e "  ${CYAN}方式1：${NC}自动下载到 Offline data/whisper-models"
    echo -e "  ${CYAN}方式2：${NC}手动将模型放入 ${WHISPER_MODELS_DIR}"
    echo ""
    
    # 询问是否下载模型
    read -p "是否现在下载离线模型（small，约463MB）？[y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "开始下载模型..."
        # 直接使用faster-whisper的下载功能，指定download_root
        python3 <<'PYTHON_EOF' "${SCRIPT_DIR}"
import os
import sys
from faster_whisper import WhisperModel

# 使用命令行参数传递路径，避免空格问题
SCRIPT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
WHISPER_MODELS_DIR = os.path.join(SCRIPT_DIR, "Offline data", "whisper-models")
os.makedirs(WHISPER_MODELS_DIR, exist_ok=True)

print("正在下载 faster-whisper-small 模型...")
print(f"下载目录: {WHISPER_MODELS_DIR}")

# 直接加载模型会自动下载
model = WhisperModel('small', device='cpu', compute_type='int8', download_root=WHISPER_MODELS_DIR)

print("✅ 模型下载完成！")
PYTHON_EOF
        if [ $? -eq 0 ]; then
            ok "离线模型下载完成！"
        else
            warn "模型下载失败，请检查网络"
        fi
    fi
else
    # 模型已存在，直接使用，先尝试在线检测更新（带超时）
    echo ""
    info "离线模型检测完毕："
    echo -e "  ${CYAN}模型名称:${NC} faster-whisper-${MODEL_NAME}"
    echo -e "  ${CYAN}模型路径:${NC} ${MODEL_PATH}"
    ok "将直接使用本地离线模型"
    echo ""
    
    # 尝试在线检测更新（带10秒超时）
    info "正在尝试在线检测更新（10秒超时）..."
    
    # 使用Python检查是否有更新（超时控制）
    UPDATE_AVAILABLE=$(python3 <<'PYTHON_EOF' 2>/dev/null
import os
import sys
import time

def check_update():
    try:
        from faster_whisper import WhisperModel
        import urllib.request
        import json
        
        # 使用命令行参数传递路径，避免空格问题
        SCRIPT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
        WHISPER_MODELS_DIR = os.path.join(SCRIPT_DIR, "Offline data", "whisper-models")
        MODEL_NAME = sys.argv[2] if len(sys.argv) > 2 else "small"
        
        # 检查本地是否有缓存目录
        repo_id = f"Systran/faster-whisper-{MODEL_NAME}"
        cache_dir = os.path.join(WHISPER_MODELS_DIR, f"models--{repo_id.replace('/', '--')}")
        
        if not os.path.exists(cache_dir):
            return "new_version"
        
        # 尝试检查Hugging Face API（简化）
        try:
            url = f"https://huggingface.co/api/models/{repo_id}"
            with urllib.request.urlopen(url, timeout=8) as response:
                data = json.loads(response.read().decode())
                return "unknown"
        except Exception:
            return "unknown"
    except Exception:
        return "unknown"

try:
    result = check_update()
    print(result)
except Exception:
    print("error")
PYTHON_EOF
    "${SCRIPT_DIR}" "${MODEL_NAME}" || UPDATE_AVAILABLE="error")
    
    case "$UPDATE_AVAILABLE" in
        "timeout"|"error")
            warn "在线检测超时或失败，继续使用本地模型"
            ;;
        "new_version")
            echo ""
            read -p "检测到可能有新版本可用，是否更新？[y/N] " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                info "正在更新模型..."
                info "提示：超时将自动放弃，继续使用本地模型"
                echo ""
                
                # 使用faster-whisper更新，带超时控制
                python3 <<'PYTHON_EOF' "${SCRIPT_DIR}" "${MODEL_NAME}"
import os
import sys
import time

def update_model():
    from faster_whisper import WhisperModel
    
    # 使用命令行参数传递路径，避免空格问题
    SCRIPT_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
    WHISPER_MODELS_DIR = os.path.join(SCRIPT_DIR, "Offline data", "whisper-models")
    MODEL_NAME = sys.argv[2] if len(sys.argv) > 2 else "small"
    
    os.makedirs(WHISPER_MODELS_DIR, exist_ok=True)
    
    print(f"正在更新 faster-whisper-{MODEL_NAME} 模型...")
    print(f"下载目录: {WHISPER_MODELS_DIR}")
    print()
    
    model = WhisperModel(MODEL_NAME, device='cpu', compute_type='int8', download_root=WHISPER_MODELS_DIR)
    print("✅ 模型更新完成！")
    return True

try:
    # 设置全局超时（通过时间检查）
    start_time = time.time()
    result = update_model()
except Exception as e:
    print(f"\n⚠️ 更新失败: {e}，将继续使用本地模型")
PYTHON_EOF
                if [ $? -eq 0 ]; then
                    ok "离线模型更新完成！"
                else
                    warn "模型更新失败或超时，继续使用本地模型"
                fi
            else
                ok "跳过更新，继续使用本地模型"
            fi
            ;;
        *)
            info "未检测到明显更新，继续使用本地模型"
            ;;
    esac
fi

# 检查离线库文件
OFFLINE_LIB="${SCRIPT_DIR}/Offline data/智记_离线库.json"
if [ -f "$OFFLINE_LIB" ]; then
    ok "离线库已存在"
else
    warn "离线库不存在（不影响识别，仅用于结果修正）"
fi

# ============================================================
# 4. 文件权限和目录准备
# ============================================================
info "设置文件权限..."
chmod +x "${SCRIPT_DIR}/zhiji.py" 2>/dev/null
chmod +x "${SCRIPT_DIR}/recognize_zh.py" 2>/dev/null
chmod +x "${SCRIPT_DIR}/zhiji.sh" 2>/dev/null
chmod +x "${SCRIPT_DIR}/install.sh" 2>/dev/null
chmod +x "${SCRIPT_DIR}/test_linux_compatibility.py" 2>/dev/null
ok "文件权限已设置"

# 创建离线数据目录
info "准备离线数据目录..."
mkdir -p "${SCRIPT_DIR}/Offline data" 2>/dev/null
ok "Offline data 目录已就绪"

# 创建文档看板目录
info "准备文档看板目录..."
mkdir -p "${SCRIPT_DIR}/Document Dashboard" 2>/dev/null
ok "Document Dashboard 目录已就绪"

# ============================================================
# 5. 桌面快捷方式
# ============================================================
info "创建桌面快捷方式..."

# 检测桌面目录
if [ -d "${HOME}/Desktop" ]; then
    DESKTOP_DIR="${HOME}/Desktop"
elif [ -d "${HOME}/桌面" ]; then
    DESKTOP_DIR="${HOME}/桌面"
else
    DESKTOP_DIR=$(xdg-user-dir DESKTOP 2>/dev/null || echo "${HOME}")
fi

# 确保图标文件存在
if [ -f "${SCRIPT_DIR}/LOGO.ico" ]; then
    ICON_LINE="Icon=${SCRIPT_DIR}/LOGO.ico"
elif [ -f "${SCRIPT_DIR}/zhiji_icon.png" ]; then
    ICON_LINE="Icon=${SCRIPT_DIR}/zhiji_icon.png"
else
    warn "图标文件不存在"
    ICON_LINE="Icon=accessories-clock"
fi

# 创建桌面文件内容
DESKTOP_CONTENT="[Desktop Entry]
Name=智记
GenericName=时间记录器
Comment=时间记录器+语音识别（支持讯飞在线+Whisper离线）
Exec=${SCRIPT_DIR}/zhiji.sh
${ICON_LINE}
Terminal=false
Type=Application
Categories=Utility;Productivity;AudioVideo;
Keywords=time;record;voice;recognition;
StartupNotify=false
X-GNOME-UsesNotifications=true
StartupWMClass=zhiji"

# 创建桌面快捷方式
DESKTOP_FILE="${DESKTOP_DIR}/zhiji.desktop"
echo "$DESKTOP_CONTENT" > "$DESKTOP_FILE" 2>/dev/null
chmod +x "$DESKTOP_FILE" 2>/dev/null

# 创建应用程序菜单快捷方式
mkdir -p "${HOME}/.local/share/applications" 2>/dev/null
echo "$DESKTOP_CONTENT" > "${HOME}/.local/share/applications/zhiji.desktop" 2>/dev/null

# 信任桌面文件（GNOME/KDE）
if command -v gio >/dev/null 2>&1; then
    gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true
fi

# 更新桌面数据库
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${HOME}/.local/share/applications" 2>/dev/null || true
fi

ok "桌面快捷方式已创建"

# ============================================================
# 6. 验证
# ============================================================
echo ""
info "运行环境检查..."

check_ok=0
check_total=0

for cmd in python3 arecord ffmpeg; do
    check_total=$((check_total+1))
    if command -v $cmd >/dev/null 2>&1; then
        ok "$cmd"
        check_ok=$((check_ok+1))
    else
        fail "$cmd 未找到"
    fi
done

check_total=$((check_total+1))
if python3 -c "import gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk" 2>/dev/null; then
    ok "GTK3"
    check_ok=$((check_ok+1))
else
    fail "GTK3 不可用"
fi

check_total=$((check_total+1))
if python3 -c "import websocket" 2>/dev/null; then
    ok "websocket-client"
    check_ok=$((check_ok+1))
else
    fail "websocket-client"
fi

check_total=$((check_total+1))
if python3 -c "from faster_whisper import WhisperModel" 2>/dev/null; then
    ok "faster-whisper"
    check_ok=$((check_ok+1))
else
    warn "faster-whisper 不可用（仅影响离线识别）"
fi

check_total=$((check_total+1))
if python3 -c "import pypinyin" 2>/dev/null; then
    ok "pypinyin"
    check_ok=$((check_ok+1))
else
    warn "pypinyin 不可用（仅影响离线库匹配）"
fi

echo ""
if [ "$check_ok" -eq "$check_total" ]; then
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  ✔ 智记安装完成！(${check_ok}/${check_total} 通过)${NC}"
    echo -e "${GREEN}${BOLD}════════════════════════════════════════════${NC}"
else
    echo -e "${YELLOW}${BOLD}════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}${BOLD}  ⚠ 安装完成但有警告 (${check_ok}/${check_total} 通过)${NC}"
    echo -e "${YELLOW}${BOLD}════════════════════════════════════════════${NC}"
fi

# ============================================================
# 7. 自动测试语音文件上传到讯飞
# ============================================================
echo ""
info "自动测试语音识别（上传到讯飞）..."

# 优先使用Audio目录下的测试文件（在program目录内）
TEST_AUDIO="${SCRIPT_DIR}/Audio/iflytek02.wav"
if [ ! -f "$TEST_AUDIO" ]; then
    TEST_AUDIO="${SCRIPT_DIR}/Audio/新石记.wav"
fi

if [ -f "$TEST_AUDIO" ]; then
    info "找到测试音频: $(basename "$TEST_AUDIO")"
    info "正在上传到讯飞进行识别..."
    
    python3 "${SCRIPT_DIR}/recognize_zh.py" "$TEST_AUDIO" 2>&1 | while read -r line; do
        echo -e "  ${CYAN}$line${NC}"
    done
    
    # 解析结果
    RECOG_RESULT=$(python3 "${SCRIPT_DIR}/recognize_zh.py" "$TEST_AUDIO" 2>/dev/null)
    if [ -n "$RECOG_RESULT" ]; then
        RECOG_TEXT=$(echo "$RECOG_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('text', ''))" 2>/dev/null || echo "$RECOG_RESULT")
        RECOG_SOURCE=$(echo "$RECOG_RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('source', ''))" 2>/dev/null || echo "xunfei")
        
        if [ -n "$RECOG_TEXT" ] && [ "$RECOG_TEXT" != "null" ]; then
            ok "语音识别成功！"
            echo -e "  ${GREEN}识别结果:${NC} ${RECOG_TEXT}"
            if [ -n "$RECOG_SOURCE" ] && [ "$RECOG_SOURCE" != "null" ]; then
                echo -e "  ${GREEN}识别来源:${NC} ${RECOG_SOURCE}"
            fi
        else
            warn "语音识别未返回文本"
        fi
    else
        warn "语音识别测试失败"
    fi
else
    warn "未找到测试音频文件（跳过测试）"
fi

echo ""
echo -e "${CYAN}启动方式：${NC}"
echo -e "  ${BOLD}方式1：双击桌面「智记」图标${NC}"
echo -e "  ${BOLD}方式2：从应用程序菜单找到「智记」启动${NC}"
echo -e "  ${BOLD}方式3：cd ${SCRIPT_DIR} && python3 zhiji.py${NC}"
echo -e "  ${BOLD}方式4：运行兼容性检测：python3 test_linux_compatibility.py${NC}"
echo ""
echo -e "${CYAN}功能说明：${NC}"
echo -e "  点击「记录」→ 记录当前时间"
echo -e "  点击「语音」→ 开始录音，静音5秒自动停止/最长18秒 → 自动识别文字"
echo -e "  📅 格式按钮 → 切换时间显示格式（中文/ISO）"
echo -e "  ❓ 帮助按钮 → 查看使用说明（支持翻页浏览）"
echo -e "  ↗️ 全屏按钮 → 一键切换全屏，文本可编辑"
echo -e "  🔄 模式切换 → 切换在线/离线识别，自动测试新模式可用性"
echo -e "  左键选中记录，右键菜单 → 修改记录/查看离线库/导出CSV/清空记录"
echo -e "  右键托盘菜单 → 显示窗口/时间格式/重置窗口大小/使用说明/退出"
echo -e "  修改记录会自动学习 → 后续识别会自动应用修正"
echo -e "  编辑记录支持语音输入 → 自动保留原时间戳"
echo -e "  拖拽窗口边缘可调整大小 → 自动保存窗口尺寸和位置"
echo -e "  支持多语音队列识别 → 上条未完成时可继续录音，自动排队处理"
echo -e "  记录保存在 Document Dashboard/时间记录.txt"
echo -e "  配置和离线库保存在项目目录/Offline data/"
echo -e "  识别日志保存在项目目录/Log/，自动保留2天"
echo -e "  Linux兼容性分析报告：Document Dashboard/Linux兼容性分析报告.md"
echo ""
echo -e "${CYAN}语音识别特性：${NC}"
echo -e "  ✅ 讯飞在线识别（首选）- 支持普通话/四川话/河南话"
echo -e "  ✅ Whisper离线识别（备用）- 模型存储在 Offline data/whisper-models"
echo -e "  ✅ 动态口音优先级 - 根据离线库自动调整识别顺序"
echo -e "  ✅ 离线库匹配 - 自动修正识别结果（按口音分类存储）"
echo -e "  ✅ 双引擎自动切换 - 讯飞失败自动切离线识别"
echo -e "  ✅ 模式手动切换 - 可手动选择在线/离线模式，自动测试可用性"
echo -e "  ✅ 多语音队列识别 - 支持连续录音，自动排队依次处理"
echo ""
echo -e "${CYAN}快捷键：${NC}"
echo -e "  Ctrl+S → 保存（全屏模式）"
echo -e "  Esc → 退出全屏"
echo ""
