import re
from PySide6.QtWidgets import QMessageBox, QLineEdit


def validate_email(email: str) -> bool:
    if not email:
        return True
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None


def validate_phone(phone: str) -> bool:
    if not phone:
        return True
    digits = re.sub(r'\D', '', phone)
    return 7 <= len(digits) <= 15


def validate_required_field(field: QLineEdit, field_name: str, parent) -> bool:
    if not field.text().strip():
        QMessageBox.warning(parent, "Validation Error", f"{field_name} is required.")
        field.setFocus()
        return False
    return True


def validate_multi_email_field(email_edit: QLineEdit, parent) -> bool:
    email_text = email_edit.text().strip()
    if email_text:
        emails = [e.strip() for e in email_text.split(';') if e.strip()]
        for email in emails:
            if not validate_email(email):
                QMessageBox.warning(parent, "Validation Error", f"Invalid email format: {email}")
                email_edit.setFocus()
                return False
    return True


def validate_multi_phone_field(phone_edit: QLineEdit, parent) -> bool:
    phone_text = phone_edit.text().strip()
    if phone_text:
        phones = [p.strip() for p in phone_text.split(';') if p.strip()]
        for phone in phones:
            if not validate_phone(phone):
                QMessageBox.warning(parent, "Validation Error", f"Invalid phone format: {phone}\nPhone should contain 7-15 digits.")
                phone_edit.setFocus()
                return False
    return True