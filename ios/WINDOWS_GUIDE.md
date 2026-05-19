# Windows 用户指南

## ⚠️ 重要提示

iOS应用的**构建和编译必须在macOS系统上完成**，无法在Windows上直接生成.ipa文件。

---

## 您有以下几种选择

### 选择一：使用Mac进行构建（推荐）

如果您有Mac电脑，请：

1. 将整个 `ios/` 文件夹复制到Mac
2. 在Mac上打开 `ios/ZhiJi.xcodeproj`
3. 按照 `BUILD_GUIDE.md` 的步骤进行构建

### 选择二：使用虚拟机安装macOS

在Windows上使用虚拟机软件安装macOS：
- VMware Workstation
- VirtualBox
- Parallels Desktop（需要Mac）

⚠️ 注意：在非Apple硬件上运行macOS可能违反Apple的许可协议。

### 选择三：使用Mac云服务

使用在线Mac云服务：
- MacStadium
- MacinCloud
- CircleCI（CI/CD服务）

### 选择四：找有Mac的朋友帮忙

将项目文件发送给有Mac的朋友，让他们帮忙构建。

---

## 项目文件已准备好！✅

所有需要的文件都已在 `ios/` 目录下：

```
ios/
├── ZhiJi.xcodeproj/          # ✅ Xcode项目文件
├── ZhiJi/                    # ✅ 源代码
├── scripts/                  # ✅ 自动化脚本
├── BUILD_GUIDE.md           # ✅ 构建指南
├── README.md                # ✅ 项目说明
└── WINDOWS_GUIDE.md         # ✅ 本文档
```

---

## 传输项目到Mac的方法

### 方法一：USB闪存盘
1. 将整个 `ios/` 文件夹复制到U盘
2. 在Mac上打开并继续构建

### 方法二：云存储
1. 上传 `ios/` 文件夹到云盘（百度云、OneDrive、Dropbox等）
2. 在Mac上下载

### 方法三：Git仓库
```bash
# 在Windows上
cd ios
git init
git add .
git commit -m "Initial commit"
# 推送到GitHub/GitLab等

# 在Mac上
git clone <your-repo-url>
```

### 方法四：局域网共享
1. 在Windows上共享 `ios/` 文件夹
2. 在Mac上通过网络访问

---

## 在Mac上的快速步骤（备忘）

当您在Mac上时，请按以下顺序操作：

```bash
# 1. 进入项目目录
cd ios

# 2. 运行设置脚本
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. 打开Xcode项目
open ZhiJi.xcodeproj

# 4. 在Xcode中配置签名和Bundle ID

# 5. 运行构建脚本
./scripts/build.sh development
```

详细步骤请查看 `BUILD_GUIDE.md`。

---

## 项目预览

虽然无法在Windows上构建，但您可以：

- ✅ 查看和编辑Swift源代码
- ✅ 检查项目配置
- ✅ 准备讯飞SDK
- ✅ 准备应用图标和资源

---

## 讯飞SDK准备

如果要使用语音识别功能，请确保：

1. `../lib/iflyMSC.framework` 存在
2. 已获取讯飞AppID
3. 准备好在Mac上集成SDK

---

## 需要帮助？

如果您有Mac但在构建过程中遇到问题，请：

1. 查看 `BUILD_GUIDE.md`
2. 查看 `README.md`
3. 检查Xcode日志输出

---

## 总结

虽然无法在Windows上直接生成.ipa文件，但：

✅ 所有项目文件已准备完毕  
✅ 提供了完整的构建指南  
✅ 提供了自动化脚本  
✅ 只需要在Mac上完成最后几步  

祝您构建顺利！🎉

当您在Mac上时，请查看 `BUILD_GUIDE.md` 获取详细构建步骤。
