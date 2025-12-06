from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup, QWidget, 
    QFormLayout, QDialogButtonBox, QMessageBox
)
from gui.dialogs.base_dialog import StaffDialogBase
from gui.widgets.styled_combo_box import StyledComboBox, populate_combo
from core.models import CourtStaff
from core.queries import JudgeQueries


class StaffDialog(StaffDialogBase):
    window_title_add = "Add Staff Member"
    window_title_edit = "Edit Staff Member"
    parent_label = "Judge:"
    parent_placeholder = "-- Select Judge --"
    parent_required = False

    def __init__(self, parent=None, judge_queries: JudgeQueries = None, 
                 staff: CourtStaff = None, preselect_judge_id: int = None):
        super().__init__(parent, judge_queries, staff, preselect_judge_id)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        staff_type_layout = QHBoxLayout()
        self.staff_type_group = QButtonGroup(self)

        self.judges_staff_radio = QRadioButton("Judge's Staff")
        self.general_staff_radio = QRadioButton("General Court Staff")

        self.staff_type_group.addButton(self.judges_staff_radio)
        self.staff_type_group.addButton(self.general_staff_radio)
        self.general_staff_radio.setChecked(True)

        staff_type_layout.addWidget(self.judges_staff_radio)
        staff_type_layout.addWidget(self.general_staff_radio)
        staff_type_layout.addStretch()
        layout.addLayout(staff_type_layout)

        self.form = QFormLayout()
        self.create_fields()
        layout.addLayout(self.form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.judges_staff_radio.toggled.connect(self.on_staff_type_changed)
        self.on_staff_type_changed()

    def create_parent_selection(self):
        self.judge_combo_widget = QWidget()
        judge_combo_layout = QVBoxLayout(self.judge_combo_widget)
        judge_combo_layout.setContentsMargins(0, 0, 0, 0)
        self.parent_combo = StyledComboBox()
        populate_combo(
            self.parent_combo,
            self.parent_queries.get_all() if self.parent_queries else [],
            lambda j: j.name,
            self.parent_placeholder
        )
        judge_combo_layout.addWidget(self.parent_combo)
        self.form.addRow("Judge:", self.judge_combo_widget)

    def create_staff_fields(self):
        super().create_staff_fields()
        self.job_title_edit.setPlaceholderText("e.g., Calendar Clerk, Law Clerk, Clerk of Court")
        self.email_edit.setPlaceholderText("e.g., clerk@court.gov")

    def on_staff_type_changed(self):
        is_judges_staff = self.judges_staff_radio.isChecked()
        self.judge_combo_widget.setVisible(is_judges_staff)
        self.parent_combo.setEnabled(is_judges_staff)

    def get_selected_parent_id(self):
        if self.judges_staff_radio.isChecked():
            return self.parent_combo.currentData()
        return None

    def validate_parent(self) -> bool:
        if self.judges_staff_radio.isChecked() and not self.parent_combo.currentData():
            QMessageBox.warning(self, "Validation Error", "Please select a judge for judge's staff.")
            self.parent_combo.setFocus()
            return False
        return True

    def load_entity(self):
        self.load_staff_fields(
            name=self.entity.name,
            job_title=self.entity.job_title,
            phone=self.entity.phone,
            email=self.entity.email,
            parent_id=self.entity.judge_id
        )

        if self.entity.judge_id:
            self.judges_staff_radio.setChecked(True)
        else:
            self.general_staff_radio.setChecked(True)

        self.on_staff_type_changed()

    def get_entity(self) -> CourtStaff:
        values = self.get_staff_field_values()
        return CourtStaff(
            name=values["name"],
            job_title=values["job_title"],
            judge_id=values["parent_id"],
            phone=values["phone"],
            email=values["email"]
        )

    def get_staff(self) -> CourtStaff:
        return self.get_entity()