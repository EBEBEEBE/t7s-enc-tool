from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor, QDesktopServices, QPalette
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextBrowser, QVBoxLayout, QWidget


def bundled_path(name: str) -> Path:
    """Resolve a bundled project resource without relying on the CWD."""
    candidates = []
    if getattr(sys, "_MEIPASS", None):
        candidates.append(Path(sys._MEIPASS) / name)
    candidates.extend((Path(__file__).resolve().parents[1] / name, Path(sys.executable).resolve().parent / name))
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(f"Bundled resource not found: {name}")


class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        title = QLabel("About")
        title.setObjectName("pageTitle")
        self.browser = QTextBrowser()
        self.browser.setOpenLinks(False)
        self.browser.setOpenExternalLinks(False)
        palette = self.browser.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor("#eef2f8"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#eef2f8"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#24364f"))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor("#17263a"))
        self.browser.setPalette(palette)
        self.browser.anchorClicked.connect(self._open_link)
        self.browser.setDocumentTitle("About t7s Enc File Tool")
        try:
            self.browser.setMarkdown(bundled_path("ABOUT.md").read_text(encoding="utf-8"))
            # Qt's Markdown renderer emits an inline bright-blue link color;
            # replace that presentation detail while retaining native parsing.
            rendered = self.browser.toHtml()
            rendered = rendered.replace("#0000ff", "#24364f").replace("#0000FF", "#24364f")
            rendered = rendered.replace(
                "</head>",
                "<style>"
                "a, a:link, a:visited, a:hover, a:active, a span "
                "{ color: #24364f !important; text-decoration: none !important; }"
                "a:hover { color: #17263a !important; text-decoration: underline !important; }"
                "</style></head>",
            )
            self.browser.setHtml(rendered)
            self.browser.document().setDefaultStyleSheet(
                "a { color: #24364f; text-decoration: none; } "
                "a:hover { color: #17263a; text-decoration: underline; }"
            )
        except (OSError, UnicodeError) as exc:
            self.browser.setPlainText(f"Unable to load ABOUT.md:\n{exc}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.addWidget(title)
        layout.addWidget(self.browser, 1)
        links = QHBoxLayout()
        license_button = QPushButton("View LICENSE")
        notices_button = QPushButton("View Third-Party Notices")
        license_button.clicked.connect(lambda: self._open_bundled_file("LICENSE"))
        notices_button.clicked.connect(lambda: self._open_bundled_file("THIRD_PARTY_NOTICES.md"))
        links.addWidget(license_button)
        links.addWidget(notices_button)
        links.addStretch()
        layout.addLayout(links)

    @staticmethod
    def _open_link(url: QUrl):
        if url.isRelative():
            try:
                target = bundled_path(url.toString())
            except FileNotFoundError:
                return
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))
        else:
            QDesktopServices.openUrl(url)

    @staticmethod
    def _open_bundled_file(name: str):
        try:
            path = bundled_path(name)
        except FileNotFoundError:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
