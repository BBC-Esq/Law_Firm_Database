from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox
)
from core.models import Case
from core.queries import ClientQueries, JudgeQueries, OpposingAttorneyQueries, RecentCountyQueries
from gui.widgets.county_combo_widget import CountyComboWidget
from gui.widgets.styled_combo_box import StyledComboBox, populate_combo, select_combo_by_data


class CaseDialog(QDialog):
    def __init__(self, parent=None, client_queries: ClientQueries = None, 
                 judge_queries: JudgeQueries = None, 
                 opposing_attorney_queries: OpposingAttorneyQueries = None,
                 recent_county_queries: RecentCountyQueries = None,
                 case: Case = None):
        super().__init__(parent)
        self.client_queries = client_queries
        self.judge_queries = judge_queries
        self.opposing_attorney_queries = opposing_attorney_queries
        self.recent_county_queries = recent_county_queries
        self.case = case
        self.setWindowTitle("Edit Case/Matter" if case else "Add Case/Matter")
        self.setMinimumWidth(450)
        self.setup_ui()

        if case:
            self.load_case()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.client_combo = StyledComboBox()
        populate_combo(
            self.client_combo,
            self.client_queries.get_all() if self.client_queries else [],
            lambda c: c.display_name,
            "-- Select Client --"
        )
        form.addRow("Client:", self.client_combo)

        self.case_name_edit = QLineEdit()
        self.case_name_edit.setPlaceholderText("e.g., Smith vs. Jones")
        form.addRow("Case Name:", self.case_name_edit)

        self.case_number_edit = QLineEdit()
        self.case_number_edit.setPlaceholderText("e.g., 2024-CV-12345")
        form.addRow("Case Number:", self.case_number_edit)

        self.court_type_combo = StyledComboBox()
        self.court_type_combo.addItem("-- Select Court (Optional) --", None)
        self.court_type_combo.addItem("Superior Court", "Superior Court")
        self.court_type_combo.addItem("Magistrate Court", "Magistrate Court")
        self.court_type_combo.addItem("State Court", "State Court")
        form.addRow("Court Type:", self.court_type_combo)

        self.county_combo = CountyComboWidget(self.recent_county_queries)
        form.addRow("County:", self.county_combo)

        self.judge_combo = StyledComboBox()
        populate_combo(
            self.judge_combo,
            self.judge_queries.get_all() if self.judge_queries else [],
            lambda j: j.name,
            "-- Select Judge --"
        )
        form.addRow("Judge:", self.judge_combo)

        self.opposing_counsel_combo = StyledComboBox()
        populate_combo(
            self.opposing_counsel_combo,
            self.opposing_attorney_queries.get_all() if self.opposing_attorney_queries else [],
            lambda a: f"{a.name} ({a.firm_name})" if a.firm_name else a.name,
            "Pro Se (No Attorney)"
        )
        form.addRow("Opposing Counsel:", self.opposing_counsel_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_case(self):
        select_combo_by_data(self.client_combo, self.case.client_id)
        self.case_name_edit.setText(self.case.case_name or "")
        self.case_number_edit.setText(self.case.case_number or "")
        select_combo_by_data(self.court_type_combo, self.case.court_type)
        self.county_combo.set_county(self.case.county or "")
        select_combo_by_data(self.judge_combo, self.case.judge_id)
        select_combo_by_data(self.opposing_counsel_combo, self.case.opposing_attorney_id)

    def validate_and_accept(self):
        if not self.client_combo.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select a client.")
            self.client_combo.setFocus()
            return

        self.county_combo.record_usage()
        self.accept()

    def get_case(self) -> Case:
        return Case(
            client_id=self.client_combo.currentData(),
            case_name=self.case_name_edit.text().strip(),
            case_number=self.case_number_edit.text().strip(),
            court_type=self.court_type_combo.currentData(),
            county=self.county_combo.get_selected_county(),
            judge_id=self.judge_combo.currentData(),
            opposing_attorney_id=self.opposing_counsel_combo.currentData()
        )