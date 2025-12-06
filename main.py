import sys
import os
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow


def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    db_path = os.path.join(get_app_path(), "law_billing.db")

    window = MainWindow(db_path=db_path)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        crash_log_path = os.path.join(get_app_path(), "crash_log.txt")
        with open(crash_log_path, "w") as f:
            traceback.print_exc(file=f)
        raise