# ClearMeta

一个简单的 GUI 工具，用于批量去除图片的 EXIF/XMP/IPTC 等元数据，保护隐私。默认优先调用 exiftool（若存在），否则使用 Pillow + piexif 进行安全重存。

## 功能
- **拖拽支持**：直接拖拽图片文件或文件夹到窗口中
- 手动选择图片或整个文件夹，自动递归收集常见图片格式（jpg/jpeg/png/webp/tif/tiff/bmp）
- 覆盖原文件或输出到指定目录
- 可选优先使用 exiftool（更彻底，建议安装），无则自动回退
- 进度条与实时日志
- 基于 PyQt5 的现代化界面

## 快速开始

### 下载预编译版本
访问 [Releases](../../releases) 页面下载对应平台的预编译版本：
- **Windows**: `ClearMeta-Windows.tar.gz` 
- **macOS**: `ClearMeta-macOS.tar.gz`
- **Linux**: `ClearMeta-Linux.tar.gz`

### 从源码运行
确保已安装依赖：

```bash
# 可选：创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

pip install -r requirements.txt
python main.py
```

可选安装 exiftool 提升清理彻底度：

- macOS（Homebrew）：`brew install exiftool`
- Windows（choco）：`choco install exiftool`
- Linux（apt）：`sudo apt-get install exiftool`

## 使用方法
1. 启动程序后，可以通过以下方式添加图片：
   - **拖拽**：直接将图片文件或包含图片的文件夹拖拽到窗口中
   - 点击"添加图片"按钮选择单个或多个图片文件
   - 点击"添加文件夹"按钮选择包含图片的文件夹
2. 选择是否覆盖原文件，或指定输出目录
3. 可选择是否优先使用 exiftool（推荐）
4. 点击"开始清理"进行批量处理

## 打包为可执行文件

### GitHub Actions 自动构建（推荐）

本项目配置了 GitHub Actions 自动构建多平台版本：

**发布版本**:
```bash
git tag v1.0.0
git push origin v1.0.0
```
自动构建并创建 Release，包含 Windows、macOS、Linux 三个平台的可执行文件。

**手动构建测试**:
1. 进入 GitHub 仓库的 Actions 页面
2. 选择 "Manual Build" 工作流
3. 点击 "Run workflow" 并选择平台
4. 下载构建产物

### 本地构建

### 自动化构建（推荐）

**macOS/Linux:**
```bash
./build.sh
```

**Windows:**
```cmd
build.bat
```

### 手动构建

#### macOS (.app 应用包)
```bash
# 使用规格文件（推荐）
pyinstaller ClearMeta.spec

# 或快速构建
pyinstaller --noconfirm --windowed --name ClearMeta main.py
```

#### Windows (.exe 可执行文件)
```bash
# 单文件版本
pyinstaller --noconfirm --windowed --onefile \
  --name ClearMeta \
  --add-data "sponsor_qr.png;." \
  --add-data "README.md;." \
  main.py

# 目录版本（启动更快）
pyinstaller --noconfirm --windowed \
  --name ClearMeta \
  --add-data "sponsor_qr.png;." \
  --add-data "README.md;." \
  main.py
```

#### Linux (可执行文件)
```bash
pyinstaller --noconfirm --windowed \
  --name ClearMeta \
  --add-data "sponsor_qr.png:." \
  --add-data "README.md:." \
  main.py
```

### 构建输出

- **macOS**: `dist/ClearMeta.app` (可拖拽到 Applications 文件夹)
- **Windows**: `dist/ClearMeta.exe` (双击运行)
- **Linux**: `dist/ClearMeta/ClearMeta` (命令行运行)

### 打包注意事项

1. **依赖包含**: 自动包含 PyQt5、Pillow、piexif 等依赖
2. **资源文件**: 包含赞助二维码和说明文档
3. **图标**: 可在 `.spec` 文件中添加自定义图标
4. **文件大小**: 大约 50-100MB（包含 Python 运行时）
5. **exiftool**: 如需包含，请使用目录版本并放入相应可执行文件

### 分发准备

**macOS**:
- 可选择安装 `create-dmg` 创建安装包: `brew install create-dmg`
- 注意代码签名要求（发布到 App Store 需要）

**Windows**:
- 建议使用杀毒软件白名单避免误报
- 可使用代码签名证书提升信任度

**Linux**:
- 可创建 `.deb` 或 `.rpm` 包
- 或制作 AppImage 便携版本

## 系统要求
- Python 3.7+
- PyQt5（GUI 框架）
- Pillow（图像处理）
- piexif（EXIF 处理）
- 可选：exiftool（更彻底的元数据清理）

## 免责声明
- 该工具会尽最大努力移除图片元数据。但在个别受支持较弱的格式或私有 chunk 中，可能仍残留。若对隐私有极高要求，建议转换为无元数据格式（如重存为 PNG/WebP 并确认无 text chunk），并用第三方校验。
