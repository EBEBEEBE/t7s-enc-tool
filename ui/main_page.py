from __future__ import annotations

import csv
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QMimeData, QObject, QRunnable, Qt, QThreadPool, Signal, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog, QFrame, QHBoxLayout, QLabel, QMenu, QMessageBox, QPushButton,
    QComboBox, QProgressBar, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from core import Keys, ProcessResult, build_output_path, process_file
from core.detection import choose_mode
from services.export import ExportService
from services.keys import KeyService
from services.settings import SettingsService
from services.tempfiles import TempFileService


@dataclass
class QueueItem:
    source: Path
    output: Path | None = None
    result: ProcessResult | None = None
    started: bool = False


class NumericTableItem(QTableWidgetItem):
    def __init__(self, text: str, value: int | None):
        super().__init__(text)
        self.setData(Qt.ItemDataRole.UserRole, value if value is not None else -1)

    def __lt__(self, other):
        if isinstance(other, QTableWidgetItem):
            left = self.data(Qt.ItemDataRole.UserRole)
            right = other.data(Qt.ItemDataRole.UserRole)
            if left is not None and right is not None:
                return left < right
        return super().__lt__(other)


class WorkerSignals(QObject):
    done = Signal(object, object)


class ProcessWorker(QRunnable):
    def __init__(self, row: int, item: QueueItem, keys: Keys, requested_mode: str | None, temp_root: Path):
        super().__init__()
        self.row = row
        self.item = item
        self.keys = keys
        self.requested_mode = requested_mode
        self.temp_root = temp_root
        self.signals = WorkerSignals()

    def run(self):
        try:
            command = "decrypt" if self.item.source.suffix.lower() == ".enc" else "encrypt"
            version, _ = choose_mode(self.item.source, command, self.requested_mode)
            output_dir = self.temp_root / str(self.row)
            output_dir.mkdir(parents=True, exist_ok=True)
            output = build_output_path(
                self.item.source, self.item.source.parent, output_dir, False,
                command, version, self.keys,
            )
            result = process_file(self.item.source, output, command, self.keys, self.requested_mode)
        except Exception as exc:
            result = ProcessResult(self.item.source, self.temp_root / self.item.source.name, command if "command" in locals() else "unknown", self.requested_mode, "unknown", error=str(exc))
        self.signals.done.emit(self.item, result)


