from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QTimer, Signal

class MatterSearchWidget(QWidget):
    matter_selected = Signal(dict)

    def __init__(self, case_queries):
        super().__init__()
        self.case_queries = case_queries
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.perform_search)
        self.debounce_ms = 300
        self.selected_matter = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type client name or case number to search...")
        self.search_input.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.search_input)

        self.results_list = QListWidget()
        self.results_list.setMaximumHeight(150)
        self.results_list.itemClicked.connect(self.on_item_clicked)
        self.results_list.hide()
        layout.addWidget(self.results_list)

    def on_text_changed(self, text):
        self.debounce_timer.stop()
        if len(text) >= 2:
            self.debounce_timer.start(self.debounce_ms)
        else:
            self.results_list.hide()

    def perform_search(self):
        query = self.search_input.text().strip()
        if len(query) < 2:
            self.results_list.hide()
            return

        results = self.case_queries.search_matters(query)
        self.results_list.clear()

        if results:
            for matter in results:
                display_text = f"{matter['client_name']} - {matter['case_number'] or 'No Case #'} - {matter['case_name'] or 'Unnamed'}"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, matter)
                self.results_list.addItem(item)
            self.results_list.show()
        else:
            self.results_list.hide()

    def on_item_clicked(self, item):
        self.selected_matter = item.data(Qt.UserRole)
        self.search_input.setText(f"{self.selected_matter['client_name']} - {self.selected_matter['case_number'] or 'No Case #'}")
        self.results_list.hide()
        self.matter_selected.emit(self.selected_matter)

    def get_selected_matter(self):
        return self.selected_matter

    def clear_selection(self):
        self.selected_matter = None
        self.search_input.clear()
        self.results_list.clear()
        self.results_list.hide()

    def set_matter(self, matter_dict):
        self.selected_matter = matter_dict
        if matter_dict:
            self.search_input.setText(f"{matter_dict.get('client_name', '')} - {matter_dict.get('case_number', 'No Case #')}")