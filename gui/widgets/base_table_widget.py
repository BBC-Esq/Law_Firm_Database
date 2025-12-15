from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLabel
)
from PySide6.QtCore import Qt


def configure_standard_table(table: QTableWidget, headers: list, hide_id_column: bool = True):
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    if hide_id_column and len(headers) > 0:
        table.setColumnHidden(0, True)
    table.setSortingEnabled(True)
    table.setWordWrap(True)
    table.setAlternatingRowColors(True)

def get_selected_row_id(table: QTableWidget, id_column: int = 0):
    selected = table.selectedItems()
    if selected:
        row = selected[0].row()
        id_item = table.item(row, id_column)
        if id_item:
            return int(id_item.text())
    return None


def populate_table_rows(table: QTableWidget, data: list, row_formatter):
    table.setSortingEnabled(False)
    table.setRowCount(len(data))
    
    for row, item in enumerate(data):
        values = row_formatter(item)
        for col, value in enumerate(values):
            table.setItem(row, col, QTableWidgetItem(str(value) if value is not None else ""))
    
    table.setSortingEnabled(True)


class BaseTableWidget(QWidget):
    column_headers = ["ID"]

    def __init__(self):
        super().__init__()
        self.table = None
        self.count_label = None
        self.add_btn = None
        self.edit_btn = None
        self.delete_btn = None
        self.refresh_btn = None

    def create_table(self) -> QTableWidget:
        table = QTableWidget()
        configure_standard_table(table, self.column_headers)
        table.doubleClicked.connect(self.edit_item)
        return table

    def create_button_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        
        self.add_btn = QPushButton(self.get_add_button_text())
        self.add_btn.clicked.connect(self.add_item)
        layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton(self.get_edit_button_text())
        self.edit_btn.clicked.connect(self.edit_item)
        layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton(self.get_delete_button_text())
        self.delete_btn.clicked.connect(self.delete_item)
        layout.addWidget(self.delete_btn)

        layout.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_btn)

        return layout

    def get_add_button_text(self) -> str:
        return "Add"

    def get_edit_button_text(self) -> str:
        return "Edit"

    def get_delete_button_text(self) -> str:
        return "Delete"

    def get_selected_id(self):
        if self.table:
            return get_selected_row_id(self.table)
        return None

    def populate_table(self, data: list):
        if self.table:
            populate_table_rows(self.table, data, self.row_to_values)
            if self.count_label:
                self.count_label.setText(f"Total: {len(data)}")

            if len(data) == 0:
                self.table.setRowCount(1)
                placeholder = QTableWidgetItem(self.get_empty_message())
                placeholder.setFlags(Qt.NoItemFlags)
                placeholder.setForeground(Qt.gray)
                self.table.setItem(0, 1, placeholder)
                self.table.setSpan(0, 1, 1, len(self.column_headers) - 1)

    def get_empty_message(self) -> str:
        return "No items found. Click 'Add' to create one."

    def row_to_values(self, item) -> list:
        raise NotImplementedError("Subclasses must implement row_to_values")

    def refresh(self):
        raise NotImplementedError("Subclasses must implement refresh")

    def add_item(self):
        raise NotImplementedError("Subclasses must implement add_item")

    def edit_item(self):
        raise NotImplementedError("Subclasses must implement edit_item")

    def delete_item(self):
        raise NotImplementedError("Subclasses must implement delete_item")

    def confirm_delete(self, message: str) -> bool:
        reply = QMessageBox.question(
            self, "Confirm Delete", message,
            QMessageBox.Yes | QMessageBox.No
        )
        return reply == QMessageBox.Yes

    def show_warning(self, message: str):
        QMessageBox.warning(self, "Warning", message)

    def show_select_warning(self, item_name: str, action: str):
        self.show_warning(f"Please select a {item_name} to {action}.")