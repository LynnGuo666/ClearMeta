# ClearMeta

一个简单的 GUI 工具，用于批量去除图片的 EXIF/XMP/IPTC 等元数据，保护隐私。默认优先调用 exiftool（若存在），否则使用 Pillow + piexif 进行安全重存。

## 功能
- **拖拽支持**：直接拖拽图片文件或文件夹到窗口中
- 手动选择图片或整个文件夹，自动递归收集常见图片格式（jpg/jpeg/png/webp/tif/tiff/bmp）
- 覆盖原文件或输出到指定目录
- 可选优先使用 exiftool（更彻底，建议安装），无则自动回退
- 进度条与实时日志
- 基于 PyQt5 的现代化界面

## 运行
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
建议使用 PyInstaller：

```bash
pip install pyinstaller
pyinstaller --noconfirm \
  --name ClearMeta \
  --windowed \
  --add-data "README.md:." \
  main.py
```

说明：
- macOS 会生成 `dist/ClearMeta.app`
- Windows 会得到 `dist/ClearMeta.exe`
- 如果你想减小体积，可添加 `--onefile`（首启会更慢）

示例（Windows onefile）：

```bash
pyinstaller --noconfirm --onefile --windowed --name ClearMeta main.py
```

如果需要把 `exiftool` 一并打包到目录，建议使用非 `--onefile` 模式并把 exiftool 可执行文件放入 `dist/ClearMeta/` 目录，程序会通过 `PATH` 自动发现。

## 系统要求
- Python 3.7+
- PyQt5（GUI 框架）
- Pillow（图像处理）
- piexif（EXIF 处理）
- 可选：exiftool（更彻底的元数据清理）

## 免责声明
- 该工具会尽最大努力移除图片元数据。但在个别受支持较弱的格式或私有 chunk 中，可能仍残留。若对隐私有极高要求，建议转换为无元数据格式（如重存为 PNG/WebP 并确认无 text chunk），并用第三方校验。
