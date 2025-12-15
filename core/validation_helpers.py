from PySide6.QtWidgets import QMessageBox
from core.queries import PersonQueries


def check_duplicate_person(parent, person_queries: PersonQueries, 
                           first_name: str, last_name: str,
                           on_use_existing=None) -> str:

    duplicates = person_queries.find_duplicates(first_name, last_name)

    if not duplicates:
        return 'create'

    msg = f"A person named '{first_name} {last_name}' already exists.\n\n"
    msg += "Would you like to use the existing person instead?"
    
    reply = QMessageBox.question(
        parent, "Possible Duplicate", msg,
        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
    )

    if reply == QMessageBox.Yes:
        if on_use_existing:
            on_use_existing(first_name, last_name)
        return 'search'
    elif reply == QMessageBox.Cancel:
        return 'cancel'

    return 'create'