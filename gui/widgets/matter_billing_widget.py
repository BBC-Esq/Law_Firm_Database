from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
    QSplitter, QFrame
)
from PySide6.QtCore import Qt
from datetime import date
from core.models import BillingEntry
from core.queries import BillingQueries, CaseQueries, PersonQueries, PaymentQueries, CasePersonQueries
from core.utils import format_matter_display
from gui.dialogs.billing_dialog import BillingDialog
from gui.dialogs.payment_dialog import PaymentDialog
from gui.widgets.styled_combo_box import StyledComboBox
from gui.widgets.base_table_widget import get_selected_row_id, configure_billing_table
from gui.utils import show_table_context_menu, format_currency_balance, load_combo_with_items


class MatterBillingWidget(QWidget):

    BILLING_HEADERS = ["ID", "Date", "Type", "Hours", "Amount", "Description"]
    PAYMENT_HEADERS = ["ID", "Date", "Fees", "Expenses", "Total", "Description"]

    def __init__(self, billing_queries: BillingQueries, payment_queries: PaymentQueries,
                 case_queries: CaseQueries, person_queries: PersonQueries,
                 case_person_queries: CasePersonQueries, get_show_closed_callback=None,
                 app_settings=None):
        super().__init__()
        self.billing_queries = billing_queries
        self.payment_queries = payment_queries
        self.case_queries = case_queries
        self.person_queries = person_queries
        self.case_person_queries = case_person_queries
        self.get_show_closed = get_show_closed_callback or (lambda: True)
        self.app_settings = app_settings
        self.selected_client_id = None
        self.selected_matter = None
        self.billing_rate_cents = 0
        self.setup_ui()
        self.load_matters_combo()
        self.update_grand_totals()

    def _create_balance_display(self, layout, label_text, is_large=False):
        layout.addWidget(QLabel(f"{label_text}:"))
        value_label = QLabel("$0.00" if ":" not in label_text else "--")
        style = "font-weight: bold;"
        if is_large:
            style += " font-size: 14px;"
        value_label.setStyleSheet(style)
        layout.addWidget(value_label)
        return value_label

    def _create_table_group(self, title, headers, add_text, add_callback,
                            edit_callback, context_callback):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton(add_text)
        add_btn.setEnabled(False)
        add_btn.clicked.connect(add_callback)
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        table = QTableWidget()
        configure_billing_table(table, headers)
        table.doubleClicked.connect(edit_callback)
        table.customContextMenuRequested.connect(context_callback)
        layout.addWidget(table)

        return group, table, add_btn

    def setup_ui(self):
        layout = QVBoxLayout(self)
        font = self.font()
        font.setPointSize(12)
        self.setFont(font)

        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Select Client Matter:"))
        self.matter_combo = StyledComboBox()
        self.matter_combo.setMinimumWidth(400)
        self.matter_combo.currentIndexChanged.connect(self.on_matter_selected)
        selection_layout.addWidget(self.matter_combo)
        selection_layout.addSpacing(30)
        selection_layout.addWidget(QLabel("All Matters —"))
        
        self.grand_fees_label = self._create_balance_display(selection_layout, "Fees")
        selection_layout.addSpacing(10)
        self.grand_expenses_label = self._create_balance_display(selection_layout, "Expenses")
        selection_layout.addSpacing(10)
        self.grand_total_label = self._create_balance_display(selection_layout, "Total")
        selection_layout.addStretch()
        layout.addLayout(selection_layout)

        self.info_frame = QFrame()
        self.info_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        info_layout = QHBoxLayout(self.info_frame)

        self.client_label = QLabel("Client: --")
        self.client_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.client_label)
        self.matter_label = QLabel("Matter: --")
        info_layout.addWidget(self.matter_label)
        self.rate_label = QLabel("Rate: --")
        info_layout.addWidget(self.rate_label)
        info_layout.addSpacing(20)

        self.fee_balance_label = self._create_balance_display(info_layout, "Fees")
        info_layout.addSpacing(10)
        self.expense_balance_label = self._create_balance_display(info_layout, "Expenses")
        info_layout.addSpacing(10)
        self.total_balance_label = self._create_balance_display(info_layout, "Total", is_large=True)
        info_layout.addStretch()
        layout.addWidget(self.info_frame)

        self.splitter = QSplitter(Qt.Vertical)

        billing_group, self.billing_table, self.add_billing_btn = self._create_table_group(
            "Billing Entries", self.BILLING_HEADERS, "Add Entry",
            self.add_billing_entry, self.edit_billing_entry, self.show_billing_context_menu
        )
        self.splitter.addWidget(billing_group)

        payment_group, self.payment_table, self.add_payment_btn = self._create_table_group(
            "Payments", self.PAYMENT_HEADERS, "Add Payment",
            self.add_payment, self.edit_payment, self.show_payment_context_menu
        )
        self.splitter.addWidget(payment_group)

        if self.app_settings:
            self.app_settings.restore_splitter_state("billing_widget", self.splitter)

        layout.addWidget(self.splitter, 1)

    def save_state(self):
        if self.app_settings:
            self.app_settings.save_splitter_state("billing_widget", self.splitter)

    def show_billing_context_menu(self, position):
        entry_id = self.get_selected_billing_id()
        if not entry_id:
            return

        extra_actions = [
            ("Duplicate with Today's Date", self.duplicate_billing_entry)
        ]

        entries = self.billing_queries.get_entries_on_same_date(entry_id)
        if len(entries) > 1:
            current_idx = None
            for i, e in enumerate(entries):
                if e['id'] == entry_id:
                    current_idx = i
                    break

            if current_idx is not None:
                if current_idx > 0:
                    extra_actions.append(("Move Up (within same date)", self.move_billing_entry_up))
                if current_idx < len(entries) - 1:
                    extra_actions.append(("Move Down (within same date)", self.move_billing_entry_down))

        show_table_context_menu(
            self.billing_table, position,
            edit_callback=self.edit_billing_entry,
            delete_callback=self.delete_billing_entry,
            extra_actions=extra_actions
        )

    def move_billing_entry_up(self):
        entry_id = self.get_selected_billing_id()
        if entry_id:
            if self.billing_queries.move_entry_up(entry_id):
                self.load_billing_entries()

    def move_billing_entry_down(self):
        entry_id = self.get_selected_billing_id()
        if entry_id:
            if self.billing_queries.move_entry_down(entry_id):
                self.load_billing_entries()

    def show_payment_context_menu(self, position):
        if not self.get_selected_payment_id():
            return
        show_table_context_menu(
            self.payment_table, position,
            edit_callback=self.edit_payment,
            delete_callback=self.delete_payment
        )

    def duplicate_billing_entry(self):
        entry_id = self.get_selected_billing_id()
        if not entry_id:
            return
        entry = self.billing_queries.get_by_id(entry_id)
        if entry:
            new_entry = BillingEntry(
                case_id=entry.case_id, entry_date=date.today(),
                hours=entry.hours, is_expense=entry.is_expense,
                amount_cents=entry.amount_cents, description=entry.description
            )
            self.billing_queries.create(new_entry)
            self._refresh_after_change()

    def load_matters_combo(self):
        include_closed = self.get_show_closed()
        matters = self.case_queries.get_all_with_client(include_closed=include_closed)
        load_combo_with_items(
            self.matter_combo, matters,
            lambda m: (format_matter_display(m, include_client=True), m),
            "-- Select a Client Matter --"
        )

    def update_button_states(self, enabled: bool):
        self.add_billing_btn.setEnabled(enabled)
        self.add_payment_btn.setEnabled(enabled)

    def _calculate_all_balances(self):
        include_closed = self.get_show_closed()
        matters = self.case_queries.get_all_with_client(include_closed=include_closed)
        total_fees, total_expenses = 0, 0

        for matter in matters:
            case_id = matter.get('id')
            if case_id:
                bt = self.billing_queries.get_case_totals(case_id)
                pt = self.payment_queries.get_case_payment_totals(case_id)
                total_fees += (pt.get("total_fee_payments_cents", 0) - bt.get("total_time_cents", 0))
                total_expenses += (pt.get("total_expense_payments_cents", 0) - bt.get("total_expense_cents", 0))

        return total_fees, total_expenses

    def update_grand_totals(self):
        fees, expenses = self._calculate_all_balances()
        for label, value in [(self.grand_fees_label, fees), 
                             (self.grand_expenses_label, expenses),
                             (self.grand_total_label, fees + expenses)]:
            text, style = format_currency_balance(value)
            label.setText(text)
            label.setStyleSheet(style)

    def on_matter_selected(self, index):
        matter = self.matter_combo.currentData()

        if not matter:
            self.selected_matter = self.selected_client_id = None
            self.billing_rate_cents = 0
            for label in [self.client_label, self.matter_label, self.rate_label]:
                label.setText(label.text().split(":")[0] + ": --")
            for label in [self.fee_balance_label, self.expense_balance_label, self.total_balance_label]:
                label.setText("--")
                label.setStyleSheet("font-weight: bold;")
            self.billing_table.setRowCount(0)
            self.payment_table.setRowCount(0)
            self.update_button_states(False)
            return

        self.selected_matter = matter
        self.selected_client_id = matter.get('client_id')
        self.billing_rate_cents = matter.get('billing_rate_cents') or 0

        self.client_label.setText(f"Client: {matter.get('client_name') or 'No Client'}")
        matter_display = matter.get('case_name') or ''
        if matter.get('case_number'):
            matter_display += f" ({matter['case_number']})"
        self.matter_label.setText(f"Matter: {matter_display}")
        self.rate_label.setText(f"Rate: ${self.billing_rate_cents / 100:.2f}/hr")

        self.update_button_states(True)
        self.load_billing_entries()
        self.load_payments()
        self.update_matter_totals()

    def update_matter_totals(self):
        if not self.selected_matter:
            return

        bt = self.billing_queries.get_case_totals(self.selected_matter["id"])
        pt = self.payment_queries.get_case_payment_totals(self.selected_matter["id"])

        fee_balance = pt.get("total_fee_payments_cents", 0) - bt.get("total_time_cents", 0)
        expense_balance = pt.get("total_expense_payments_cents", 0) - bt.get("total_expense_cents", 0)

        for label, value, large in [(self.fee_balance_label, fee_balance, False),
                                     (self.expense_balance_label, expense_balance, False),
                                     (self.total_balance_label, fee_balance + expense_balance, True)]:
            text, style = format_currency_balance(value, large)
            label.setText(text)
            label.setStyleSheet(style)

    def _populate_billing_row(self, row, entry):
        is_expense = entry.get("is_expense", 0)
        hours = entry.get("hours") or 0
        rate = (entry.get("billing_rate_cents") or self.billing_rate_cents) / 100.0

        if is_expense:
            amount = (entry.get("amount_cents") or 0) / 100.0
            entry_type, hours_display = "Expense", "--"
        else:
            amount = hours * rate
            entry_type, hours_display = "Time", f"{hours:.1f}"

        items = [
            (str(entry["id"]), None),
            (str(entry.get("entry_date")), Qt.AlignCenter),
            (entry_type, Qt.AlignCenter),
            (hours_display, Qt.AlignCenter),
            (f"${amount:.2f}", Qt.AlignCenter),
            (entry.get("description") or "", None)
        ]
        for col, (text, alignment) in enumerate(items):
            item = QTableWidgetItem(text)
            if alignment:
                item.setTextAlignment(alignment)
            self.billing_table.setItem(row, col, item)

    def load_billing_entries(self):
        if not self.selected_matter:
            return
        entries = self.billing_queries.get_by_case(self.selected_matter["id"])
        self.billing_table.setSortingEnabled(False)
        self.billing_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self._populate_billing_row(row, entry)
        self.billing_table.setSortingEnabled(True)
        self.billing_table.resizeRowsToContents()

    def _populate_payment_row(self, row, payment):
        fee_cents = payment.get("amount_cents") or 0
        expense_cents = payment.get("expense_amount_cents") or 0
        
        items = [
            (str(payment["id"]), None),
            (str(payment["payment_date"]), Qt.AlignCenter),
            (f"${fee_cents / 100:.2f}", Qt.AlignCenter),
            (f"${expense_cents / 100:.2f}", Qt.AlignCenter),
            (f"${(fee_cents + expense_cents) / 100:.2f}", Qt.AlignCenter),
            (payment.get("notes") or "", None)
        ]
        for col, (text, alignment) in enumerate(items):
            item = QTableWidgetItem(text)
            if alignment:
                item.setTextAlignment(alignment)
            self.payment_table.setItem(row, col, item)

    def load_payments(self):
        if not self.selected_matter:
            return
        payments = self.payment_queries.get_by_case(self.selected_matter["id"])
        self.payment_table.setSortingEnabled(False)
        self.payment_table.setRowCount(len(payments))
        for row, payment in enumerate(payments):
            self._populate_payment_row(row, payment)
        self.payment_table.setSortingEnabled(True)
        self.payment_table.resizeRowsToContents()

    def get_selected_billing_id(self):
        return get_selected_row_id(self.billing_table)

    def get_selected_payment_id(self):
        return get_selected_row_id(self.payment_table)

    def _refresh_after_change(self):
        self.load_billing_entries()
        self.load_payments()
        self.update_matter_totals()
        self.update_grand_totals()

    def add_billing_entry(self):
        if not self.selected_matter:
            return
        dialog = BillingDialog(self, self.case_queries, case_id=self.selected_matter["id"],
                               billing_rate_cents=self.billing_rate_cents)
        if dialog.exec():
            self.billing_queries.create(dialog.get_entry())
            self._refresh_after_change()

    def edit_billing_entry(self):
        entry_id = self.get_selected_billing_id()
        if not entry_id:
            return
        entry = self.billing_queries.get_by_id(entry_id)
        if entry:
            dialog = BillingDialog(self, self.case_queries, entry=entry,
                                   case_id=self.selected_matter["id"],
                                   billing_rate_cents=self.billing_rate_cents)
            if dialog.exec():
                updated = dialog.get_entry()
                updated.id = entry_id
                self.billing_queries.update(updated)
                self._refresh_after_change()

    def delete_billing_entry(self):
        entry_id = self.get_selected_billing_id()
        if entry_id and QMessageBox.question(
            self, "Confirm Delete", "Are you sure you want to delete this billing entry?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.billing_queries.delete(entry_id)
            self._refresh_after_change()

    def add_payment(self):
        if not self.selected_matter or not self.selected_client_id:
            return
        dialog = PaymentDialog(self, self.person_queries, self.case_queries,
                               client_id=self.selected_client_id,
                               case_id=self.selected_matter["id"])
        if dialog.exec():
            self.payment_queries.create(dialog.get_payment())
            self._refresh_after_change()

    def edit_payment(self):
        payment_id = self.get_selected_payment_id()
        if not payment_id:
            return
        payment = self.payment_queries.get_by_id(payment_id)
        if payment:
            dialog = PaymentDialog(self, self.person_queries, self.case_queries,
                                   payment=payment, client_id=self.selected_client_id,
                                   case_id=self.selected_matter["id"])
            if dialog.exec():
                updated = dialog.get_payment()
                updated.id = payment_id
                self.payment_queries.update(updated)
                self._refresh_after_change()

    def delete_payment(self):
        payment_id = self.get_selected_payment_id()
        if payment_id and QMessageBox.question(
            self, "Confirm Delete", "Are you sure you want to delete this payment?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.payment_queries.delete(payment_id)
            self._refresh_after_change()

    def refresh(self):
        current_id = self.selected_matter["id"] if self.selected_matter else None
        self.load_matters_combo()
        self.update_grand_totals()
        if current_id:
            for i in range(self.matter_combo.count()):
                matter = self.matter_combo.itemData(i)
                if matter and matter.get("id") == current_id:
                    self.matter_combo.setCurrentIndex(i)
                    break
            else:
                self.on_matter_selected(0)
        else:
            self.on_matter_selected(0)