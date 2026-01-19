import re
import csv
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QDateEdit, QLabel, QComboBox,
    QGroupBox, QCheckBox, QHeaderView, QMessageBox, QLineEdit, QMenu
)
from PySide6.QtCore import QDate, Qt, QSignalBlocker
from PySide6.QtGui import QCursor
from core.models import ROLE_DISPLAY_NAMES
from gui.dialogs.quick_billing_dialog import QuickBillingDialog

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class CallLogWidget(QWidget):
    def __init__(self, person_queries, case_queries, billing_queries):
        super().__init__()
        self.person_queries = person_queries
        self.case_queries = case_queries
        self.billing_queries = billing_queries

        self.phone_to_name = {}
        self._loading = False

        if HAS_PANDAS:
            self.df = pd.DataFrame(columns=['call_datetime', 'call_date', 'phone_number', 'phone_digits', 'duration_minutes'])
        else:
            self.records = []

        self.setup_ui()
        self.load_phone_contacts()
        self.refresh_table()

    def load_phone_contacts(self):
        self.phone_to_name = {}

        contacts = self.person_queries.get_phone_contacts()
        for contact in contacts:
            phone = contact.get('phone')
            if phone:
                phone_digits = self.normalize_phone(phone)
                if phone_digits:
                    first_name = contact.get('first_name') or ''
                    last_name = contact.get('last_name') or ''
                    full_name = f"{first_name} {last_name}".strip()

                    roles = contact.get('roles')
                    if roles:
                        role_list = roles.split(',')
                        role_display = ROLE_DISPLAY_NAMES.get(role_list[0].strip(), '')
                        if role_display:
                            full_name = f"{full_name} ({role_display})"

                    self.phone_to_name[phone_digits] = full_name

    def get_contact_name(self, phone_digits):
        if not phone_digits:
            return ""
            
        if phone_digits in self.phone_to_name:
            return self.phone_to_name[phone_digits]

        for stored_digits, name in self.phone_to_name.items():
            if len(phone_digits) >= 10 and len(stored_digits) >= 10:
                if stored_digits.endswith(phone_digits[-10:]) or phone_digits.endswith(stored_digits[-10:]):
                    return name

        return ""

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load CSV Files")
        self.load_btn.clicked.connect(self.load_csv)
        top_layout.addWidget(self.load_btn)
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_data)
        top_layout.addWidget(self.clear_btn)
        self.refresh_contacts_btn = QPushButton("Refresh Contacts")
        self.refresh_contacts_btn.clicked.connect(self.on_refresh_contacts)
        top_layout.addWidget(self.refresh_contacts_btn)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        filter_group = QGroupBox("Filter & Sort")
        filter_layout = QHBoxLayout(filter_group)

        date_layout = QVBoxLayout()
        self.use_date_filter = QCheckBox("Enable Date Filter")
        self.use_date_filter.stateChanged.connect(self.on_filter_changed)
        date_layout.addWidget(self.use_date_filter)
        date_range_layout = QHBoxLayout()
        date_range_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setEnabled(False)
        self.start_date.dateChanged.connect(self.on_filter_changed)
        date_range_layout.addWidget(self.start_date)
        date_range_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setEnabled(False)
        self.end_date.dateChanged.connect(self.on_filter_changed)
        date_range_layout.addWidget(self.end_date)
        date_layout.addLayout(date_range_layout)
        filter_layout.addLayout(date_layout)

        filter_layout.addSpacing(20)

        phone_layout = QVBoxLayout()
        phone_layout.addWidget(QLabel("Phone Number:"))
        self.phone_filter = QLineEdit()
        self.phone_filter.setPlaceholderText("e.g. 470-843-8261")
        self.phone_filter.textChanged.connect(self.on_filter_changed)
        phone_layout.addWidget(self.phone_filter)
        filter_layout.addLayout(phone_layout)

        filter_layout.addSpacing(20)

        sort_layout = QVBoxLayout()
        sort_layout.addWidget(QLabel("Sort By:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Date (Newest First)", "Date (Oldest First)", "Phone Number", "Contact Name"])
        self.sort_combo.currentIndexChanged.connect(self.on_filter_changed)
        sort_layout.addWidget(self.sort_combo)
        filter_layout.addLayout(sort_layout)

        filter_layout.addStretch()
        main_layout.addWidget(filter_group)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date/Time", "Phone Number", "Contact", "Duration (Min)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        main_layout.addWidget(self.table)

        self.status_label = QLabel("Records: 0")
        main_layout.addWidget(self.status_label)

    def on_filter_changed(self):
        if not self._loading:
            self.toggle_date_filter()
            self.refresh_table()

    def on_refresh_contacts(self):
        self.load_phone_contacts()
        self.refresh_table()
        QMessageBox.information(self, "Contacts Refreshed", f"Loaded {len(self.phone_to_name)} contacts from database.")

    def show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return
        menu = QMenu()
        billing_action = menu.addAction("Add Billing Entry")
        action = menu.exec(QCursor.pos())
        if action == billing_action:
            self.add_billing_entry(row)

    def add_billing_entry(self, row):
        date_item = self.table.item(row, 0)
        phone_item = self.table.item(row, 1)
        contact_item = self.table.item(row, 2)
        duration_item = self.table.item(row, 3)

        prefill_parts = []
        if date_item and date_item.text():
            prefill_parts.append(f"Phone call on {date_item.text()}")

        if contact_item and contact_item.text():
            prefill_parts.append(f"with {contact_item.text()}")
        elif phone_item and phone_item.text():
            prefill_parts.append(f"with {phone_item.text()}")

        if duration_item and duration_item.text():
            prefill_parts.append(f"({duration_item.text()} min)")

        prefill_description = " ".join(prefill_parts)

        dialog = QuickBillingDialog(
            self,
            case_queries=self.case_queries,
            prefill_description=prefill_description
        )

        if dialog.exec():
            entry_data = dialog.get_entry_data()
            self.billing_queries.create_from_dict(entry_data)
            QMessageBox.information(self, "Success", "Billing entry added successfully.")

    def toggle_date_filter(self):
        enabled = self.use_date_filter.isChecked()
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)

    def normalize_phone(self, phone):
        if not phone:
            return ""
        return re.sub(r'\D', '', str(phone))

    def parse_csv_file(self, file_path):
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            lines = list(reader)
            data_start = 0
            for i, line in enumerate(lines):
                if line and line[0].strip() == "Date (Pacific)":
                    data_start = i + 1
                    break
            for row in lines[data_start:]:
                if len(row) >= 4 and row[0].strip() and '/' in row[0]:
                    date_str = row[0].strip()
                    phone = row[1].strip()
                    phone_digits = self.normalize_phone(phone)
                    minutes_str = row[3].strip().replace(" Min", "").replace(" min", "")
                    try:
                        dt = datetime.strptime(date_str, "%m/%d/%Y %I:%M %p")
                        call_datetime = dt.strftime("%Y-%m-%d %H:%M:%S")
                        call_date = dt.strftime("%Y-%m-%d")
                        duration = int(minutes_str)
                        records.append({
                            'call_datetime': call_datetime,
                            'call_date': call_date,
                            'phone_number': phone,
                            'phone_digits': phone_digits,
                            'duration_minutes': duration
                        })
                    except (ValueError, AttributeError):
                        continue
        return records

    def load_csv(self):
        if not HAS_PANDAS:
            QMessageBox.warning(self, "Missing Dependency", "pandas is required for Call Log functionality.\nInstall with: pip install pandas")
            return

        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open CSV Files", "", "CSV Files (*.csv)")
        if not file_paths:
            return

        self._loading = True
        
        try:
            total_loaded = 0
            total_duplicates = 0
            failed_files = []

            existing_keys = set()
            if not self.df.empty:
                existing_keys = set(
                    self.df['call_datetime'] + '|' + self.df['phone_number'] + '|' + self.df['duration_minutes'].astype(str)
                )

            all_new_records = []

            for file_path in file_paths:
                try:
                    records = self.parse_csv_file(file_path)
                    for record in records:
                        key = f"{record['call_datetime']}|{record['phone_number']}|{record['duration_minutes']}"
                        if key in existing_keys:
                            total_duplicates += 1
                        else:
                            existing_keys.add(key)
                            all_new_records.append(record)
                            total_loaded += 1

                except Exception as e:
                    failed_files.append(f"{file_path.split('/')[-1]}: {str(e)}")

            if all_new_records:
                new_df = pd.DataFrame(all_new_records)
                if self.df.empty:
                    self.df = new_df
                else:
                    self.df = pd.concat([self.df, new_df], ignore_index=True)

        finally:
            self._loading = False

        self.refresh_table()

        message = f"Files processed: {len(file_paths)}\nLoaded: {total_loaded} new records\nSkipped: {total_duplicates} duplicates"
        if failed_files:
            message += f"\n\nFailed files:\n" + "\n".join(failed_files)
            QMessageBox.warning(self, "Import Complete with Errors", message)
        else:
            QMessageBox.information(self, "Import Complete", message)

    def refresh_table(self):
        if self._loading:
            return
            
        if not HAS_PANDAS:
            self.table.setRowCount(0)
            self.status_label.setText("pandas not installed")
            return

        if self.df.empty:
            self.table.setRowCount(0)
            self.status_label.setText("Records: 0")
            return

        try:
            filtered_df = self.df.copy()

            if self.use_date_filter.isChecked():
                start = self.start_date.date().toString("yyyy-MM-dd")
                end = self.end_date.date().toString("yyyy-MM-dd")
                mask = (filtered_df['call_date'] >= start) & (filtered_df['call_date'] <= end)
                filtered_df = filtered_df[mask]

            phone_input = self.phone_filter.text().strip()
            if phone_input:
                phone_digits = self.normalize_phone(phone_input)
                if phone_digits:
                    mask = filtered_df['phone_digits'].str.contains(phone_digits, na=False)
                    filtered_df = filtered_df[mask]

            contact_names = filtered_df['phone_digits'].apply(self.get_contact_name)

            sort_option = self.sort_combo.currentIndex()
            if sort_option == 0:
                sort_indices = filtered_df['call_datetime'].sort_values(ascending=False).index
            elif sort_option == 1:
                sort_indices = filtered_df['call_datetime'].sort_values(ascending=True).index
            elif sort_option == 2:
                sort_indices = filtered_df['phone_number'].sort_values().index
            else:
                temp_df = filtered_df.copy()
                temp_df['_sort_contact'] = contact_names
                sort_indices = temp_df['_sort_contact'].sort_values().index

            filtered_df = filtered_df.loc[sort_indices]
            contact_names = contact_names.loc[sort_indices]

            self.table.setRowCount(len(filtered_df))
            for row_idx, (idx, row) in enumerate(filtered_df.iterrows()):
                try:
                    dt = datetime.strptime(row['call_datetime'], "%Y-%m-%d %H:%M:%S")
                    display_dt = dt.strftime("%m/%d/%Y %I:%M %p")
                except (ValueError, TypeError):
                    display_dt = str(row['call_datetime'])

                self.table.setItem(row_idx, 0, QTableWidgetItem(display_dt))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row['phone_number'])))
                self.table.setItem(row_idx, 2, QTableWidgetItem(contact_names.loc[idx]))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(row['duration_minutes'])))

            self.status_label.setText(f"Records: {len(filtered_df)} (Total loaded: {len(self.df)})")
            
        except Exception as e:
            self.status_label.setText(f"Error refreshing: {str(e)}")

    def clear_data(self):
        reply = QMessageBox.question(
            self, "Confirm Clear",
            "Are you sure you want to clear all loaded records?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if HAS_PANDAS:
                self.df = pd.DataFrame(columns=['call_datetime', 'call_date', 'phone_number', 'phone_digits', 'duration_minutes'])
            self.refresh_table()

    def refresh(self):
        self.load_phone_contacts()
        self.refresh_table()