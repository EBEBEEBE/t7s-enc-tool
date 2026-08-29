from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PlaceholderPage(QWidget):
    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        body = QLabel(description)
        body.setWordWrap(True)
        body.setObjectName("placeholder")
        layout.addWidget(heading)
        layout.addWidget(body)
        layout.addStretch()
