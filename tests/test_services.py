import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from core import Keys, ProcessResult
from services.apk_extractor import ApkKeyExtractor, FIELDS, METADATA_PATH
from services.export import ExportService
from services.keys import KeyService
from services.settings import AppSettings, SettingsService
from services.tempfiles import TempFileService


KEYS = Keys(b"0123456789abcdef", b"fedcba9876543210", b"t7s-enc", b"hmac-secret12345")


class TestServices(unittest.TestCase):
    def test_settings_save_load_and_program_bootstrap(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); user = root / "user"; program = root / "program"
            service = SettingsService(program, user)
            service.settings = AppSettings(str(root / "exports"), True, str(root / "temp"))
            service.save()
            loaded = SettingsService(program, user)
            self.assertEqual(loaded.active_location, "user")
            self.assertEqual(loaded.settings.default_folder, str(root / "exports"))
            loaded.switch_location("program", KeyService.to_text(KEYS))
            self.assertEqual(SettingsService(program, user).active_location, "program")
            self.assertEqual(Keys.from_file(program / "keys.txt"), KEYS)

    def test_settings_location_migration_to_user_removes_marker(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); program = root / "program"; user = root / "user"
            service = SettingsService(program, user)
            service.switch_location("program", KeyService.to_text(KEYS))
            service.switch_location("user", KeyService.to_text(KEYS))
            self.assertFalse((program / "settings.json").exists())
            self.assertTrue((user / "settings.json").exists())

    def test_key_txt_import_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "keys.txt"
            path.write_text(KeyService.to_text(KEYS), encoding="utf-8")
            self.assertEqual(KeyService.from_text(path), KEYS)
            path.write_text("V1AESKey = too-short\n", encoding="utf-8")
            with self.assertRaises(Exception): KeyService.from_text(path)

    def test_apk_and_xapk_extraction(self):
        metadata = bytearray(0x0AE2F2 + 7)
        values = {"V1AESKey": b"0123456789abcdef", "V2Key": b"fedcba9876543210", "V2Signature": b"t7s-enc", "HMACKey": b"hmac-secret12345"}
        for name, (offset, length) in FIELDS.items(): metadata[offset:offset + length] = values[name]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); apk_bytes = tempfile.NamedTemporaryFile(suffix=".apk", delete=False).name
            try:
                with zipfile.ZipFile(apk_bytes, "w") as apk: apk.writestr(METADATA_PATH, metadata)
                apk_path = Path(apk_bytes)
                self.assertEqual(ApkKeyExtractor.extract(apk_path), KEYS)
                xapk_path = root / "bundle.xapk"
                with zipfile.ZipFile(xapk_path, "w") as xapk: xapk.write(apk_path, "jp.ne.donuts.t7s.apk")
                self.assertEqual(ApkKeyExtractor.extract(xapk_path), KEYS)
            finally: Path(apk_bytes).unlink(missing_ok=True)

    def test_custom_temp_folder_and_atomic_export_grouping(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); temp = TempFileService().create_session(str(root / "temp"))
            self.assertEqual(temp.parent, root / "temp")
            output = temp / "result.bin"; output.write_bytes(b"done")
            result = ProcessResult(root / "usage_123.jpg", output, "encrypt", "v2", "v2", 1, 4, True)
            final = ExportService.export_file(result.source_path, output, result, root / "exports")
            self.assertEqual(final.parent, root / "exports" / "Encrypted" / "usage")
            self.assertEqual(final.read_bytes(), b"done")


if __name__ == "__main__": unittest.main()
