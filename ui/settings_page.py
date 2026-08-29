from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, QTimer, Signal, Qt
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QRadioButton, QToolButton, QVBoxLayout,
    QToolTip, QWidget,
)

from core import Keys
from services.apk_extractor import ApkKeyExtractor
from services.keys import KeyService


class HelpButton(QToolButton):
    """Help icon with a predictable one-second, readable tooltip delay."""

    def __init__(self, text: str):
        super().__init__()
        self.setObjectName("helpButton")
        self.setText("?")
        self.setFixedSize(20, 20)
        self._help_text = text
        self._tooltip_timer = QTimer(self)
        self._tooltip_timer.setSingleShot(True)
        self._tooltip_timer.setInterval(1000)
        self._tooltip_timer.timeout.connect(self._show_help)

    def enterEvent(self, event):
        self._tooltip_timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._tooltip_timer.stop()
        QToolTip.hideText()
        super().leaveEvent(event)

    def _show_help(self):
        QToolTip.showText(self.mapToGlobal(QPoint(self.width() + 6, 0)), self._help_text, self)


class SettingsPage(QWidget):
    settingsChanged = Signal()

    def __init__(self, settings_service, key_service: KeyService):
        super().__init__()
        self.settings_service = settings_service
        self.key_service = key_service

        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("No default output folder")
        output_browse = QPushButton("Browse")
        output_clear = QPushButton("Clear")
        output_browse.clicked.connect(self._browse_output)
        output_clear.clicked.connect(self._clear_output)
        self.auto_export = QCheckBox("Automatically export processed files to this folder")
        self.auto_export.toggled.connect(self._toggle_auto_export)

        self.key_edits = {}
        key_form = QFormLayout()
        for field, label in (("v1_aes_key", "V1 AES Key"), ("v2_raw_key", "V2 Encryption Key"), ("v2_signature", "V2 Signature"), ("hmac_key", "HMAC Encryption Key")):
            edit = QLineEdit()
            edit.editingFinished.connect(self._save_keys)
            self.key_edits[field] = edit
            key_form.addRow(label, edit)
        import_txt = QPushButton("Import from TXT")
        import_apk = QPushButton("Import from APK/XAPK")
        import_txt.clicked.connect(self._import_txt)
        import_apk.clicked.connect(self._import_apk)
        key_buttons = QHBoxLayout()
        key_buttons.addWidget(import_txt); key_buttons.addWidget(import_apk); key_buttons.addStretch()

        self.temp_path = QLineEdit()
        self.temp_path.setPlaceholderText("System default")
        temp_browse = QPushButton("Browse")
        temp_clear = QPushButton("Clear")
        temp_browse.clicked.connect(self._browse_temp)
        temp_clear.clicked.connect(self._clear_temp)
        self.temp_browse, self.temp_clear = temp_browse, temp_clear

        self.user_radio = QRadioButton("User folder")
        self.program_radio = QRadioButton("Program folder")
        self.user_radio.toggled.connect(lambda checked: self._change_location("user") if checked else None)
        self.program_radio.toggled.connect(lambda checked: self._change_location("program") if checked else None)
        location_row = QHBoxLayout(); location_row.addWidget(self.user_radio); location_row.addWidget(self.program_radio); location_row.addStretch()
        self.program_radio.setEnabled(self.settings_service.is_writable())
        if not self.program_radio.isEnabled(): self.program_radio.setToolTip("The program folder is not writable. Use the user settings folder or move the application to a writable location.")

        general = QGroupBox("General")
        general_form = QFormLayout(general)
        output_row = QHBoxLayout(); output_row.addWidget(self.output_path, 1); output_row.addWidget(output_browse); output_row.addWidget(output_clear)
        general_form.addRow(self._label_with_help("Default Output Folder", "<b>Default Output Folder</b><br>Choose a default folder for &quot;Export Files&quot; dialog.<br>Leave empty or clear it to use the default.<br><br><b>Automatically export processed files to this folder</b><br>When set, processed files will be automatically saved to this location without manual exporting."), output_row)
        general_form.addRow("", self.auto_export)
        general_form.addRow(self._label_with_help("Encryption / Decryption Keys", "<b>Encryption / Decryption Keys</b><br>Required by encryption and decryption process.<br>Automatically detected if a valid key.txt exists.<br><br>If no valid key.txt exists, you can supply these<br>keys yourself. Alternatively, import them from<br>either a txt file or source an APK/XAPK file of<br>Tokyo 7th Sisters.<br><br>Importing from X/APK only works with the <b><i>final</i></b><br>version of Tokyo 7th Sisters."), key_form)
        general_form.addRow("", key_buttons)

        advanced = QGroupBox("Advanced")
        advanced_form = QFormLayout(advanced)
        temp_row = QHBoxLayout(); temp_row.addWidget(self.temp_path, 1); temp_row.addWidget(temp_browse); temp_row.addWidget(temp_clear)
        advanced_form.addRow(self._label_with_help("Temporary Folder Location", "Controls where temporary processed files<br>are stored before export.<br>Leave empty to use the system default."), temp_row)
        advanced_form.addRow(self._label_with_help("Settings Location", "User folder is <b><i>recommended</i></b>.<br>Program folder enables portable mode."), location_row)

        layout = QVBoxLayout(self); layout.setContentsMargins(32, 28, 32, 24); layout.setSpacing(18)
        title = QLabel("Settings"); title.setObjectName("pageTitle"); layout.addWidget(title); layout.addWidget(general); layout.addWidget(advanced); layout.addStretch()
        self._load_values()

    @staticmethod
    def _label_with_help(text: str, tip: str) -> QWidget:
        widget = QWidget(); row = QHBoxLayout(widget); row.setContentsMargins(0, 0, 8, 0)
        label = QLabel(text); label.setObjectName("settingLabel")
        row.addWidget(label); row.addWidget(HelpButton(tip)); row.addStretch()
        return widget

    def _load_values(self):
        settings = self.settings_service.settings
        if settings.default_folder: self.output_path.setText(settings.default_folder)
        if settings.temp_folder: self.temp_path.setText(settings.temp_folder)
        self.auto_export.blockSignals(True); self.auto_export.setChecked(settings.auto_export); self.auto_export.blockSignals(False)
        try: keys = self.key_service.load_active()
        except Exception: keys = Keys()
        for field, edit in self.key_edits.items(): edit.setText((getattr(keys, field) or b"").decode("utf-8", errors="replace"))
        self.user_radio.blockSignals(True); self.program_radio.blockSignals(True)
        (self.program_radio if self.settings_service.active_location == "program" else self.user_radio).setChecked(True)
        self.user_radio.blockSignals(False); self.program_radio.blockSignals(False)
        self._update_temp_enabled()

    def _save_settings(self):
        try:
            self.settings_service.save(); self.settingsChanged.emit()
        except OSError as exc: QMessageBox.warning(self, "Settings", f"Could not save settings: {exc}")

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Choose default output folder", self.output_path.text())
        if path: self.output_path.setText(path); self.settings_service.settings.default_folder = path; self._save_settings()

    def _clear_output(self):
        self.output_path.clear(); self.settings_service.settings.default_folder = None; self.settings_service.settings.auto_export = False
        self.auto_export.setChecked(False); self._save_settings()

    def _toggle_auto_export(self, checked: bool):
        if checked:
            folder = Path(self.output_path.text()) if self.output_path.text() else None
            if not folder or not self._valid_folder(folder):
                QMessageBox.warning(self, "Automatic export", "Choose a writable default output folder first.")
                self.auto_export.blockSignals(True); self.auto_export.setChecked(False); self.auto_export.blockSignals(False); return
        self.settings_service.settings.auto_export = checked; self._update_temp_enabled(); self._save_settings()

    @staticmethod
    def _valid_folder(path: Path) -> bool:
        try:
            path.mkdir(parents=True, exist_ok=True); probe = path / ".t7s-folder-test"; probe.write_text("", encoding="utf-8"); probe.unlink(); return True
        except OSError: return False

    def _save_keys(self):
        try:
            keys = Keys(**{field: (edit.text().encode("utf-8") if edit.text() else None) for field, edit in self.key_edits.items()})
            self.key_service.save(keys)
            self.settingsChanged.emit()
        except Exception as exc: QMessageBox.warning(self, "Keys", f"Keys were not saved: {exc}")

    def _apply_keys(self, keys: Keys):
        for field, edit in self.key_edits.items(): edit.setText((getattr(keys, field) or b"").decode("utf-8"))
        self._save_keys()

    def _import_txt(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import key file", "", "Text files (*.txt);;All files (*)")
        if not path: return
        try: self._apply_keys(self.key_service.from_text(Path(path)))
        except Exception as exc: QMessageBox.warning(self, "Import keys", f"Could not import keys: {exc}")

    def _import_apk(self):
        notice = QMessageBox(QMessageBox.Icon.Information, "APK/XAPK key extraction", "Select the base APK or XAPK from the final game version (13.0.2). Keys extracted from other versions may not be compatible.", QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel, self)
        if notice.exec() != QMessageBox.StandardButton.Ok: return
        path, _ = QFileDialog.getOpenFileName(self, "Import from APK/XAPK", "", "APK/XAPK files (*.apk *.xapk)")
        if not path: return
        try:
            keys = ApkKeyExtractor.extract(Path(path)); self._apply_keys(keys)
            QMessageBox.information(self, "Import keys", "✓ V1 AES Key found\n✓ V2 Encryption Key found\n✓ V2 Signature found\n✓ HMAC Encryption Key found")
        except Exception as exc: QMessageBox.critical(self, "APK/XAPK extraction failed", str(exc))

    def _browse_temp(self):
        path = QFileDialog.getExistingDirectory(self, "Choose temporary folder", self.temp_path.text())
        if path and self._valid_folder(Path(path)):
            self.temp_path.setText(path); self.settings_service.settings.temp_folder = path; self._save_settings()

    def _clear_temp(self):
        self.temp_path.clear(); self.settings_service.settings.temp_folder = None; self._save_settings()

    def _update_temp_enabled(self):
        enabled = not self.auto_export.isChecked()
        for control in (self.temp_path, self.temp_browse, self.temp_clear): control.setEnabled(enabled)
        if not enabled:
            tip = "Automatic export is enabled, so completed files use temporary files in the destination location instead of the normal session temp folder."
            self.temp_path.setToolTip(tip); self.temp_browse.setToolTip(tip); self.temp_clear.setToolTip(tip)

    def _change_location(self, location: str):
        if location == self.settings_service.active_location: return
        try:
            current = Keys(**{field: (edit.text().encode("utf-8") if edit.text() else None) for field, edit in self.key_edits.items()})
            self.key_service.validate(current)
            self.settings_service.switch_location(location, self.key_service.to_text(current))
            self.settingsChanged.emit()
        except Exception as exc:
            QMessageBox.warning(self, "Settings location", f"Could not switch settings location: {exc}")
            self.user_radio.blockSignals(True); self.program_radio.blockSignals(True)
            (self.program_radio if self.settings_service.active_location == "program" else self.user_radio).setChecked(True)
            self.user_radio.blockSignals(False); self.program_radio.blockSignals(False)
