from gui.dialogs.base_dialog import StaffDialogBase
from core.models import OpposingStaff
from core.queries import OpposingAttorneyQueries


class OpposingStaffDialog(StaffDialogBase):
    window_title_add = "Add Staff Member"
    window_title_edit = "Edit Staff Member"
    parent_label = "Attorney:"
    parent_placeholder = "-- Select Attorney --"

    def __init__(self, parent=None, attorney_queries: OpposingAttorneyQueries = None, 
                 staff: OpposingStaff = None, preselect_attorney_id: int = None):
        super().__init__(parent, attorney_queries, staff, preselect_attorney_id)

    def format_parent_item(self, attorney) -> str:
        display = attorney.name
        if attorney.firm_name:
            display += f" ({attorney.firm_name})"
        return display

    def load_entity(self):
        self.load_staff_fields(
            name=self.entity.name,
            job_title=self.entity.job_title,
            phone=self.entity.phone,
            email=self.entity.email,
            parent_id=self.entity.attorney_id
        )

    def get_entity(self) -> OpposingStaff:
        values = self.get_staff_field_values()
        return OpposingStaff(
            name=values["name"],
            job_title=values["job_title"],
            attorney_id=values["parent_id"],
            phone=values["phone"],
            email=values["email"]
        )

    def get_staff(self) -> OpposingStaff:
        return self.get_entity()