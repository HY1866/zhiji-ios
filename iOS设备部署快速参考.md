# iOS设备部署 - 快速参考

---

## ⚡ 30秒快速开始

### 在Mac上：
```bash
# 1. 克隆项目
cd ~/Desktop
git clone https://github.com/HY1866/zhiji-ios.git
cd zhiji-ios

# 2. 运行设置脚本
./mac-setup.sh

# 3. 打开Xcode
cd ios
open ZhiJi.xcodeproj
```

### 在Xcode中：
1. 选择Team（您的Apple账号）
2. 连接iPhone/iPad
3. 选择您的设备
4. 点击播放按钮（▶️）

---

## 📋 完整操作步骤

### 第一步：准备Mac
- ✅ 确保Mac已联网
- ✅ Xcode已安装（从App Store下载）
- ✅ Apple开发者账号已登录（免费即可）

### 第二步：获取项目
```bash
cd ~/Desktop
git clone https://github.com/HY1866/zhiji-ios.git
cd zhiji-ios
```

### 第三步：运行设置
```bash
./mac-setup.sh
```

### 第四步：配置Xcode
1. 双击打开 `ios/ZhiJi.xcodeproj`
2. 选择项目（蓝色图标）
3. TARGETS - ZhiJi - Signing & Capabilities
4. 选择Team（您的Apple账号）
5. 修改Bundle Identifier为唯一的（如：com.hy1866.zhiji）

### 第五步：连接设备
1. 用USB线连接iPhone/iPad到Mac
2. 在设备上点击"信任"
3. 输入设备密码

### 第六步：运行
1. 在Xcode顶部选择您的设备
2. 点击播放按钮（▶️）或按 Cmd+R
3. 等一会，应用会在设备上打开！

---

## 🔑 关键配置

### Bundle Identifier示例
```
com.hy1866.zhiji
com.yourname.zhiji
com.zhiji.app
```
**必须唯一！**

### 签名配置
- ✅ Team：选择您的Apple ID
- ✅ Automatically manage signing：勾选
- ✅ Signing Certificate：Apple Development

---

## ❓ 常见问题速查

### 问题1：找不到设备
**解决：**
- 检查USB连接
- 设备上点击"信任"
- 重启设备和Mac

### 问题2：签名错误
**解决：**
- 登录Apple ID
- 检查Bundle Identifier唯一
- Clean项目（Product - Clean Build Folder）

### 问题3：设备上无法打开
**解决：**
- 设置 - 通用 - VPN与设备管理 - 信任您的账号

---

## 📦 分发选项

### 选项1：直接设备调试（最快）
- 免费
- USB连接
- 立即测试

### 选项2：TestFlight（给别人测试）
- 需要付费开发者账号
- 无线分发
- 最多10000测试员

### 选项3：App Store（发布）
- 需要付费开发者账号
- 所有人都能下载
- 审核通过后上线

---

## 💡 提示

- **免费账号：** 可在真机测试，但应用7天后过期
- **付费账号（$99/年）：** 可发布到App Store，应用不过期
- **先用免费账号测试，没问题再考虑付费！**

---

## 📚 详细文档

查看完整指南：`iOS部署到设备指南.md`
