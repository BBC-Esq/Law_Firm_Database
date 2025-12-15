from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox,
    QDialogButtonBox, QDateEdit, QTextEdit, QMessageBox, QCheckBox, QLabel
)
from PySide6.QtCore import QDate
from core.models import BillingEntry
from core.queries import CaseQueries
from gui.utils import select_all_on_focus
from datetime import date


class BillingDialog(QDialog):
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

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Date:", self.date_edit)

        self.expense_checkbox = QCheckBox("This is an expense (not billable time)")
        self.expense_checkbox.toggled.connect(self.on_expense_toggled)
        form.addRow("", self.expense_checkbox)

        self.hours_label = QLabel("Hours:")
        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(0.1, 24.0)
        self.hours_spin.setSingleStep(0.1)
        self.hours_spin.setDecimals(1)
        self.hours_spin.setValue(0.5)
        self.hours_spin.valueChanged.connect(self.update_amount_preview)
        select_all_on_focus(self.hours_spin)
        form.addRow(self.hours_label, self.hours_spin)

        self.amount_label = QLabel("Amount:")
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 100000.00)
        self.amount_spin.setSingleStep(1.00)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("$")
        self.amount_spin.setValue(0.01)
        self.amount_spin.valueChanged.connect(self.update_amount_preview)
        select_all_on_focus(self.amount_spin)
        self.amount_label.hide()
        self.amount_spin.hide()
        form.addRow(self.amount_label, self.amount_spin)

        self.preview_label = QLabel()
        self.update_amount_preview()
        form.addRow("Total:", self.preview_label)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Enter description of work performed or expense details...")
        form.addRow("Description:", self.description_edit)

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
            amount = self.amount_spin.value()
            self.preview_label.setText(f"${amount:.2f}")
        else:
            hours = self.hours_spin.value()
            rate = self.billing_rate_cents / 100.0
            total = hours * rate
            self.preview_label.setText(f"${total:.2f} ({hours:.1f} hrs × ${rate:.2f}/hr)")

    def load_entry(self):
        if self.entry.entry_date:
            self.date_edit.setDate(QDate(
                self.entry.entry_date.year,
                self.entry.entry_date.month,
                self.entry.entry_date.day
            ))
        
        if self.entry.is_expense:
            self.expense_checkbox.setChecked(True)
            if self.entry.amount_cents:
                self.amount_spin.setValue(self.entry.amount_cents / 100.0)
        else:
            self.expense_checkbox.setChecked(False)
            if self.entry.hours:
                self.hours_spin.setValue(self.entry.hours)
        
        self.description_edit.setText(self.entry.description or "")

    def validate_and_accept(self):
        if self.expense_checkbox.isChecked():
            if self.amount_spin.value() <= 0:
                QMessageBox.warning(self, "Validation Error", "Please enter an amount greater than zero.")
                self.amount_spin.setFocus()
                return
        else:
            if self.hours_spin.value() <= 0:
                QMessageBox.warning(self, "Validation Error", "Please enter hours greater than zero.")
                self.hours_spin.setFocus()
                return
        
        self.accept()

    def get_entry(self) -> BillingEntry:
        qdate = self.date_edit.date()
        entry_date = date(qdate.year(), qdate.month(), qdate.day())
        
        is_expense = self.expense_checkbox.isChecked()
        
        if is_expense:
            hours = None
            amount_cents = int(round(self.amount_spin.value() * 100))
        else:
            hours = self.hours_spin.value()
            amount_cents = None
        
        return BillingEntry(
            case_id=self.case_id,
            entry_date=entry_date,
            hours=hours,
            is_expense=is_expense,
            amount_cents=amount_cents,
            description=self.description_edit.toPlainText().strip()
        )