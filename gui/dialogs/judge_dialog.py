from gui.dialogs.base_dialog import SimpleEntityDialog
from core.models import Judge


class JudgeDialog(SimpleEntityDialog):
    window_title_add = "Add Judge"
    window_title_edit = "Edit Judge"

    def __init__(self, parent=None, judge: Judge = None):
        super().__init__(parent, judge)

    def create_fields(self):
        super().create_fields()
        self.email_edit.setPlaceholderText("e.g., judge@court.gov")

    def load_entity(self):
        self.load_entity_fields(
            name=self.entity.name,
            phone=self.entity.phone,
            email=self.entity.email,
            address=self.entity.address
        )

    def get_entity(self) -> Judge:
        values = self.get_field_values()
        return Judge(
            name=values["name"],
            phone=values["phone"],
            email=values["email"],
            address=values["address"]
        )

    def get_judge(self) -> Judge:
        return self.get_entity()