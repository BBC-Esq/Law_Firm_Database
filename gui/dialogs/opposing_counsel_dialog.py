from gui.dialogs.base_dialog import SimpleEntityDialog
from core.models import OpposingAttorney


class OpposingCounselDialog(SimpleEntityDialog):
    window_title_add = "Add Opposing Counsel"
    window_title_edit = "Edit Opposing Counsel"

    def create_fields(self):
        self.name_edit = self.add_line_edit("Name:", attr_name="name_edit")
        self.firm_edit = self.add_line_edit("Firm:", "Law firm name (optional)", attr_name="firm_edit")
        self.phone_edit = self.add_line_edit("Phone:", "e.g., 555-123-4567", attr_name="phone_edit")
        self.email_edit = self.add_line_edit("Email:", "e.g., attorney@lawfirm.com", attr_name="email_edit")
        self.address_edit = self.add_text_edit("Address:", 80, attr_name="address_edit")

    def load_entity(self):
        self.load_entity_fields(
            name=self.entity.name,
            phone=self.entity.phone,
            email=self.entity.email,
            address=self.entity.address
        )
        self.firm_edit.setText(self.entity.firm_name or "")

    def get_entity(self) -> OpposingAttorney:
        values = self.get_field_values()
        return OpposingAttorney(
            name=values["name"],
            firm_name=self.firm_edit.text().strip(),
            phone=values["phone"],
            email=values["email"],
            address=values["address"]
        )

    def get_attorney(self) -> OpposingAttorney:
        return self.get_entity()