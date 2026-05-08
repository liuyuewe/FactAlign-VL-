# GitHub 上传完整步骤指南

> 本指南将帮助您将 FactAlign-VL 项目完整上传到 GitHub

---

## 第一步：准备工作

### 1.1 安装 Git

**Windows 用户：**
1. 访问 https://git-scm.com/download/win
2. 下载安装包并运行
3. 安装选项保持默认，点击 "Next" 直到完成

**验证安装：**
```bash
git --version
# 应显示: git version 2.x.x
```

### 1.2 配置 Git

```bash
# 设置用户名（替换为你的 GitHub 用户名）
git config --global user.name "YourUsername"

# 设置邮箱（替换为你的 GitHub 邮箱）
git config --global user.email "your.email@example.com"

# 验证配置
git config --list
```

### 1.3 创建 GitHub 账户

1. 访问 https://github.com
2. 点击 "Sign up" 注册账户
3. 选择免费计划 (Free)
4. 验证邮箱

---

## 第二步：创建远程仓库

### 2.1 在 GitHub 上创建仓库

1. 登录 GitHub
2. 点击右上角 **"+"** → **"New repository"**

3. 填写仓库信息：
   - **Repository name**: `FactAlign-VL`
   - **Description**: `🔍 针对多模态大模型"数字失认症"问题的视觉事实核查系统`
   - **Visibility**: 选择 **Public** (公开) 或 **Private** (私有)
   - ⚠️ **不要**勾选 "Add a README file"（我们已有）
   - ⚠️ **不要**勾选 "Add .gitignore"（我们已有）

4. 点击 **"Create repository"**

5. **重要**：复制仓库 URL，类似：
   - HTTPS: `https://github.com/yourusername/FactAlign-VL.git`
   - SSH: `git@github.com:yourusername/FactAlign-VL.git`

---

## 第三步：初始化本地仓库

### 3.1 打开命令提示符

按 `Win + R`，输入 `cmd`，回车

### 3.2 进入项目目录

```bash
# 方法1: 如果已经在项目目录，直接 cd
cd "f:\aiproject\FactAlign-VL 视觉事实核查器"

# 方法2: 使用完整路径
cd /d "F:\aiproject\FactAlign-VL 视觉事实核查器"

# 验证当前目录
cd
```

### 3.3 初始化 Git 仓库

```bash
git init
```

应该看到：`Initialized empty Git repository in F:/aiproject/FactAlign-VL 视觉事实核查器/.git/`

---

## 第四步：添加文件到仓库

### 4.1 创建 .gitignore 文件

在项目根目录创建 `.gitignore` 文件：

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv/

# Jupyter
.ipynb_checkpoints/

# IDE
.vscode/
.idea/
*.swp

# 数据文件（仅保留少量样例）
data/annotations/
data/metadata/
data/charts/
data/descriptions/

# 模型文件
models/
*.bin
*.safetensors

# 日志
*.log

# 系统文件
.DS_Store
Thumbs.db
```

### 4.2 查看文件状态

```bash
git status
```

应该看到所有文件显示为红色（未跟踪）

### 4.3 添加所有文件

```bash
git add .
```

### 4.4 再次查看状态

```bash
git status
```

应该看到所有文件显示为绿色（已暂存）

---

## 第五步：提交文件

### 5.1 创建首次提交

```bash
git commit -m "Initial commit: FactAlign-VL visual fact checker

- 项目结构完整
- 数据生成模块
- 模型微调模块
- 评估模块
- Gradio 演示界面
"
```

如果配置了编辑器，会打开编辑器，输入 `:wq` 保存退出

---

## 第六步：连接远程仓库

### 6.1 添加远程仓库

```bash
# 替换 YOUR_USERNAME 为你的 GitHub 用户名
git remote add origin https://github.com/YOUR_USERNAME/FactAlign-VL.git

# 验证连接
git remote -v
```

应该看到：
```
origin  https://github.com/YOUR_USERNAME/FactAlign-VL.git (fetch)
origin  https://github.com/YOUR_USERNAME/FactAlign-VL.git (push)
```

---

## 第七步：上传到 GitHub

### 7.1 首次推送

```bash
git branch -M main
git push -u origin main
```

### 7.2 输入凭据

- **第一次推送**：会弹出窗口要求登录 GitHub
- 输入你的 GitHub 用户名和密码（或 Personal Access Token）

> ⚠️ **注意**：如果使用 2FA，需要创建 Personal Access Token：
> 1. GitHub → Settings → Developer settings
> 2. Personal access tokens → Generate new token
> 3. 勾选 `repo` 权限
> 4. 使用 token 代替密码登录

### 7.3 验证上传成功

1. 打开 https://github.com/YOUR_USERNAME/FactAlign-VL
2. 应该看到所有文件已上传
3. 仓库信息正确显示

---

## 第八步：添加样例数据（可选）

### 8.1 创建样例目录

```bash
mkdir -p data/samples
```

### 8.2 添加少量样例文件

```bash
# 复制几个元数据文件
copy data\metadata\chart_00001.json data\samples\
copy data\metadata\chart_00002.json data\samples\
copy data\metadata\chart_00003.json data\samples\

# 复制少量标注数据
copy data\annotations\val.jsonl data\samples\val_sample.jsonl
```

### 8.3 提交并推送

```bash
git add data/samples/
git commit -m "Add sample data"
git push
```

---

## 常见问题

### Q1: 推送被拒绝？

```
! [rejected] main -> main (fetch first)
```

解决：
```bash
git pull origin main --rebase
git push origin main
```

### Q2: 文件太大？

GitHub 限制单文件 100MB，超过会失败。

解决：
1. 将大文件添加到 .gitignore
2. 或使用 Git LFS：
```bash
git lfs install
git lfs track "*.png"
```

### Q3: 忘记添加 .gitignore？

```bash
# 编辑 .gitignore
notepad .gitignore

# 移除已跟踪的文件
git rm -r --cached data/annotations/
git rm -r --cached data/metadata/
git rm -r --cached data/charts/
git add .gitignore
git commit -m "Update .gitignore and remove large data files"
git push
```

### Q4: 中文路径名显示乱码？

在 Windows 上执行：
```bash
git config --global core.quotepath false
```

---

## 完整命令速查

```bash
# 1. 进入项目目录
cd /d "F:\aiproject\FactAlign-VL 视觉事实核查器"

# 2. 初始化
git init

# 3. 配置（如未配置）
git config --global user.name "YOUR_USERNAME"
git config --global user.email "YOUR_EMAIL"
git config --global core.quotepath false

# 4. 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/FactAlign-VL.git

# 5. 添加文件
git add .

# 6. 提交
git commit -m "Initial commit"

# 7. 推送
git branch -M main
git push -u origin main
```

---

## 上传后检查清单

- [ ] 仓库名称正确
- [ ] 描述已添加
- [ ] README.md 正常显示
- [ ] LICENSE 文件可见
- [ ] 文件结构正确
- [ ] 不包含敏感信息
