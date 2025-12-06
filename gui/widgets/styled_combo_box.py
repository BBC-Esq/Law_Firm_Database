from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import QPoint


def populate_combo(combo, items, format_func, placeholder="-- Select --", placeholder_data=None):
    combo.clear()
    combo.addItem(placeholder, placeholder_data)
    if items:
        for item in items:
            combo.addItem(format_func(item), item.id)


def select_combo_by_data(combo, data):
    for i in range(combo.count()):
        if combo.itemData(i) == data:
            combo.setCurrentIndex(i)
            return True
    return False


class StyledComboBox(QComboBox):
    MAX_VISIBLE_ITEMS = 15
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaxVisibleItems(self.MAX_VISIBLE_ITEMS)
    
    def showPopup(self):
        super().showPopup()
        popup = self.view().parent()
        popup_pos = self.mapToGlobal(QPoint(0, self.height()))
        popup.move(popup_pos)