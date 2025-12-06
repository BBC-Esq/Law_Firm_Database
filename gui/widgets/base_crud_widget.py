from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QLabel, QMenu, QApplication,
    QGroupBox, QSplitter
)
from PySide6.QtCore import Qt
from typing import List, Any, Optional


class SortableTableWidgetItem(QTableWidgetItem):
    def __init__(self, display_text: str, sort_value=None):
        super().__init__(display_text)
        self._sort_value = sort_value if sort_value is not None else display_text
        self.setToolTip(display_text)

    def __lt__(self, other):
        if isinstance(other, SortableTableWidgetItem):
            if self._sort_value is None or self._sort_value == "":
                return False
            if other._sort_value is None or other._sort_value == "":
                return True

            try:
                return float(self._sort_value) < float(other._sort_value)
            except (ValueError, TypeError):
                return str(self._sort_value).lower() < str(other._sort_value).lower()
        return super().__lt__(other)


def parse_sort_value(display_text: str):
    if not display_text:
        return ""

    text = display_text.strip()

    if text.startswith("$"):
        try:
            return float(text.replace("$", "").replace(",", ""))
        except ValueError:
            return text

    if text.endswith("%"):
        try:
            return float(text.replace("%", ""))
        except ValueError:
            return text

    try:
        return float(text)
    except ValueError:
        return text


