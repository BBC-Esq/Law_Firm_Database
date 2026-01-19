from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox,
    QDialogButtonBox, QMessageBox, QCheckBox, QLabel, QTextEdit
)
from PySide6.QtCore import QDate
from core.utils import qdate_to_date, format_matter_display
from gui.dialogs.dialog_helpers import DialogFieldsMixin
from gui.widgets.styled_combo_box import StyledComboBox
from gui.utils import select_all_on_focus, load_combo_with_items


class QuickBillingDialog(QDialog, DialogFieldsMixin):
    def __init__(self, parent=None, case_queries=None, prefill_description=""):
        super().__init__(parent)
        self.case_queries = case_queries
        self.prefill_description = prefill_description
        self.billing_rate_cents = 0

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

        self.expense_checkbox = QCheckBox("This is an expense (not billable time)")
        self.expense_checkbox.toggled.connect(self.on_expense_toggled)
        form.addRow("", self.expense_checkbox)

        self.hours_label = QLabel("Hours:")
        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(0.0, 24.0)
        self.hours_spin.setSingleStep(0.1)
        self.hours_spin.setDecimals(1)
        self.hours_spin.setValue(0.1)
        self.hours_spin.valueChanged.connect(self.update_preview)
        select_all_on_focus(self.hours_spin)
        form.addRow(self.hours_label, self.hours_spin)

        self.amount_label = QLabel("Amount:")
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 100000.0)
        self.amount_spin.setSingleStep(1.0)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("$")
        self.amount_spin.setValue(0.01)
        self.amount_spin.valueChanged.connect(self.update_preview)
        select_all_on_focus(self.amount_spin)
        form.addRow(self.amount_label, self.amount_spin)
        self.amount_label.hide()
        self.amount_spin.hide()

        self.preview_label = QLabel()
        form.addRow("Total:", self.preview_label)

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

        self.update_preview()

    def load_matters(self):
        if not self.case_queries:
            return

        matters = self.case_queries.get_open_matters_with_client()
        load_combo_with_items(
            self.matter_combo,
            matters,
            lambda m: (format_matter_display(m, include_client=True), m),
            "-- Select a Matter --"
        )

    def on_matter_changed(self, index):
        matter = self.matter_combo.currentData()
        if matter:
            self.billing_rate_cents = matter.get('billing_rate_cents') or 0
            self.rate_label.setText(f"${self.billing_rate_cents / 100:.2f}/hr")
        else:
            self.billing_rate_cents = 0
            self.rate_label.setText("--")
        self.update_preview()

    def on_expense_toggled(self, checked):
        self.hours_label.setVisible(not checked)
        self.hours_spin.setVisible(not checked)
        self.amount_label.setVisible(checked)
        self.amount_spin.setVisible(checked)
        self.update_preview()
        self.adjustSize()

    def update_preview(self):
        if self.expense_checkbox.isChecked():
            self.preview_label.setText(f"${self.amount_spin.value():.2f}")
        else:
            hours = self.hours_spin.value()
            rate = self.billing_rate_cents / 100.0
            self.preview_label.setText(f"${hours * rate:.2f} ({hours:.1f} hrs × ${rate:.2f}/hr)")

    def validate_and_accept(self):
        if not self.matter_combo.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select a matter.")
            self.matter_combo.setFocus()
            return

        if self.expense_checkbox.isChecked():
            if self.amount_spin.value() <= 0:
                QMessageBox.warning(self, "Validation Error", "Please enter an amount greater than zero.")
                self.amount_spin.setFocus()
                return
        elif self.hours_spin.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Please enter hours greater than zero.")
            self.hours_spin.setFocus()
            return

        self.accept()

    def get_entry_data(self) -> dict:
        matter = self.matter_combo.currentData()
        is_expense = self.expense_checkbox.isChecked()
        entry_date = qdate_to_date(self.date_edit.date())

        return {
            'case_id': matter['id'],
            'entry_date': entry_date.isoformat(),
            'hours': None if is_expense else self.hours_spin.value(),
            'is_expense': 1 if is_expense else 0,
            'amount_cents': int(round(self.amount_spin.value() * 100)) if is_expense else None,
            'description': self.description_edit.toPlainText().strip()
        }