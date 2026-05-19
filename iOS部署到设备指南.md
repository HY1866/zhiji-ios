# iOS部署到设备完整指南

---

## 📋 目录
1. [前置要求](#前置要求)
2. [在Mac上获取项目](#在mac上获取项目)
3. [配置Xcode项目](#配置xcode项目)
4. [连接iOS设备](#连接ios设备)
5. [构建并安装到设备](#构建并安装到设备)
6. [通过TestFlight分发](#通过testflight分发)
7. [常见问题](#常见问题)

---

## 🔧 前置要求

### 必须有：
- ✅ 一台Mac电脑（macOS 12.0或更高）
- ✅ Xcode 14.0或更高版本
- ✅ Apple开发者账号（免费或付费）
- ✅ iOS设备（iPhone/iPad）
- ✅ USB线（连接设备和Mac）

### 可选：
- 🌐 网络连接（下载Xcode）

---

## 💻 在Mac上获取项目

### 方法1：从GitHub克隆（推荐）

1. **打开终端（Terminal）**
2. **运行以下命令：**

```bash
cd ~/Desktop
git clone https://github.com/HY1866/zhiji-ios.git
cd zhiji-ios/ios
```

### 方法2：从压缩包解压

如果您有项目的ZIP文件：
1. 解压到桌面
2. 进入 `ios` 文件夹

---

## 🛠️ 配置Xcode项目

### 步骤1：打开项目

1. **双击打开：** `ios/ZhiJi.xcodeproj`
2. **或在终端运行：**
   ```bash
   open ios/ZhiJi.xcodeproj
   ```

### 步骤2：配置签名（最重要）

1. **在Xcode左侧，点击项目名称 "ZhiJi"**（蓝色图标）
2. **在中间窗口，选择 "TARGETS" - "ZhiJi"**
3. **选择 "Signing & Capabilities" 标签**

#### 配置签名：
- **Team：** 选择您的Apple开发者账号
  - 如果没有，点击 "Add Account..." 登录
- **Bundle Identifier：** 确保是唯一的
  - 可以改成：`com.yourname.zhiji`
  - 例如：`com.hy1866.zhiji`
- **Automatically manage signing：** 勾选 ✅

#### 检查配置：
- ✅ "Signing Certificate" 显示 "Apple Development"
- ✅ "Provisioning Profile" 显示 "Xcode Managed Profile"

---

## 📱 连接iOS设备

### 步骤1：物理连接

1. **用USB线连接iPhone/iPad到Mac**
2. **在iOS设备上：**
   - 弹出 "Trust This Computer?" 对话框
   - 点击 "Trust"
   - 输入设备密码确认

### 步骤2：在Xcode中选择设备

1. **在Xcode顶部工具栏，找到设备选择器**
   - 默认可能是 "Any iOS Device" 或 "iPhone 15"
2. **点击下拉菜单**
3. **选择您的设备（例如："张三的 iPhone"）**

---

## 🚀 构建并安装到设备

### 方法1：使用Xcode（最简单）

1. **在Xcode中选择您的设备**
2. **点击左上角的播放按钮（▶️）**
   - 或按快捷键：`Cmd + R`
3. **等待构建完成**
4. **应用会自动安装并在设备上打开**

### 方法2：使用脚本

在项目根目录运行：

```bash
cd ios
chmod +x scripts/build.sh
./scripts/build.sh development
```

### 方法3：使用Xcode菜单

1. **Product - Destination - 选择您的设备**
2. **Product - Run**

---

## 🔐 首次运行的信任设置

### 如果您使用免费开发者账号：

第一次在设备上运行应用后：

1. **在iOS设备上打开设置**
2. **进入 "通用" - "VPN与设备管理"**
3. **找到您的Apple ID**
4. **点击并信任该账号**
5. **回到主屏幕，再次打开应用**

---

## 📦 通过TestFlight分发（给其他人测试）

### 步骤1：存档应用

1. **在Xcode中：**
   - Project - Destination - "Any iOS Device"
   - Product - Archive

2. **等待构建完成，会自动打开Organizer窗口**

### 步骤2：上传到App Store Connect

1. **在Organizer中，选择刚创建的Archive**
2. **点击 "Distribute App"**
3. **选择 "App Store Connect" - "Next"**
4. **选择 "Automatically manage signing" - "Next"**
5. **点击 "Upload"**

### 步骤3：在App Store Connect设置TestFlight

1. **访问：** https://appstoreconnect.apple.com/
2. **选择您的App**
3. **进入 "TestFlight" 标签**
4. **添加测试员**
5. **测试员会收到邮件邀请**

---

## 📋 完整的Mac端操作流程

### 1. 准备工作
```bash
# 克隆项目
cd ~/Desktop
git clone https://github.com/HY1866/zhiji-ios.git
cd zhiji-ios

# 进入ios目录
cd ios

# 检查文件
ls
```

### 2. 运行设置脚本
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3. 打开Xcode
```bash
open ZhiJi.xcodeproj
```

### 4. 在Xcode中配置
- 选择Team
- 修改Bundle Identifier
- 连接设备

### 5. 运行
- 点击播放按钮
- 或按 Cmd+R

---

## ❓ 常见问题

### Q: 提示 "No signing certificate found"
**A:** 
- 登录Apple开发者账号
- 勾选 "Automatically manage signing"
- 等待Xcode自动生成证书

### Q: 提示 "Could not find Developer Disk Image"
**A:** 
- 更新Xcode到最新版本
- 或更新iOS设备到最新系统

### Q: 设备上无法打开，提示 "Untrusted Developer"
**A:** 
- 设置 - 通用 - VPN与设备管理 - 信任您的账号

### Q: 构建失败，提示 "Provisioning profile" 错误
**A:** 
- 确保Bundle Identifier唯一
- 尝试重新选择Team
- Clean项目（Product - Clean Build Folder）

---

## 🎯 快速开始检查清单

- [ ] Mac电脑已准备好
- [ ] Xcode已安装（最新版本）
- [ ] Apple开发者账号已登录
- [ ] 项目已克隆到Mac
- [ ] iOS设备已通过USB连接
- [ ] 设备已信任Mac
- [ ] Xcode中已选择设备
- [ ] 签名配置已完成
- [ ] 点击播放按钮测试

---

## 📚 相关文档

- 查看 `ios/README.md` 了解项目结构
- 查看 `ios/scripts/README.md` 了解构建脚本

---

## 💡 提示

- **免费开发者账号：** 可以在真机测试，但应用7天后会过期
- **付费开发者账号（$99/年）：** 可以发布到App Store，应用不过期
- **建议先用免费账号测试，没问题再考虑付费**

---

## 🆘 需要帮助？

如果遇到问题：
1. 先检查本指南的常见问题部分
2. 查看Xcode的错误提示
3. 搜索相关错误信息
4. 检查Apple开发者文档
