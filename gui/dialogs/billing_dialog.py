from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox,
    QDialogButtonBox, QMessageBox, QCheckBox, QLabel
)
from PySide6.QtCore import QDate
from core.models import BillingEntry
from core.queries import CaseQueries
from core.utils import qdate_to_date
from gui.dialogs.dialog_helpers import DialogFieldsMixin
from gui.utils import select_all_on_focus


class BillingDialog(QDialog, DialogFieldsMixin):
    def __init__(self, parent=None, case_queries: CaseQueries = None,
                 entry: BillingEntry = None, case_id: int = None,
                 billing_rate_cents: int = 30000):
        super().__init__(parent)
        self.case_queries = case_queries
        self.entry = entry
        self.case_id = case_id
        self.billing_rate_cents = billing_rate_cents

        self.setWindowTitle("Edit Billing Entry" if entry else "Add Billing Entry")
        self.setMinimumWidth(400)
        self.setup_ui()
        if entry:
            self.load_entry()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.date_edit = self.create_date_field(form)
        self.expense_checkbox = self.create_checkbox(
            form, "This is an expense (not billable time)", self.on_expense_toggled
        )

        # Hours field - create manually to control label visibility
        self.hours_label = QLabel("Hours:")
        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(0.0, 24.0)
        self.hours_spin.setSingleStep(0.1)
        self.hours_spin.setDecimals(1)
        self.hours_spin.setValue(0.5)
        self.hours_spin.valueChanged.connect(self.update_amount_preview)
        select_all_on_focus(self.hours_spin)
        form.addRow(self.hours_label, self.hours_spin)

        # Amount field - create manually to control label visibility
        self.amount_label = QLabel("Amount:")
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 100000.0)
        self.amount_spin.setSingleStep(1.0)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("$")
        self.amount_spin.setValue(0.01)
        self.amount_spin.valueChanged.connect(self.update_amount_preview)
        select_all_on_focus(self.amount_spin)
        form.addRow(self.amount_label, self.amount_spin)
        self.amount_label.hide()
        self.amount_spin.hide()

        self.preview_label = self.create_preview_label(form)
        self.update_amount_preview()

        self.description_edit = self.create_description_field(
            form, placeholder="Enter description of work performed or expense details..."
        )

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_expense_toggled(self, checked):
        self.hours_label.setVisible(not checked)
        self.hours_spin.setVisible(not checked)
        self.amount_label.setVisible(checked)
        self.amount_spin.setVisible(checked)
        self.update_amount_preview()
        self.adjustSize()

    def update_amount_preview(self):
        if self.expense_checkbox.isChecked():
            self.preview_label.setText(f"${self.amount_spin.value():.2f}")
        else:
            hours = self.hours_spin.value()
            rate = self.billing_rate_cents / 100.0
            self.preview_label.setText(f"${hours * rate:.2f} ({hours:.1f} hrs × ${rate:.2f}/hr)")

    def load_entry(self):
        if self.entry.entry_date:
            d = self.entry.entry_date
            self.date_edit.setDate(QDate(d.year, d.month, d.day))

        if self.entry.is_expense:
            self.expense_checkbox.setChecked(True)
            if self.entry.amount_cents:
                self.amount_spin.setValue(self.entry.amount_cents / 100.0)
        elif self.entry.hours:
            self.hours_spin.setValue(self.entry.hours)

        self.description_edit.setText(self.entry.description or "")

    def validate_and_accept(self):
        if self.expense_checkbox.isChecked():
            if self.amount_spin.value() <= 0:
                QMessageBox.warning(self, "Validation Error", "Please enter an amount greater than zero.")
                self.amount_spin.setFocus()
                return
        elif self.hours_spin.value() < 0:
            QMessageBox.warning(self, "Validation Error", "Please enter hours zero or greater.")
            self.hours_spin.setFocus()
            return
        self.accept()

    def get_entry(self) -> BillingEntry:
        is_expense = self.expense_checkbox.isChecked()
        return BillingEntry(
            case_id=self.case_id,
            entry_date=qdate_to_date(self.date_edit.date()),
            hours=None if is_expense else self.hours_spin.value(),
            is_expense=is_expense,
            amount_cents=int(round(self.amount_spin.value() * 100)) if is_expense else None,
            description=self.description_edit.toPlainText().strip()
        )