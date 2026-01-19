from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QRadioButton,
    QButtonGroup, QCheckBox, QMessageBox
)
from core.models import Person, CasePerson, ROLE_DISPLAY_NAMES, PARTY_DESIGNATIONS, PARTY_DESIGNATION_DISPLAY
from core.queries import PersonQueries
from gui.dialogs.base_dialog import BaseFormDialog
from gui.widgets.person_form_widget import PersonFormWidget
from gui.widgets.styled_combo_box import StyledComboBox
from gui.utils import load_combo_with_items


class AddPersonToCaseDialog(BaseFormDialog):
    def __init__(self, parent=None, person_queries: PersonQueries = None,
                 case_id: int = None, role: str = None, 
                 represents_person_id: int = None, represents_name: str = None,
                 existing_parties: list = None, is_litigation: bool = False):
        self.person_queries = person_queries
        self.case_id = case_id
        self.role = role
        self.represents_person_id = represents_person_id
        self.represents_name = represents_name
        self.existing_parties = existing_parties or []
        self.is_litigation = is_litigation
        self.selected_person = None

        self.represents_person_data = None
        if represents_person_id and role in ('opposing_staff', 'judge_staff'):
            self.represents_person_data = person_queries.get_by_id(represents_person_id)

        title = f"Add {ROLE_DISPLAY_NAMES.get(role, 'Person')} to Case"
        super().__init__(parent, title=title, min_width=500)

    def setup_ui(self):
        role_label = QLabel(f"<b>Role:</b> {ROLE_DISPLAY_NAMES.get(self.role, self.role)}")
        self.main_layout.addWidget(role_label)

        if self.represents_name:
            rep_label = QLabel(f"<b>Representing:</b> {self.represents_name}")
            self.main_layout.addWidget(rep_label)

        if self.role == 'opposing_counsel' and not self.represents_person_id and self.existing_parties:
            party_group = QGroupBox("Represents Which Party?")
            party_layout = QVBoxLayout(party_group)
            self.party_combo = StyledComboBox()
            self.party_combo.addItem("-- Select Party --", None)
            for party in self.existing_parties:
                name = f"{party['first_name']} {party['last_name']}"
                self.party_combo.addItem(name, party['person_id'])
            party_layout.addWidget(self.party_combo)
            self.main_layout.addWidget(party_group)
        else:
            self.party_combo = None

        if self.role in ('client', 'opposing_party') and self.is_litigation:
            designation_group = QGroupBox("Party Designation")
            designation_layout = QVBoxLayout(designation_group)
            self.designation_combo = StyledComboBox()
            self.designation_combo.addItem("-- Select --", None)
            for designation in PARTY_DESIGNATIONS:
                self.designation_combo.addItem(PARTY_DESIGNATION_DISPLAY[designation], designation)
            designation_layout.addWidget(self.designation_combo)
            self.main_layout.addWidget(designation_group)
        else:
            self.designation_combo = None

        method_group = QGroupBox("Find or Create Person")
        method_layout = QVBoxLayout(method_group)

        self.method_button_group = QButtonGroup(self)
        self.select_radio = QRadioButton("Select existing person")
        self.create_radio = QRadioButton("Create new person")
        self.method_button_group.addButton(self.select_radio)
        self.method_button_group.addButton(self.create_radio)
        self.select_radio.setChecked(True)

        method_layout.addWidget(self.select_radio)
        method_layout.addWidget(self.create_radio)
        self.main_layout.addWidget(method_group)

        self.select_group = QGroupBox("Select Existing Person")
        select_layout = QVBoxLayout(self.select_group)
        
        self.person_combo = StyledComboBox()
        self.person_combo.currentIndexChanged.connect(self.on_person_combo_changed)
        self.load_person_combo()
        select_layout.addWidget(self.person_combo)
        
        self.main_layout.addWidget(self.select_group)

        self.create_group = QGroupBox("Create New Person")
        create_layout = QVBoxLayout(self.create_group)
        self.person_form = PersonFormWidget(show_professional=True, compact=True)
        
        if self.represents_person_data and self.role in ('opposing_staff', 'judge_staff'):
            self._prepopulate_staff_fields()
        
        create_layout.addWidget(self.person_form)
        self.main_layout.addWidget(self.create_group)
        self.create_group.hide()

        if self.role == 'opposing_party':
            self.pro_se_checkbox = QCheckBox("This party is representing themselves (Pro Se)")
            self.main_layout.addWidget(self.pro_se_checkbox)
        else:
            self.pro_se_checkbox = None

        self.select_radio.toggled.connect(self.on_method_changed)
        self.create_radio.toggled.connect(self.on_method_changed)

    def _prepopulate_staff_fields(self):
        if not self.represents_person_data:
            return
        
        person = self.represents_person_data
        
        if person.phone:
            self.person_form.phone_edit.setText(person.phone)
        if person.address:
            self.person_form.address_edit.setText(person.address)
        if person.firm_name and self.person_form.firm_edit:
            self.person_form.firm_edit.setText(person.firm_name)

    def load_person_combo(self):
        def formatter(person):
            display = person.display_name
            if person.firm_name:
                display += f" ({person.firm_name})"
            elif person.job_title:
                display += f" ({person.job_title})"
            return (display, person)
        load_combo_with_items(
            self.person_combo,
            self.person_queries.get_all(),
            formatter,
            "-- Select a Person --"
        )

    def set_initial_focus(self):
        if self.select_radio.isChecked():
            self.person_combo.setFocus()

    def on_person_combo_changed(self, index):
        self.selected_person = self.person_combo.currentData()

    def on_method_changed(self):
        is_select = self.select_radio.isChecked()
        self.select_group.setVisible(is_select)
        self.create_group.setVisible(not is_select)
        
        if not is_select and self.represents_person_data and self.role in ('opposing_staff', 'judge_staff'):
            self._prepopulate_staff_fields()
        self.adjustSize()

    def validate(self) -> bool:
        if self.party_combo and not self.party_combo.currentData():
            self.show_validation_warning("Please select which party this attorney represents.")
            return False

        if self.select_radio.isChecked():
            if not self.selected_person:
                self.show_validation_warning("Please select a person.")
                self.person_combo.setFocus()
                return False
        else:
            if not self.person_form.validate(self):
                return False

            first = self.person_form.get_first_name()
            last = self.person_form.get_last_name()
            duplicates = self.person_queries.find_duplicates(first, last)
            
            if duplicates:
                msg = f"A person named '{first} {last}' already exists.\n\n"
                msg += "Would you like to use the existing person instead?"
                
                reply = QMessageBox.question(
                    self, "Possible Duplicate", msg,
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                )
                if reply == QMessageBox.Yes:
                    self.select_radio.setChecked(True)
                    self.load_person_combo()
                    return False
                elif reply == QMessageBox.Cancel:
                    return False

        return True

    def get_person(self) -> Person:
        if self.select_radio.isChecked():
            return self.selected_person
        else:
            return self.person_form.get_person()

    def is_creating_new(self) -> bool:
        return self.create_radio.isChecked()

    def get_case_person(self, person_id: int) -> CasePerson:
        rep_id = self.represents_person_id
        if self.party_combo and self.party_combo.currentData():
            rep_id = self.party_combo.currentData()

        party_designation = None
        if self.designation_combo and self.designation_combo.currentData():
            party_designation = self.designation_combo.currentData()

        return CasePerson(
            case_id=self.case_id,
            person_id=person_id,
            role=self.role,
            party_designation=party_designation,
            represents_person_id=rep_id,
            is_pro_se=self.pro_se_checkbox.isChecked() if self.pro_se_checkbox else False
        )