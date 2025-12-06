from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QStatusBar
)
from core.database import Database
from core.queries import (
    ClientQueries, JudgeQueries, CourtStaffQueries, CaseQueries, 
    BillingQueries, OpposingAttorneyQueries, OpposingStaffQueries, 
    PaymentQueries, RecentCountyQueries
)
from gui.widgets.client_widget import ClientWidget
from gui.widgets.case_widget import CaseWidget
from gui.widgets.court_widget import CourtWidget
from gui.widgets.billing_widget import BillingWidget
from gui.widgets.opposing_counsel_widget import OpposingCounselWidget
from gui.widgets.payments_widget import PaymentsWidget


class MainWindow(QMainWindow):
    def __init__(self, db_path=None):
        super().__init__()
        self.setWindowTitle("Law Firm Billing System")
        self.setMinimumSize(1200, 800)

        if db_path:
            self.db = Database(db_path)
        else:
            self.db = Database()
        self.client_queries = ClientQueries(self.db)
        self.judge_queries = JudgeQueries(self.db)
        self.staff_queries = CourtStaffQueries(self.db)
        self.case_queries = CaseQueries(self.db)
        self.billing_queries = BillingQueries(self.db)
        self.opposing_attorney_queries = OpposingAttorneyQueries(self.db)
        self.opposing_staff_queries = OpposingStaffQueries(self.db)
        self.payment_queries = PaymentQueries(self.db)
        self.recent_county_queries = RecentCountyQueries(self.db)

        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self.client_widget = ClientWidget(self.client_queries)
        self.tab_widget.addTab(self.client_widget, "Clients")

        self.case_widget = CaseWidget(
            self.case_queries, self.client_queries, 
            self.judge_queries, self.opposing_attorney_queries,
            self.recent_county_queries
        )
        self.tab_widget.addTab(self.case_widget, "Cases/Matters")

        self.court_widget = CourtWidget(self.judge_queries, self.staff_queries)
        self.tab_widget.addTab(self.court_widget, "Court")

        self.opposing_counsel_widget = OpposingCounselWidget(
            self.opposing_attorney_queries, self.opposing_staff_queries
        )
        self.tab_widget.addTab(self.opposing_counsel_widget, "Opposing Counsel")

        self.billing_widget = BillingWidget(self.billing_queries, self.case_queries, self.client_queries)
        self.tab_widget.addTab(self.billing_widget, "Billing")

        self.payments_widget = PaymentsWidget(
            self.payment_queries, self.client_queries, self.case_queries
        )
        self.tab_widget.addTab(self.payments_widget, "Payments")

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