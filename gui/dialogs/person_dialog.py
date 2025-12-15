from core.models import Person
from core.validation_helpers import check_duplicate_person
from gui.dialogs.base_dialog import BaseFormDialog
from gui.widgets.person_form_widget import PersonFormWidget


class PersonDialog(BaseFormDialog):
    def __init__(self, parent=None, person_queries=None, person: Person = None):
        self.person_queries = person_queries
        self.person = person
        title = "Edit Person" if person else "Add Person"
        super().__init__(parent, title=title, min_width=500)
        
        if person:
            self.person_form.set_person(person)

    def setup_ui(self):
        self.person_form = PersonFormWidget(show_professional=True, compact=False)
        self.main_layout.addWidget(self.person_form)

    def set_initial_focus(self):
        self.person_form.first_name_edit.setFocus()

    def validate(self) -> bool:
        if not self.person_form.validate(self):
            return False

        if not self.person:
            result = check_duplicate_person(
                self, self.person_queries,
                self.person_form.get_first_name(),
                self.person_form.get_last_name()
            )
            if result != 'create':
                return False

        return True

    def get_person(self) -> Person:
        return self.person_form.get_person()