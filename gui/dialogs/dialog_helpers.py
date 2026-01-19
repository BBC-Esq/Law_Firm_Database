from PySide6.QtWidgets import (
    QDateEdit, QDoubleSpinBox, QTextEdit, QFormLayout, QLabel,
    QCheckBox, QLineEdit
)
from PySide6.QtCore import QDate
from gui.utils import select_all_on_focus


class DialogFieldsMixin:
    
    def create_date_field(self, form: QFormLayout, label: str = "Date:") -> QDateEdit:
        edit = QDateEdit()
        edit.setCalendarPopup(True)
        edit.setDate(QDate.currentDate())
        form.addRow(label, edit)
        return edit
    
    def create_money_field(self, form: QFormLayout, label: str,
                           max_val: float = 100000.0, 
                           step: float = 1.0,
                           initial: float = 0.0,
                           add_to_form: bool = True) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.0, max_val)
        spin.setSingleStep(step)
        spin.setDecimals(2)
        spin.setPrefix("$")
        spin.setValue(initial)
        select_all_on_focus(spin)
        if add_to_form and label:
            form.addRow(label, spin)
        return spin
    
    def create_hours_field(self, form: QFormLayout, label: str = "Hours:",
                           initial: float = 0.5) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.0, 24.0)
        spin.setSingleStep(0.1)
        spin.setDecimals(1)
        spin.setValue(initial)
        select_all_on_focus(spin)
        form.addRow(label, spin)
        return spin
    
    def create_description_field(self, form: QFormLayout,
                                  placeholder: str = "",
                                  max_height: int = 100,
                                  label: str = "Description:") -> QTextEdit:
        edit = QTextEdit()
        edit.setMaximumHeight(max_height)
        edit.setPlaceholderText(placeholder)
        form.addRow(label, edit)
        return edit
    
    def create_preview_label(self, form: QFormLayout, label: str = "Total:") -> QLabel:
        preview = QLabel()
        form.addRow(label, preview)
        return preview

    def create_checkbox(self, form: QFormLayout, text: str, 
                        callback=None) -> QCheckBox:
        checkbox = QCheckBox(text)
        if callback:
            checkbox.toggled.connect(callback)
        form.addRow("", checkbox)
        return checkbox

    def create_line_edit(self, form: QFormLayout, label: str,
                         placeholder: str = "") -> QLineEdit:
        edit = QLineEdit()
        if placeholder:
            edit.setPlaceholderText(placeholder)
        form.addRow(label, edit)
        return edit