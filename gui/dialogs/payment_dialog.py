from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QTextEdit, QDateEdit, QDoubleSpinBox, QMessageBox
)
from PySide6.QtCore import QDate
from core.models import Payment
from core.queries import ClientQueries, CaseQueries
from core.utils import date_to_qdate, qdate_to_date
from gui.widgets.styled_combo_box import StyledComboBox, populate_combo, select_combo_by_data


class PaymentDialog(QDialog):
    def __init__(self, parent=None, client_queries: ClientQueries = None, 
                 case_queries: CaseQueries = None, payment: Payment = None):
        super().__init__(parent)
        self.client_queries = client_queries
        self.case_queries = case_queries
        self.payment = payment
        self.setWindowTitle("Edit Payment" if payment else "Add Payment")
        self.setMinimumWidth(450)
        self.setup_ui()

        if payment:
            self.load_payment()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.client_combo = StyledComboBox()
        populate_combo(
            self.client_combo,
            self.client_queries.get_all() if self.client_queries else [],
            lambda c: c.display_name,
            "-- Select Client --"
        )
        self.client_combo.currentIndexChanged.connect(self.on_client_changed)
        form.addRow("Client:", self.client_combo)

        self.case_combo = StyledComboBox()
        self.case_combo.addItem("General Payment (No Specific Case)", None)
        form.addRow("Case (Optional):", self.case_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Payment Date:", self.date_edit)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 1000000)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("$")
        self.amount_spin.setValue(0.00)
        form.addRow("Amount:", self.amount_spin)

        self.method_combo = StyledComboBox()
        self.method_combo.setEditable(True)
        self.method_combo.addItems(["", "Check", "Cash", "Credit Card", "Wire Transfer", "ACH", "Money Order"])
        form.addRow("Payment Method:", self.method_combo)

        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("Check number, transaction ID, etc.")
        form.addRow("Reference Number:", self.reference_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Optional notes about this payment...")
        form.addRow("Notes:", self.notes_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def on_client_changed(self):
        client_id = self.client_combo.currentData()
        self.case_combo.clear()
        self.case_combo.addItem("General Payment (No Specific Case)", None)

        if client_id and self.case_queries:
            cases = self.case_queries.get_by_client(client_id)
            for case in cases:
                display = case["case_number"] or case["case_name"] or f"Case #{case['id']}"
                self.case_combo.addItem(display, case["id"])

    def load_payment(self):
        select_combo_by_data(self.client_combo, self.payment.client_id)
        self.on_client_changed()
        select_combo_by_data(self.case_combo, self.payment.case_id)

        if self.payment.payment_date:
            self.date_edit.setDate(date_to_qdate(self.payment.payment_date))

        self.amount_spin.setValue(self.payment.amount)
        self.method_combo.setCurrentText(self.payment.payment_method or "")
        self.reference_edit.setText(self.payment.reference_number or "")
        self.notes_edit.setText(self.payment.notes or "")

    def validate_and_accept(self):
        if not self.client_combo.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select a client.")
            self.client_combo.setFocus()
            return

        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Payment amount must be greater than zero.")
            self.amount_spin.setFocus()
            return

        self.accept()

    def get_payment(self) -> Payment:
        return Payment(
            client_id=self.client_combo.currentData(),
            case_id=self.case_combo.currentData(),
            payment_date=qdate_to_date(self.date_edit.date()),
            amount_cents=int(round(self.amount_spin.value() * 100)),
            payment_method=self.method_combo.currentText().strip(),
            reference_number=self.reference_edit.text().strip(),
            notes=self.notes_edit.toPlainText().strip()
        )