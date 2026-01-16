import sys
from PySide6.QtWidgets import QApplication

from app.ui.app_context import AppContext
from app.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    ctx = AppContext()
    w = MainWindow(ctx)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
