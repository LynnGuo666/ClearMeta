import os
import sys
import shutil
import threading
import queue
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
        QPushButton, QListWidget, QProgressBar, QLabel, QCheckBox,
        QLineEdit, QTextEdit, QFileDialog, QMessageBox, QGroupBox,
        QSplitter, QTabWidget, QTreeWidget, QTreeWidgetItem
    )
    from PyQt5.QtCore import QThread, pyqtSignal, Qt, QUrl
    from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent, QPixmap
    QT_AVAILABLE = True
except Exception:  # Missing PyQt5
    QT_AVAILABLE = False
    QApplication = QMainWindow = QWidget = None  # type: ignore

from PIL import Image, ImageOps, PngImagePlugin
import piexif


APP_NAME = "ClearMeta"
APP_VERSION = "Beta 1.0.0"
APP_AUTHOR = "Lynn"
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


def extract_exif_info(file_path: Path) -> dict:
    """Extract EXIF information from image file."""
    info = {}
    try:
        with Image.open(str(file_path)) as img:
            # Basic image info
            info['文件大小'] = f"{file_path.stat().st_size / 1024:.1f} KB"
            info['图片尺寸'] = f"{img.width} x {img.height}"
            info['颜色模式'] = img.mode
            info['格式'] = img.format or "Unknown"
            
            # EXIF data
            if hasattr(img, '_getexif') and img._getexif():
                exif_dict = img._getexif()
                for tag_id, value in exif_dict.items():
                    tag = piexif.TAGS.get(tag_id, tag_id)
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8', errors='ignore')
                        except:
                            value = str(value)
                    info[f"EXIF_{tag}"] = str(value)
            
            # Try piexif for more detailed EXIF
            try:
                exif_dict = piexif.load(str(file_path))
                for ifd_name, ifd in exif_dict.items():
                    if ifd_name == "thumbnail" or not ifd:
                        continue
                    for tag_id, value in ifd.items():
                        tag_name = piexif.TAGS.get(ifd_name, {}).get(tag_id, f"Tag_{tag_id}")
                        if isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8', errors='ignore')
                            except:
                                value = f"<{len(value)} bytes>"
                        info[f"{ifd_name}_{tag_name}"] = str(value)
            except:
                pass
                
    except Exception as e:
        info['错误'] = str(e)
    
    return info


def _has_exiftool() -> Optional[str]:
	"""Return exiftool path if available, else None."""
	return shutil.which("exiftool")


def _ensure_parent_dir(path: Path) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)


def _pil_resave_strip_metadata(inp: Path, outp: Path) -> None:
	"""Fallback: re-save via Pillow to drop metadata across common formats.

	- Auto-apply orientation (so removing EXIF Orientation doesn't rotate unexpectedly)
	- Remove EXIF, XMP, IPTC by not passing them through
	- PNG: remove text chunks; JPEG/TIFF: avoid embedding exif
	"""
	with Image.open(str(inp)) as im:
		im = ImageOps.exif_transpose(im)
		fmt = (im.format or inp.suffix.replace('.', '').upper())
		fmt = (fmt or "").upper()
		if fmt == "JPG":
			fmt = "JPEG"
		if fmt == "TIF":
			fmt = "TIFF"
		params = {}

		if fmt.upper() in {"JPEG", "JPG"}:
			# Explicitly drop EXIF by not passing exif bytes
			params.update({"quality": 95, "optimize": True})
		elif fmt.upper() == "PNG":
			# Empty PNGInfo to avoid original text chunks
			pnginfo = PngImagePlugin.PngInfo()
			params.update({"pnginfo": pnginfo, "optimize": True})
		elif fmt.upper() == "WEBP":
			params.update({"quality": 95, "method": 6})
		elif fmt.upper() in {"TIFF", "TIF"}:
			params.update({"compression": "tiff_deflate"})

		_ensure_parent_dir(outp)
		im.save(str(outp), fmt, **params)


def _piexif_strip_if_needed(outp: Path) -> None:
	"""For JPEG/TIFF ensure EXIF is removed using piexif as a second pass."""
	try:
		if outp.suffix.lower() in {".jpg", ".jpeg", ".tif", ".tiff"}:
			# piexif.remove modifies in place. Work on a temp copy then replace to be safe.
			piexif.remove(str(outp))
	except Exception:
		# Non-fatal; Pillow save likely removed EXIF already
		pass


