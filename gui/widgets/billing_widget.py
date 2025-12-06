from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QLabel, QGroupBox
)
from core.queries import BillingQueries, CaseQueries, ClientQueries
from gui.dialogs.billing_dialog import BillingDialog
from gui.widgets.matter_search_widget import MatterSearchWidget
from gui.widgets.base_crud_widget import (
    create_table, populate_table, get_selected_id, show_context_menu
)


class BillingWidget(QWidget):
    column_headers = ["ID", "Date", "Client", "Case Number", "Hours", "Amount", "Description"]

    def __init__(self, billing_queries: BillingQueries, case_queries: CaseQueries, client_queries: ClientQueries):
        super().__init__()
        self.billing_queries = billing_queries
        self.case_queries = case_queries
        self.client_queries = client_queries
        self.current_filter_case_id = None
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        filter_group = QGroupBox("Filter by Client/Matter")
        filter_layout = QVBoxLayout(filter_group)

        self.matter_search = MatterSearchWidget(self.case_queries)
        self.matter_search.matter_selected.connect(self.on_matter_selected)
        filter_layout.addWidget(self.matter_search)

        filter_btn_layout = QHBoxLayout()
        self.apply_filter_btn = QPushButton("Apply Filter")
        self.apply_filter_btn.clicked.connect(self.apply_filter)
        filter_btn_layout.addWidget(self.apply_filter_btn)

        self.clear_filter_btn = QPushButton("Clear Filter")
        self.clear_filter_btn.clicked.connect(self.clear_filter)
        filter_btn_layout.addWidget(self.clear_filter_btn)
        filter_btn_layout.addStretch()
        filter_layout.addLayout(filter_btn_layout)

        layout.addWidget(filter_group)

        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("Add Billing Entry")
        self.add_btn.clicked.connect(self.add_entry)
        button_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("Edit Entry")
        self.edit_btn.clicked.connect(self.edit_entry)
        button_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete Entry")
        self.delete_btn.clicked.connect(self.delete_entry)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(self.refresh_btn)

        layout.addLayout(button_layout)

        self.table = create_table(
            self.column_headers,
            self.edit_entry,
            lambda pos: show_context_menu(self.table, pos)
        )
        layout.addWidget(self.table)

        totals_layout = QHBoxLayout()
        self.total_hours_label = QLabel("Total Hours: 0.0")
        totals_layout.addWidget(self.total_hours_label)

        self.total_amount_label = QLabel("Total Amount: $0.00")
        totals_layout.addWidget(self.total_amount_label)

        totals_layout.addStretch()

        self.entry_count_label = QLabel("Entries: 0")
        totals_layout.addWidget(self.entry_count_label)

        layout.addLayout(totals_layout)

    def on_matter_selected(self, matter):
        pass

    def apply_filter(self):
        matter = self.matter_search.get_selected_matter()
        if matter:
            self.current_filter_case_id = matter["id"]
            self.load_entries()
        else:
            QMessageBox.warning(self, "Warning", "Please select a client/matter to filter.")

    def clear_filter(self):
        self.current_filter_case_id = None
        self.matter_search.clear_selection()
        self.load_entries()

    def refresh(self):
        self.load_entries()

    def entry_to_row(self, entry):
        hours = entry["hours"]
        rate = entry["billing_rate_cents"] / 100.0
        amount = hours * rate
        return [
            str(entry["id"]),
            str(entry["entry_date"]),
            entry["client_name"],
            entry["case_number"] or "",
            f"{hours:.1f}",
            f"${amount:.2f}",
            entry["description"] or ""
        ]

    def load_entries(self):
        if self.current_filter_case_id:
            entries = self.billing_queries.get_by_case(self.current_filter_case_id)
        else:
            entries = self.billing_queries.get_all_with_details()

        populate_table(self.table, entries, self.entry_to_row)

        total_hours = 0.0
        total_amount = 0.0
        for entry in entries:
            hours = entry["hours"]
            rate = entry["billing_rate_cents"] / 100.0
            total_hours += hours
            total_amount += hours * rate

        self.total_hours_label.setText(f"Total Hours: {total_hours:.1f}")
        self.total_amount_label.setText(f"Total Amount: ${total_amount:.2f}")
        self.entry_count_label.setText(f"Entries: {len(entries)}")

    def get_selected_id(self):
        return get_selected_id(self.table)

    def add_entry(self):
        dialog = BillingDialog(self, self.case_queries)

        matter = self.matter_search.get_selected_matter()
        if matter:
            dialog.set_matter(matter)

        if dialog.exec():
            entry = dialog.get_entry()
            self.billing_queries.create(entry)
            self.refresh()

    def edit_entry(self):
        entry_id = self.get_selected_id()
        if not entry_id:
            QMessageBox.warning(self, "Warning", "Please select an entry to edit.")
            return

        entry = self.billing_queries.get_by_id(entry_id)
        if entry:
            dialog = BillingDialog(self, self.case_queries, entry)
            if dialog.exec():
                updated_entry = dialog.get_entry()
                updated_entry.id = entry_id
                self.billing_queries.update(updated_entry)
                self.refresh()

    def delete_entry(self):
        entry_id = self.get_selected_id()
        if not entry_id:
            QMessageBox.warning(self, "Warning", "Please select an entry to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this billing entry?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.billing_queries.delete(entry_id)
            self.refresh()