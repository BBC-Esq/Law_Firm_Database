from gui.widgets.base_crud_widget import BaseMasterDetailWidget
from gui.dialogs.judge_dialog import JudgeDialog
from gui.dialogs.staff_dialog import StaffDialog
from core.queries import JudgeQueries, CourtStaffQueries


class CourtWidget(BaseMasterDetailWidget):
    parent_entity_name = "Judge"
    parent_entity_name_plural = "Judges"
    parent_column_headers = ["ID", "Name", "Phone", "Email", "Address"]
    parent_group_title = "Judges"

    child_entity_name = "Staff Member"
    child_entity_name_plural = "Staff Members"
    child_column_headers = ["ID", "Name", "Job Title", "Phone", "Email"]
    child_group_title = "Court Staff"
    child_filter_all_text = "All Staff"

    has_general_children = True
    general_children_text = "General Court Staff"

    def __init__(self, judge_queries: JudgeQueries, staff_queries: CourtStaffQueries):
        super().__init__(judge_queries, staff_queries)

    def parent_to_row(self, judge):
        return [
            str(judge.id),
            judge.name,
            judge.phone or "",
            judge.email or "",
            judge.address or ""
        ]

    def child_to_row(self, staff):
        return [
            str(staff.id),
            staff.name,
            staff.job_title,
            staff.phone or "",
            staff.email or ""
        ]

    def get_parent_dialog(self, judge=None):
        return JudgeDialog(self, judge)

    def get_child_dialog(self, staff=None, preselect_parent_id=None):
        return StaffDialog(self, self.parent_queries, staff, preselect_judge_id=preselect_parent_id)

    def get_parent_from_dialog(self, dialog):
        return dialog.get_judge()

    def get_child_from_dialog(self, dialog):
        return dialog.get_staff()

    def format_parent_filter_text(self, judge):
        return f"{judge.name}'s Staff"