from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QDialogButtonBox, QMessageBox, QLabel
)
from PySide6.QtCore import QDate
from core.models import Payment
from core.queries import PersonQueries, CaseQueries
from core.utils import qdate_to_date
from gui.dialogs.dialog_helpers import DialogFieldsMixin


class PaymentDialog(QDialog, DialogFieldsMixin):
    def __init__(self, parent=None, person_queries: PersonQueries = None,
                 case_queries: CaseQueries = None, payment: Payment = None,
                 client_id: int = None, case_id: int = None):
        super().__init__(parent)
        self.person_queries = person_queries
        self.case_queries = case_queries
        self.payment = payment
        self.client_id = client_id
        self.case_id = case_id
        
        self.setWindowTitle("Edit Payment" if payment else "Add Payment")
        self.setMinimumWidth(400)
        self.setup_ui()
        if payment:
            self.load_payment()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.date_edit = self.create_date_field(form)
        self.fee_amount_spin = self.create_money_field(form, "Fee Payment:", max_val=1000000.0, step=100.0)
        self.fee_amount_spin.valueChanged.connect(self.update_total)

        self.include_expense_checkbox = self.create_checkbox(
            form, "Include expense advance", self.on_expense_toggled
        )

        self.expense_amount_label = QLabel("Expense Advance:")
        self.expense_amount_spin = self.create_money_field(form, "", max_val=1000000.0, step=100.0, add_to_form=False)
        self.expense_amount_spin.valueChanged.connect(self.update_total)
        form.addRow(self.expense_amount_label, self.expense_amount_spin)
        self.expense_amount_label.hide()
        self.expense_amount_spin.hide()

        self.total_label = QLabel("Total: $0.00")
        self.total_label.setStyleSheet("font-weight: bold;")
        form.addRow("", self.total_label)

        self.description_edit = self.create_description_field(
            form, placeholder="Payment method, check number, notes, etc.", max_height=80
        )

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_expense_toggled(self, checked):
        self.expense_amount_label.setVisible(checked)
        self.expense_amount_spin.setVisible(checked)
        if not checked:
            self.expense_amount_spin.setValue(0.00)
        self.update_total()
        self.adjustSize()

    def update_total(self):
        fee = self.fee_amount_spin.value()
        expense = self.expense_amount_spin.value() if self.include_expense_checkbox.isChecked() else 0
        self.total_label.setText(f"Total: ${fee + expense:.2f}")

    def load_payment(self):
        if self.payment.payment_date:
            d = self.payment.payment_date
            self.date_edit.setDate(QDate(d.year, d.month, d.day))
        self.fee_amount_spin.setValue(self.payment.amount_cents / 100.0)
        if self.payment.expense_amount_cents > 0:
            self.include_expense_checkbox.setChecked(True)
            self.expense_amount_spin.setValue(self.payment.expense_amount_cents / 100.0)
        self.description_edit.setText(self.payment.notes or "")

    def validate_and_accept(self):
        fee = self.fee_amount_spin.value()
        expense = self.expense_amount_spin.value() if self.include_expense_checkbox.isChecked() else 0
        if fee <= 0 and expense <= 0:
            QMessageBox.warning(self, "Validation Error", 
                "Please enter a fee payment amount and/or an expense advance amount.")
            self.fee_amount_spin.setFocus()
            return
        self.accept()

    def get_payment(self) -> Payment:
        return Payment(
            person_id=self.client_id,
            case_id=self.case_id,
            payment_date=qdate_to_date(self.date_edit.date()),
            amount_cents=int(round(self.fee_amount_spin.value() * 100)),
            expense_amount_cents=int(round(self.expense_amount_spin.value() * 100)) if self.include_expense_checkbox.isChecked() else 0,
            payment_method="",
            reference_number="",
            notes=self.description_edit.toPlainText().strip()
        )