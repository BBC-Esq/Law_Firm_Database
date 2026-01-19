import re
import os
from datetime import datetime
from email import policy
from email.parser import BytesParser
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QDateEdit, QLabel, QComboBox,
    QGroupBox, QCheckBox, QHeaderView, QMessageBox, QMenu,
    QTextEdit, QSplitter
)
from PySide6.QtCore import QDate, Qt, QSignalBlocker
from PySide6.QtGui import QCursor, QDesktopServices
from gui.dialogs.quick_billing_dialog import QuickBillingDialog

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class EmailLogWidget(QWidget):
    def __init__(self, case_queries, billing_queries):
        super().__init__()
        self.case_queries = case_queries
        self.billing_queries = billing_queries
        self._loading = False

        if HAS_PANDAS:
            self.df = pd.DataFrame(columns=[
                'file_path', 'email_datetime', 'email_date', 'sender', 'sender_normalized',
                'recipients', 'recipients_normalized', 'cc', 'cc_normalized', 'subject', 'attachments'
            ])
        else:
            self.records = []

        self.setup_ui()
        self.refresh_table()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load EML Files")
        self.load_btn.clicked.connect(self.load_eml_files)
        top_layout.addWidget(self.load_btn)
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_data)
        top_layout.addWidget(self.clear_btn)
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

        sort_layout = QVBoxLayout()
        sort_layout.addWidget(QLabel("Sort By:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Date (Newest First)", "Date (Oldest First)", "Sender", "Subject"])
        self.sort_combo.currentIndexChanged.connect(self.on_filter_changed)
        sort_layout.addWidget(self.sort_combo)
        filter_layout.addLayout(sort_layout)

        filter_layout.addStretch()
        main_layout.addWidget(filter_group)

        splitter = QSplitter(Qt.Vertical)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Date/Time", "Sender", "Recipients", "CC", "Subject", "Attachments", "File Path"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 140)
        self.table.setColumnWidth(1, 180)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 200)
        self.table.setColumnHidden(6, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        splitter.addWidget(self.table)

        self.email_viewer = QTextEdit()
        self.email_viewer.setReadOnly(True)
        self.email_viewer.setPlaceholderText("Select an email to view its contents")
        splitter.addWidget(self.email_viewer)

        splitter.setSizes([400, 300])
        main_layout.addWidget(splitter)

        self.status_label = QLabel("Records: 0")
        main_layout.addWidget(self.status_label)

    def on_filter_changed(self):
        if not self._loading:
            self.toggle_date_filter()
            self.refresh_table()

    def show_context_menu(self, position):
        row = self.table.rowAt(position.y())
        if row < 0:
            return
        menu = QMenu()
        open_action = menu.addAction("Open with Default App")
        menu.addSeparator()
        billing_action = menu.addAction("Add Billing Entry")
        action = menu.exec(QCursor.pos())
        if action == open_action:
            self.open_email(row)
        elif action == billing_action:
            self.add_billing_entry(row)

    def add_billing_entry(self, row):
        date_item = self.table.item(row, 0)
        sender_item = self.table.item(row, 1)
        subject_item = self.table.item(row, 4)

        prefill_parts = []
        if date_item and date_item.text():
            prefill_parts.append(f"Email dated {date_item.text()}")
        if sender_item and sender_item.text():
            prefill_parts.append(f"from {sender_item.text()}")
        if subject_item and subject_item.text():
            prefill_parts.append(f"re: {subject_item.text()}")

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

    def open_email(self, row):
        file_path_item = self.table.item(row, 6)
        if file_path_item:
            file_path = file_path_item.text()
            if os.path.exists(file_path):
                from PySide6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            else:
                QMessageBox.warning(self, "File Not Found", f"The file no longer exists:\n{file_path}")

    def on_row_selected(self):
        if self._loading:
            return
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.email_viewer.clear()
            return
        row = selected_rows[0].row()
        file_path_item = self.table.item(row, 6)
        if file_path_item:
            file_path = file_path_item.text()
            if os.path.exists(file_path):
                self.display_email(file_path)
            else:
                self.email_viewer.setPlainText(f"File not found:\n{file_path}")

    def display_email(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)
            output = []
            output.append(f"From: {msg.get('From', '')}")
            output.append(f"To: {msg.get('To', '')}")
            output.append(f"Cc: {msg.get('Cc', '')}")
            output.append(f"Date: {msg.get('Date', '')}")
            output.append(f"Subject: {msg.get('Subject', '')}")
            output.append("")
            body = msg.get_body(preferencelist=('plain', 'html'))
            if body:
                try:
                    content = body.get_content()
                    output.append(content)
                except Exception:
                    output.append("[Could not decode email body]")
            else:
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == 'text/plain':
                        try:
                            output.append(part.get_content())
                        except Exception:
                            output.append("[Could not decode text/plain content]")
                        break
                    elif content_type == 'text/html':
                        try:
                            output.append(part.get_content())
                        except Exception:
                            output.append("[Could not decode text/html content]")
                        break
            attachments = []
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        attachments.append(filename)
            if attachments:
                output.append("")
                output.append("=" * 60)
                output.append("ATTACHMENTS")
                output.append("=" * 60)
                for att in attachments:
                    output.append(f"  - {att}")
            self.email_viewer.setPlainText("\n".join(output))
        except Exception as e:
            self.email_viewer.setPlainText(f"Error loading email:\n{str(e)}")

    def toggle_date_filter(self):
        enabled = self.use_date_filter.isChecked()
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)

    def normalize_email(self, email):
        if not email:
            return ""
        return re.sub(r'[^a-zA-Z0-9@.;]', '', email.lower())

    def extract_email_addresses(self, text):
        if not text:
            return ""
        all_emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', str(text), re.IGNORECASE)
        seen = set()
        unique_emails = []
        for email in all_emails:
            lower = email.lower()
            if lower not in seen:
                seen.add(lower)
                unique_emails.append(lower)
        return "; ".join(unique_emails)

    def parse_email_date(self, date_str):
        if not date_str:
            return "", ""
        date_formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S",
            "%d %b %Y %H:%M:%S",
        ]
        clean_date = re.sub(r'\s+\([^)]+\)', '', str(date_str)).strip()
        for fmt in date_formats:
            try:
                dt = datetime.strptime(clean_date, fmt)
                return dt.strftime("%Y-%m-%d %H:%M:%S"), dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return str(date_str), str(date_str)[:10] if len(str(date_str)) >= 10 else str(date_str)

    def parse_eml_file(self, file_path):
        with open(file_path, 'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)
        date_str = msg.get('Date', '')
        email_datetime, email_date = self.parse_email_date(date_str)
        sender = self.extract_email_addresses(msg.get('From', ''))
        recipients = self.extract_email_addresses(msg.get('To', ''))
        cc = self.extract_email_addresses(msg.get('Cc', ''))
        subject = msg.get('Subject', '') or ''
        attachments_list = []
        for part in msg.walk():
            content_disposition = part.get_content_disposition()
            if content_disposition == 'attachment':
                filename = part.get_filename()
                if filename:
                    attachments_list.append(filename)
        attachments = "; ".join(attachments_list)
        sender_normalized = self.normalize_email(sender)
        recipients_normalized = self.normalize_email(recipients)
        cc_normalized = self.normalize_email(cc)
        return {
            'file_path': os.path.abspath(file_path),
            'email_datetime': email_datetime,
            'email_date': email_date,
            'sender': sender,
            'sender_normalized': sender_normalized,
            'recipients': recipients,
            'recipients_normalized': recipients_normalized,
            'cc': cc,
            'cc_normalized': cc_normalized,
            'subject': subject,
            'attachments': attachments
        }

    def load_eml_files(self):
        if not HAS_PANDAS:
            QMessageBox.warning(self, "Missing Dependency", "pandas is required for Email Log functionality.\nInstall with: pip install pandas")
            return

        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open EML Files", "", "EML Files (*.eml)")
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
                    self.df['email_datetime'].astype(str) + '|' + self.df['sender'].astype(str) + '|' + self.df['subject'].astype(str)
                )

            all_new_records = []

            for file_path in file_paths:
                try:
                    record = self.parse_eml_file(file_path)
                    if record:
                        key = f"{record['email_datetime']}|{record['sender']}|{record['subject']}"
                        if key in existing_keys:
                            total_duplicates += 1
                        else:
                            existing_keys.add(key)
                            all_new_records.append(record)
                            total_loaded += 1

                except Exception as e:
                    failed_files.append(f"{os.path.basename(file_path)}: {str(e)}")

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
            self.email_viewer.clear()
            return

        try:
            filtered_df = self.df.copy()

            if self.use_date_filter.isChecked():
                start = self.start_date.date().toString("yyyy-MM-dd")
                end = self.end_date.date().toString("yyyy-MM-dd")
                mask = (filtered_df['email_date'] >= start) & (filtered_df['email_date'] <= end)
                filtered_df = filtered_df[mask]

            sort_option = self.sort_combo.currentIndex()
            if sort_option == 0:
                filtered_df = filtered_df.sort_values('email_datetime', ascending=False)
            elif sort_option == 1:
                filtered_df = filtered_df.sort_values('email_datetime', ascending=True)
            elif sort_option == 2:
                filtered_df = filtered_df.sort_values(['sender', 'email_datetime'], ascending=[True, False])
            else:
                filtered_df = filtered_df.sort_values(['subject', 'email_datetime'], ascending=[True, False])

            filtered_df = filtered_df.reset_index(drop=True)

            self.table.setRowCount(len(filtered_df))
            for row_idx, row in filtered_df.iterrows():
                try:
                    dt = datetime.strptime(str(row['email_datetime']), "%Y-%m-%d %H:%M:%S")
                    display_dt = dt.strftime("%m/%d/%Y %I:%M %p")
                except (ValueError, TypeError):
                    display_dt = str(row['email_datetime'])

                self.table.setItem(row_idx, 0, QTableWidgetItem(display_dt))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row['sender'] or "")))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(row['recipients'] or "")))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(row['cc'] or "")))
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(row['subject'] or "")))
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(row['attachments'] or "")))
                self.table.setItem(row_idx, 6, QTableWidgetItem(str(row['file_path'] or "")))

            self.status_label.setText(f"Records: {len(filtered_df)} (Total loaded: {len(self.df)})")
            self.email_viewer.clear()

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
                self.df = pd.DataFrame(columns=[
                    'file_path', 'email_datetime', 'email_date', 'sender', 'sender_normalized',
                    'recipients', 'recipients_normalized', 'cc', 'cc_normalized', 'subject', 'attachments'
                ])
            self.refresh_table()

    def refresh(self):
        self.refresh_table()