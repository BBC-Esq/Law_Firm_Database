from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QTextEdit, QGroupBox, QVBoxLayout
)
from core.models import Person
from core.validators import validate_required_field, validate_multi_email_field, validate_multi_phone_field


class PersonFormWidget(QWidget):
    def __init__(self, parent=None, show_professional=True, compact=False):
        super().__init__(parent)
        self.show_professional = show_professional
        self.compact = compact
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if self.compact:
            form = QFormLayout()
            layout.addLayout(form)
        else:
            name_group = QGroupBox("Name")
            form = QFormLayout(name_group)
            layout.addWidget(name_group)

        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("Required")
        form.addRow("First Name:", self.first_name_edit)

        self.middle_name_edit = QLineEdit()
        form.addRow("Middle Name:", self.middle_name_edit)
        
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("Required")
        form.addRow("Last Name:", self.last_name_edit)

        if self.compact:
            contact_form = form
        else:
            contact_group = QGroupBox("Contact Information")
            contact_form = QFormLayout(contact_group)
            layout.addWidget(contact_group)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("e.g., 555-123-4567")
        contact_form.addRow("Phone:", self.phone_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("e.g., email@example.com")
        contact_form.addRow("Email:", self.email_edit)

        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(60 if self.compact else 80)
        contact_form.addRow("Address:", self.address_edit)

        if self.show_professional:
            if self.compact:
                prof_form = form
            else:
                prof_group = QGroupBox("Professional Information")
                prof_form = QFormLayout(prof_group)
                layout.addWidget(prof_group)

            self.firm_edit = QLineEdit()
            self.firm_edit.setPlaceholderText("Law firm or company name")
            prof_form.addRow("Firm/Company:", self.firm_edit)

            self.job_title_edit = QLineEdit()
            self.job_title_edit.setPlaceholderText("e.g., Attorney, Paralegal")
            prof_form.addRow("Job Title:", self.job_title_edit)
        else:
            self.firm_edit = None
            self.job_title_edit = None

    def validate(self, parent) -> bool:
        if not validate_required_field(self.first_name_edit, "First name", parent):
            return False
        if not validate_required_field(self.last_name_edit, "Last name", parent):
            return False
        if not validate_multi_email_field(self.email_edit, parent):
            return False
        if not validate_multi_phone_field(self.phone_edit, parent):
            return False
        return True

    def get_person(self) -> Person:
        return Person(
            first_name=self.first_name_edit.text().strip(),
            middle_name=self.middle_name_edit.text().strip(),
            last_name=self.last_name_edit.text().strip(),
            phone=self.phone_edit.text().strip(),
            email=self.email_edit.text().strip(),
            address=self.address_edit.toPlainText().strip(),
            firm_name=self.firm_edit.text().strip() if self.firm_edit else "",
            job_title=self.job_title_edit.text().strip() if self.job_title_edit else ""
        )

    def set_person(self, person: Person):
        self.first_name_edit.setText(person.first_name)
        self.middle_name_edit.setText(person.middle_name or "")
        self.last_name_edit.setText(person.last_name)
        self.phone_edit.setText(person.phone or "")
        self.email_edit.setText(person.email or "")
        self.address_edit.setText(person.address or "")
        if self.firm_edit:
            self.firm_edit.setText(person.firm_name or "")
        if self.job_title_edit:
            self.job_title_edit.setText(person.job_title or "")

    def get_first_name(self) -> str:
        return self.first_name_edit.text().strip()
    
    def get_last_name(self) -> str:
        return self.last_name_edit.text().strip()

    def clear(self):
        self.first_name_edit.clear()
        self.middle_name_edit.clear()
        self.last_name_edit.clear()
        self.phone_edit.clear()
        self.email_edit.clear()
        self.address_edit.clear()
        if self.firm_edit:
            self.firm_edit.clear()
        if self.job_title_edit:
            self.job_title_edit.clear()