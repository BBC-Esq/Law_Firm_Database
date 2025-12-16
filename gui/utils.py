from PySide6.QtCore import QObject, QTimer, QEvent, Qt
from PySide6.QtWidgets import QMenu, QApplication
from PySide6.QtGui import QAction


class SpinBoxSelectAllFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            QTimer.singleShot(0, obj.selectAll)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            QTimer.singleShot(0, obj.selectAll)
        return super().eventFilter(obj, event)


def select_all_on_focus(spinbox):
    filter = SpinBoxSelectAllFilter(spinbox)
    spinbox.lineEdit().installEventFilter(filter)
    return filter


def show_table_context_menu(table, position, edit_callback=None, delete_callback=None, extra_actions=None):
    selected = table.selectedItems()
    if not selected:
        return

    menu = QMenu(table)

    if edit_callback:
        edit_action = QAction("Edit", table)
        edit_action.triggered.connect(edit_callback)
        menu.addAction(edit_action)

    menu.addSeparator()

    row = selected[0].row()
    for col in range(table.columnCount()):
        if table.isColumnHidden(col):
            continue

        item = table.item(row, col)
        if not item or not item.text():
            continue

        header = table.horizontalHeaderItem(col)
        header_text = header.text() if header else f"Column {col}"
        cell_text = item.text()

        display_text = cell_text if len(cell_text) <= 30 else cell_text[:27] + "..."

        copy_action = QAction(f"Copy {header_text}: {display_text}", table)
        copy_action.triggered.connect(lambda checked, t=cell_text: QApplication.clipboard().setText(t))
        menu.addAction(copy_action)

    if extra_actions:
        menu.addSeparator()
        for label, callback in extra_actions:
            action = QAction(label, table)
            action.triggered.connect(callback)
            menu.addAction(action)

    if delete_callback:
        menu.addSeparator()
        delete_action = QAction("Delete", table)
        delete_action.triggered.connect(delete_callback)
        menu.addAction(delete_action)

    menu.exec(table.viewport().mapToGlobal(position))