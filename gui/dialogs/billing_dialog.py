from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox
from PySide6.QtCore import QDate
from core.models import BillingEntry
from core.utils import qdate_to_date
from gui.dialogs.dialog_helpers import DialogFieldsMixin
from gui.dialogs.billing_entry_mixin import BillingEntryMixin


class BillingDialog(QDialog, DialogFieldsMixin, BillingEntryMixin):
    def __init__(self, parent=None, case_queries=None,
                 entry: BillingEntry = None, case_id: int = None,
                 billing_rate_cents: int = 30000):
        super().__init__(parent)
        self.case_queries = case_queries
        self.entry = entry
        self.case_id = case_id

        self.setWindowTitle("Edit Billing Entry" if entry else "Add Billing Entry")
        self.setMinimumWidth(400)
        self.setup_ui()
        self.set_billing_rate(billing_rate_cents)
        if entry:
            self.load_entry()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.date_edit = self.create_date_field(form)
        self.setup_billing_fields(form, initial_hours=0.5)
        self.description_edit = self.create_description_field(
            form, placeholder="Enter description of work performed or expense details..."
        )

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_entry(self):
        if self.entry.entry_date:
            d = self.entry.entry_date
            self.date_edit.setDate(QDate(d.year, d.month, d.day))

        self.load_billing_values(
            hours=self.entry.hours,
            is_expense=self.entry.is_expense,
            amount_cents=self.entry.amount_cents
        )
        self.description_edit.setText(self.entry.description or "")

    def validate_and_accept(self):
        if self.validate_billing_fields(self):
            self.accept()

    def get_entry(self) -> BillingEntry:
        billing_values = self.get_billing_values()
        return BillingEntry(
            case_id=self.case_id,
            entry_date=qdate_to_date(self.date_edit.date()),
            hours=billing_values['hours'],
            is_expense=billing_values['is_expense'],
            amount_cents=billing_values['amount_cents'],
            description=self.description_edit.toPlainText().strip()
        )