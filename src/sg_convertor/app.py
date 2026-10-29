"""Application entry point."""

import sys

from PySide6.QtWidgets import QApplication

from sg_convertor.ui.main_window import MainWindow
from sg_convertor.ui.styles import STYLESHEET


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("SG Convertor")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
