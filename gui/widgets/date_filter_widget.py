from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QDateEdit
from PySide6.QtCore import QDate, Signal


class DateFilterWidget(QWidget):
    filter_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._suppress_signals = False
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.use_date_filter = QCheckBox("Enable Date Filter")
        self.use_date_filter.stateChanged.connect(self._on_state_changed)
        layout.addWidget(self.use_date_filter)

        date_range_layout = QHBoxLayout()
        date_range_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setEnabled(False)
        self.start_date.dateChanged.connect(self._on_date_changed)
        date_range_layout.addWidget(self.start_date)

        date_range_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setEnabled(False)
        self.end_date.dateChanged.connect(self._on_date_changed)
        date_range_layout.addWidget(self.end_date)

        layout.addLayout(date_range_layout)

    def _on_state_changed(self):
        enabled = self.use_date_filter.isChecked()
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)
        if not self._suppress_signals:
            self.filter_changed.emit()

    def _on_date_changed(self):
        if not self._suppress_signals:
            self.filter_changed.emit()

    def is_enabled(self) -> bool:
        return self.use_date_filter.isChecked()

    def get_range(self) -> tuple:
        return (
            self.start_date.date().toString("yyyy-MM-dd"),
            self.end_date.date().toString("yyyy-MM-dd")
        )

    def set_suppressed(self, suppressed: bool):
        self._suppress_signals = suppressed