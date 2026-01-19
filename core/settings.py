from PySide6.QtCore import QSettings, QByteArray


class AppSettings:
    def __init__(self):
        self.settings = QSettings("ChintellaLaw", "BillingSystem")

    def save_window_geometry(self, window):
        self.settings.setValue("main_window/geometry", window.saveGeometry())
        self.settings.setValue("main_window/state", window.saveState())

    def restore_window_geometry(self, window):
        geometry = self.settings.value("main_window/geometry")
        state = self.settings.value("main_window/state")
        if geometry:
            window.restoreGeometry(geometry)
        if state:
            window.restoreState(state)

    def save_splitter_state(self, name: str, splitter):
        self.settings.setValue(f"splitters/{name}", splitter.saveState())

    def restore_splitter_state(self, name: str, splitter) -> bool:
        state = self.settings.value(f"splitters/{name}")
        if state:
            splitter.restoreState(state)
            return True
        return False

    def save_value(self, key: str, value):
        self.settings.setValue(key, value)

    def get_value(self, key: str, default=None):
        return self.settings.value(key, default)

    def save_tab_index(self, index: int):
        self.settings.setValue("main_window/tab_index", index)

    def get_tab_index(self) -> int:
        return int(self.settings.value("main_window/tab_index", 0))