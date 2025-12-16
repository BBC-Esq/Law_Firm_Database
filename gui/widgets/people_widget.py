from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel,
    QGroupBox, QSplitter
)
from PySide6.QtCore import Qt
from core.queries import PersonQueries, CaseQueries, CasePersonQueries
from core.models import ROLE_DISPLAY_NAMES
from gui.dialogs.person_dialog import PersonDialog
from gui.widgets.base_table_widget import BaseTableWidget, configure_standard_table


class PeopleWidget(BaseTableWidget):
    column_headers = ["ID", "Last Name", "First Name", "Phone", "Email", "Firm/Title"]
    case_headers = ["Case Number", "Case Name", "Role(s)", "Client"]

    def __init__(self, person_queries: PersonQueries, case_queries: CaseQueries,
                 case_person_queries: CasePersonQueries):
        super().__init__()
        self.person_queries = person_queries
        self.case_queries = case_queries
        self.case_person_queries = case_person_queries
        self.setup_ui()
        self.refresh()

    def get_add_button_text(self) -> str:
        return "Add Person"

    def setup_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Vertical)

        list_widget = QGroupBox()
        list_layout = QVBoxLayout(list_widget)

        list_layout.addLayout(self.create_button_row())

        self.table = self.create_table()
        self.table.itemSelectionChanged.connect(self.on_person_selected)
        list_layout.addWidget(self.table)

        self.count_label = QLabel()
        list_layout.addWidget(self.count_label)

        splitter.addWidget(list_widget)

        cases_group = QGroupBox("Cases Involving Selected Person")
        cases_layout = QVBoxLayout(cases_group)

        self.cases_table = QTableWidget()
        self.cases_table.setColumnCount(len(self.case_headers))
        self.cases_table.setHorizontalHeaderLabels(self.case_headers)
        self.cases_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cases_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cases_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cases_table.setAlternatingRowColors(True)
        cases_layout.addWidget(self.cases_table)

        self.cases_count_label = QLabel("Select a person to view their cases")
        self.cases_count_label.setStyleSheet("color: gray; font-style: italic;")
        cases_layout.addWidget(self.cases_count_label)

        splitter.addWidget(cases_group)
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)

    def row_to_values(self, person) -> list:
        firm_title = person.firm_name or person.job_title or ""
        return [
            person.id,
            person.last_name,
            person.first_name,
            person.phone or "",
            person.email or "",
            firm_title
        ]

    def on_person_selected(self):
        person_id = self.get_selected_id()
        if person_id:
            self.load_person_cases(person_id)
        else:
            self.cases_table.setRowCount(0)
            self.cases_count_label.setText("Select a person to view their cases")

    def load_person_cases(self, person_id: int):
        cases = self.case_queries.get_cases_for_person(person_id)

        self.cases_table.setRowCount(len(cases))

        for row, case_data in enumerate(cases):
            self.cases_table.setItem(row, 0, QTableWidgetItem(case_data.get('case_number') or ''))
            self.cases_table.setItem(row, 1, QTableWidgetItem(case_data.get('case_name') or ''))

            roles_str = case_data.get('roles') or ''
            roles_display = ", ".join(
                ROLE_DISPLAY_NAMES.get(r.strip(), r.strip()) 
                for r in roles_str.split(',') if r.strip()
            )
            self.cases_table.setItem(row, 2, QTableWidgetItem(roles_display))
            self.cases_table.setItem(row, 3, QTableWidgetItem(case_data.get('client_name') or ''))

        if cases:
            self.cases_count_label.setText(f"Involved in {len(cases)} case(s)")
        else:
            self.cases_count_label.setText("Not involved in any cases")

    def refresh(self):
        people = self.person_queries.get_all()
        self.populate_table(people)

    def add_item(self):
        dialog = PersonDialog(self, self.person_queries)
        if dialog.exec():
            person = dialog.get_person()
            self.person_queries.create(person)
            self.refresh()

    def edit_item(self):
        person_id = self.get_selected_id()
        if not person_id:
            return

        person = self.person_queries.get_by_id(person_id)
        if person:
            dialog = PersonDialog(self, self.person_queries, person)
            if dialog.exec():
                updated_person = dialog.get_person()
                updated_person.id = person_id
                self.person_queries.update(updated_person)
                self.refresh()

    def delete_item(self):
        person_id = self.get_selected_id()
        if not person_id:
            return

        person = self.person_queries.get_by_id(person_id)
        person_name = person.display_name if person else "this person"

        cases = self.case_queries.get_cases_for_person(person_id)

        if cases:
            confirmed = self.confirm_delete(
                f"'{person_name}' is involved in {len(cases)} case(s).\n\n"
                "Deleting them will remove them from all cases.\n"
                "Are you sure you want to delete this person?"
            )
        else:
            confirmed = self.confirm_delete(f"Are you sure you want to delete '{person_name}'?")

        if confirmed:
            self.person_queries.delete(person_id)
            self.cases_table.setRowCount(0)
            self.cases_count_label.setText("Select a person to view their cases")
            self.refresh()