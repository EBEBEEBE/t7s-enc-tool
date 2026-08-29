import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLineEdit

from services.keys import KeyService
from services.settings import SettingsService
from services.tempfiles import TempFileService
from ui.main_page import MainPage
from ui.settings_page import SettingsPage


class TestSettingsUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_auto_export_disables_temp_controls(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            service = SettingsService(root / "program", root / "user")
            keys = KeyService(service)
            page = SettingsPage(service, keys)
            page.output_path.setText(str(root / "exports"))
            service.settings.default_folder = str(root / "exports")
            page.auto_export.setChecked(True)
            self.assertFalse(page.temp_path.isEnabled())
            self.assertFalse(page.temp_browse.isEnabled())
            self.assertFalse(page.temp_clear.isEnabled())
            page.auto_export.setChecked(False)
            self.assertTrue(page.temp_path.isEnabled())
            self.assertEqual(page.key_edits["v1_aes_key"].echoMode(), QLineEdit.EchoMode.Normal)
            page.deleteLater()

    def test_main_page_automatically_exports_successful_job(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); program = root / "program"; user = root / "user"; target = root / "exports"
            program.mkdir()
            (program / "key.txt").write_text("V1AESKey = 0123456789abcdef\nV2Key = fedcba9876543210\nV2Signature = t7s-enc\nHMACKey = hmac-secret12345\n", encoding="utf-8")
            source = root / "payload.json"; source.write_text('{"ok": true}', encoding="utf-8")
            settings = SettingsService(program, user)
            settings.settings.default_folder = str(target)
            settings.settings.auto_export = True
            page = MainPage(settings, KeyService(settings), TempFileService())
            page.add_paths([source])
            QTimer.singleShot(700, self.app.quit); self.app.exec()
            self.assertTrue(page.items[0].result.success, page.items[0].result.error)
            self.assertTrue(page.items[0].output.exists())
            self.assertEqual(page.items[0].output.parent, target / "Encrypted" / "json")
            self.assertFalse(page.temp_root.exists())
            page.cleanup()


if __name__ == "__main__": unittest.main()
