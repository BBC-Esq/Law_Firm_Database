from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
from gui.utils import show_table_context_menu
from typing import Callable, List, Dict, Any, Optional


class TooltipTableWidgetItem(QTableWidgetItem):
    def __init__(self, text: str):
        super().__init__(text)
        self.setToolTip(text)


def configure_standard_table(table: QTableWidget, headers: list, 
                             hide_id_column: bool = True,
                             stretch_last: bool = False,
                             resize_mode: QHeaderView.ResizeMode = QHeaderView.Stretch):
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setSectionResizeMode(resize_mode)
    if stretch_last and len(headers) > 1:
        table.horizontalHeader().setSectionResizeMode(len(headers) - 1, QHeaderView.Stretch)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    if hide_id_column and len(headers) > 0:
        table.setColumnHidden(0, True)
    table.setSortingEnabled(True)
    table.setAlternatingRowColors(True)
    table.setContextMenuPolicy(Qt.CustomContextMenu)


def configure_billing_table(table: QTableWidget, headers: list):
    """Configure a table for billing/payment entries with word wrap."""
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setColumnHidden(0, True)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.setWordWrap(True)
    table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    table.horizontalHeader().setSectionResizeMode(len(headers) - 1, QHeaderView.Stretch)
    table.setContextMenuPolicy(Qt.CustomContextMenu)


def get_selected_row_id(table: QTableWidget, id_column: int = 0):
    selected = table.selectedItems()
    if selected:
        row = selected[0].row()
        id_item = table.item(row, id_column)
        if id_item:
            return int(id_item.text())
    return None


def populate_table_rows(table: QTableWidget, data: list, row_formatter: Callable,
                        alignments: Optional[Dict[int, int]] = None,
                        row_styler: Optional[Callable] = None):
    table.setSortingEnabled(False)
    table.setRowCount(len(data))
    
    for row, item in enumerate(data):
        values = row_formatter(item)
        for col, value in enumerate(values):
            text = str(value) if value is not None else ""
            table_item = TooltipTableWidgetItem(text)
            if alignments and col in alignments:
                table_item.setTextAlignment(alignments[col])
            table.setItem(row, col, table_item)
        
        if row_styler:
            row_styler(table, row, item)

    table.setSortingEnabled(True)


class BaseTableWidget(QWidget):
    column_headers = ["ID"]

    def __init__(self):
        super().__init__()
        self.table = None
        self.count_label = None
        self.add_btn = None
        self.refresh_btn = None

    def create_table(self) -> QTableWidget:
        table = QTableWidget()
        configure_standard_table(table, self.column_headers)
        table.doubleClicked.connect(self.edit_item)
        table.customContextMenuRequested.connect(self.show_context_menu)
        return table

    def create_button_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        self.add_btn = QPushButton(self.get_add_button_text())
        self.add_btn.clicked.connect(self.add_item)
        layout.addWidget(self.add_btn)
        layout.addStretch()
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_btn)
        return layout

    def get_add_button_text(self) -> str:
        return "Add"

    def get_selected_id(self):
        return get_selected_row_id(self.table) if self.table else None

    def populate_table(self, data: list):
        if self.table:
            populate_table_rows(self.table, data, self.row_to_values)
            if self.count_label:
                self.count_label.setText(f"Total: {len(data)}")

    def show_context_menu(self, position):
        show_table_context_menu(
            self.table, position,
            edit_callback=self.edit_item,
            delete_callback=self.delete_item,
            extra_actions=self.get_extra_context_actions()
        )

    def get_extra_context_actions(self) -> list:
        return None

    def row_to_values(self, item) -> list:
        raise NotImplementedError

    def refresh(self):
        raise NotImplementedError

    def add_item(self):
        raise NotImplementedError

    def edit_item(self):
        raise NotImplementedError

    def delete_item(self):
        raise NotImplementedError

    def confirm_delete(self, message: str) -> bool:
        return QMessageBox.question(
            self, "Confirm Delete", message,
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes

    def show_warning(self, message: str):
        QMessageBox.warning(self, "Warning", message)

    def show_select_warning(self, item_name: str, action: str):
        self.show_warning(f"Please select a {item_name} to {action}.")