from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor, QDesktopServices, QPalette
from PySide6.QtWidgets import QTabWidget, QTextBrowser, QVBoxLayout, QWidget, QLabel

from .about_page import bundled_path


class HelpPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        title = QLabel("Help")
        title.setObjectName("pageTitle")

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.quickstart_browser = self._create_browser("Quickstart")
        self.readme_browser = self._create_browser("README")
        self.tabs.addTab(self.quickstart_browser, "Quickstart")
        self.tabs.addTab(self.readme_browser, "README")

        self._load_document(self.quickstart_browser, "docs/QUICKSTART.md")
        self._load_document(self.readme_browser, "README.md")
        self.tabs.setCurrentIndex(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 24)
        layout.addWidget(title)
        layout.addWidget(self.tabs, 1)

    @staticmethod
    def _create_browser(tab_name: str) -> QTextBrowser:
        browser = QTextBrowser()
        browser.setOpenLinks(False)
        browser.setOpenExternalLinks(False)
        browser.setDocumentTitle(f"{tab_name} - t7s Enc File Tool")
        palette = browser.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor("#eef2f8"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#eef2f8"))
        palette.setColor(QPalette.ColorRole.Link, QColor("#24364f"))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor("#17263a"))
        browser.setPalette(palette)
        browser.anchorClicked.connect(HelpPage._open_link)
        return browser

    @staticmethod
    def _load_document(browser: QTextBrowser, name: str):
        try:
            browser.setMarkdown(bundled_path(name).read_text(encoding="utf-8"))
            rendered = browser.toHtml()
            rendered = rendered.replace("#0000ff", "#24364f").replace("#0000FF", "#24364f")
            rendered = rendered.replace(
                "</head>",
                "<style>"
                "a, a:link, a:visited, a:hover, a:active, a span "
                "{ color: #24364f !important; text-decoration: none !important; }"
                "a:hover { color: #17263a !important; text-decoration: underline !important; }"
                "</style></head>",
            )
            browser.setHtml(rendered)
            browser.document().setDefaultStyleSheet(
                "a { color: #24364f; text-decoration: none; } "
                "a:hover { color: #17263a; text-decoration: underline; }"
            )
        except (OSError, UnicodeError) as exc:
            browser.setPlainText(f"Unable to load {name}:\n{exc}")

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