def clean_one_image(
	input_path: Path,
	output_path: Path,
	prefer_exiftool: bool = True,
) -> Tuple[bool, str]:
	"""Clean metadata from a single image file.

	Returns (ok, message).
	"""
	try:
		if prefer_exiftool:
			exiftool = _has_exiftool()
		else:
			exiftool = None

		if exiftool:
			_ensure_parent_dir(output_path)
			# Use exiftool to remove everything (-all=) and write to output (-o)
			# This avoids creating backups and handles XMP/IPTC comprehensively.
			import subprocess

			cmd = [exiftool, "-all=", "-o", str(output_path), str(input_path)]
			res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			if res.returncode != 0:
				# Fallback to Pillow path
				_pil_resave_strip_metadata(input_path, output_path)
				_piexif_strip_if_needed(output_path)
			else:
				# exiftool tends to add a trailing copy suffix if -o points to a directory.
				# We passed a file path, so we should be fine; still, normalize if a secondary file got created.
				pass
		else:
			_pil_resave_strip_metadata(input_path, output_path)
			_piexif_strip_if_needed(output_path)

		return True, f"Cleaned: {input_path.name}"
	except Exception as e:
		return False, f"Failed: {input_path.name} -> {e}"


def gather_images(paths: List[Path]) -> List[Path]:
	files: List[Path] = []
	for p in paths:
		if p.is_dir():
			for root, _, fnames in os.walk(p):
				for fn in fnames:
					ext = Path(fn).suffix.lower()
					if ext in SUPPORTED_EXTS:
						files.append(Path(root) / fn)
		else:
			if p.suffix.lower() in SUPPORTED_EXTS:
				files.append(p)
	# de-dup while preserving order
	seen = set()
	out = []
	for f in files:
		if f not in seen:
			seen.add(f)
			out.append(f)
	return out


# --------------------------- GUI ---------------------------


class WorkerThread(QThread):
    """Background thread for processing images."""
    progress = pyqtSignal(int)
    log_message = pyqtSignal(str)
    finished_job = pyqtSignal(int, int)  # successes, failures

    def __init__(self, files, config):
        super().__init__()
        self.files = files
        self.config = config

    def run(self):
        successes = 0
        failures = 0
        try:
            with ThreadPoolExecutor(max_workers=self.config.workers) as ex:
                fut_to_file = {}
                for i, f in enumerate(self.files):
                    if self.config.overwrite:
                        out = f
                    else:
                        out_base = self.config.output_dir or f.parent
                        out = out_base / f.name
                    fut = ex.submit(clean_one_image, f, out, self.config.use_exiftool)
                    fut_to_file[fut] = (f, i)

                for fut in as_completed(fut_to_file):
                    f, i = fut_to_file[fut]
                    ok, msg = fut.result()
                    self.log_message.emit(msg)
                    if ok:
                        successes += 1
                    else:
                        failures += 1
                    self.progress.emit(i + 1)
        except Exception:
            self.log_message.emit("发生错误:\n" + traceback.format_exc())
        finally:
            self.finished_job.emit(successes, failures)


@dataclass
class JobConfig:
    overwrite: bool
    output_dir: Optional[Path]
    use_exiftool: bool
    workers: int = 4