class DropZone(QFrame):
    filesDropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Drop files here")
        title.setObjectName("dropTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint = QLabel(".enc files decrypt automatically; other files encrypt")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(hint)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event):
        self.filesDropped.emit([Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()])
        event.acceptProposedAction()


class MainPage(QWidget):
    HEADERS = ["Status", "File", "Action", "File Type", "Mode", "Input Size", "Output Size", "Error"]

    def __init__(self, settings_service: SettingsService | None = None, key_service: KeyService | None = None, temp_service: TempFileService | None = None, export_service: ExportService | None = None):
        super().__init__()
        self.settings_service = settings_service
        self.key_service = key_service
        self.temp_service = temp_service or TempFileService()
        self.export_service = export_service or ExportService()
        self.items: list[QueueItem] = []
        self.thread_pool = QThreadPool.globalInstance()
        self.temp_root = self._new_temp_root()
        self.table = QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        self.table.cellDoubleClicked.connect(lambda row, col: self.open_output(row))
        self.table.setAlternatingRowColors(True)

        title = QLabel("Asset processing")
        title.setObjectName("pageTitle")
        self.mode = QComboBox()
        for label, value in (("Auto", None), ("V1", "v1"), ("V2", "v2"), ("V2 with LZ4", "v2z")):
            self.mode.addItem(label, value)
        add = QPushButton("Add files")
        add.setObjectName("primary")
        add.clicked.connect(self._choose_files)
        toolbar = QHBoxLayout()
        toolbar.addWidget(title)
        toolbar.addStretch()
        toolbar.addWidget(QLabel("Mode:"))
        toolbar.addWidget(self.mode)
        toolbar.addWidget(add)

        self.drop_zone = DropZone()
        self.drop_zone.setMinimumHeight(150)
        self.drop_zone.filesDropped.connect(self.add_paths)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.count = QLabel("0 / 0")
        clear = QPushButton("Clear Queue")
        export = QPushButton("Export Files")
        csv_button = QPushButton("Export CSV")
        clear.clicked.connect(self.clear_queue)
        export.clicked.connect(self.export_files)
        csv_button.clicked.connect(self.export_csv)
        bottom = QHBoxLayout()
        bottom.addWidget(self.count)
        bottom.addWidget(self.progress, 1)
        bottom.addStretch()
        bottom.addWidget(clear)
        bottom.addWidget(export)
        bottom.addWidget(csv_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.addLayout(toolbar)
        layout.addWidget(self.drop_zone)
        layout.addWidget(self.table, 1)
        layout.addLayout(bottom)

    def _choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose asset files")
        if paths: self.add_paths([Path(path) for path in paths])

    def add_paths(self, paths: list[Path]):
        expanded = []
        for path in paths:
            if path.is_dir(): expanded.extend(p for p in path.rglob("*") if p.is_file())
            elif path.is_file(): expanded.append(path)
        existing = {item.source.resolve() for item in self.items}
        new_items = [QueueItem(path) for path in sorted(expanded) if path.resolve() not in existing]
        for item in new_items:
            self.items.append(item)
            self._append_row(item)
        if new_items: self._start_items(len(self.items) - len(new_items))

    def _append_row(self, item: QueueItem):
        row = self.table.rowCount()
        self.table.setSortingEnabled(False)
        self.table.insertRow(row)
        action = "Decrypt" if item.source.suffix.lower() == ".enc" else "Encrypt"
        values = ["Queued", item.source.name, action, item.source.suffix.lower() or "(none)", self.mode.currentText(), self._size(item.source.stat().st_size), "—", ""]
        for column, value in enumerate(values):
            if column == 5:
                cell = NumericTableItem(value, item.source.stat().st_size)
            elif column == 6:
                cell = NumericTableItem(value, None)
            else:
                cell = QTableWidgetItem(value)
            if column == 1: cell.setToolTip(str(item.source))
            if column == 1: cell.setData(Qt.ItemDataRole.UserRole, str(item.source.resolve()))
            self.table.setItem(row, column, cell)
        self.table.setSortingEnabled(True)

    def _row_for_item(self, item: QueueItem) -> int:
        source = str(item.source.resolve())
        for row in range(self.table.rowCount()):
            file_cell = self.table.item(row, 1)
            if file_cell and file_cell.data(Qt.ItemDataRole.UserRole) == source:
                return row
        return -1

    def _item_for_row(self, row: int) -> QueueItem | None:
        if row < 0 or row >= self.table.rowCount(): return None
        file_cell = self.table.item(row, 1)
        source = file_cell.data(Qt.ItemDataRole.UserRole) if file_cell else None
        return next((item for item in self.items if str(item.source.resolve()) == source), None)

    def _set_status(self, row: int, status: str):
        cell = self.table.item(row, 0)
        if not cell: return
        cell.setText(status)
        if status == "Completed":
            cell.setBackground(QColor("#bbf7d0"))
            cell.setForeground(QColor("#166534"))
        elif status == "Failed":
            cell.setBackground(QColor("#fecaca"))
            cell.setForeground(QColor("#991b1b"))

    def _start_items(self, first_row: int):
        try: keys = self.key_service.load_active() if self.key_service else Keys.from_file(Path("key.txt"))
        except Exception as exc:
            for row in range(first_row, len(self.items)):
                self._finish(self.items[row], ProcessResult(self.items[row].source, self.temp_root / self.items[row].source.name, "unknown", self.mode.currentData(), "unknown", error=str(exc)))
            return
        requested = self.mode.currentData()
        for row in range(first_row, len(self.items)):
            item = self.items[row]
            item.started = True
            current_row = self._row_for_item(item)
            if current_row >= 0: self._set_status(current_row, "Processing")
            worker = ProcessWorker(row, item, keys, requested, self.temp_root)
            worker.signals.done.connect(self._finish)
            self.thread_pool.start(worker)
        self.progress.setVisible(True)
        self._update_count()

    def _new_temp_root(self) -> Path:
        if self.settings_service:
            settings = self.settings_service.settings
            folder = settings.default_folder if settings.auto_export and settings.default_folder else settings.temp_folder
            return self.temp_service.create_session(folder)
        return Path(tempfile.mkdtemp(prefix="t7s-assetcrypt-"))

    def apply_settings(self):
        if self.settings_service:
            self.temp_root = self._new_temp_root()

    def _finish(self, item: QueueItem, result: ProcessResult):
        if item not in self.items: return
        item.result, item.output = result, result.output_path
        if result.success and self.settings_service and self.settings_service.settings.auto_export and self.settings_service.settings.default_folder:
            try:
                temporary_output = result.output_path
                result.output_path = self.export_service.export_file(item.source, temporary_output, result, Path(self.settings_service.settings.default_folder))
                temporary_output.unlink(missing_ok=True)
                shutil.rmtree(temporary_output.parent, ignore_errors=True)
                try:
                    self.temp_root.rmdir()
                except OSError:
                    pass
                item.output = result.output_path
                result.output_size = result.output_path.stat().st_size
            except Exception as exc:
                result.success = False
                result.error = f"Automatic export failed: {exc}"
        current_row = self._row_for_item(item)
        if current_row < 0: return
        self.table.setSortingEnabled(False)
        self.table.item(current_row, 4).setText(result.resolved_mode)
        output_cell = NumericTableItem(self._size(result.output_size), result.output_size)
        self.table.setItem(current_row, 6, output_cell)
        self.table.item(current_row, 7).setText(result.error or "")
        self._set_status(current_row, "Completed" if result.success else "Failed")
        self.table.setSortingEnabled(True)
        self._update_count()

    def _update_count(self):
        done = sum(1 for item in self.items if item.result is not None)
        self.count.setText(f"{done} / {len(self.items)}")
        self.progress.setVisible(bool(self.items) and done < len(self.items))

    @staticmethod
    def _size(size: int | None) -> str:
        if size is None: return "—"
        return f"{size:,} B"

    def _selected_items(self):
        rows = sorted({index.row() for index in self.table.selectedIndexes()})
        selected = [item for row in rows if (item := self._item_for_row(row)) is not None]
        return selected if selected else [item for item in self.items if item.result and item.result.success]

    def open_output(self, row: int):
        item = self._item_for_row(row)
        if item is None: return
        if item.output and item.output.exists(): QDesktopServices.openUrl(QUrl.fromLocalFile(str(item.output)))

    def _context_menu(self, position):
        row = self.table.indexAt(position).row()
        if row < 0: return
        item = self._item_for_row(row)
        if item is None: return
        self.table.selectRow(row)
        menu = QMenu(self)
        menu.addAction("Open File", lambda: self.open_output(row))
        menu.addAction("Locate File", lambda: self._locate(item.output))
        menu.addAction("Copy File", self.copy_files)
        menu.addAction("Copy Log", self.copy_log)
        menu.exec(self.table.viewport().mapToGlobal(position))

    def _locate(self, path: Path | None):
        if not path: return
        if os.name == "nt": subprocess.Popen(["explorer", "/select,", str(path)])
        else: QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))

    def copy_files(self):
        urls = [QUrl.fromLocalFile(str(item.output)) for item in self._selected_items() if item.output and item.output.exists()]
        mime = QMimeData(); mime.setUrls(urls)
        QApplication.clipboard().setMimeData(mime)

    def copy_log(self):
        lines = []
        for item in self._selected_items():
            result = item.result
            if result: lines.append(f"Source: {result.source_path}\nOutput: {result.output_path}\nAction: {result.action}\nMode: {result.resolved_mode}\nStatus: {'Completed' if result.success else 'Failed'}\nInput size: {self._size(result.input_size)}\nOutput size: {self._size(result.output_size)}\nError: {result.error or ''}")
        QApplication.clipboard().setText("\n\n".join(lines))

    def clear_queue(self):
        self.thread_pool.clear()
        shutil.rmtree(self.temp_root, ignore_errors=True)
        self.temp_root = self._new_temp_root()
        self.items.clear(); self.table.setRowCount(0); self._update_count()

    def export_files(self):
        default = self.settings_service.settings.default_folder if self.settings_service else ""
        target = QFileDialog.getExistingDirectory(self, "Export processed files", default or "")
        if not target: return
        for item in self._selected_items():
            if not item.result or not item.result.success or not item.output: continue
            try:
                self.export_service.export_file(item.source, item.output, item.result, Path(target))
            except Exception as exc:
                QMessageBox.warning(self, "Export files", f"Could not export {item.source.name}: {exc}")

    def export_csv(self):
        target, _ = QFileDialog.getSaveFileName(self, "Export queue CSV", "assetcrypt_queue.csv", "CSV files (*.csv)")
        if not target: return
        with open(target, "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Source", "Output", "Action", "Requested Mode", "Resolved Mode", "File Type", "Input Size", "Output Size", "Status", "Error"])
            for item in self.items:
                result = item.result
                writer.writerow([item.source, result.output_path if result else "", result.action if result else "", result.requested_mode if result else self.mode.currentData(), result.resolved_mode if result else "", item.source.suffix, result.input_size if result else "", result.output_size if result else "", "Completed" if result and result.success else "Failed" if result else "🕒Queued", result.error if result else ""])

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)

    def cleanup(self):
        self.thread_pool.clear()
        shutil.rmtree(self.temp_root, ignore_errors=True)
