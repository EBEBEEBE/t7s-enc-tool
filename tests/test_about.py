import os
import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

from ui.about_page import AboutPage, bundled_path


class TestAboutPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_about_markdown_renders_from_bundled_resource(self):
        original = Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as other:
                os.chdir(other)
                page = AboutPage()
                self.assertIn("t7s Enc File Tool", page.browser.toPlainText())
                self.assertIn("Generative AI Usage Disclosure", page.browser.toPlainText())
                self.assertIn("github.com/EBEBEEBE/t7s-enc-tool", page.browser.toHtml())
                self.assertEqual(bundled_path("ABOUT.md").name, "ABOUT.md")
                page.deleteLater()
                os.chdir(original)
        finally:
            os.chdir(original)

    def test_referenced_license_files_exist(self):
        root = bundled_path("ABOUT.md").parent
        for relative in ("LICENSE", "THIRD_PARTY_NOTICES.md", "THIRD_PARTY_LICENSES"):
            self.assertTrue((root / relative).exists(), relative)
        license_dir = root / "THIRD_PARTY_LICENSES"
        expected = (
            "SeventhResource-MIT.txt",
            "PySide6-LGPL-3.0-only.txt",
            "cryptography-Apache-2.0.txt",
            "cryptography-BSD-3-Clause.txt",
            "python-lz4-BSD-3-Clause.txt",
            "LZ4-BSD-2-Clause.txt",
        )
        for name in expected:
            self.assertTrue((license_dir / name).is_file(), name)


if __name__ == "__main__": unittest.main()
