from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QTextEdit, QMessageBox
)
from core.validators import validate_email_field, validate_phone_field, validate_required_field


class BaseEntityDialog(QDialog):
    window_title_add: str = "Add Item"
    window_title_edit: str = "Edit Item"
    min_width: int = 400

    def __init__(self, parent=None, entity=None):
        super().__init__(parent)
        self.entity = entity
        self.setWindowTitle(self.window_title_edit if entity else self.window_title_add)
        self.setMinimumWidth(self.min_width)
        self.form = None
        self.setup_ui()

        if entity:
            self.load_entity()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.form = QFormLayout()

        self.create_fields()

        layout.addLayout(self.form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def create_fields(self):
        raise NotImplementedError

    def load_entity(self):
        raise NotImplementedError

    def get_entity(self):
        raise NotImplementedError

    def validate_fields(self) -> bool:
        return True

    def validate_and_accept(self):
        if self.validate_fields():
            self.accept()

    def add_line_edit(self, label: str, placeholder: str = "", attr_name: str = None) -> QLineEdit:
        edit = QLineEdit()
        if placeholder:
            edit.setPlaceholderText(placeholder)
        self.form.addRow(label, edit)
        if attr_name:
            setattr(self, attr_name, edit)
        return edit

    def add_text_edit(self, label: str, max_height: int = 80, placeholder: str = "", attr_name: str = None) -> QTextEdit:
        edit = QTextEdit()
        edit.setMaximumHeight(max_height)
        if placeholder:
            edit.setPlaceholderText(placeholder)
        self.form.addRow(label, edit)
        if attr_name:
            setattr(self, attr_name, edit)
        return edit


class SimpleEntityDialog(BaseEntityDialog):
    has_name: bool = True
    has_phone: bool = True
    has_email: bool = True
    has_address: bool = True
    name_required: bool = True

    def create_fields(self):
        if self.has_name:
            self.name_edit = self.add_line_edit("Name:", attr_name="name_edit")

        if self.has_phone:
            self.phone_edit = self.add_line_edit("Phone:", "e.g., 555-123-4567", attr_name="phone_edit")

        if self.has_email:
            self.email_edit = self.add_line_edit("Email:", "", attr_name="email_edit")

        if self.has_address:
            self.address_edit = self.add_text_edit("Address:", 80, attr_name="address_edit")

    def validate_fields(self) -> bool:
        if self.has_name and self.name_required:
            if not validate_required_field(self.name_edit, "Name", self):
                return False
        if self.has_email:
            if not validate_email_field(self.email_edit, self):
                return False
        if self.has_phone:
            if not validate_phone_field(self.phone_edit, self):
                return False
        return True

    def load_entity_fields(self, name="", phone="", email="", address=""):
        if self.has_name:
            self.name_edit.setText(name or "")
        if self.has_phone:
            self.phone_edit.setText(phone or "")
        if self.has_email:
            self.email_edit.setText(email or "")
        if self.has_address:
            self.address_edit.setText(address or "")

    def get_field_values(self) -> dict:
        values = {}
        if self.has_name:
            values["name"] = self.name_edit.text().strip()
        if self.has_phone:
            values["phone"] = self.phone_edit.text().strip()
        if self.has_email:
            values["email"] = self.email_edit.text().strip()
        if self.has_address:
            values["address"] = self.address_edit.toPlainText().strip()
        return values


class StaffDialogBase(BaseEntityDialog):
    parent_label: str = "Parent:"
    parent_placeholder: str = "-- Select --"
    parent_required: bool = True

    def __init__(self, parent=None, parent_queries=None, entity=None, preselect_parent_id: int = None):
        self.parent_queries = parent_queries
        self.preselect_parent_id = preselect_parent_id
        super().__init__(parent, entity)

        if not entity and preselect_parent_id:
            self.select_parent_by_id(preselect_parent_id)

    def create_fields(self):
        self.create_parent_selection()
        self.create_staff_fields()

    def create_parent_selection(self):
        from gui.widgets.styled_combo_box import StyledComboBox, populate_combo
        self.parent_combo = StyledComboBox()
        populate_combo(
            self.parent_combo,
            self.parent_queries.get_all() if self.parent_queries else [],
            self.format_parent_item,
            self.parent_placeholder
        )
        self.form.addRow(self.parent_label, self.parent_combo)

    def format_parent_item(self, item) -> str:
        return str(item.name) if hasattr(item, 'name') else str(item)

    def select_parent_by_id(self, parent_id: int):
        from gui.widgets.styled_combo_box import select_combo_by_data
        select_combo_by_data(self.parent_combo, parent_id)

    def get_selected_parent_id(self):
        return self.parent_combo.currentData()

    def create_staff_fields(self):
        self.name_edit = self.add_line_edit("Name:", attr_name="name_edit")
        self.job_title_edit = self.add_line_edit("Job Title:", "e.g., Paralegal, Legal Assistant", attr_name="job_title_edit")
        self.phone_edit = self.add_line_edit("Phone:", "e.g., 555-123-4567", attr_name="phone_edit")
        self.email_edit = self.add_line_edit("Email:", "", attr_name="email_edit")

    def validate_fields(self) -> bool:
        if not self.validate_parent():
            return False
        if not validate_required_field(self.name_edit, "Name", self):
            return False
        if not validate_required_field(self.job_title_edit, "Job title", self):
            return False
        if not validate_email_field(self.email_edit, self):
            return False
        if not validate_phone_field(self.phone_edit, self):
            return False
        return True

    def validate_parent(self) -> bool:
        if self.parent_required and not self.get_selected_parent_id():
            QMessageBox.warning(self, "Validation Error", f"Please select a {self.parent_label.replace(':', '').lower()}.")
            self.parent_combo.setFocus()
            return False
        return True

    def load_staff_fields(self, name="", job_title="", phone="", email="", parent_id=None):
        self.name_edit.setText(name or "")
        self.job_title_edit.setText(job_title or "")
        self.phone_edit.setText(phone or "")
        self.email_edit.setText(email or "")
        if parent_id:
            self.select_parent_by_id(parent_id)

    def get_staff_field_values(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "job_title": self.job_title_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "parent_id": self.get_selected_parent_id()
        }