from PySide6.QtWidgets import QDoubleSpinBox, QCheckBox, QLabel, QFormLayout, QMessageBox
from gui.utils import select_all_on_focus


class BillingEntryMixin:
    def setup_billing_fields(self, form: QFormLayout, initial_hours: float = 0.1):
        self.billing_rate_cents = 0

        self.expense_checkbox = QCheckBox("This is an expense (not billable time)")
        self.expense_checkbox.toggled.connect(self._on_expense_toggled)
        form.addRow("", self.expense_checkbox)

        self.hours_label = QLabel("Hours:")
        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setRange(0.0, 24.0)
        self.hours_spin.setSingleStep(0.1)
        self.hours_spin.setDecimals(1)
        self.hours_spin.setValue(initial_hours)
        self.hours_spin.valueChanged.connect(self._update_billing_preview)
        select_all_on_focus(self.hours_spin)
        form.addRow(self.hours_label, self.hours_spin)

        self.amount_label = QLabel("Amount:")
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 100000.0)
        self.amount_spin.setSingleStep(1.0)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("$")
        self.amount_spin.setValue(0.01)
        self.amount_spin.valueChanged.connect(self._update_billing_preview)
        select_all_on_focus(self.amount_spin)
        form.addRow(self.amount_label, self.amount_spin)
        self.amount_label.hide()
        self.amount_spin.hide()

        self.preview_label = QLabel()
        form.addRow("Total:", self.preview_label)
        self._update_billing_preview()

    def _on_expense_toggled(self, checked):
        self.hours_label.setVisible(not checked)
        self.hours_spin.setVisible(not checked)
        self.amount_label.setVisible(checked)
        self.amount_spin.setVisible(checked)
        self._update_billing_preview()
        self.adjustSize()

    def _update_billing_preview(self):
        if self.expense_checkbox.isChecked():
            self.preview_label.setText(f"${self.amount_spin.value():.2f}")
        else:
            hours = self.hours_spin.value()
            rate = self.billing_rate_cents / 100.0
            self.preview_label.setText(f"${hours * rate:.2f} ({hours:.1f} hrs × ${rate:.2f}/hr)")

    def validate_billing_fields(self, parent) -> bool:
        if self.expense_checkbox.isChecked():
            if self.amount_spin.value() <= 0:
                QMessageBox.warning(parent, "Validation Error", "Please enter an amount greater than zero.")
                self.amount_spin.setFocus()
                return False
        elif self.hours_spin.value() <= 0:
            QMessageBox.warning(parent, "Validation Error", "Please enter hours greater than zero.")
            self.hours_spin.setFocus()
            return False
        return True

    def get_billing_values(self) -> dict:
        is_expense = self.expense_checkbox.isChecked()
        return {
            'hours': None if is_expense else self.hours_spin.value(),
            'is_expense': is_expense,
            'amount_cents': int(round(self.amount_spin.value() * 100)) if is_expense else None
        }

    def load_billing_values(self, hours: float = None, is_expense: bool = False, amount_cents: int = None):
        if is_expense:
            self.expense_checkbox.setChecked(True)
            if amount_cents:
                self.amount_spin.setValue(amount_cents / 100.0)
        elif hours:
            self.hours_spin.setValue(hours)

    def set_billing_rate(self, rate_cents: int):
        self.billing_rate_cents = rate_cents
        self._update_billing_preview()