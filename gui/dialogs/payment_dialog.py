from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox,
    QDialogButtonBox, QDateEdit, QTextEdit, QMessageBox,
    QCheckBox, QLabel
)
from PySide6.QtCore import QDate
from core.models import Payment
from core.queries import PersonQueries, CaseQueries
from gui.utils import select_all_on_focus
from datetime import date


class PaymentDialog(QDialog):
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

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Date:", self.date_edit)

        self.fee_amount_spin = QDoubleSpinBox()
        self.fee_amount_spin.setRange(0.00, 1000000.00)
        self.fee_amount_spin.setSingleStep(100.00)
        self.fee_amount_spin.setDecimals(2)
        self.fee_amount_spin.setPrefix("$")
        self.fee_amount_spin.setValue(0.00)
        self.fee_amount_spin.valueChanged.connect(self.update_total)
        select_all_on_focus(self.fee_amount_spin)
        form.addRow("Fee Payment:", self.fee_amount_spin)

        self.include_expense_checkbox = QCheckBox("Include expense advance")
        self.include_expense_checkbox.toggled.connect(self.on_expense_toggled)
        form.addRow("", self.include_expense_checkbox)

        self.expense_amount_label = QLabel("Expense Advance:")
        self.expense_amount_spin = QDoubleSpinBox()
        self.expense_amount_spin.setRange(0.00, 1000000.00)
        self.expense_amount_spin.setSingleStep(100.00)
        self.expense_amount_spin.setDecimals(2)
        self.expense_amount_spin.setPrefix("$")
        self.expense_amount_spin.setValue(0.00)
        self.expense_amount_spin.valueChanged.connect(self.update_total)
        select_all_on_focus(self.expense_amount_spin)
        self.expense_amount_label.hide()
        self.expense_amount_spin.hide()
        form.addRow(self.expense_amount_label, self.expense_amount_spin)

        self.total_label = QLabel("Total: $0.00")
        self.total_label.setStyleSheet("font-weight: bold;")
        form.addRow("", self.total_label)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Payment method, check number, notes, etc.")
        form.addRow("Description:", self.description_edit)

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
        total = fee + expense
        self.total_label.setText(f"Total: ${total:.2f}")

    def load_payment(self):
        if self.payment.payment_date:
            self.date_edit.setDate(QDate(
                self.payment.payment_date.year,
                self.payment.payment_date.month,
                self.payment.payment_date.day
            ))
        
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
        qdate = self.date_edit.date()
        payment_date = date(qdate.year(), qdate.month(), qdate.day())
        
        fee_cents = int(round(self.fee_amount_spin.value() * 100))
        expense_cents = 0
        if self.include_expense_checkbox.isChecked():
            expense_cents = int(round(self.expense_amount_spin.value() * 100))
        
        return Payment(
            person_id=self.client_id,
            case_id=self.case_id,
            payment_date=payment_date,
            amount_cents=fee_cents,
            expense_amount_cents=expense_cents,
            payment_method="",
            reference_number="",
            notes=self.description_edit.toPlainText().strip()
        )