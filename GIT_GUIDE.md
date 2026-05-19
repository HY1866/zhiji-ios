# Git仓库与构建指南

本指南将帮助您使用Git管理智记iOS项目并完成构建。

---

## 📋 目录
1. [快速开始](#快速开始)
2. [Git初始化](#git初始化)
3. [远程仓库](#远程仓库)
4. [日常开发](#日常开发)
5. [CI/CD自动构建](#cicd自动构建)
6. [在Mac上构建](#在mac上构建)

---

## 🚀 快速开始

### Windows用户
```batch
# 1. 进入项目目录
cd e:\聊天记录\智记ios版

# 2. 初始化Git
scripts\init-git.bat

# 3. 推送至远程（按提示操作）
```

### macOS/Linux用户
```bash
# 1. 进入项目目录
cd /path/to/zhiji-ios

# 2. 初始化Git
chmod +x scripts/init-git.sh
./scripts/init-git.sh

# 3. 推送至远程（按提示操作）
```

---

## 🛠️ Git初始化

### 第一步：准备Git环境

检查Git是否安装：
```bash
git --version
```

如果没有安装，请从 https://git-scm.com/ 下载安装。

### 第二步：配置Git用户

```bash
# 配置用户名和邮箱（全局）
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 查看配置
git config --list
```

### 第三步：初始化仓库

#### 方法一：使用脚本（推荐）

**Windows:**
```batch
scripts\init-git.bat
```

**macOS/Linux:**
```bash
chmod +x scripts/init-git.sh
./scripts/init-git.sh
```

#### 方法二：手动操作

```bash
# 1. 初始化Git
git init

# 2. 添加文件
git add .

# 3. 创建提交
git commit -m "Initial commit: 智记iOS项目"

# 4. 切换到main分支
git branch -M main
```

---

## 🌐 远程仓库

### 创建远程仓库

1. 访问 GitHub / GitLab / Gitee
2. 创建新仓库（不要初始化README、.gitignore等）
3. 复制仓库URL

### 连接远程仓库

```bash
# 添加远程仓库
git remote add origin https://github.com/你的用户名/zhiji-ios.git

# 推送到远程
git push -u origin main
```

### 常用Git命令

```bash
# 查看状态
git status

# 查看变更
git diff

# 暂存变更
git add .
# 或
git add 文件名

# 提交
git commit -m "描述信息"

# 拉取更新
git pull

# 推送
git push

# 查看日志
git log --oneline

# 创建分支
git branch 分支名

# 切换分支
git checkout 分支名

# 合并分支
git merge 分支名
```

---

## 💻 日常开发工作流

### 1. 开始新功能

```bash
# 确保main是最新的
git checkout main
git pull

# 创建新分支
git checkout -b feature/新功能名称
```

### 2. 开发过程中

```bash
# 查看变更
git status

# 暂存修改
git add .

# 提交
git commit -m "描述这次修改"
```

### 3. 完成功能

```bash
# 切换回main
git checkout main
git pull

# 合并功能分支
git merge feature/新功能名称

# 推送到远程
git push
```

### 4. 推送到远程后在Mac上构建

参考「在Mac上构建」部分。

---

## 🔄 CI/CD自动构建（GitHub Actions）

项目已包含GitHub Actions配置文件 `.github/workflows/build.yml`

### 启用自动构建

1. 将代码推送到GitHub
2. 进入仓库的 `Actions` 标签
3. GitHub Actions会自动开始构建

### 构建流程

每次推送代码到 `main` 或 `master` 分支时：
- ✅ 运行模拟器构建检查
- ✅ 创建XCArchive归档
- ✅ 上传Artifacts（可下载）

### 下载构建结果

1. 进入GitHub Actions
2. 点击成功的Workflow
3. 在Artifacts部分下载 `xcarchive`
4. 在本地Mac上完成签名和导出

---

## 🍎 在Mac上构建

### 方式一：从Git克隆（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/zhiji-ios.git
cd zhiji-ios

# 2. 运行设置脚本
cd ios
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. 打开项目
open ZhiJi.xcodeproj

# 4. 在Xcode中配置签名

# 5. 构建
./scripts/build.sh development
```

### 方式二：从GitHub Actions下载

1. 下载Actions生成的 `xcarchive`
2. 在Xcode的Organizer中导入
3. 完成签名和导出

### 方式三：使用自动化脚本

```bash
cd ios

# Development版本（测试用）
./scripts/build.sh development

# Ad Hoc版本（有限分发）
./scripts/build.sh ad-hoc

# App Store版本
./scripts/build.sh app-store
```

详细步骤请查看 `ios/BUILD_GUIDE.md`

---

## 📁 完整工作流示例

### Windows端（开发）

```batch
# 1. 初始化Git
scripts\init-git.bat

# 2. 开发和修改代码...

# 3. 提交变更
git add .
git commit -m "添加新功能"

# 4. 推送到远程
git push
```

### Mac端（构建）

```bash
# 1. 克隆或拉取最新代码
git clone https://github.com/你的用户名/zhiji-ios.git
# 或
git pull

# 2. 构建
cd ios
./scripts/build.sh development

# 3. 获取.ipa文件
# 位置: ios/build/export/ZhiJi.ipa
```

---

## 🔧 分支策略建议

```
main (主分支)
  └── feature/login (功能分支)
  └── feature/voice-recognition (功能分支)
  └── fix/bug-xxx (修复分支)
  └── release/v1.0 (发布分支)
```

### 创建功能分支
```bash
git checkout -b feature/功能名称
```

### 创建修复分支
```bash
git checkout -b fix/问题描述
```

---

## ⚠️ 注意事项

1. **不要提交构建产物**：已在 `.gitignore` 中配置
2. **不要提交敏感信息**：API Key、证书等
3. **定期提交**：不要等太多变更才提交
4. **写清晰的提交信息**：让团队成员了解变更内容
5. **推送前先拉取**：避免冲突

---

## 📚 相关文档

- `ios/BUILD_GUIDE.md` - 详细构建指南
- `ios/README.md` - 项目说明
- `ios/WINDOWS_GUIDE.md` - Windows用户指南

---

## ❓ 需要帮助？

- Git文档：https://git-scm.com/doc
- GitHub文档：https://docs.github.com
- Xcode构建：查看 `ios/BUILD_GUIDE.md`

---

**祝您使用愉快！** 🎉
