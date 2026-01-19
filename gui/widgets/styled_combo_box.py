from PySide6.QtWidgets import QComboBox, QApplication
from PySide6.QtCore import Qt, QPoint, QTimer


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

    def showPopup(self):
        super().showPopup()
        QTimer.singleShot(0, self._adjustPopupSize)

    def _adjustPopupSize(self):
        popup = self.view().window()
        view = self.view()
        
        item_count = min(self.count(), self.MAX_VISIBLE_ITEMS)
        if item_count <= 0:
            return
        
        row_height = view.sizeHintForRow(0)
        if row_height <= 0:
            row_height = 25
        
        desired_height = (item_count * row_height) + 4
        
        screen = QApplication.screenAt(self.mapToGlobal(QPoint(0, 0)))
        if screen is None:
            screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        popup_rect = popup.geometry()
        combo_global = self.mapToGlobal(QPoint(0, 0))
        
        space_below = screen_rect.bottom() - combo_global.y() - self.height()
        space_above = combo_global.y() - screen_rect.top()
        
        if desired_height <= space_below:
            final_height = desired_height
            final_y = combo_global.y() + self.height()
        elif desired_height <= space_above:
            final_height = desired_height
            final_y = combo_global.y() - desired_height
        elif space_below >= space_above:
            final_height = max(space_below - 5, row_height * 3)
            final_y = combo_global.y() + self.height()
        else:
            final_height = max(space_above - 5, row_height * 3)
            final_y = combo_global.y() - final_height
        
        popup.setGeometry(popup_rect.x(), int(final_y), popup_rect.width(), int(final_height))