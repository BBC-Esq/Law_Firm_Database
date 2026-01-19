from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QStatusBar
)
from core.database import Database
from core.queries import (
    PersonQueries, CaseQueries, CasePersonQueries,
    BillingQueries, PaymentQueries, RecentCountyQueries
)
from gui.widgets.case_widget import CaseWidget
from gui.widgets.people_widget import PeopleWidget
from gui.widgets.matter_billing_widget import MatterBillingWidget


class MainWindow(QMainWindow):
    def __init__(self, db_path=None):
        super().__init__()
        self.setWindowTitle("Law Firm Billing System")
        self.resize(1200, 900)
        self.setMinimumSize(400, 300)
        if db_path:
            self.db = Database(db_path)
        else:
            self.db = Database()
        self.person_queries = PersonQueries(self.db)
        self.case_queries = CaseQueries(self.db)
        self.case_person_queries = CasePersonQueries(self.db)
        self.billing_queries = BillingQueries(self.db)
        self.payment_queries = PaymentQueries(self.db)
        self.recent_county_queries = RecentCountyQueries(self.db)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        self.case_widget = CaseWidget(
            self.case_queries,
            self.person_queries,
            self.case_person_queries,
            self.recent_county_queries
        )
        self.tab_widget.addTab(self.case_widget, "Client Matters")
        self.people_widget = PeopleWidget(
            self.person_queries,
            self.case_queries,
            self.case_person_queries
        )
        self.tab_widget.addTab(self.people_widget, "People")
        self.billing_widget = MatterBillingWidget(
            self.billing_queries,
            self.payment_queries,
            self.case_queries,
            self.person_queries,
            self.case_person_queries
        )
        self.tab_widget.addTab(self.billing_widget, "Billing/Payments")
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        widget = self.tab_widget.widget(index)
        if hasattr(widget, 'refresh'):
            widget.refresh()

    def closeEvent(self, event):
        self.db.close()
        event.accept()