from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QMessageBox, QCheckBox, QGroupBox,
    QLabel, QHBoxLayout, QDoubleSpinBox, QTextEdit, QRadioButton, QButtonGroup
)
from core.models import Case, Person, PARTY_DESIGNATIONS, PARTY_DESIGNATION_DISPLAY, MATTER_STATUSES
from core.queries import CaseQueries, PersonQueries, RecentCountyQueries
from gui.widgets.county_combo_widget import CountyComboWidget
from gui.widgets.styled_combo_box import StyledComboBox, select_combo_by_data
from gui.utils import select_all_on_focus


class CaseDialog(QDialog):
    def __init__(self, parent=None, case_queries: CaseQueries = None,
                 person_queries: PersonQueries = None,
                 recent_county_queries: RecentCountyQueries = None, 
                 case: Case = None, existing_client_id: int = None,
                 client_party_designation: str = None):
        super().__init__(parent)
        self.case_queries = case_queries
        self.person_queries = person_queries
        self.recent_county_queries = recent_county_queries
        self.case = case
        self.existing_client_id = existing_client_id
        self.client_party_designation = client_party_designation
        self.selected_client = None
        self.selected_client_id = None
        self.selected_person = None
        self.selected_person_id = None
        self.is_edit_mode = case is not None
        self.matter_number_label = None
        
        self.setWindowTitle("Edit Matter" if case else "Create New Matter")
        self.setMinimumWidth(500)
        self.setup_ui()

        if case:
            self.load_case()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        if not self.is_edit_mode:
            client_group = QGroupBox("Client (Required)")
            client_layout = QVBoxLayout(client_group)

            self.client_method_group = QButtonGroup(self)
            self.select_client_radio = QRadioButton("Select existing client")
            self.select_person_radio = QRadioButton("Select from all people")
            self.create_client_radio = QRadioButton("Create new client")
            self.client_method_group.addButton(self.select_client_radio)
            self.client_method_group.addButton(self.select_person_radio)
            self.client_method_group.addButton(self.create_client_radio)
            self.select_client_radio.setChecked(True)

            method_layout = QHBoxLayout()
            method_layout.addWidget(self.select_client_radio)
            method_layout.addWidget(self.select_person_radio)
            method_layout.addWidget(self.create_client_radio)
            method_layout.addStretch()
            client_layout.addLayout(method_layout)

            self.select_client_widget = QGroupBox()
            select_client_layout = QVBoxLayout(self.select_client_widget)
            select_client_layout.setContentsMargins(0, 0, 0, 0)
            
            self.client_combo = StyledComboBox()
            self.client_combo.currentIndexChanged.connect(self.on_client_combo_changed)
            self.load_client_combo()
            select_client_layout.addWidget(self.client_combo)
            
            client_layout.addWidget(self.select_client_widget)

            self.select_person_widget = QGroupBox()
            select_person_layout = QVBoxLayout(self.select_person_widget)
            select_person_layout.setContentsMargins(0, 0, 0, 0)
            
            self.person_combo = StyledComboBox()
            self.person_combo.currentIndexChanged.connect(self.on_person_combo_changed)
            self.load_person_combo()
            select_person_layout.addWidget(self.person_combo)
            
            self.select_person_widget.hide()
            client_layout.addWidget(self.select_person_widget)

            self.create_client_widget = QGroupBox()
            create_form = QFormLayout(self.create_client_widget)
            create_form.setContentsMargins(0, 0, 0, 0)

            self.first_name_edit = QLineEdit()
            self.first_name_edit.setPlaceholderText("Required")
            self.first_name_edit.textChanged.connect(self.update_matter_number_preview)
            create_form.addRow("First Name:", self.first_name_edit)

            self.middle_name_edit = QLineEdit()
            create_form.addRow("Middle Name:", self.middle_name_edit)

            self.last_name_edit = QLineEdit()
            self.last_name_edit.setPlaceholderText("Required")
            self.last_name_edit.textChanged.connect(self.update_matter_number_preview)
            create_form.addRow("Last Name:", self.last_name_edit)

            self.phone_edit = QLineEdit()
            self.phone_edit.setPlaceholderText("e.g., 555-123-4567")
            create_form.addRow("Phone:", self.phone_edit)

            self.email_edit = QLineEdit()
            self.email_edit.setPlaceholderText("e.g., email@example.com")
            create_form.addRow("Email:", self.email_edit)

            self.address_edit = QTextEdit()
            self.address_edit.setMaximumHeight(60)
            create_form.addRow("Address:", self.address_edit)

            self.create_client_widget.hide()
            client_layout.addWidget(self.create_client_widget)

            self.select_client_radio.toggled.connect(self.on_client_method_changed)
            self.select_person_radio.toggled.connect(self.on_client_method_changed)
            self.create_client_radio.toggled.connect(self.on_client_method_changed)

            layout.addWidget(client_group)

            self.matter_number_label = QLabel("Matter #: Will be generated automatically")
            self.matter_number_label.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(self.matter_number_label)

        matter_group = QGroupBox("Matter Details")
        matter_form = QFormLayout(matter_group)

        if self.is_edit_mode:
            self.status_combo = StyledComboBox()
            for status in MATTER_STATUSES:
                self.status_combo.addItem(status, status)
            matter_form.addRow("Status:", self.status_combo)

        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0, 10000)
        self.rate_spin.setDecimals(2)
        self.rate_spin.setPrefix("$")
        self.rate_spin.setSuffix("/hr")
        self.rate_spin.setValue(300.00)
        matter_form.addRow("Billing Rate:", self.rate_spin)
        select_all_on_focus(self.rate_spin)

        layout.addWidget(matter_group)

        if self.is_edit_mode:
            info_label = QLabel("Matter number cannot be changed after creation.")
            info_label.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(info_label)

        litigation_group = QGroupBox("Litigation")
        litigation_layout = QVBoxLayout(litigation_group)

        self.is_litigation_checkbox = QCheckBox("This matter involves litigation")
        self.is_litigation_checkbox.toggled.connect(self.on_litigation_changed)
        litigation_layout.addWidget(self.is_litigation_checkbox)

        self.designation_label = QLabel("Client is:")
        self.designation_label.hide()
        litigation_layout.addWidget(self.designation_label)
        
        self.designation_combo = StyledComboBox()
        self.designation_combo.addItem("-- Select Party Designation --", None)
        for designation in PARTY_DESIGNATIONS:
            self.designation_combo.addItem(PARTY_DESIGNATION_DISPLAY[designation], designation)
        self.designation_combo.hide()
        litigation_layout.addWidget(self.designation_combo)

        self.case_number_label = QLabel("Case Number:")
        self.case_number_label.hide()
        litigation_layout.addWidget(self.case_number_label)
        self.case_number_edit = QLineEdit()
        self.case_number_edit.setPlaceholderText("e.g., 2024-CV-12345")
        self.case_number_edit.hide()
        litigation_layout.addWidget(self.case_number_edit)

        self.court_type_label = QLabel("Court Type:")
        self.court_type_label.hide()
        litigation_layout.addWidget(self.court_type_label)
        self.court_type_combo = StyledComboBox()
        self.court_type_combo.addItem("-- Select Court --", None)
        self.court_type_combo.addItem("Superior Court", "Superior Court")
        self.court_type_combo.addItem("Magistrate Court", "Magistrate Court")
        self.court_type_combo.addItem("State Court", "State Court")
        self.court_type_combo.addItem("Juvenile Court", "Juvenile Court")
        self.court_type_combo.hide()
        litigation_layout.addWidget(self.court_type_combo)

        self.county_label = QLabel("County:")
        self.county_label.hide()
        litigation_layout.addWidget(self.county_label)
        self.county_combo = CountyComboWidget(self.recent_county_queries)
        self.county_combo.hide()
        litigation_layout.addWidget(self.county_combo)

        layout.addWidget(litigation_group)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize)

    def load_client_combo(self):
        self.client_combo.clear()
        self.client_combo.addItem("-- Select a Client --", None)
        
        clients = self.person_queries.get_all_clients()
        for client in clients:
            self.client_combo.addItem(client.display_name, client)

    def load_person_combo(self):
        self.person_combo.clear()
        self.person_combo.addItem("-- Select a Person --", None)
        
        people = self.person_queries.get_all()
        for person in people:
            display = person.display_name
            if person.firm_name:
                display += f" ({person.firm_name})"
            elif person.job_title:
                display += f" ({person.job_title})"
            self.person_combo.addItem(display, person)

    def on_client_combo_changed(self, index):
        client = self.client_combo.currentData()
        if client:
            self.selected_client = client
            self.selected_client_id = client.id
        else:
            self.selected_client = None
            self.selected_client_id = None
        self.update_matter_number_preview()

    def on_person_combo_changed(self, index):
        person = self.person_combo.currentData()
        if person:
            self.selected_person = person
            self.selected_person_id = person.id
        else:
            self.selected_person = None
            self.selected_person_id = None
        self.update_matter_number_preview()

    def on_client_method_changed(self):
        self.select_client_widget.setVisible(self.select_client_radio.isChecked())
        self.select_person_widget.setVisible(self.select_person_radio.isChecked())
        self.create_client_widget.setVisible(self.create_client_radio.isChecked())
        self.update_matter_number_preview()
        self.adjustSize()

    def update_matter_number_preview(self):
        if self.is_edit_mode or self.matter_number_label is None:
            return
            
        last_name = None
        if self.select_client_radio.isChecked() and self.selected_client:
            last_name = self.selected_client.last_name
        elif self.select_person_radio.isChecked() and self.selected_person:
            last_name = self.selected_person.last_name
        elif self.create_client_radio.isChecked():
            last_name = self.last_name_edit.text().strip()
        
        if last_name:
            preview = self.case_queries.generate_matter_number(last_name)
            self.matter_number_label.setText(f"Matter #: {preview}")
            self.matter_number_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.matter_number_label.setText("Matter #: Will be generated automatically")
            self.matter_number_label.setStyleSheet("color: gray; font-style: italic;")

    def on_litigation_changed(self, checked):
        self.designation_label.setVisible(checked)
        self.designation_combo.setVisible(checked)
        self.case_number_label.setVisible(checked)
        self.case_number_edit.setVisible(checked)
        self.court_type_label.setVisible(checked)
        self.court_type_combo.setVisible(checked)
        self.county_label.setVisible(checked)
        self.county_combo.setVisible(checked)
        self.adjustSize()

    def load_case(self):
        self.is_litigation_checkbox.setChecked(self.case.is_litigation)
        self.case_number_edit.setText(self.case.case_number or "")
        select_combo_by_data(self.court_type_combo, self.case.court_type)
        self.county_combo.set_county(self.case.county or "")
        select_combo_by_data(self.status_combo, self.case.status)
        self.rate_spin.setValue(self.case.billing_rate_cents / 100.0)
        
        if self.client_party_designation:
            select_combo_by_data(self.designation_combo, self.client_party_designation)

    def validate_and_accept(self):
        if not self.is_edit_mode:
            if self.select_client_radio.isChecked():
                if not self.selected_client:
                    QMessageBox.warning(self, "Validation Error", "Please select a client.")
                    self.client_combo.setFocus()
                    return
            elif self.select_person_radio.isChecked():
                if not self.selected_person:
                    QMessageBox.warning(self, "Validation Error", "Please select a person.")
                    self.person_combo.setFocus()
                    return
            else:
                if not self.first_name_edit.text().strip():
                    QMessageBox.warning(self, "Validation Error", "Client first name is required.")
                    self.first_name_edit.setFocus()
                    return
                if not self.last_name_edit.text().strip():
                    QMessageBox.warning(self, "Validation Error", "Client last name is required.")
                    self.last_name_edit.setFocus()
                    return

                first = self.first_name_edit.text().strip()
                last = self.last_name_edit.text().strip()
                duplicates = self.person_queries.find_duplicates(first, last)
                
                if duplicates:
                    msg = f"A person named '{first} {last}' already exists.\n\n"
                    msg += "Would you like to use the existing person instead?"
                    
                    reply = QMessageBox.question(
                        self, "Possible Duplicate", msg,
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                    )
                    if reply == QMessageBox.Yes:
                        self.select_person_radio.setChecked(True)
                        self.load_person_combo()
                        return
                    elif reply == QMessageBox.Cancel:
                        return

        if self.is_litigation_checkbox.isChecked():
            self.county_combo.record_usage()
            
        self.accept()

    def get_case(self) -> Case:
        is_litigation = self.is_litigation_checkbox.isChecked()
        
        if self.is_edit_mode:
            case_name = self.case.case_name
            status = self.status_combo.currentData()
        else:
            if self.select_client_radio.isChecked():
                last_name = self.selected_client.last_name
            elif self.select_person_radio.isChecked():
                last_name = self.selected_person.last_name
            else:
                last_name = self.last_name_edit.text().strip()
            case_name = self.case_queries.generate_matter_number(last_name)
            status = "Open"
        
        return Case(
            case_name=case_name,
            is_litigation=is_litigation,
            case_number=self.case_number_edit.text().strip() if is_litigation else "",
            court_type=self.court_type_combo.currentData() if is_litigation else None,
            county=self.county_combo.get_selected_county() if is_litigation else "",
            status=status,
            billing_rate_cents=int(round(self.rate_spin.value() * 100))
        )

    def get_client(self) -> Person:
        if self.select_client_radio.isChecked():
            return self.selected_client
        elif self.select_person_radio.isChecked():
            return self.selected_person
        else:
            return Person(
                first_name=self.first_name_edit.text().strip(),
                middle_name=self.middle_name_edit.text().strip(),
                last_name=self.last_name_edit.text().strip(),
                phone=self.phone_edit.text().strip(),
                email=self.email_edit.text().strip(),
                address=self.address_edit.toPlainText().strip()
            )

    def is_creating_new_client(self) -> bool:
        return not self.is_edit_mode and self.create_client_radio.isChecked()

    def get_party_designation(self) -> str:
        if self.is_litigation_checkbox.isChecked():
            return self.designation_combo.currentData()
        return None