# 智记 - iOS版本

智记是一款简洁高效的时间记录应用，支持语音识别，让记录变得更加便捷。

## 功能特性

- ✅ **快速记录**：一键记录当前时间
- 🎤 **语音识别**：支持在线/离线语音识别（集成讯飞SDK）
- 📝 **记录管理**：查看、编辑、删除记录
- 📅 **时间格式**：支持中文格式和ISO格式切换
- 📤 **数据导出**：支持导出CSV格式
- 💾 **本地存储**：数据安全存储在本地
- 🎨 **精美界面**：深色主题，护眼设计

## 项目结构

```
ios/
├── ZhiJi.xcodeproj/          # Xcode项目文件
└── ZhiJi/                    # 源代码目录
    ├── AppDelegate.swift     # 应用入口
    ├── SceneDelegate.swift   # 场景管理
    ├── ViewController.swift  # 主界面（包含SwiftUI视图）
    ├── DataManager.swift     # 数据管理
    ├── SpeechRecognizer.swift # 语音识别管理
    ├── RecordManager.swift   # 记录管理
    ├── Info.plist            # 应用配置
    ├── Main.storyboard       # 主故事板
    ├── LaunchScreen.storyboard # 启动屏
    └── Assets.xcassets/      # 资源文件
```

## 系统要求

- iOS 15.0+
- Xcode 14.0+
- Swift 5.0+

## 安装说明

### 1. 打开项目

使用Xcode打开 `ZhiJi.xcodeproj` 文件。

### 2. 配置签名

1. 选择项目导航器中的 `ZhiJi` 项目
2. 选择 `ZhiJi` target
3. 在 `Signing & Capabilities` 中配置您的开发团队
4. 修改 `Bundle Identifier` 为您自己的标识符

### 3. 集成讯飞SDK

1. 确保 `../lib/iflyMSC.framework` 存在于项目路径中
2. 在Xcode中，将 `iflyMSC.framework` 添加到项目中（如果尚未添加）
3. 在 `Build Phases` -> `Link Binary With Libraries` 中确保包含讯飞框架
4. 在 `SpeechRecognizer.swift` 中填入您的讯飞AppID

### 4. 配置权限

确保在 `Info.plist` 中已配置麦克风权限描述：

```xml
<key>NSMicrophoneUsageDescription</key>
<string>智记需要访问麦克风来进行语音识别</string>
```

### 5. 运行项目

1. 连接iOS设备或选择模拟器
2. 点击Xcode的运行按钮（或按 `Cmd + R`）

## 讯飞SDK集成指南

### 获取AppID

1. 访问 [讯飞开放平台](https://www.xfyun.cn/)
2. 注册账号并创建应用
3. 获取您的AppID

### 集成步骤

在 `SpeechRecognizer.swift` 中完成以下步骤：

1. 导入讯飞SDK头文件
2. 初始化讯飞语音识别
3. 实现识别回调
4. 处理识别结果

详细集成文档请参考 `../doc/com.iflytek.IFlyMSC.docset`

## 使用说明

### 快速记录

点击「记录」按钮即可快速添加一条当前时间的记录。

### 语音识别

1. 点击「语音」按钮开始录音
2. 说出您要记录的内容
3. 再次点击或等待静音自动停止
4. 识别结果会自动保存

### 编辑记录

1. 在记录列表中点击任意记录
2. 在弹出的编辑界面中修改内容
3. 点击「保存」保存修改

### 切换时间格式

点击顶部的「中」或「ISO」按钮切换时间显示格式。

### 导出数据

在记录列表中长按，选择导出选项，即可将记录导出为CSV文件。

## 文件存储

- 记录数据：`Documents/zhiji_records.json`
- 配置文件：`Documents/zhiji_config.json`
- 录音文件：临时目录，识别后自动删除

## 技术栈

- **语言**：Swift 5.0
- **UI框架**：SwiftUI + UIKit
- **数据存储**：JSON文件
- **语音识别**：讯飞MSC SDK
- **音频录制**：AVFoundation

## 注意事项

1. **语音识别**：当前使用模拟识别，需要接入讯飞SDK才能正常使用
2. **真机测试**：语音识别功能需要在真机上测试
3. **网络权限**：在线识别需要网络连接
4. **麦克风权限**：首次使用需要授权麦克风访问

## 开发计划

- [ ] 完整集成讯飞在线识别
- [ ] 实现离线识别功能
- [ ] 添加数据备份/恢复功能
- [ ] 支持iCloud同步
- [ ] 添加标签分类功能
- [ ] 实现数据统计功能

## 许可证

本项目仅供学习和个人使用。

## 致谢

- 讯飞语音识别SDK
- iOS开发社区

## 联系方式

如有问题或建议，欢迎反馈。

---

**智记** - 让记录变得更简单 📝
