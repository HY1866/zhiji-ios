# PowerShell Git 问题修复

## ❌ 问题原因

您在PowerShell中运行Git命令时遇到了错误，这是因为：
- PowerShell把URL中的`>`字符误认为是重定向操作符
- PowerShell的解析规则与CMD不同

---

## ✅ 解决方案

### 方法一：使用我为您创建的脚本（推荐）

#### 1. 设置远程仓库
双击运行：
```
设置远程仓库.bat
```

然后按提示输入您的仓库URL：
```
https://github.com/HY1866/zhiji-ios.git
```

#### 2. 推送到远程
双击运行：
```
推送到远程.bat
```

---

### 方法二：手动修复（使用引号）

如果您想手动运行Git命令，需要用引号包裹URL：

```powershell
# 正确的方式 - 使用引号
git remote add origin "https://github.com/HY1866/zhiji-ios.git"
git push -u origin main
```

---

### 方法三：使用CMD而不是PowerShell

按 `Win + R`，输入 `cmd`，然后在CMD中运行：

```cmd
git remote add origin https://github.com/HY1866/zhiji-ios.git
git push -u origin main
```

---

## 📋 完整步骤

### 第一步：设置远程仓库（使用脚本）

1. 双击 `设置远程仓库.bat`
2. 输入您的仓库URL：`https://github.com/HY1866/zhiji-ios.git`
3. 按提示操作

### 第二步：推送到远程

1. 双击 `推送到远程.bat`
2. 脚本会自动提交并推送

---

## 💡 脚本说明

| 脚本文件 | 说明 |
|----------|------|
| `设置远程仓库.bat` | 设置Git远程仓库 ⭐ |
| `推送到远程.bat` | 推送到远程仓库 ⭐ |
| `scripts\setup-remote.ps1` | PowerShell脚本 |
| `scripts\push.ps1` | PowerShell推送脚本 |

---

## 🔧 如果还没有初始化Git

如果Git仓库还没有初始化，运行：

```batch
scripts\init-git.bat
```

或者使用 `设置远程仓库.bat`，它会自动检测并初始化。

---

## 📝 在PowerShell中正确运行Git命令的技巧

### 技巧1：使用引号
```powershell
git remote add origin "https://github.com/HY1866/zhiji-ios.git"
```

### 技巧2：使用转义字符
```powershell
git remote add origin https://github.com/HY1866/zhiji-ios.git
```

### 技巧3：使用单引号
```powershell
git remote add origin 'https://github.com/HY1866/zhiji-ios.git'
```

---

## ✅ 验证远程仓库是否设置成功

运行：
```powershell
git remote -v
```

应该看到：
```
origin  https://github.com/HY1866/zhiji-ios.git (fetch)
origin  https://github.com/HY1866/zhiji-ios.git (push)
```

---

## 🚀 推荐的工作流

### Windows端
```batch
# 1. 修改代码...

# 2. 推送到远程
推送到远程.bat
```

### Mac端
```bash
# 1. 拉取更新
git pull

# 2. 构建
cd ios
./scripts/build.sh development
```

---

## ❓ 仍然有问题？

1. 查看 `GIT_GUIDE.md`
2. 查看 `QUICK_REFERENCE.md`
3. 确保Git已正确安装：`git --version`

---

**使用脚本更简单！** 🎉
