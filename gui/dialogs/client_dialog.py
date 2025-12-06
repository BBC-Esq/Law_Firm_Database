from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDoubleSpinBox,
    QDialogButtonBox, QTextEdit, QLabel, QMessageBox
)
from core.models import Client
from core.validators import validate_required_field, validate_multi_email_field, validate_multi_phone_field

class ClientDialog(QDialog):
    def __init__(self, parent=None, client: Client = None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle("Edit Client" if client else "Add Client")
        self.setMinimumWidth(450)
        self.setup_ui()

        if client:
            self.load_client()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("Required")
        form.addRow("First Name:", self.first_name_edit)

        self.middle_name_edit = QLineEdit()
        self.middle_name_edit.setPlaceholderText("Optional")
        form.addRow("Middle Name:", self.middle_name_edit)

        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("Required")
        form.addRow("Last Name:", self.last_name_edit)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Use semicolon for multiple: 555-123-4567; 555-987-6543")
        form.addRow("Phone(s):", self.phone_edit)

        phone_hint = QLabel("Separate multiple phone numbers with semicolons")
        phone_hint.setStyleSheet("color: gray; font-size: 10px;")
        form.addRow("", phone_hint)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Use semicolon for multiple: a@b.com; c@d.com")
        form.addRow("Email(s):", self.email_edit)

        email_hint = QLabel("Separate multiple email addresses with semicolons")
        email_hint.setStyleSheet("color: gray; font-size: 10px;")
        form.addRow("", email_hint)

        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.address_edit.setPlaceholderText("Use semicolons to separate multiple addresses")
        form.addRow("Address(es):", self.address_edit)

        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0, 10000)
        self.rate_spin.setDecimals(2)
        self.rate_spin.setPrefix("$")
        self.rate_spin.setValue(300.00)
        form.addRow("Billing Rate:", self.rate_spin)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_client(self):
        self.first_name_edit.setText(self.client.first_name)
        self.middle_name_edit.setText(self.client.middle_name or "")
        self.last_name_edit.setText(self.client.last_name)
        self.phone_edit.setText(self.client.phone or "")
        self.email_edit.setText(self.client.email or "")
        self.address_edit.setText(self.client.address or "")
        self.rate_spin.setValue(self.client.billing_rate_cents / 100.0)

    def validate_and_accept(self):
        if not validate_required_field(self.first_name_edit, "First name", self):
            return
        if not validate_required_field(self.last_name_edit, "Last name", self):
            return
        if not validate_multi_email_field(self.email_edit, self):
            return
        if not validate_multi_phone_field(self.phone_edit, self):
            return

        rate = self.rate_spin.value()
        if rate == 0:
            reply = QMessageBox.question(
                self, "Confirm Billing Rate",
                "Billing rate is set to $0.00. Are you sure this is correct?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                self.rate_spin.setFocus()
                return
        elif rate > 2000:
            reply = QMessageBox.question(
                self, "Confirm Billing Rate",
                f"Billing rate is set to ${rate:.2f}/hour, which is unusually high. Are you sure this is correct?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                self.rate_spin.setFocus()
                return

        self.accept()

    def get_client(self) -> Client:
        return Client(
            first_name=self.first_name_edit.text().strip(),
            middle_name=self.middle_name_edit.text().strip(),
            last_name=self.last_name_edit.text().strip(),
            phone=self.phone_edit.text().strip(),
            email=self.email_edit.text().strip(),
            address=self.address_edit.toPlainText().strip(),
            billing_rate_cents=int(round(self.rate_spin.value() * 100))
        )