from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget, QLabel

from services.export import ExportService
from services.keys import KeyService
from services.settings import SettingsService
from services.tempfiles import TempFileService

from .main_page import MainPage
from .about_page import AboutPage
from .pages import PlaceholderPage
from .settings_page import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("t7s-enc-tool")
        self.resize(1180, 760)
        self.setMinimumSize(900, 600)

        self.settings_service = SettingsService()
        self.key_service = KeyService(self.settings_service)
        self.temp_service = TempFileService()
        self.export_service = ExportService()
        self.main_page = MainPage(self.settings_service, self.key_service, self.temp_service, self.export_service)
        self.settings_page = SettingsPage(self.settings_service, self.key_service)
        self.settings_page.settingsChanged.connect(self.main_page.apply_settings)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(AboutPage())

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 24, 16, 16)
        side_layout.setSpacing(8)
        brand = QLabel("t7s Enc File Tool")
        brand.setObjectName("brand")
        # brand.setEnabled(False)
        side_layout.addWidget(brand)
        for index, label in enumerate(("Main", "Settings", "About")):
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self._show_page(i))
            side_layout.addWidget(button)
            if index == 0:
                self.main_button = button
        side_layout.addStretch()
        self.main_button.setChecked(True)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

    def _show_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for button in self.findChildren(QPushButton, "navButton"):
            button.setChecked(button.text() == ("Main", "Settings", "About")[index])

    def closeEvent(self, event):
        self.main_page.cleanup()
        super().closeEvent(event)