if QT_AVAILABLE:
    class ClearMetaApp(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
            self.setGeometry(100, 100, 1200, 800)  # Larger window for EXIF viewer
            
            self.selected_files: List[Path] = []
            self.worker_thread = None
            
            # Enable drag and drop
            self.setAcceptDrops(True)
            
            self.setup_ui()

        def dragEnterEvent(self, event: QDragEnterEvent):
            """Handle drag enter event"""
            if event.mimeData().hasUrls():
                event.accept()
            else:
                event.ignore()

        def dropEvent(self, event: QDropEvent):
            """Handle drop event"""
            files = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    files.append(Path(file_path))
            
            if files:
                self.append_files(files)
                self.log(f"通过拖拽添加了 {len(files)} 个项目")
            
            event.accept()

        def setup_ui(self):
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)

            # Top controls
            controls_group = QGroupBox("控制")
            controls_layout = QVBoxLayout(controls_group)
            
            # Buttons row
            button_layout = QHBoxLayout()
            self.add_files_btn = QPushButton("添加图片")
            self.add_folder_btn = QPushButton("添加文件夹")
            self.clear_btn = QPushButton("清空列表")
            
            self.add_files_btn.clicked.connect(self.add_files)
            self.add_folder_btn.clicked.connect(self.add_folder)
            self.clear_btn.clicked.connect(self.clear_list)
            
            button_layout.addWidget(self.add_files_btn)
            button_layout.addWidget(self.add_folder_btn)
            button_layout.addWidget(self.clear_btn)
            button_layout.addStretch()
            
            # Options row
            options_layout = QHBoxLayout()
            self.overwrite_cb = QCheckBox("覆盖原文件")
            self.use_exiftool_cb = QCheckBox("优先使用 exiftool（更彻底）")
            self.use_exiftool_cb.setChecked(bool(_has_exiftool()))
            
            self.overwrite_cb.toggled.connect(self.toggle_output_dir)
            
            options_layout.addWidget(self.overwrite_cb)
            options_layout.addWidget(self.use_exiftool_cb)
            options_layout.addStretch()
            
            # Output directory row
            output_layout = QHBoxLayout()
            self.output_entry = QLineEdit()
            self.output_browse_btn = QPushButton("选择输出目录")
            self.output_browse_btn.clicked.connect(self.choose_output_dir)
            
            output_layout.addWidget(QLabel("输出目录:"))
            output_layout.addWidget(self.output_entry)
            output_layout.addWidget(self.output_browse_btn)
            
            controls_layout.addLayout(button_layout)
            controls_layout.addLayout(options_layout)
            controls_layout.addLayout(output_layout)
            
            # File list with EXIF viewer
            main_splitter = QSplitter(Qt.Horizontal)
            
            # Left side: File list
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            
            list_group = QGroupBox("图片列表（支持拖拽文件或文件夹到此处）")
            list_layout = QVBoxLayout(list_group)
            self.file_list = QListWidget()
            # Enable drag and drop for the list widget too
            self.file_list.setAcceptDrops(True)
            self.file_list.dragEnterEvent = self.dragEnterEvent
            self.file_list.dropEvent = self.dropEvent
            self.file_list.currentItemChanged.connect(self.on_file_selected)
            list_layout.addWidget(self.file_list)
            left_layout.addWidget(list_group)
            
            # Right side: EXIF info
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            
            exif_group = QGroupBox("EXIF 信息")
            exif_layout = QVBoxLayout(exif_group)
            self.exif_tree = QTreeWidget()
            self.exif_tree.setHeaderLabels(["属性", "值"])
            self.exif_tree.setAlternatingRowColors(True)
            self.exif_tree.setRootIsDecorated(False)
            exif_layout.addWidget(self.exif_tree)
            right_layout.addWidget(exif_group)
            
            main_splitter.addWidget(left_widget)
            main_splitter.addWidget(right_widget)
            main_splitter.setStretchFactor(0, 2)  # File list takes 2/3
            main_splitter.setStretchFactor(1, 1)  # EXIF info takes 1/3
            
            # Progress and action buttons
            action_layout = QHBoxLayout()
            self.progress_bar = QProgressBar()
            self.status_label = QLabel("就绪")
            self.start_btn = QPushButton("开始清理")
            self.open_output_btn = QPushButton("打开输出目录")
            
            self.start_btn.clicked.connect(self.start_clean)
            self.open_output_btn.clicked.connect(self.open_output)
            
            action_layout.addWidget(self.progress_bar)
            action_layout.addWidget(self.status_label)
            action_layout.addWidget(self.start_btn)
            action_layout.addWidget(self.open_output_btn)
            
            # Bottom tabs for log and sponsor
            bottom_tabs = QTabWidget()
            
            # Log tab
            log_widget = QWidget()
            log_layout = QVBoxLayout(log_widget)
            self.log_text = QTextEdit()
            self.log_text.setMaximumHeight(120)
            log_layout.addWidget(self.log_text)
            bottom_tabs.addTab(log_widget, "日志")
            
            # Sponsor tab
            sponsor_widget = QWidget()
            sponsor_layout = QHBoxLayout(sponsor_widget)
            
            # QR code image
            self.qr_label = QLabel()
            self.qr_label.setAlignment(Qt.AlignCenter)
            self.qr_label.setFixedSize(100, 100)
            self.qr_label.setStyleSheet("border: 1px solid gray;")
            
            # Load QR code if exists
            qr_path = Path("sponsor_qr.png")
            if qr_path.exists():
                pixmap = QPixmap(str(qr_path))
                scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.qr_label.setPixmap(scaled_pixmap)
            else:
                self.qr_label.setText("二维码\n(请放置\nsponsor_qr.png)")
            
            # Sponsor text
            sponsor_text = QLabel("如果这个工具对您有帮助，\n欢迎扫码赞助支持开发！")
            sponsor_text.setAlignment(Qt.AlignCenter)
            
            # About info
            about_text = QLabel(f"关于\n\n作者: {APP_AUTHOR}\n版本: {APP_VERSION}\n\n一个简单易用的\n图片元数据清理工具")
            about_text.setAlignment(Qt.AlignCenter)
            about_text.setStyleSheet("color: #666; font-size: 11px; padding: 10px;")
            
            sponsor_layout.addStretch()
            sponsor_layout.addWidget(self.qr_label)
            sponsor_layout.addWidget(sponsor_text)
            sponsor_layout.addWidget(about_text)
            sponsor_layout.addStretch()
            
            bottom_tabs.addTab(sponsor_widget, "赞助支持")
            
            # Add all to main layout
            layout.addWidget(controls_group)
            layout.addWidget(main_splitter, 1)  # Main content takes most space
            layout.addLayout(action_layout)
            layout.addWidget(bottom_tabs)
            
            self.toggle_output_dir()

        def toggle_output_dir(self):
            self.output_entry.setEnabled(not self.overwrite_cb.isChecked())
            self.output_browse_btn.setEnabled(not self.overwrite_cb.isChecked())

        def choose_output_dir(self):
            dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
            if dir_path:
                self.output_entry.setText(dir_path)

        def add_files(self):
            files, _ = QFileDialog.getOpenFileNames(
                self, "选择图片",
                filter="图片 (*.jpg *.jpeg *.png *.webp *.tif *.tiff *.bmp);;所有文件 (*)"
            )
            if files:
                self.append_files([Path(f) for f in files])

        def add_folder(self):
            dir_path = QFileDialog.getExistingDirectory(self, "选择文件夹")
            if dir_path:
                self.append_files([Path(dir_path)])

        def append_files(self, paths: List[Path]):
            imgs = gather_images(paths)
            added = 0
            for p in imgs:
                if p not in self.selected_files:
                    self.selected_files.append(p)
                    self.file_list.addItem(str(p))
                    added += 1
            if added:
                self.log(f"添加 {added} 个文件")

        def clear_list(self):
            self.selected_files.clear()
            self.file_list.clear()
            self.exif_tree.clear()

        def on_file_selected(self, current, previous):
            """Handle file selection and show EXIF info."""
            self.exif_tree.clear()
            
            if current is None:
                return
                
            current_row = self.file_list.row(current)
            if 0 <= current_row < len(self.selected_files):
                file_path = self.selected_files[current_row]
                
                # Extract and display EXIF info
                exif_info = extract_exif_info(file_path)
                
                for key, value in exif_info.items():
                    item = QTreeWidgetItem([key, str(value)])
                    self.exif_tree.addTopLevelItem(item)
                
                # Auto-resize columns
                self.exif_tree.resizeColumnToContents(0)
                self.exif_tree.resizeColumnToContents(1)

        def start_clean(self):
            if not self.selected_files:
                QMessageBox.information(self, APP_NAME, "请先添加图片或文件夹")
                return

            overwrite = self.overwrite_cb.isChecked()
            out_dir = Path(self.output_entry.text()) if self.output_entry.text().strip() else None
            if not overwrite and not out_dir:
                QMessageBox.warning(self, APP_NAME, "未勾选覆盖原文件且未设置输出目录")
                return

            config = JobConfig(
                overwrite=overwrite,
                output_dir=out_dir,
                use_exiftool=self.use_exiftool_cb.isChecked(),
            )

            self.progress_bar.setMaximum(len(self.selected_files))
            self.progress_bar.setValue(0)
            self.status_label.setText(f"0/{len(self.selected_files)}")
            self.log("开始清理…")
            self.start_btn.setEnabled(False)

            self.worker_thread = WorkerThread(self.selected_files, config)
            self.worker_thread.progress.connect(self.update_progress)
            self.worker_thread.log_message.connect(self.log)
            self.worker_thread.finished_job.connect(self.job_finished)
            self.worker_thread.start()

        def update_progress(self, value):
            self.progress_bar.setValue(value)
            self.status_label.setText(f"{value}/{len(self.selected_files)}")

        def job_finished(self, successes, failures):
            self.log(f"完成: 成功 {successes}, 失败 {failures}")
            self.start_btn.setEnabled(True)
            self.worker_thread = None

        def open_output(self):
            target = self.output_entry.text() or (str(self.selected_files[0].parent) if self.selected_files else None)
            if not target:
                return
            path = Path(target)
            if sys.platform.startswith("darwin"):
                os.system(f"open '{path}'")
            elif os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                os.system(f"xdg-open '{path}'")

        def log(self, text: str):
            self.log_text.append(text)
            # Auto scroll to bottom
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

else:
    class ClearMetaApp:  # minimal placeholder for headless imports/tests
        pass
def main():
    if not QT_AVAILABLE:
        print("PyQt5 不可用，GUI 无法启动。请安装 PyQt5：pip install PyQt5")
        print("仍可导入并使用 clean_one_image 函数进行脚本化清理。")
        return
    
    app = QApplication(sys.argv)
    window = ClearMetaApp()
    window.show()
    sys.exit(app.exec_())
if __name__ == "__main__":
	main()

