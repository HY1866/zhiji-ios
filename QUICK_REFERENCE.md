# 🚀 智记 - 快速参考卡

## 目录
- [Windows用户](#windows用户)
- [Mac用户](#mac用户)
- [Git命令速查](#git命令速查)
- [构建命令速查](#构建命令速查)

---

## Windows用户

### 📦 打包项目（传给Mac）
双击运行：
```
ios\package.bat
```

### 🛠️ 初始化Git
双击运行：
```
scripts\init-git.bat
```

### Git常用命令
```bash
# 查看状态
git status

# 添加所有文件
git add .

# 提交
git commit -m "提交信息"

# 推送
git push

# 拉取
git pull
```

### 完整工作流
```batch
# 1. 修改代码...

# 2. 提交
git add .
git commit -m "更新内容"

# 3. 推送
git push

# 4. 告诉Mac端的同事拉取构建
```

---

## Mac用户

### 📦 从Git获取代码
```bash
# 克隆
git clone https://github.com/你的用户名/zhiji-ios.git
cd zhiji-ios

# 或拉取更新
git pull
```

### 🔧 设置项目
```bash
cd ios
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 🚀 构建
```bash
# Development（测试用）
./scripts/build.sh development

# Ad Hoc（有限分发）
./scripts/build.sh ad-hoc

# App Store
./scripts/build.sh app-store
```

### 📱 打开项目
```bash
open ios/ZhiJi.xcodeproj
```

---

## Git命令速查

### 基础命令
| 命令 | 说明 |
|------|------|
| `git init` | 初始化仓库 |
| `git clone <url>` | 克隆远程仓库 |
| `git status` | 查看状态 |
| `git add .` | 添加所有文件 |
| `git add <file>` | 添加指定文件 |
| `git commit -m "msg"` | 提交 |
| `git push` | 推送到远程 |
| `git pull` | 拉取更新 |
| `git log --oneline` | 查看提交历史 |

### 分支命令
| 命令 | 说明 |
|------|------|
| `git branch` | 查看分支 |
| `git branch <name>` | 创建分支 |
| `git checkout <name>` | 切换分支 |
| `git checkout -b <name>` | 创建并切换 |
| `git merge <name>` | 合并分支 |
| `git branch -d <name>` | 删除分支 |

### 远程仓库
| 命令 | 说明 |
|------|------|
| `git remote -v` | 查看远程 |
| `git remote add origin <url>` | 添加远程 |
| `git push -u origin main` | 推送并关联 |

---

## 构建命令速查

### macOS构建脚本
```bash
cd ios/scripts

# 权限（第一次需要）
chmod +x build.sh setup.sh

# 设置
./setup.sh

# 构建
./build.sh development
./build.sh ad-hoc
./build.sh app-store
```

### Xcode手动操作
| 操作 | 快捷键 |
|------|--------|
| 运行 | Cmd + R |
| 测试 | Cmd + U |
| 清理 | Cmd + Shift + K |
| 归档 | Cmd + Shift + B |

---

## 📂 项目文件速查

| 文件 | 说明 |
|------|------|
| `GIT_GUIDE.md` | Git完整指南 ⭐ |
| `QUICK_REFERENCE.md` | 本文档 |
| `ios/BUILD_GUIDE.md` | Mac构建指南 ⭐ |
| `ios/README.md` | 项目说明 |
| `ios/WINDOWS_GUIDE.md` | Windows指南 |
| `ios/ZhiJi.xcodeproj` | Xcode项目 |

---

## 🔗 完整流程示例

### Windows开发 → Mac构建

```
Windows端:
1. 修改代码
2. git add .
3. git commit -m "更新"
4. git push

Mac端:
1. git pull
2. cd ios
3. ./scripts/build.sh development
4. 得到 .ipa 文件！
```

---

## ⚡ 一键命令（复制粘贴）

### Windows初始化Git
```batch
cd e:\聊天记录\智记ios版
scripts\init-git.bat
```

### Mac首次构建
```bash
git clone https://github.com/你的用户名/zhiji-ios.git
cd zhiji-ios/ios
chmod +x scripts/*.sh
./scripts/setup.sh
./scripts/build.sh development
```

### 日常开发（Windows）
```batch
git add .
git commit -m "你的修改"
git push
```

### 日常构建（Mac）
```bash
git pull
cd ios
./scripts/build.sh development
```

---

## 💡 提示

- 需要详细说明？看 `GIT_GUIDE.md`
- 需要构建帮助？看 `ios/BUILD_GUIDE.md`
- Windows用户？看 `ios/WINDOWS_GUIDE.md`
- 项目说明？看 `ios/README.md`

---

祝使用愉快！🎉
