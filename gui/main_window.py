from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QStatusBar
)
from core.database import Database
from core.settings import AppSettings
from core.queries import (
    PersonQueries, CaseQueries, CasePersonQueries,
    BillingQueries, PaymentQueries, RecentCountyQueries, InvoiceQueries, ReportQueries
)
from gui.widgets.case_widget import CaseWidget
from gui.widgets.people_widget import PeopleWidget
from gui.widgets.matter_billing_widget import MatterBillingWidget
from gui.widgets.call_log_widget import CallLogWidget
from gui.widgets.email_log_widget import EmailLogWidget
from gui.widgets.invoice_widget import InvoiceWidget
from gui.widgets.reports_widget import ReportsWidget


class MainWindow(QMainWindow):
    def __init__(self, db_path=None):
        super().__init__()
        self.setWindowTitle("Law Firm Billing System")
        self.resize(1200, 900)
        self.setMinimumSize(400, 300)

        self.app_settings = AppSettings()

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
        self.invoice_queries = InvoiceQueries(self.db)
        self.report_queries = ReportQueries(self.db)

        self.setup_ui()
        self.restore_state()

    def get_show_closed(self) -> bool:
        return self.case_widget.get_show_closed()

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
            self.recent_county_queries,
            app_settings=self.app_settings
        )
        self.case_widget.show_closed_changed.connect(self.on_show_closed_changed)
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
            self.case_person_queries,
            get_show_closed_callback=self.get_show_closed,
            app_settings=self.app_settings
        )
        self.tab_widget.addTab(self.billing_widget, "Billing/Payments")

        self.call_log_widget = CallLogWidget(
            self.person_queries,
            self.case_queries,
            self.billing_queries
        )
        self.tab_widget.addTab(self.call_log_widget, "Call Log")

        self.email_log_widget = EmailLogWidget(
            self.case_queries,
            self.billing_queries,
            app_settings=self.app_settings
        )
        self.tab_widget.addTab(self.email_log_widget, "Email Log")

        self.invoice_widget = InvoiceWidget(
            self.case_queries,
            self.billing_queries,
            self.invoice_queries,
            get_show_closed_callback=self.get_show_closed
        )
        self.tab_widget.addTab(self.invoice_widget, "Invoicing")

        self.reports_widget = ReportsWidget(
            self.report_queries,
            get_show_closed_callback=self.get_show_closed
        )
        self.tab_widget.addTab(self.reports_widget, "Reports")

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def restore_state(self):
        self.app_settings.restore_window_geometry(self)
        saved_tab = self.app_settings.get_tab_index()
        if 0 <= saved_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(saved_tab)

    def save_state(self):
        self.app_settings.save_window_geometry(self)
        self.app_settings.save_tab_index(self.tab_widget.currentIndex())

        self.case_widget.save_state()
        self.billing_widget.save_state()
        self.email_log_widget.save_state()

    def on_show_closed_changed(self, show_closed: bool):
        self.billing_widget.refresh()
        self.invoice_widget.refresh()

    def on_tab_changed(self, index):
        widget = self.tab_widget.widget(index)
        if hasattr(widget, 'refresh'):
            widget.refresh()

    def closeEvent(self, event):
        try:
            self.save_state()
        except Exception as e:
            print(f"Warning: Failed to save state: {e}")
        finally:
            self.db.close()
            event.accept()
