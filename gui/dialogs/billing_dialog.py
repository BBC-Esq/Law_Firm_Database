from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox,
    QDialogButtonBox, QTextEdit, QDateEdit, QLabel, QMessageBox
)
from PySide6.QtCore import QDate
from core.models import BillingEntry
from core.queries import CaseQueries
from core.utils import date_to_qdate, qdate_to_date
from gui.widgets.matter_search_widget import MatterSearchWidget

class BillingDialog(QDialog):
    def __init__(self, parent=None, case_queries: CaseQueries = None, entry: BillingEntry = None):
        super().__init__(parent)
        self.case_queries = case_queries
        self.entry = entry
        self.selected_case_id = None
        self.billing_rate_cents = 0
        self.setWindowTitle("Edit Billing Entry" if entry else "Add Billing Entry")
        self.setMinimumWidth(500)
        self.setup_ui()

        if entry:
            self.load_entry()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.matter_search = MatterSearchWidget(self.case_queries)
        self.matter_search.matter_selected.connect(self.on_matter_selected)
        form.addRow("Client/Matter:", self.matter_search)

        self.rate_label = QLabel("Rate: $0.00/hr")
        form.addRow("", self.rate_label)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Date:", self.date_edit)

        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(0, 24)
        self.hours_spin.setDecimals(1)
        self.hours_spin.setSingleStep(0.1)
        self.hours_spin.setValue(0.1)
        self.hours_spin.valueChanged.connect(self.update_amount)
        form.addRow("Hours:", self.hours_spin)

        self.amount_label = QLabel("Amount: $0.00")
        form.addRow("", self.amount_label)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Describe the legal service performed...")
        form.addRow("Description:", self.description_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_matter_selected(self, matter):
        self.selected_case_id = matter["id"]
        self.billing_rate_cents = matter["billing_rate_cents"]
        self.rate_label.setText(f"Rate: ${self.billing_rate_cents / 100:.2f}/hr")
        self.update_amount()

    def update_amount(self):
        amount_cents = self.hours_spin.value() * self.billing_rate_cents
        self.amount_label.setText(f"Amount: ${amount_cents / 100:.2f}")

    def set_matter(self, matter):
        self.selected_case_id = matter["id"]
        self.billing_rate_cents = matter["billing_rate_cents"]
        self.rate_label.setText(f"Rate: ${self.billing_rate_cents / 100:.2f}/hr")
        self.matter_search.set_matter(matter)
        self.update_amount()

    def load_entry(self):
        if self.entry.case_id:
            matter = self.case_queries.get_matter_by_id(self.entry.case_id)
            if matter:
                self.set_matter(matter)

        if self.entry.entry_date:
            self.date_edit.setDate(date_to_qdate(self.entry.entry_date))

        self.hours_spin.setValue(self.entry.hours)
        self.description_edit.setText(self.entry.description or "")

    def validate_and_accept(self):
        if not self.selected_case_id:
            QMessageBox.warning(self, "Validation Error", "Please select a client/matter.")
            self.matter_search.search_input.setFocus()
            return
        if self.hours_spin.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Hours must be greater than zero.")
            self.hours_spin.setFocus()
            return
        self.accept()

    def get_entry(self) -> BillingEntry:
        return BillingEntry(
            case_id=self.selected_case_id,
            entry_date=qdate_to_date(self.date_edit.date()),
            hours=self.hours_spin.value(),
            description=self.description_edit.toPlainText().strip()
        )