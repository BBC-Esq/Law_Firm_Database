from gui.widgets.base_crud_widget import BaseMasterDetailWidget
from gui.dialogs.opposing_counsel_dialog import OpposingCounselDialog
from gui.dialogs.opposing_staff_dialog import OpposingStaffDialog
from core.queries import OpposingAttorneyQueries, OpposingStaffQueries


class OpposingCounselWidget(BaseMasterDetailWidget):
    parent_entity_name = "Attorney"
    parent_entity_name_plural = "Attorneys"
    parent_column_headers = ["ID", "Name", "Firm", "Phone", "Email", "Address"]
    parent_group_title = "Opposing Attorneys"

    child_entity_name = "Staff Member"
    child_entity_name_plural = "Staff Members"
    child_column_headers = ["ID", "Name", "Job Title", "Phone", "Email"]
    child_group_title = "Staff Members"
    child_filter_all_text = "All Staff"

    has_general_children = False

    def __init__(self, attorney_queries: OpposingAttorneyQueries, staff_queries: OpposingStaffQueries):
        super().__init__(attorney_queries, staff_queries)

    def parent_to_row(self, attorney):
        return [
            str(attorney.id),
            attorney.name,
            attorney.firm_name or "",
            attorney.phone or "",
            attorney.email or "",
            attorney.address or ""
        ]

    def child_to_row(self, staff):
        return [
            str(staff.id),
            staff.name,
            staff.job_title,
            staff.phone or "",
            staff.email or ""
        ]

    def get_parent_dialog(self, attorney=None):
        return OpposingCounselDialog(self, attorney)

    def get_child_dialog(self, staff=None, preselect_parent_id=None):
        return OpposingStaffDialog(self, self.parent_queries, staff, preselect_attorney_id=preselect_parent_id)

    def get_parent_from_dialog(self, dialog):
        return dialog.get_attorney()

    def get_child_from_dialog(self, dialog):
        return dialog.get_staff()

    def format_parent_filter_text(self, attorney):
        display = attorney.name
        if attorney.firm_name:
            display += f" ({attorney.firm_name})"
        return f"{display}'s Staff"