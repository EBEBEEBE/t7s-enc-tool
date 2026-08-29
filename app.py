from __future__ import annotations

import sys

def main(argv: list[str] | None = None) -> int:
    """Use the CLI when arguments are supplied; otherwise launch the GUI."""
    arguments = sys.argv[1:] if argv is None else list(argv)
    if arguments:
        from cli import main as cli_main
        return cli_main(arguments)
    return launch_gui()


def launch_gui() -> int:
    from PySide6.QtGui import QColor, QIcon, QPalette
    from PySide6.QtWidgets import QApplication
    from ui.about_page import bundled_path
    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("T7S Enc File Tool")
    app.setWindowIcon(QIcon(str(bundled_path("assets/app_icon.png"))))
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Link, QColor("#24364f"))
    palette.setColor(QPalette.ColorRole.LinkVisited, QColor("#17263a"))
    app.setPalette(palette)
    app.setStyleSheet(
        """
        QMainWindow, QWidget { background: #f5f7fb; color: #172033; font-size: 14px; }
        #sidebar { background: #172033; }
        #brand { background: transparent; color: #ffffff; font-size: 18px; font-weight: 700; border: 0; text-align: left; padding: 8px; }
        #navButton { background: #202b43; color: #b8c3d8; border: 1px solid #34425e; border-radius: 8px; padding: 12px; text-align: left; font-size: 14px; font-weight: 600; }
        #navButton:hover, #navButton:checked { background: #2d6cdf; color: white; border-color: #5a8df0; }
        #pageTitle { font-size: 28px; font-weight: 700; }
        #dropZone { border: 2px dashed #9eabc2; border-radius: 12px; background: #ffffff; }
        #dropZone:hover { border-color: #2d6cdf; background: #f3f7ff; }
        #dropTitle { font-size: 20px; font-weight: 600; }
        QPushButton { background: #ffffff; color: #172033; border: 1px solid #aebbd0; border-radius: 7px; padding: 8px 14px; min-height: 18px; font-weight: 600; }
        QPushButton:hover { background: #edf3ff; border-color: #2d6cdf; }
        QPushButton:pressed { background: #dce8ff; }
        QPushButton:disabled { background: #edf0f5; color: #8995a8; border-color: #d5dbe5; }
        QPushButton#primary { background: #2d6cdf; color: white; border-color: #245cc2; }
        QPushButton#primary:hover { background: #245cc2; }
        QComboBox, QLineEdit { background: #ffffff; border: 1px solid #aebbd0; border-radius: 6px; padding: 7px 9px; min-height: 18px; }
        QComboBox:focus, QLineEdit:focus { border: 2px solid #5a8df0; padding: 6px 8px; }
        QCheckBox, QRadioButton { spacing: 8px; font-weight: 600; }
        QCheckBox::indicator, QRadioButton::indicator { width: 17px; height: 17px; border: 2px solid #8292aa; background: #ffffff; }
        QCheckBox::indicator { border-radius: 4px; }
        QRadioButton::indicator { border-radius: 10px; }
        QCheckBox::indicator:checked, QRadioButton::indicator:checked { background: #2d6cdf; border-color: #245cc2; }
        QCheckBox::indicator:disabled, QRadioButton::indicator:disabled { background: #edf0f5; border-color: #c5cedd; }
        QGroupBox { border: 1px solid #d5dce8; border-radius: 10px; margin-top: 18px; padding: 24px 14px 14px 14px; font-size: 18px; font-weight: 700; }
        QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 7px; background: #f5f7fb; }
        #settingLabel { font-size: 14px; font-weight: 700; }
        #helpButton { background: #e5edff; color: #245cc2; border: 1px solid #8eabeb; border-radius: 10px; padding: 0; font-weight: 700; }
        #helpButton:hover { background: #2d6cdf; color: white; }
        QToolTip { background: #172033; color: #ffffff; border: 1px solid #5a8df0; border-radius: 5px; padding: 8px 10px; font-size: 13px; }
        QTextBrowser { background: #eef2f8; border: 1px solid #d5dce8; border-radius: 8px; padding: 10px; }
        QTableWidget { background: white; border: 1px solid #dce2ec; border-radius: 8px; gridline-color: #edf0f5; }
        QHeaderView::section { background: #eef2f8; border: 0; padding: 8px; font-weight: 600; }
        """
    )
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