def create_table(column_headers: List[str], double_click_handler=None, context_menu_handler=None) -> QTableWidget:
    table = QTableWidget()
    table.setColumnCount(len(column_headers))
    table.setHorizontalHeaderLabels(column_headers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.setSelectionBehavior(QTableWidget.SelectRows)
    table.setSelectionMode(QTableWidget.SingleSelection)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setColumnHidden(0, True)
    table.setSortingEnabled(True)
    table.setContextMenuPolicy(Qt.CustomContextMenu)

    if double_click_handler:
        table.doubleClicked.connect(double_click_handler)
    if context_menu_handler:
        table.customContextMenuRequested.connect(context_menu_handler)

    return table


def populate_table(table: QTableWidget, items: List[Any], item_to_row_func):
    table.setSortingEnabled(False)
    table.setRowCount(len(items))

    for row, item in enumerate(items):
        values = item_to_row_func(item)
        for col, value in enumerate(values):
            sort_value = parse_sort_value(str(value))
            table_item = SortableTableWidgetItem(str(value), sort_value)
            table.setItem(row, col, table_item)

    table.setSortingEnabled(True)


def get_selected_id(table: QTableWidget) -> Optional[int]:
    selected = table.selectedItems()
    if selected:
        row = selected[0].row()
        id_item = table.item(row, 0)
        if id_item:
            return int(id_item.text())
    return None


def show_context_menu(table: QTableWidget, position):
    item = table.itemAt(position)
    if item is None:
        return

    menu = QMenu(table)
    copy_action = menu.addAction("Copy Value")
    action = menu.exec(table.viewport().mapToGlobal(position))

    if action == copy_action:
        clipboard = QApplication.clipboard()
        clipboard.setText(item.text())


class BaseCRUDWidget(QWidget):
    entity_name: str = "Item"
    entity_name_plural: str = "Items"
    column_headers: List[str] = ["ID"]
    delete_warning: str = "Are you sure you want to delete this item?"

    def __init__(self, queries):
        super().__init__()
        self.queries = queries
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        filter_layout = self.create_filter_section()
        if filter_layout:
            layout.addLayout(filter_layout)

        button_layout = QHBoxLayout()

        self.add_btn = QPushButton(f"Add {self.entity_name}")
        self.add_btn.clicked.connect(self.add_item)
        button_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton(f"Edit {self.entity_name}")
        self.edit_btn.clicked.connect(self.edit_item)
        button_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton(f"Delete {self.entity_name}")
        self.delete_btn.clicked.connect(self.delete_item)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(self.refresh_btn)

        layout.addLayout(button_layout)

        self.table = create_table(
            self.column_headers,
            self.edit_item,
            lambda pos: show_context_menu(self.table, pos)
        )
        layout.addWidget(self.table)

        self.count_label = QLabel()
        layout.addWidget(self.count_label)

    def create_filter_section(self) -> Optional[QHBoxLayout]:
        return None

    def get_selected_id(self) -> Optional[int]:
        return get_selected_id(self.table)

    def get_items(self) -> List[Any]:
        return self.queries.get_all()

    def item_to_row(self, item) -> List[str]:
        return [str(item.id)]

    def get_dialog(self, item=None):
        raise NotImplementedError

    def get_entity_from_dialog(self, dialog):
        raise NotImplementedError

    def refresh(self):
        items = self.get_items()
        populate_table(self.table, items, self.item_to_row)
        self.count_label.setText(f"Total {self.entity_name_plural}: {len(items)}")

    def add_item(self):
        dialog = self.get_dialog()
        if dialog.exec():
            entity = self.get_entity_from_dialog(dialog)
            self.queries.create(entity)
            self.refresh()

    def edit_item(self):
        item_id = self.get_selected_id()
        if not item_id:
            QMessageBox.warning(self, "Warning", f"Please select a {self.entity_name.lower()} to edit.")
            return

        item = self.queries.get_by_id(item_id)
        if item:
            dialog = self.get_dialog(item)
            if dialog.exec():
                updated = self.get_entity_from_dialog(dialog)
                updated.id = item_id
                self.queries.update(updated)
                self.refresh()

    def delete_item(self):
        item_id = self.get_selected_id()
        if not item_id:
            QMessageBox.warning(self, "Warning", f"Please select a {self.entity_name.lower()} to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete", self.delete_warning,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.queries.delete(item_id)
            self.refresh()


class FilterableCRUDWidget(BaseCRUDWidget):
    filter_label: str = "Filter:"
    filter_all_text: str = "All Items"

    def __init__(self, queries, filter_queries):
        self.filter_queries = filter_queries
        super().__init__(queries)

    def create_filter_section(self) -> QHBoxLayout:
        from gui.widgets.styled_combo_box import StyledComboBox

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel(self.filter_label))
        self.filter_combo = StyledComboBox()
        self.filter_combo.addItem(self.filter_all_text, None)
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        return filter_layout

    def on_filter_changed(self):
        self.load_items()

    def get_filter_items(self) -> List[Any]:
        return self.filter_queries.get_all()

    def format_filter_item(self, item) -> str:
        return str(item)

    def get_filter_item_id(self, item) -> int:
        return item.id

    def refresh_filter(self):
        from gui.widgets.styled_combo_box import select_combo_by_data

        current_data = self.filter_combo.currentData()
        self.filter_combo.blockSignals(True)
        self.filter_combo.clear()
        self.filter_combo.addItem(self.filter_all_text, None)

        items = self.get_filter_items()
        for item in items:
            self.filter_combo.addItem(self.format_filter_item(item), self.get_filter_item_id(item))

        select_combo_by_data(self.filter_combo, current_data)
        self.filter_combo.blockSignals(False)

    def get_filtered_items(self, filter_id: Optional[int]) -> List[Any]:
        if filter_id:
            return self.queries.get_by_parent(filter_id)
        return self.queries.get_all()

    def load_items(self):
        filter_id = self.filter_combo.currentData()
        items = self.get_filtered_items(filter_id)
        populate_table(self.table, items, self.item_to_row)
        self.count_label.setText(f"Total {self.entity_name_plural}: {len(items)}")

    def refresh(self):
        self.refresh_filter()
        self.load_items()


class BaseMasterDetailWidget(QWidget):
    parent_entity_name: str = "Parent"
    parent_entity_name_plural: str = "Parents"
    parent_column_headers: List[str] = ["ID", "Name"]
    parent_group_title: str = "Parents"

    child_entity_name: str = "Child"
    child_entity_name_plural: str = "Children"
    child_column_headers: List[str] = ["ID", "Name"]
    child_group_title: str = "Children"
    child_filter_all_text: str = "All Items"

    has_general_children: bool = False
    general_children_text: str = "General Items"

    def __init__(self, parent_queries, child_queries):
        super().__init__()
        self.parent_queries = parent_queries
        self.child_queries = child_queries
        self.setup_ui()
        self.refresh()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Vertical)

        parent_group = QGroupBox(self.parent_group_title)
        parent_layout = QVBoxLayout(parent_group)

        parent_btn_layout = QHBoxLayout()
        self.add_parent_btn = QPushButton(f"Add {self.parent_entity_name}")
        self.add_parent_btn.clicked.connect(self.add_parent)
        parent_btn_layout.addWidget(self.add_parent_btn)

        self.edit_parent_btn = QPushButton(f"Edit {self.parent_entity_name}")
        self.edit_parent_btn.clicked.connect(self.edit_parent)
        parent_btn_layout.addWidget(self.edit_parent_btn)

        self.delete_parent_btn = QPushButton(f"Delete {self.parent_entity_name}")
        self.delete_parent_btn.clicked.connect(self.delete_parent)
        parent_btn_layout.addWidget(self.delete_parent_btn)

        parent_btn_layout.addStretch()
        parent_layout.addLayout(parent_btn_layout)

        self.parent_table = create_table(
            self.parent_column_headers,
            self.edit_parent,
            lambda pos: show_context_menu(self.parent_table, pos)
        )
        self.parent_table.itemSelectionChanged.connect(self.on_parent_selected)
        parent_layout.addWidget(self.parent_table)

        self.parent_count_label = QLabel()
        parent_layout.addWidget(self.parent_count_label)

        splitter.addWidget(parent_group)

        child_group = QGroupBox(self.child_group_title)
        child_layout = QVBoxLayout(child_group)

        from gui.widgets.styled_combo_box import StyledComboBox
        child_filter_layout = QHBoxLayout()
        child_filter_layout.addWidget(QLabel("View:"))
        self.child_filter_combo = StyledComboBox()
        self.child_filter_combo.currentIndexChanged.connect(self.on_child_filter_changed)
        child_filter_layout.addWidget(self.child_filter_combo)
        child_filter_layout.addStretch()
        child_layout.addLayout(child_filter_layout)

        child_btn_layout = QHBoxLayout()
        self.add_child_btn = QPushButton(f"Add {self.child_entity_name}")
        self.add_child_btn.clicked.connect(self.add_child)
        child_btn_layout.addWidget(self.add_child_btn)

        self.edit_child_btn = QPushButton(f"Edit {self.child_entity_name}")
        self.edit_child_btn.clicked.connect(self.edit_child)
        child_btn_layout.addWidget(self.edit_child_btn)

        self.delete_child_btn = QPushButton(f"Delete {self.child_entity_name}")
        self.delete_child_btn.clicked.connect(self.delete_child)
        child_btn_layout.addWidget(self.delete_child_btn)

        child_btn_layout.addStretch()
        child_layout.addLayout(child_btn_layout)

        self.child_table = create_table(
            self.child_column_headers,
            self.edit_child,
            lambda pos: show_context_menu(self.child_table, pos)
        )
        child_layout.addWidget(self.child_table)

        self.child_count_label = QLabel()
        child_layout.addWidget(self.child_count_label)

        splitter.addWidget(child_group)
        splitter.setSizes([300, 300])

        layout.addWidget(splitter)

    def parent_to_row(self, parent) -> List[str]:
        raise NotImplementedError

    def child_to_row(self, child) -> List[str]:
        raise NotImplementedError

    def get_parent_dialog(self, parent=None):
        raise NotImplementedError

    def get_child_dialog(self, child=None, preselect_parent_id=None):
        raise NotImplementedError

    def get_parent_from_dialog(self, dialog):
        raise NotImplementedError

    def get_child_from_dialog(self, dialog):
        raise NotImplementedError

    def format_parent_filter_text(self, parent) -> str:
        raise NotImplementedError

    def get_children_for_filter(self, filter_value) -> List[Any]:
        if filter_value == "all" or filter_value is None:
            return self.child_queries.get_all()
        elif filter_value == "general" and self.has_general_children:
            return self.child_queries.get_general_staff()
        else:
            return self.child_queries.get_by_parent(filter_value)

    def get_parent_child_count(self, parent_id: int) -> int:
        return len(self.child_queries.get_by_parent(parent_id))

    def get_parent_delete_warning(self, parent_id: int) -> str:
        count = self.get_parent_child_count(parent_id)
        if count > 0:
            return f"Are you sure you want to delete this {self.parent_entity_name.lower()}? This will also delete {count} associated {self.child_entity_name_plural.lower()}."
        return f"Are you sure you want to delete this {self.parent_entity_name.lower()}?"

    def refresh(self):
        self.refresh_parents()
        self.refresh_child_filter()
        self.refresh_children()

    def refresh_parents(self):
        parents = self.parent_queries.get_all()
        populate_table(self.parent_table, parents, self.parent_to_row)
        self.parent_count_label.setText(f"Total {self.parent_entity_name_plural}: {len(parents)}")

    def refresh_child_filter(self):
        from gui.widgets.styled_combo_box import select_combo_by_data

        current_data = self.child_filter_combo.currentData()
        self.child_filter_combo.blockSignals(True)
        self.child_filter_combo.clear()

        self.child_filter_combo.addItem(self.child_filter_all_text, "all")

        if self.has_general_children:
            self.child_filter_combo.addItem(self.general_children_text, "general")

        parents = self.parent_queries.get_all()
        for parent in parents:
            self.child_filter_combo.addItem(self.format_parent_filter_text(parent), parent.id)

        select_combo_by_data(self.child_filter_combo, current_data)
        self.child_filter_combo.blockSignals(False)

    def refresh_children(self):
        filter_value = self.child_filter_combo.currentData()
        children = self.get_children_for_filter(filter_value)
        populate_table(self.child_table, children, self.child_to_row)
        self.child_count_label.setText(f"Total {self.child_entity_name_plural}: {len(children)}")

    def on_parent_selected(self):
        from gui.widgets.styled_combo_box import select_combo_by_data

        selected = self.parent_table.selectedItems()
        if selected:
            row = selected[0].row()
            id_item = self.parent_table.item(row, 0)
            if id_item:
                parent_id = int(id_item.text())
                select_combo_by_data(self.child_filter_combo, parent_id)

    def on_child_filter_changed(self):
        self.refresh_children()

    def get_selected_parent_id(self) -> Optional[int]:
        return get_selected_id(self.parent_table)

    def get_selected_child_id(self) -> Optional[int]:
        return get_selected_id(self.child_table)

    def add_parent(self):
        dialog = self.get_parent_dialog()
        if dialog.exec():
            parent = self.get_parent_from_dialog(dialog)
            self.parent_queries.create(parent)
            self.refresh_parents()
            self.refresh_child_filter()

    def edit_parent(self):
        parent_id = self.get_selected_parent_id()
        if not parent_id:
            QMessageBox.warning(self, "Warning", f"Please select a {self.parent_entity_name.lower()} to edit.")
            return

        parent = self.parent_queries.get_by_id(parent_id)
        if parent:
            dialog = self.get_parent_dialog(parent)
            if dialog.exec():
                updated = self.get_parent_from_dialog(dialog)
                updated.id = parent_id
                self.parent_queries.update(updated)
                self.refresh_parents()
                self.refresh_child_filter()

    def delete_parent(self):
        parent_id = self.get_selected_parent_id()
        if not parent_id:
            QMessageBox.warning(self, "Warning", f"Please select a {self.parent_entity_name.lower()} to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete", self.get_parent_delete_warning(parent_id),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.parent_queries.delete(parent_id)
            self.refresh()

    def add_child(self):
        preselect_parent_id = None
        filter_value = self.child_filter_combo.currentData()
        if filter_value not in ("all", "general", None):
            preselect_parent_id = filter_value

        dialog = self.get_child_dialog(preselect_parent_id=preselect_parent_id)
        if dialog.exec():
            child = self.get_child_from_dialog(dialog)
            self.child_queries.create(child)
            self.refresh_children()

    def edit_child(self):
        child_id = self.get_selected_child_id()
        if not child_id:
            QMessageBox.warning(self, "Warning", f"Please select a {self.child_entity_name.lower()} to edit.")
            return

        child = self.child_queries.get_by_id(child_id)
        if child:
            dialog = self.get_child_dialog(child)
            if dialog.exec():
                updated = self.get_child_from_dialog(dialog)
                updated.id = child_id
                self.child_queries.update(updated)
                self.refresh_children()

    def delete_child(self):
        child_id = self.get_selected_child_id()
        if not child_id:
            QMessageBox.warning(self, "Warning", f"Please select a {self.child_entity_name.lower()} to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete this {self.child_entity_name.lower()}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.child_queries.delete(child_id)
            self.refresh_children()