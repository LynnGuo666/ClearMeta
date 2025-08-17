# GitHub Actions 自动构建说明

## 工作流文件

### `release.yml` - 自动构建和发布
- **触发条件**: 推送版本标签 (如 `v1.0.0`) 或手动触发
- **功能**: 自动构建三个平台版本并创建 GitHub Release
- **并行构建**: Windows、macOS、Linux 同时构建
- **输出**: 发布页面中的下载文件

## 使用方法

### 发布新版本
1. 更新代码中的版本号 (`APP_VERSION`)
2. 提交并推送代码:
   ```bash
   git add .
   git commit -m "Release v1.0.0"
   git push
   ```
3. 创建并推送标签:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
4. GitHub Actions 自动构建并创建 Release

### 手动测试构建
1. 进入 GitHub 仓库的 Actions 页面
2. 选择 "Build and Release" 工作流
3. 点击 "Run workflow"
4. 等待构建完成后下载 Artifacts

## 构建输出

### Windows
- 文件: `ClearMeta.exe`
- 格式: 单文件可执行程序 (.zip 压缩包)
- 大小: ~50-80MB

### macOS
- 文件: `ClearMeta.app`
- 格式: 应用程序包 (.tar.gz 压缩包)
- 安装: 拖拽到 Applications 文件夹

### Linux
- 文件: `ClearMeta/ClearMeta`
- 格式: 可执行文件目录 (.tar.gz 压缩包)
- 运行: `./ClearMeta/ClearMeta`

## 注意事项

1. **权限要求**: 需要 GitHub 仓库的 write 权限
2. **构建时间**: 每个平台约 5-10 分钟
3. **资源包含**: 自动包含赞助二维码和说明文档
4. **依赖处理**: 自动安装所有 Python 依赖

## 自定义构建

如需修改构建配置，编辑 `.github/workflows/build.yml`:

- 添加图标: 在 PyInstaller 命令中添加 `--icon=icon.ico`
- 修改文件名: 更改 `--name` 参数
- 包含额外文件: 添加更多 `--add-data` 参数
- 调整构建选项: 修改 PyInstaller 参数

## 发布模板

GitHub Release 会自动生成包含以下信息的描述:
- 版本功能特性
- 下载说明
- 作者和版本信息
- 使用提示

## 故障排除

- **构建失败**: 检查 requirements.txt 和依赖兼容性
- **文件缺失**: 确保 sponsor_qr.png 存在或由脚本创建
- **权限错误**: 检查 GitHub Token 权限设置
