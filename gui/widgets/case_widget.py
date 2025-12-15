from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter,
    QTableWidget, QTableWidgetItem, QMessageBox, QLabel, QGroupBox
)
from PySide6.QtCore import Qt
from core.queries import CaseQueries, PersonQueries, CasePersonQueries, RecentCountyQueries
from gui.dialogs.case_dialog import CaseDialog
from gui.widgets.case_detail_widget import CaseDetailWidget
from gui.widgets.styled_combo_box import StyledComboBox
from gui.widgets.base_table_widget import configure_standard_table, get_selected_row_id


class CaseWidget(QWidget):
    column_headers = ["ID", "Matter #", "Client", "Status", "Litigation", "Case Number", "Court", "County", "Rate"]
    def __init__(self, case_queries: CaseQueries, person_queries: PersonQueries,
                 case_person_queries: CasePersonQueries, recent_county_queries: RecentCountyQueries):
        super().__init__()
        self.case_queries = case_queries
        self.person_queries = person_queries
        self.case_person_queries = case_person_queries
        self.recent_county_queries = recent_county_queries
        
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Vertical)

        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)

        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Select Matter:"))
        self.matter_combo = StyledComboBox()
        self.matter_combo.setMinimumWidth(300)
        self.matter_combo.currentIndexChanged.connect(self.on_combo_matter_selected)
        selection_layout.addWidget(self.matter_combo)
        selection_layout.addStretch()
        list_layout.addLayout(selection_layout)

        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("Create Matter")
        self.add_btn.clicked.connect(self.add_case)
        button_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("Edit Matter")
        self.edit_btn.setEnabled(False)
        self.edit_btn.clicked.connect(self.edit_case)
        button_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete Matter")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_case)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(self.refresh_btn)

        list_layout.addLayout(button_layout)

        self.table = QTableWidget()
        configure_standard_table(self.table, self.column_headers)
        self.table.itemSelectionChanged.connect(self.on_case_selected)
        self.table.doubleClicked.connect(self.edit_case)
        list_layout.addWidget(self.table)

        self.count_label = QLabel()
        list_layout.addWidget(self.count_label)

        splitter.addWidget(list_widget)

        detail_group = QGroupBox("Matter Details")
        detail_layout = QVBoxLayout(detail_group)
        detail_layout.setContentsMargins(5, 5, 5, 5)

        self.detail_widget = CaseDetailWidget(
            self.person_queries, 
            self.case_person_queries,
            self.case_queries
        )
        self.detail_widget.case_updated.connect(self.on_case_detail_updated)
        detail_layout.addWidget(self.detail_widget)

        splitter.addWidget(detail_group)

        splitter.setSizes([400, 400])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    def load_matter_combo(self, cases: list):
        self.matter_combo.blockSignals(True)
        self.matter_combo.clear()
        self.matter_combo.addItem("-- Select a Matter --", None)
        
        for case_data in cases:
            matter_name = case_data.get('case_name') or ''
            case_id = case_data.get('id')
            self.matter_combo.addItem(matter_name, case_id)
        
        self.matter_combo.blockSignals(False)

    def on_combo_matter_selected(self, index):
        case_id = self.matter_combo.currentData()
        if case_id is None:
            self.table.clearSelection()
            self.detail_widget.set_case(None)
            return
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and int(item.text()) == case_id:
                self.table.selectRow(row)
                break

    def populate_table(self, cases: list):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(cases))

        for row, case_data in enumerate(cases):
            self.table.setItem(row, 0, QTableWidgetItem(str(case_data.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(case_data.get('case_name') or ''))
            self.table.setItem(row, 2, QTableWidgetItem(case_data.get('client_name') or 'No Client'))
            self.table.setItem(row, 3, QTableWidgetItem(case_data.get('status') or 'Open'))
            
            is_litigation = case_data.get('is_litigation')
            litigation_display = "Yes" if is_litigation else "No"
            self.table.setItem(row, 4, QTableWidgetItem(litigation_display))
            
            self.table.setItem(row, 5, QTableWidgetItem(case_data.get('case_number') or ''))
            self.table.setItem(row, 6, QTableWidgetItem(case_data.get('court_type') or ''))
            
            county = case_data.get('county')
            county_display = f"{county} County" if county else ''
            self.table.setItem(row, 7, QTableWidgetItem(county_display))
            
            rate_cents = case_data.get('billing_rate_cents') or 0
            rate_display = f"${rate_cents / 100:.2f}/hr"
            self.table.setItem(row, 8, QTableWidgetItem(rate_display))

        self.table.setSortingEnabled(True)
        self.count_label.setText(f"Total Matters: {len(cases)}")

    def get_selected_case_id(self) -> int:
        return get_selected_row_id(self.table)

    def on_case_selected(self):
        case_id = self.get_selected_case_id()
        self.detail_widget.set_case(case_id)

        has_selection = case_id is not None
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

        if case_id:
            self.matter_combo.blockSignals(True)
            for i in range(self.matter_combo.count()):
                if self.matter_combo.itemData(i) == case_id:
                    self.matter_combo.setCurrentIndex(i)
                    break
            self.matter_combo.blockSignals(False)

    def on_case_detail_updated(self):
        self.refresh()

    def refresh(self):
        cases = self.case_queries.get_all_with_client()
        self.populate_table(cases)
        self.load_matter_combo(cases)

        selected_id = self.get_selected_case_id()
        if selected_id:
            self.detail_widget.refresh()

    def select_case(self, case_id: int):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and int(item.text()) == case_id:
                self.table.selectRow(row)
                break
        
        self.matter_combo.blockSignals(True)
        for i in range(self.matter_combo.count()):
            if self.matter_combo.itemData(i) == case_id:
                self.matter_combo.setCurrentIndex(i)
                break
        self.matter_combo.blockSignals(False)
        
        self.detail_widget.set_case(case_id)

    def add_case(self):
        dialog = CaseDialog(
            parent=self, 
            case_queries=self.case_queries,
            person_queries=self.person_queries,
            recent_county_queries=self.recent_county_queries
        )
        if dialog.exec():
            case = dialog.get_case()
            client = dialog.get_client()
            party_designation = dialog.get_party_designation()
            
            if dialog.is_creating_new_client():
                client_id = self.person_queries.create(client)
            else:
                client_id = client.id
            
            case_id = self.case_queries.create_with_client(case, client_id, party_designation)
            self.refresh()
            self.select_case(case_id)

    def edit_case(self):
        case_id = self.get_selected_case_id()
        if not case_id:
            QMessageBox.warning(self, "Warning", "Please select a matter to edit.")
            return

        case = self.case_queries.get_by_id(case_id)
        if case:
            client_info = self.case_person_queries.get_by_role(case_id, 'client')
            client_party_designation = None
            if client_info:
                client_party_designation = client_info[0].get('party_designation')
            
            dialog = CaseDialog(
                parent=self, 
                case_queries=self.case_queries,
                person_queries=self.person_queries,
                recent_county_queries=self.recent_county_queries,
                case=case,
                client_party_designation=client_party_designation
            )
            if dialog.exec():
                updated_case = dialog.get_case()
                updated_case.id = case_id
                self.case_queries.update(updated_case)
                
                new_party_designation = dialog.get_party_designation()
                self.case_person_queries.update_client_designation(case_id, new_party_designation)
                
                self.refresh()
                self.select_case(case_id)

    def delete_case(self):
        case_id = self.get_selected_case_id()
        if not case_id:
            QMessageBox.warning(self, "Warning", "Please select a matter to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this matter?\n\n"
            "This will also delete all billing entries and payment associations for this matter.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.case_queries.delete(case_id)
            self.detail_widget.set_case(None)
            self.refresh()