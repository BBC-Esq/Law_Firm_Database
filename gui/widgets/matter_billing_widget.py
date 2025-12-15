from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
    QSplitter, QFrame
)
from PySide6.QtCore import Qt
from core.queries import BillingQueries, CaseQueries, PersonQueries, PaymentQueries, CasePersonQueries
from gui.dialogs.billing_dialog import BillingDialog
from gui.dialogs.payment_dialog import PaymentDialog
from gui.widgets.styled_combo_box import StyledComboBox
from gui.widgets.base_table_widget import configure_standard_table, get_selected_row_id


class MatterBillingWidget(QWidget):

    billing_headers = ["ID", "Date", "Type", "Hours", "Amount", "Description"]
    payment_headers = ["ID", "Date", "Fees", "Expenses", "Total", "Description"]

    def __init__(self, billing_queries: BillingQueries, payment_queries: PaymentQueries,
                 case_queries: CaseQueries, person_queries: PersonQueries,
                 case_person_queries: CasePersonQueries):
        super().__init__()
        self.billing_queries = billing_queries
        self.payment_queries = payment_queries
        self.case_queries = case_queries
        self.person_queries = person_queries
        self.case_person_queries = case_person_queries
        self.selected_client_id = None
        self.selected_matter = None
        self.billing_rate_cents = 0
        self.setup_ui()
        self.load_matters_combo()
        self.update_grand_totals()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Select Client Matter:"))
        self.matter_combo = StyledComboBox()
        self.matter_combo.setMinimumWidth(400)
        self.matter_combo.currentIndexChanged.connect(self.on_matter_selected)
        selection_layout.addWidget(self.matter_combo)
        
        selection_layout.addSpacing(30)
        
        selection_layout.addWidget(QLabel("All Matters —"))
        
        selection_layout.addWidget(QLabel("Fees:"))
        self.grand_fees_label = QLabel("$0.00")
        self.grand_fees_label.setStyleSheet("font-weight: bold;")
        selection_layout.addWidget(self.grand_fees_label)
        
        selection_layout.addSpacing(10)
        
        selection_layout.addWidget(QLabel("Expenses:"))
        self.grand_expenses_label = QLabel("$0.00")
        self.grand_expenses_label.setStyleSheet("font-weight: bold;")
        selection_layout.addWidget(self.grand_expenses_label)
        
        selection_layout.addSpacing(10)
        
        selection_layout.addWidget(QLabel("Total:"))
        self.grand_total_label = QLabel("$0.00")
        self.grand_total_label.setStyleSheet("font-weight: bold;")
        selection_layout.addWidget(self.grand_total_label)
        
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
        
        info_layout.addWidget(QLabel("Fees:"))
        self.fee_balance_label = QLabel("--")
        self.fee_balance_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.fee_balance_label)
        
        info_layout.addSpacing(10)
        
        info_layout.addWidget(QLabel("Expenses:"))
        self.expense_balance_label = QLabel("--")
        self.expense_balance_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.expense_balance_label)
        
        info_layout.addSpacing(10)
        
        info_layout.addWidget(QLabel("Total:"))
        self.total_balance_label = QLabel("--")
        self.total_balance_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(self.total_balance_label)
        
        info_layout.addStretch()
        layout.addWidget(self.info_frame)

        splitter = QSplitter(Qt.Vertical)

        billing_group = QGroupBox("Billing Entries")
        billing_layout = QVBoxLayout(billing_group)

        billing_btn_layout = QHBoxLayout()
        self.add_billing_btn = QPushButton("Add Entry")
        self.add_billing_btn.setEnabled(False)
        self.add_billing_btn.clicked.connect(self.add_billing_entry)
        billing_btn_layout.addWidget(self.add_billing_btn)

        self.edit_billing_btn = QPushButton("Edit Entry")
        self.edit_billing_btn.setEnabled(False)
        self.edit_billing_btn.clicked.connect(self.edit_billing_entry)
        billing_btn_layout.addWidget(self.edit_billing_btn)

        self.delete_billing_btn = QPushButton("Delete Entry")
        self.delete_billing_btn.setEnabled(False)
        self.delete_billing_btn.clicked.connect(self.delete_billing_entry)
        billing_btn_layout.addWidget(self.delete_billing_btn)

        billing_btn_layout.addStretch()
        billing_layout.addLayout(billing_btn_layout)

        self.billing_table = QTableWidget()
        configure_standard_table(self.billing_table, self.billing_headers)
        self.billing_table.doubleClicked.connect(self.edit_billing_entry)
        billing_layout.addWidget(self.billing_table)

        splitter.addWidget(billing_group)

        payment_group = QGroupBox("Payments")
        payment_layout = QVBoxLayout(payment_group)

        payment_btn_layout = QHBoxLayout()
        self.add_payment_btn = QPushButton("Add Payment")
        self.add_payment_btn.setEnabled(False)
        self.add_payment_btn.clicked.connect(self.add_payment)
        payment_btn_layout.addWidget(self.add_payment_btn)

        self.edit_payment_btn = QPushButton("Edit Payment")
        self.edit_payment_btn.setEnabled(False)
        self.edit_payment_btn.clicked.connect(self.edit_payment)
        payment_btn_layout.addWidget(self.edit_payment_btn)

        self.delete_payment_btn = QPushButton("Delete Payment")
        self.delete_payment_btn.setEnabled(False)
        self.delete_payment_btn.clicked.connect(self.delete_payment)
        payment_btn_layout.addWidget(self.delete_payment_btn)

        payment_btn_layout.addStretch()
        payment_layout.addLayout(payment_btn_layout)

        self.payment_table = QTableWidget()
        configure_standard_table(self.payment_table, self.payment_headers)
        self.payment_table.doubleClicked.connect(self.edit_payment)
        payment_layout.addWidget(self.payment_table)

        splitter.addWidget(payment_group)

        layout.addWidget(splitter, 1)

    def format_balance(self, amount_cents: int) -> tuple:
        amount = abs(amount_cents) / 100.0
        text = f"${amount:.2f}"
        
        if amount_cents > 0:
            style = "font-weight: bold; color: green;"
        elif amount_cents < 0:
            style = "font-weight: bold; color: red;"
        else:
            style = "font-weight: bold; color: yellow;"
        
        return text, style

    def format_balance_large(self, amount_cents: int) -> tuple:
        amount = abs(amount_cents) / 100.0
        text = f"${amount:.2f}"
        
        if amount_cents > 0:
            style = "font-weight: bold; font-size: 14px; color: green;"
        elif amount_cents < 0:
            style = "font-weight: bold; font-size: 14px; color: red;"
        else:
            style = "font-weight: bold; font-size: 14px; color: yellow;"
        
        return text, style

    def load_matters_combo(self):
        self.matter_combo.clear()
        self.matter_combo.addItem("-- Select a Client Matter --", None)
        
        matters = self.case_queries.get_all_with_client()
        
        for matter in matters:
            client_name = matter.get('client_name') or 'No Client'
            matter_name = matter.get('case_name') or ''
            case_number = matter.get('case_number') or ''
            
            display = f"{client_name} - {matter_name}"
            if case_number:
                display += f" ({case_number})"
            
            self.matter_combo.addItem(display, matter)

    def update_button_states(self, enabled: bool):
        self.add_billing_btn.setEnabled(enabled)
        self.edit_billing_btn.setEnabled(enabled)
        self.delete_billing_btn.setEnabled(enabled)
        self.add_payment_btn.setEnabled(enabled)
        self.edit_payment_btn.setEnabled(enabled)
        self.delete_payment_btn.setEnabled(enabled)

    def update_grand_totals(self):
        matters = self.case_queries.get_all_with_client()
        
        total_fees_balance = 0
        total_expenses_balance = 0
        
        for matter in matters:
            case_id = matter.get('id')
            if case_id:
                billing_totals = self.billing_queries.get_case_totals(case_id)
                payment_totals = self.payment_queries.get_case_payment_totals(case_id)
                
                fee_billed = billing_totals.get("total_time_cents") or 0
                fee_paid = payment_totals.get("total_fee_payments_cents") or 0
                total_fees_balance += (fee_paid - fee_billed)
                
                expense_incurred = billing_totals.get("total_expense_cents") or 0
                expense_paid = payment_totals.get("total_expense_payments_cents") or 0
                total_expenses_balance += (expense_paid - expense_incurred)
        
        grand_total = total_fees_balance + total_expenses_balance
        
        text, style = self.format_balance(total_fees_balance)
        self.grand_fees_label.setText(text)
        self.grand_fees_label.setStyleSheet(style)
        
        text, style = self.format_balance(total_expenses_balance)
        self.grand_expenses_label.setText(text)
        self.grand_expenses_label.setStyleSheet(style)
        
        text, style = self.format_balance(grand_total)
        self.grand_total_label.setText(text)
        self.grand_total_label.setStyleSheet(style)

    def on_matter_selected(self, index):
        matter = self.matter_combo.currentData()
        
        if not matter:
            self.selected_matter = None
            self.selected_client_id = None
            self.billing_rate_cents = 0
            self.client_label.setText("Client: --")
            self.matter_label.setText("Matter: --")
            self.rate_label.setText("Rate: --")
            self.fee_balance_label.setText("--")
            self.fee_balance_label.setStyleSheet("font-weight: bold;")
            self.expense_balance_label.setText("--")
            self.expense_balance_label.setStyleSheet("font-weight: bold;")
            self.total_balance_label.setText("--")
            self.total_balance_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            self.billing_table.setRowCount(0)
            self.payment_table.setRowCount(0)
            self.update_button_states(False)
            return
        
        self.selected_matter = matter
        self.selected_client_id = matter.get('client_id')
        self.billing_rate_cents = matter.get('billing_rate_cents') or 0
        
        client_name = matter.get('client_name') or 'No Client'
        matter_name = matter.get('case_name') or ''
        case_number = matter.get('case_number') or ''
        
        self.client_label.setText(f"Client: {client_name}")
        
        matter_display = matter_name
        if case_number:
            matter_display += f" ({case_number})"
        self.matter_label.setText(f"Matter: {matter_display}")
        
        self.rate_label.setText(f"Rate: ${self.billing_rate_cents / 100:.2f}/hr")

        self.update_button_states(True)
        self.load_billing_entries()
        self.load_payments()
        self.update_matter_totals()

    def update_matter_totals(self):
        if not self.selected_matter:
            return

        billing_totals = self.billing_queries.get_case_totals(self.selected_matter["id"])
        payment_totals = self.payment_queries.get_case_payment_totals(self.selected_matter["id"])

        fee_billed = billing_totals.get("total_time_cents") or 0
        expense_incurred = billing_totals.get("total_expense_cents") or 0
        
        fee_paid = payment_totals.get("total_fee_payments_cents") or 0
        expense_paid = payment_totals.get("total_expense_payments_cents") or 0

        fee_balance = fee_paid - fee_billed
        expense_balance = expense_paid - expense_incurred
        total_balance = fee_balance + expense_balance

        text, style = self.format_balance(fee_balance)
        self.fee_balance_label.setText(text)
        self.fee_balance_label.setStyleSheet(style)

        text, style = self.format_balance(expense_balance)
        self.expense_balance_label.setText(text)
        self.expense_balance_label.setStyleSheet(style)

        text, style = self.format_balance_large(total_balance)
        self.total_balance_label.setText(text)
        self.total_balance_label.setStyleSheet(style)

    def load_billing_entries(self):
        if not self.selected_matter:
            return

        entries = self.billing_queries.get_by_case(self.selected_matter["id"])
        
        self.billing_table.setSortingEnabled(False)
        self.billing_table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            is_expense = entry.get("is_expense", 0)
            hours = entry.get("hours") or 0
            rate = (entry.get("billing_rate_cents") or self.billing_rate_cents) / 100.0
            
            if is_expense:
                amount_cents = entry.get("amount_cents") or 0
                amount = amount_cents / 100.0
                entry_type = "Expense"
                hours_display = "--"
            else:
                amount = hours * rate
                entry_type = "Time"
                hours_display = f"{hours:.1f}"

            self.billing_table.setItem(row, 0, QTableWidgetItem(str(entry["id"])))
            self.billing_table.setItem(row, 1, QTableWidgetItem(str(entry["entry_date"])))
            self.billing_table.setItem(row, 2, QTableWidgetItem(entry_type))
            self.billing_table.setItem(row, 3, QTableWidgetItem(hours_display))
            self.billing_table.setItem(row, 4, QTableWidgetItem(f"${amount:.2f}"))
            self.billing_table.setItem(row, 5, QTableWidgetItem(entry.get("description") or ""))

        self.billing_table.setSortingEnabled(True)

    def load_payments(self):
        if not self.selected_matter:
            return

        payments = self.payment_queries.get_by_case(self.selected_matter["id"])
        
        self.payment_table.setSortingEnabled(False)
        self.payment_table.setRowCount(len(payments))

        for row, payment in enumerate(payments):
            fee_cents = payment.get("amount_cents") or 0
            expense_cents = payment.get("expense_amount_cents") or 0
            total_cents = fee_cents + expense_cents
            
            self.payment_table.setItem(row, 0, QTableWidgetItem(str(payment["id"])))
            self.payment_table.setItem(row, 1, QTableWidgetItem(str(payment["payment_date"])))
            self.payment_table.setItem(row, 2, QTableWidgetItem(f"${fee_cents / 100:.2f}"))
            self.payment_table.setItem(row, 3, QTableWidgetItem(f"${expense_cents / 100:.2f}"))
            self.payment_table.setItem(row, 4, QTableWidgetItem(f"${total_cents / 100:.2f}"))
            self.payment_table.setItem(row, 5, QTableWidgetItem(payment.get("notes") or ""))

        self.payment_table.setSortingEnabled(True)

    def get_selected_billing_id(self):
        return get_selected_row_id(self.billing_table)

    def get_selected_payment_id(self):
        return get_selected_row_id(self.payment_table)

    def add_billing_entry(self):
        if not self.selected_matter:
            return

        dialog = BillingDialog(
            self, 
            self.case_queries,
            case_id=self.selected_matter["id"],
            billing_rate_cents=self.billing_rate_cents
        )

        if dialog.exec():
            entry = dialog.get_entry()
            self.billing_queries.create(entry)
            self.load_billing_entries()
            self.update_matter_totals()
            self.update_grand_totals()

    def edit_billing_entry(self):
        entry_id = self.get_selected_billing_id()
        if not entry_id:
            return

        entry = self.billing_queries.get_by_id(entry_id)
        if entry:
            dialog = BillingDialog(
                self, 
                self.case_queries, 
                entry=entry,
                case_id=self.selected_matter["id"],
                billing_rate_cents=self.billing_rate_cents
            )
            if dialog.exec():
                updated_entry = dialog.get_entry()
                updated_entry.id = entry_id
                self.billing_queries.update(updated_entry)
                self.load_billing_entries()
                self.update_matter_totals()
                self.update_grand_totals()

    def delete_billing_entry(self):
        entry_id = self.get_selected_billing_id()
        if not entry_id:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this billing entry?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.billing_queries.delete(entry_id)
            self.load_billing_entries()
            self.update_matter_totals()
            self.update_grand_totals()

    def add_payment(self):
        if not self.selected_matter or not self.selected_client_id:
            return

        dialog = PaymentDialog(
            self,
            self.person_queries,
            self.case_queries,
            client_id=self.selected_client_id,
            case_id=self.selected_matter["id"]
        )

        if dialog.exec():
            payment = dialog.get_payment()
            self.payment_queries.create(payment)
            self.load_payments()
            self.update_matter_totals()
            self.update_grand_totals()

    def edit_payment(self):
        payment_id = self.get_selected_payment_id()
        if not payment_id:
            return

        payment = self.payment_queries.get_by_id(payment_id)
        if payment:
            dialog = PaymentDialog(
                self,
                self.person_queries,
                self.case_queries,
                payment=payment,
                client_id=self.selected_client_id,
                case_id=self.selected_matter["id"]
            )
            if dialog.exec():
                updated_payment = dialog.get_payment()
                updated_payment.id = payment_id
                self.payment_queries.update(updated_payment)
                self.load_payments()
                self.update_matter_totals()
                self.update_grand_totals()

    def delete_payment(self):
        payment_id = self.get_selected_payment_id()
        if not payment_id:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this payment?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.payment_queries.delete(payment_id)
            self.load_payments()
            self.update_matter_totals()
            self.update_grand_totals()

    def refresh(self):
        current_matter_id = self.selected_matter["id"] if self.selected_matter else None
        self.load_matters_combo()
        self.update_grand_totals()
        
        if current_matter_id:
            for i in range(self.matter_combo.count()):
                matter = self.matter_combo.itemData(i)
                if matter and matter.get("id") == current_matter_id:
                    self.matter_combo.setCurrentIndex(i)
                    break