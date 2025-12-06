from PySide6.QtWidgets import QHBoxLayout, QLabel, QMessageBox
from gui.widgets.base_crud_widget import FilterableCRUDWidget, populate_table
from gui.dialogs.payment_dialog import PaymentDialog
from core.queries import PaymentQueries, ClientQueries, CaseQueries


class PaymentsWidget(FilterableCRUDWidget):
    entity_name = "Payment"
    entity_name_plural = "Payments"
    column_headers = ["ID", "Date", "Client", "Case", "Amount", "Method", "Reference"]
    delete_warning = "Are you sure you want to delete this payment?"
    filter_label = "Filter by Client:"
    filter_all_text = "All Clients"

    def __init__(self, payment_queries: PaymentQueries, client_queries: ClientQueries, case_queries: CaseQueries):
        self.client_queries = client_queries
        self.case_queries = case_queries
        self.total_label = None
        super().__init__(payment_queries, client_queries)

    def setup_ui(self):
        super().setup_ui()

        layout = self.layout()

        totals_layout = QHBoxLayout()
        self.total_label = QLabel("Total Payments: $0.00")
        totals_layout.addWidget(self.total_label)
        totals_layout.addStretch()

        layout.addLayout(totals_layout)

    def format_filter_item(self, client):
        return client.display_name

    def get_filtered_items(self, filter_id):
        if filter_id:
            return self.queries.get_by_client(filter_id)
        return self.queries.get_all_with_details()

    def item_to_row(self, payment):
        return [
            str(payment["id"]),
            str(payment["payment_date"]),
            payment["client_name"],
            payment["case_number"] or "General",
            f"${payment['amount_cents'] / 100:.2f}",
            payment["payment_method"] or "",
            payment["reference_number"] or ""
        ]

    def load_items(self):
        filter_id = self.filter_combo.currentData()
        items = self.get_filtered_items(filter_id)
        populate_table(self.table, items, self.item_to_row)

        total_amount_cents = sum(p["amount_cents"] for p in items)

        self.count_label.setText(f"Total {self.entity_name_plural}: {len(items)}")
        if self.total_label:
            self.total_label.setText(f"Total Payments: ${total_amount_cents / 100:.2f}")

    def get_dialog(self, payment=None):
        if payment and isinstance(payment, dict):
            payment = self.queries.get_by_id(payment["id"])
        return PaymentDialog(self, self.client_queries, self.case_queries, payment)

    def get_entity_from_dialog(self, dialog):
        return dialog.get_payment()

    def edit_item(self):
        item_id = self.get_selected_id()
        if not item_id:
            QMessageBox.warning(self, "Warning", f"Please select a {self.entity_name.lower()} to edit.")
            return

        payment = self.queries.get_by_id(item_id)
        if payment:
            dialog = PaymentDialog(self, self.client_queries, self.case_queries, payment)
            if dialog.exec():
                updated = dialog.get_payment()
                updated.id = item_id
                self.queries.update(updated)
                self.refresh()