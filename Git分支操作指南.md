# Git分支操作指南

---

## 📋 目录
1. [创建新分支并推送](#创建新分支并推送)
2. [切换到已有分支](#切换到已有分支)
3. [推送到指定分支](#推送到指定分支)
4. [查看所有分支](#查看所有分支)
5. [手动命令参考](#手动命令参考)

---

## 🚀 方法1：使用脚本（最简单）⭐

### 创建新分支并推送
**双击运行：** `git-create-branch.bat`

输入分支名称即可，例如：
```
feature/login
fix/bug-123
dev
test
```

### 切换分支
**双击运行：** `git-switch-branch.bat`

选择要切换到的分支。

### 推送到指定分支
**双击运行：** `git-push-to-branch.bat`

输入要推送到的分支名称。

---

## 🔧 方法2：手动命令

### 1. 创建新分支并推送

```cmd
git checkout -b feature/login
git add .
git commit -m "Add login feature"
git push -u origin feature/login
```

### 2. 切换到已有分支

```cmd
git checkout main
```
或
```cmd
git checkout feature/login
```

### 3. 在当前分支推送

```cmd
git add .
git commit -m "Update"
git push
```

### 4. 推送到指定分支（即使当前在其他分支）

```cmd
git add .
git commit -m "Update"
git push -u origin feature/login
```

---

## 📊 查看分支

### 查看本地分支
```cmd
git branch
```

### 查看远程分支
```cmd
git branch -r
```

### 查看所有分支（本地+远程）
```cmd
git branch -a
```

### 查看当前分支
```cmd
git branch --show-current
```

---

## 💡 分支命名建议

### 功能分支
```
feature/login
feature/user-profile
feature/settings
```

### 修复分支
```
fix/crash-on-launch
fix/login-bug
fix/typo
```

### 开发分支
```
dev
develop
test
staging
```

---

## 🎯 完整工作流示例

### 场景：开发新功能

1. **创建功能分支**
   ```cmd
   git checkout -b feature/login
   ```

2. **开发代码...**

3. **提交更改**
   ```cmd
   git add .
   git commit -m "Add login feature"
   ```

4. **推送到远程**
   ```cmd
   git push -u origin feature/login
   ```

5. **回到main分支**
   ```cmd
   git checkout main
   ```

6. **合并功能（可选）**
   ```cmd
   git merge feature/login
   git push
   ```

---

## 📝 脚本说明

| 脚本 | 功能 |
|------|------|
| `git-create-branch.bat` | 创建新分支并推送 |
| `git-switch-branch.bat` | 切换分支 |
| `git-push-to-branch.bat` | 推送到指定分支 |

---

## ⚠️ 注意事项

1. **切换分支前先提交或暂存更改**，否则会丢失未提交的更改
2. **分支名不要有空格**，用连字符或下划线代替
3. **首次推送新分支时要用 `-u`**：`git push -u origin branch-name`
4. **之后推送可以直接用**：`git push`

---

## ❓ 常见问题

### Q: 如何删除分支？
```cmd
git branch -d branch-name          # 删除本地分支
git push origin --delete branch-name  # 删除远程分支
```

### Q: 如何重命名分支？
```cmd
git branch -m old-name new-name
git push origin :old-name new-name
git push -u origin new-name
```

### Q: 如何从远程拉取新分支？
```cmd
git fetch
git checkout branch-name
```
