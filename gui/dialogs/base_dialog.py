from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import QTimer


class BaseFormDialog(QDialog):
    def __init__(self, parent=None, title: str = "Dialog", min_width: int = 450):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(min_width)
        self.main_layout = QVBoxLayout(self)
        self.setup_ui()
        self.add_button_box()

        QTimer.singleShot(0, self.set_initial_focus)

    def setup_ui(self):
        raise NotImplementedError("Subclasses must implement setup_ui")

    def add_button_box(self):
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(self.button_box)

    def validate_and_accept(self):
        if self.validate():
            self.accept()

    def validate(self) -> bool:
        return True

    def show_validation_warning(self, message: str):
        QMessageBox.warning(self, "Validation Error", message)

    def set_initial_focus(self):
        pass