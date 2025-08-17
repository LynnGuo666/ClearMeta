@echo off
REM ClearMeta Windows 构建脚本

echo 🚀 开始构建 ClearMeta...

REM 检查虚拟环境
if not exist ".venv" (
    echo ❌ 未找到虚拟环境，请先运行：
    echo python -m venv .venv
    echo .venv\Scripts\activate
    echo pip install -r requirements.txt
    pause
    exit /b 1
)

REM 激活虚拟环境
call .venv\Scripts\activate

echo 📦 安装/更新依赖...
pip install -r requirements.txt

echo 🧹 清理旧构建文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM 检查必要文件
if not exist "sponsor_qr.png" (
    echo ⚠️  未找到 sponsor_qr.png，创建占位图片...
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (200, 200), color='white'); draw = ImageDraw.Draw(img); draw.rectangle([10, 10, 190, 190], outline='black', width=2); draw.text((100, 80), '赞助', fill='black', anchor='mm'); draw.text((100, 100), '二维码', fill='black', anchor='mm'); draw.text((100, 120), '占位图', fill='gray', anchor='mm'); img.save('sponsor_qr.png')"
)

echo 🔨 开始打包...
echo 🪟 构建 Windows .exe 文件...

pyinstaller --noconfirm --windowed --onefile --name ClearMeta --add-data "sponsor_qr.png;." --add-data "README.md;." main.py

if exist "dist\ClearMeta.exe" (
    echo ✅ Windows 可执行文件构建成功！
    echo 📂 文件位置: dist\ClearMeta.exe
) else (
    echo ❌ 可执行文件构建失败
    pause
    exit /b 1
)

echo.
echo 🎉 构建完成！
echo 📁 输出目录: %CD%\dist\
echo 🚀 享受使用 ClearMeta！

pause
