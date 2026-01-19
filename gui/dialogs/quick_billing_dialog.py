from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox, QMessageBox, QLabel, QTextEdit
from core.utils import qdate_to_date, format_matter_display
from gui.dialogs.dialog_helpers import DialogFieldsMixin
from gui.dialogs.billing_entry_mixin import BillingEntryMixin
from gui.widgets.styled_combo_box import StyledComboBox
from gui.utils import load_combo_with_items


class QuickBillingDialog(QDialog, DialogFieldsMixin, BillingEntryMixin):
    def __init__(self, parent=None, case_queries=None, prefill_description=""):
        super().__init__(parent)
        self.case_queries = case_queries
        self.prefill_description = prefill_description

        self.setWindowTitle("Add Billing Entry")
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_matters()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.matter_combo = StyledComboBox()
        self.matter_combo.setMinimumWidth(400)
        self.matter_combo.currentIndexChanged.connect(self.on_matter_changed)
        form.addRow("Matter:", self.matter_combo)

        self.rate_label = QLabel("--")
        form.addRow("Billing Rate:", self.rate_label)

        self.date_edit = self.create_date_field(form)
        self.setup_billing_fields(form, initial_hours=0.1)

        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Enter description of work performed...")
        self.description_edit.setText(self.prefill_description)
        form.addRow("Description:", self.description_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_matters(self):
        if not self.case_queries:
            return

        matters = self.case_queries.get_all_with_client(include_closed=False)
        load_combo_with_items(
            self.matter_combo,
            matters,
            lambda m: (format_matter_display(m, include_client=True), m),
            "-- Select a Matter --"
        )

    def on_matter_changed(self, index):
        matter = self.matter_combo.currentData()
        if matter:
            rate_cents = matter.get('billing_rate_cents') or 0
            self.set_billing_rate(rate_cents)
            self.rate_label.setText(f"${rate_cents / 100:.2f}/hr")
        else:
            self.set_billing_rate(0)
            self.rate_label.setText("--")

    def validate_and_accept(self):
        if not self.matter_combo.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select a matter.")
            self.matter_combo.setFocus()
            return

        if self.validate_billing_fields(self):
            self.accept()

    def get_entry_data(self) -> dict:
        matter = self.matter_combo.currentData()
        entry_date = qdate_to_date(self.date_edit.date())
        billing_values = self.get_billing_values()

        return {
            'case_id': matter['id'],
            'entry_date': entry_date.isoformat(),
            'hours': billing_values['hours'],
            'is_expense': 1 if billing_values['is_expense'] else 0,
            'amount_cents': billing_values['amount_cents'],
            'description': self.description_edit.toPlainText().strip()
        }