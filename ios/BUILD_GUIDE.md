# 智记 iOS 构建指南

本指南将帮助您在macOS上构建智记iOS应用并生成.ipa安装文件。

## 前置条件

### 必需
- ✅ macOS 12.0 或更高版本
- ✅ Xcode 14.0 或更高版本
- ✅ Apple Developer 账号（用于签名）
- ✅ iOS 设备（用于真机测试）

### 可选
- 讯飞语音SDK（用于语音识别功能）

---

## 快速开始

### 方法一：使用自动化脚本（推荐）

```bash
# 1. 进入项目目录
cd ios

# 2. 运行设置脚本
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. 打开Xcode项目进行配置
open ZhiJi.xcodeproj

# 4. 配置完成后运行构建脚本
./scripts/build.sh development
```

### 方法二：手动构建

请参考下面的「详细步骤」部分。

---

## 详细步骤

### 第一步：配置项目

1. **打开项目**
   ```bash
   cd ios
   open ZhiJi.xcodeproj
   ```

2. **配置签名**
   - 在Xcode左侧项目导航器中选择最顶部的 `ZhiJi` 项目
   - 选择 `ZhiJi` target
   - 点击 `Signing & Capabilities` 标签
   - 勾选 `Automatically manage signing`
   - 选择您的开发团队（Team）
   - 修改 `Bundle Identifier` 为唯一标识符（例如：`com.yourname.zhiji`）

3. **配置设备**
   - 将您的iOS设备连接到Mac
   - 在Xcode顶部工具栏的设备选择器中选择您的设备
   - 如果是首次连接，需要在设备上信任这台Mac

### 第二步：测试运行

1. **在模拟器上测试**
   - 选择任意模拟器（如 iPhone 15）
   - 点击运行按钮（▶️）或按 `Cmd + R`
   - 确认应用可以正常启动和运行

2. **在真机上测试**
   - 选择您的真机设备
   - 点击运行按钮
   - 如果是首次安装，需要在设备的「设置」→「通用」→「VPN与设备管理」中信任开发者

### 第三步：归档（Archive）

1. **选择设备**
   - 在设备选择器中选择 `Any iOS Device (arm64)` 或您的真机设备

2. **开始归档**
   - 菜单栏：`Product` → `Archive`
   - 或按快捷键：`Cmd + Shift + B`
   - 等待归档完成，Xcode会自动打开「Organizer」窗口

### 第四步：导出.ipa

1. **在Organizer中**
   - 选择刚才创建的归档
   - 点击 `Distribute App` 按钮

2. **选择分发方式**
   - **Development**：开发测试用（推荐）
   - **Ad Hoc**：有限设备分发
   - **App Store**：提交到App Store
   - **Enterprise**：企业内部分发

3. **完成导出**
   - 按照向导完成导出设置
   - 选择导出位置
   - 等待导出完成，您将获得.ipa文件

---

## 使用自动化脚本

### 构建脚本说明

```bash
# 进入scripts目录
cd ios/scripts

# 添加执行权限
chmod +x build.sh setup.sh

# 1. 先运行设置脚本
./setup.sh

# 2. 构建development版本（用于测试）
./build.sh development

# 3. 构建ad-hoc版本（用于有限分发）
./build.sh ad-hoc

# 4. 构建app-store版本（用于提交App Store）
./build.sh app-store
```

### 脚本配置

在使用脚本前，请编辑 `scripts/ExportOptions.plist`：

```xml
<key>teamID</key>
<string>YOUR_TEAM_ID</string>  <!-- 替换为您的Team ID -->
```

如何获取Team ID：
1. 登录 [Apple Developer](https://developer.apple.com/account/)
2. 进入 `Membership` 页面
3. 复制 `Team ID`

---

## 生成的文件位置

- **归档文件**：`ios/build/ZhiJi.xcarchive`
- **.ipa文件**：`ios/build/export/ZhiJi.ipa`
- **构建日志**：Xcode Report Navigator

---

## 安装.ipa到设备

### 方法一：使用Xcode

1. 连接设备到Mac
2. 打开 `Xcode` → `Window` → `Devices and Simulators`
3. 将.ipa文件拖到已连接设备的「Installed Apps」区域

### 方法二：使用Apple Configurator

1. 从Mac App Store安装「Apple Configurator」
2. 连接设备
3. 拖入.ipa文件进行安装

### 方法三：使用iTunes/Finder

1. 连接设备到Mac
2. 打开Finder（macOS Catalina及以上）或iTunes
3. 选择您的设备
4. 将.ipa文件拖到设备的「文件共享」区域

### 方法四：使用TestFlight（需要App Store Connect）

1. 将.ipa上传到App Store Connect
2. 使用TestFlight进行内部/外部测试

---

## 常见问题

### Q: 代码签名错误
**A:** 
- 确认已正确选择开发团队
- 检查Bundle Identifier是否唯一
- 尝试在Xcode中清理项目（`Cmd + Shift + K`）

### Q: 归档失败
**A:**
- 确保选择了「Any iOS Device」
- 检查Build Settings中的代码签名配置
- 查看Xcode日志获取详细错误信息

### Q: 无法安装到设备
**A:**
- 确认设备已添加到开发者账号
- 检查.ipa的签名方式是否匹配设备
- 尝试重启设备和Xcode

### Q: 讯飞SDK集成问题
**A:**
- 确保 `iflyMSC.framework` 在 `../lib/` 目录
- 检查 `Build Phases` 中是否正确链接
- 参考 `../sample/MSCDemo/` 中的示例

---

## 项目文件结构

```
ios/
├── ZhiJi.xcodeproj/          # Xcode项目
├── ZhiJi/                    # 源代码
│   ├── AppDelegate.swift
│   ├── SceneDelegate.swift
│   ├── ViewController.swift
│   ├── DataManager.swift
│   ├── SpeechRecognizer.swift
│   ├── RecordManager.swift
│   └── ...
├── scripts/                  # 构建脚本
│   ├── build.sh             # 构建脚本
│   ├── setup.sh             # 设置脚本
│   └── ExportOptions.plist  # 导出配置
├── build/                    # 构建输出（自动生成）
├── README.md                # 项目说明
└── BUILD_GUIDE.md           # 本文档
```

---

## 下一步

构建成功后，您可以：

1. 📱 在真机上测试应用功能
2. 🐛 修复发现的问题
3. 🚀 准备提交到App Store
4. 🎁 分发给测试人员

---

## 获取帮助

如遇到问题：
1. 查看Xcode日志（Report Navigator）
2. 检查本指南的「常见问题」部分
3. 参考项目README.md
4. 访问Apple Developer文档

---

**祝您构建顺利！** 🎉

如有问题，请随时反馈。
