import sys
import os
import shutil
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import concurrent.futures
from gui.main_window import MainWindow


def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def auto_backup(db_path, keep_count=5):
    if not os.path.exists(db_path):
        return
    
    backup_dir = Path(db_path).parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"law_billing_backup_{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    
    backups = sorted(backup_dir.glob("law_billing_backup_*.db"), reverse=True)
    for old_backup in backups[keep_count:]:
        old_backup.unlink()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    db_path = os.path.join(get_app_path(), "law_billing.db")

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(auto_backup, db_path)

    def start_main_window_when_ready():
        if not future.done():
            QTimer.singleShot(50, start_main_window_when_ready)
            return

        executor.shutdown(wait=False)

        window = MainWindow(db_path=db_path)
        window.show()

    QTimer.singleShot(0, start_main_window_when_ready)
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