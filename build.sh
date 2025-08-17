#!/bin/bash

# ClearMeta 自动构建脚本
# 用于打包 PyQt5 应用为可执行文件

set -e  # 遇到错误时退出

echo "🚀 开始构建 ClearMeta..."

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 未找到虚拟环境，请先运行："
    echo "python3 -m venv .venv"
    echo "source .venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

echo "📦 安装/更新依赖..."
pip install -r requirements.txt

echo "🧹 清理旧构建文件..."
rm -rf build/ dist/ *.spec.bak

# 检查必要文件
if [ ! -f "sponsor_qr.png" ]; then
    echo "⚠️  未找到 sponsor_qr.png，创建占位图片..."
    python3 -c "
from PIL import Image, ImageDraw
img = Image.new('RGB', (200, 200), color='white')
draw = ImageDraw.Draw(img)
draw.rectangle([10, 10, 190, 190], outline='black', width=2)
draw.text((100, 80), '赞助', fill='black', anchor='mm')
draw.text((100, 100), '二维码', fill='black', anchor='mm')
draw.text((100, 120), '占位图', fill='gray', anchor='mm')
img.save('sponsor_qr.png')
"
fi

echo "🔨 开始打包..."

# 根据平台选择打包方式
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 检测到 macOS，构建 .app 应用包..."
    pyinstaller ClearMeta.spec
    
    if [ -d "dist/ClearMeta.app" ]; then
        echo "✅ macOS 应用包构建成功！"
        echo "📂 应用位置: dist/ClearMeta.app"
        echo "💡 可以直接拖拽到 Applications 文件夹"
        
        # 可选：创建 DMG 文件
        read -p "🤔 是否创建 DMG 安装包？(y/N): " create_dmg
        if [[ $create_dmg =~ ^[Yy]$ ]]; then
            if command -v create-dmg &> /dev/null; then
                echo "📀 创建 DMG 文件..."
                create-dmg \
                    --volname "ClearMeta" \
                    --window-pos 200 120 \
                    --window-size 600 300 \
                    --icon-size 100 \
                    --icon "ClearMeta.app" 175 120 \
                    --hide-extension "ClearMeta.app" \
                    --app-drop-link 425 120 \
                    "dist/ClearMeta.dmg" \
                    "dist/"
                echo "✅ DMG 文件创建完成: dist/ClearMeta.dmg"
            else
                echo "⚠️  未安装 create-dmg，跳过 DMG 创建"
                echo "💡 安装命令: brew install create-dmg"
            fi
        fi
    else
        echo "❌ 应用包构建失败"
        exit 1
    fi
    
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "🪟 检测到 Windows，构建 .exe 文件..."
    pyinstaller --noconfirm --windowed --onefile \
        --name ClearMeta \
        --add-data "sponsor_qr.png;." \
        --add-data "README.md;." \
        main.py
    
    if [ -f "dist/ClearMeta.exe" ]; then
        echo "✅ Windows 可执行文件构建成功！"
        echo "📂 文件位置: dist/ClearMeta.exe"
    else
        echo "❌ 可执行文件构建失败"
        exit 1
    fi
    
else
    echo "🐧 检测到 Linux，构建可执行文件..."
    pyinstaller --noconfirm --windowed \
        --name ClearMeta \
        --add-data "sponsor_qr.png:." \
        --add-data "README.md:." \
        main.py
    
    if [ -f "dist/ClearMeta/ClearMeta" ]; then
        echo "✅ Linux 可执行文件构建成功！"
        echo "📂 文件位置: dist/ClearMeta/"
        echo "💡 运行命令: ./dist/ClearMeta/ClearMeta"
    else
        echo "❌ 可执行文件构建失败"
        exit 1
    fi
fi

echo ""
echo "🎉 构建完成！"
echo "📁 输出目录: $(pwd)/dist/"

# 显示文件大小
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "📏 应用大小: $(du -sh dist/ClearMeta.app | cut -f1)"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "📏 文件大小: $(du -sh dist/ClearMeta.exe | cut -f1)"
else
    echo "📏 目录大小: $(du -sh dist/ClearMeta | cut -f1)"
fi

echo ""
echo "🚀 享受使用 ClearMeta！"
