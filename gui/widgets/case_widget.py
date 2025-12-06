from PySide6.QtWidgets import QTableWidgetItem
from gui.widgets.base_crud_widget import FilterableCRUDWidget
from gui.dialogs.case_dialog import CaseDialog
from core.queries import CaseQueries, ClientQueries, JudgeQueries, OpposingAttorneyQueries, RecentCountyQueries

class CaseWidget(FilterableCRUDWidget):
    entity_name = "Case/Matter"
    entity_name_plural = "Cases/Matters"
    column_headers = ["ID", "Client", "Case Number", "Case Name", "Court Type", "County", "Judge", "Opposing Counsel"]
    delete_warning = "Are you sure you want to delete this case? This will also delete all associated billing entries."
    filter_label = "Filter by Client:"
    filter_all_text = "All Clients"

    def __init__(self, case_queries: CaseQueries, client_queries: ClientQueries, 
                 judge_queries: JudgeQueries, opposing_attorney_queries: OpposingAttorneyQueries,
                 recent_county_queries: RecentCountyQueries):
        self.client_queries = client_queries
        self.judge_queries = judge_queries
        self.opposing_attorney_queries = opposing_attorney_queries
        self.recent_county_queries = recent_county_queries
        super().__init__(case_queries, client_queries)

    def format_filter_item(self, client):
        return client.display_name

    def get_filtered_items(self, filter_id):
        if filter_id:
            return self.queries.get_by_client(filter_id)
        return self.queries.get_all()

    def item_to_row(self, case):
        return [
            str(case["id"]),
            case["client_name"] or "N/A",
            case["case_number"] or "",
            case["case_name"] or "",
            case["court_type"] or "",
            f"{case['county']} County" if case["county"] else "",
            case["judge_name"] or "N/A",
            case["opposing_attorney_name"] or "Pro Se"
        ]

    def get_dialog(self, case=None):
        if case and isinstance(case, dict):
            case = self.queries.get_by_id(case["id"])
        return CaseDialog(
            self, self.client_queries, self.judge_queries,
            self.opposing_attorney_queries, self.recent_county_queries, case
        )

    def get_entity_from_dialog(self, dialog):
        return dialog.get_case()

    def edit_item(self):
        item_id = self.get_selected_id()
        if not item_id:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", f"Please select a {self.entity_name.lower()} to edit.")
            return

        case = self.queries.get_by_id(item_id)
        if case:
            dialog = CaseDialog(
                self, self.client_queries, self.judge_queries,
                self.opposing_attorney_queries, self.recent_county_queries, case
            )
            if dialog.exec():
                updated = dialog.get_case()
                updated.id = item_id
                self.queries.update(updated)
                self.refresh()