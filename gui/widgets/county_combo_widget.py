from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt
from core.georgia_counties import GEORGIA_COUNTIES
from core.queries import RecentCountyQueries
from gui.widgets.styled_combo_box import StyledComboBox

class CountyComboWidget(StyledComboBox):
    SEPARATOR = "─" * 30
    NA_VALUE = "N/A (No pending court case)"

    def __init__(self, recent_county_queries: RecentCountyQueries, parent=None):
        super().__init__(parent)
        self.recent_county_queries = recent_county_queries
        self.refresh_items()

    def refresh_items(self):
        self.clear()

        model = QStandardItemModel()

        na_item = QStandardItem(self.NA_VALUE)
        na_item.setData("", Qt.UserRole)
        model.appendRow(na_item)

        recent_counties = self.recent_county_queries.get_recent(5)

        if recent_counties:
            for county in recent_counties:
                item = QStandardItem(f"{county} County")
                item.setData(county, Qt.UserRole)
                model.appendRow(item)

        separator_item = QStandardItem(self.SEPARATOR)
        separator_item.setData("__separator__", Qt.UserRole)
        separator_item.setEnabled(False)
        separator_item.setSelectable(False)
        model.appendRow(separator_item)

        for county in GEORGIA_COUNTIES:
            item = QStandardItem(f"{county} County")
            item.setData(county, Qt.UserRole)
            model.appendRow(item)

        self.setModel(model)

    def get_selected_county(self) -> str:
        data = self.currentData(Qt.UserRole)
        if data == "" or data == "__separator__":
            return ""
        return data or ""

    def set_county(self, county_name: str):
        if not county_name:
            self.setCurrentIndex(0)
            return

        model = self.model()
        for i in range(model.rowCount()):
            item = model.item(i)
            if item.data(Qt.UserRole) == county_name:
                self.setCurrentIndex(i)
                return

        self.setCurrentIndex(0)

    def record_usage(self):
        county = self.get_selected_county()
        if county and county != "__separator__":
            self.recent_county_queries.add_recent(county)