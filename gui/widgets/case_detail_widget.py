from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QMessageBox, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Signal
from core.queries import PersonQueries, CasePersonQueries, CaseQueries
from core.models import ROLE_DISPLAY_NAMES, PARTY_DESIGNATION_DISPLAY
from gui.dialogs.add_person_to_case_dialog import AddPersonToCaseDialog
from gui.dialogs.person_dialog import PersonDialog


class CompactPersonCard(QFrame):
    edit_clicked = Signal(int)
    remove_clicked = Signal(int)
    add_staff_clicked = Signal(int, str)

    def __init__(self, person_data: dict, show_remove: bool = True, show_add_staff: bool = False, parent=None):
        super().__init__(parent)
        self.person_data = person_data
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        self.setup_ui(show_remove, show_add_staff)

    def setup_ui(self, show_remove: bool, show_add_staff: bool):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(12)

        name = f"{self.person_data['first_name']} {self.person_data['last_name']}"
        if self.person_data.get('role') == 'judge':
            name = f"Hon. {name}"
        name_label = QLabel(f"<b>{name}</b>")
        name_label.setMinimumWidth(120)
        layout.addWidget(name_label)

        info_parts = []
        if self.person_data.get('party_designation'):
            info_parts.append(PARTY_DESIGNATION_DISPLAY.get(self.person_data['party_designation'], ''))
        if self.person_data.get('firm_name'):
            info_parts.append(self.person_data['firm_name'])
        if self.person_data.get('job_title'):
            info_parts.append(self.person_data['job_title'])
        if self.person_data.get('phone'):
            info_parts.append(self.person_data['phone'])
        if self.person_data.get('email'):
            info_parts.append(self.person_data['email'])

        if info_parts:
            info_label = QLabel(" | ".join(info_parts))
            info_label.setStyleSheet("color: #aaa;")
            layout.addWidget(info_label)

        if self.person_data.get('is_pro_se') and self.person_data.get('role') == 'opposing_party':
            pro_se_label = QLabel("<i>Pro Se</i>")
            pro_se_label.setStyleSheet("color: orange;")
            layout.addWidget(pro_se_label)

        layout.addStretch()

        if show_add_staff:
            add_staff_btn = QPushButton("Add Staff")
            add_staff_btn.setFixedWidth(70)
            person_id = self.person_data['person_id']
            person_name = f"{self.person_data['first_name']} {self.person_data['last_name']}"
            add_staff_btn.clicked.connect(lambda: self.add_staff_clicked.emit(person_id, person_name))
            layout.addWidget(add_staff_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setFixedWidth(50)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.person_data['person_id']))
        layout.addWidget(edit_btn)

        if show_remove:
            remove_btn = QPushButton("Remove")
            remove_btn.setFixedWidth(60)
            remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self.person_data['id']))
            layout.addWidget(remove_btn)


class CaseDetailWidget(QWidget):
    case_updated = Signal()

    def __init__(self, person_queries: PersonQueries, case_person_queries: CasePersonQueries,
                 case_queries: CaseQueries, parent=None):
        super().__init__(parent)
        self.person_queries = person_queries
        self.case_person_queries = case_person_queries
        self.case_queries = case_queries
        self.current_case_id = None
        self.current_case = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        scroll_content = QWidget()
        self.layout = QVBoxLayout(scroll_content)

        self.no_case_label = QLabel("Select a matter to view details")
        self.no_case_label.setStyleSheet("color: gray; font-style: italic; padding: 20px;")
        self.layout.addWidget(self.no_case_label)

        self.content_widget = QWidget()
        content_layout = QHBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(10)

        left_widget = QWidget()
        left_widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        left_column = QVBoxLayout(left_widget)
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(10)

        self.client_group = self.create_client_section()
        left_column.addWidget(self.client_group)

        self.opposing_group = self.create_opposing_section()
        left_column.addWidget(self.opposing_group)

        left_column.addStretch()
        content_layout.addWidget(left_widget, 1)

        right_widget = QWidget()
        right_widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        right_column = QVBoxLayout(right_widget)
        right_column.setContentsMargins(0, 0, 0, 0)
        right_column.setSpacing(10)

        self.court_group = self.create_court_section()
        right_column.addWidget(self.court_group)

        self.other_group = self.create_other_section()
        right_column.addWidget(self.other_group)

        right_column.addStretch()
        content_layout.addWidget(right_widget, 1)

        self.content_widget.hide()
        self.layout.addWidget(self.content_widget)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def create_client_section(self) -> QGroupBox:
        group = QGroupBox("Client")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self.client_container = QWidget()
        client_container_layout = QVBoxLayout(self.client_container)
        client_container_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.client_container)

        btn_layout = QHBoxLayout()
        self.change_client_btn = QPushButton("Change Client")
        self.change_client_btn.setFixedWidth(150)
        self.change_client_btn.clicked.connect(self.change_client)
        btn_layout.addWidget(self.change_client_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return group

    def create_court_section(self) -> QGroupBox:
        group = QGroupBox("Court")
        layout = QVBoxLayout(group)

        judge_label = QLabel("<b>Judge</b>")
        layout.addWidget(judge_label)

        self.judge_container = QWidget()
        judge_container_layout = QVBoxLayout(self.judge_container)
        judge_container_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.judge_container)

        judge_staff_label = QLabel("<b>Judge's Staff</b>")
        layout.addWidget(judge_staff_label)

        self.judge_staff_container = QWidget()
        judge_staff_layout = QVBoxLayout(self.judge_staff_container)
        judge_staff_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.judge_staff_container)

        court_staff_label = QLabel("<b>Court Staff</b>")
        layout.addWidget(court_staff_label)

        self.court_staff_container = QWidget()
        court_staff_layout = QVBoxLayout(self.court_staff_container)
        court_staff_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.court_staff_container)

        btn_layout = QHBoxLayout()
        self.set_judge_btn = QPushButton("Set Judge")
        self.set_judge_btn.setFixedWidth(120)
        self.set_judge_btn.clicked.connect(lambda: self.add_person('judge'))
        btn_layout.addWidget(self.set_judge_btn)

        self.add_judge_staff_btn = QPushButton("Add Judge's Staff")
        self.add_judge_staff_btn.setFixedWidth(120)
        self.add_judge_staff_btn.clicked.connect(lambda: self.add_person('judge_staff'))
        btn_layout.addWidget(self.add_judge_staff_btn)

        self.add_court_staff_btn = QPushButton("Add Court Staff")
        self.add_court_staff_btn.setFixedWidth(120)
        self.add_court_staff_btn.clicked.connect(lambda: self.add_person('court_staff'))
        btn_layout.addWidget(self.add_court_staff_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return group

    def create_opposing_section(self) -> QGroupBox:
        group = QGroupBox("Opposing Side")
        layout = QVBoxLayout(group)

        btn_layout = QHBoxLayout()
        self.add_opposing_party_btn = QPushButton("Add Opposing Party")
        self.add_opposing_party_btn.setFixedWidth(150)
        self.add_opposing_party_btn.clicked.connect(lambda: self.add_person('opposing_party'))
        btn_layout.addWidget(self.add_opposing_party_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.opposing_container = QWidget()
        opposing_layout = QVBoxLayout(self.opposing_container)
        opposing_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.opposing_container)

        return group

    def create_other_section(self) -> QGroupBox:
        group = QGroupBox("Other Parties")
        layout = QVBoxLayout(group)

        gal_label = QLabel("<b>Guardian ad Litem</b>")
        layout.addWidget(gal_label)

        self.gal_container = QWidget()
        gal_layout = QVBoxLayout(self.gal_container)
        gal_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.gal_container)

        gal_btn_layout = QHBoxLayout()
        self.add_gal_btn = QPushButton("Add Guardian ad Litem")
        self.add_gal_btn.setFixedWidth(150)
        self.add_gal_btn.clicked.connect(lambda: self.add_person('guardian_ad_litem'))
        gal_btn_layout.addWidget(self.add_gal_btn)
        gal_btn_layout.addStretch()
        layout.addLayout(gal_btn_layout)

        co_counsel_label = QLabel("<b>Co-Counsel</b>")
        layout.addWidget(co_counsel_label)

        self.co_counsel_container = QWidget()
        co_counsel_layout = QVBoxLayout(self.co_counsel_container)
        co_counsel_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.co_counsel_container)

        co_counsel_btn_layout = QHBoxLayout()
        self.add_co_counsel_btn = QPushButton("Add Co-Counsel")
        self.add_co_counsel_btn.setFixedWidth(150)
        self.add_co_counsel_btn.clicked.connect(lambda: self.add_person('co_counsel'))
        co_counsel_btn_layout.addWidget(self.add_co_counsel_btn)
        co_counsel_btn_layout.addStretch()
        layout.addLayout(co_counsel_btn_layout)

        return group

    def set_case(self, case_id: int):
        self.current_case_id = case_id

        if case_id:
            self.current_case = self.case_queries.get_by_id(case_id)
            self.no_case_label.hide()
            self.content_widget.show()
            self.update_visibility()
            self.refresh()
        else:
            self.current_case = None
            self.no_case_label.show()
            self.content_widget.hide()

    def update_visibility(self):
        is_litigation = self.current_case and self.current_case.is_litigation
        self.court_group.setVisible(is_litigation)
        self.opposing_group.setVisible(is_litigation)

    def refresh(self):
        if not self.current_case_id:
            return

        summary = self.case_person_queries.get_case_summary(self.current_case_id)

        self.update_client_section(summary.get('client'))

        self.update_single_person_section(
            self.judge_container,
            self.set_judge_btn,
            summary.get('judge'),
            "Set Judge",
            "Change Judge"
        )

        self.update_container_with_cards(
            self.judge_staff_container,
            summary.get('judge_staff', [])
        )

        self.update_container_with_cards(
            self.court_staff_container,
            summary.get('court_staff', [])
        )

        self.update_opposing_section(summary.get('opposing_parties', []))

        self.update_single_person_section(
            self.gal_container,
            self.add_gal_btn,
            summary.get('guardian_ad_litem'),
            "Add Guardian ad Litem",
            "Change GAL"
        )

        self.update_container_with_cards(
            self.co_counsel_container,
            summary.get('co_counsel', [])
        )

    def clear_container(self, container: QWidget):
        layout = container.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def update_container_with_cards(self, container: QWidget, people: list,
                                     show_remove: bool = True,
                                     show_add_staff: bool = False):
        self.clear_container(container)
        layout = container.layout()

        for person_data in people:
            card = CompactPersonCard(person_data, show_remove, show_add_staff)
            card.edit_clicked.connect(self.edit_person)
            card.remove_clicked.connect(self.remove_person)
            if show_add_staff:
                card.add_staff_clicked.connect(self.on_add_opposing_staff)
            layout.addWidget(card)

    def update_client_section(self, client_data: dict):
        self.clear_container(self.client_container)
        layout = self.client_container.layout()

        if client_data:
            card = CompactPersonCard(client_data, show_remove=False)
            card.edit_clicked.connect(self.edit_person)
            layout.addWidget(card)

    def update_single_person_section(self, container: QWidget, button: QPushButton,
                                      person_data: dict, empty_text: str, filled_text: str):
        self.clear_container(container)
        layout = container.layout()

        if person_data:
            card = CompactPersonCard(person_data)
            card.edit_clicked.connect(self.edit_person)
            card.remove_clicked.connect(self.remove_person)
            layout.addWidget(card)
            button.setText(filled_text)
        else:
            button.setText(empty_text)

    def update_opposing_section(self, opposing_parties: list):
        self.clear_container(self.opposing_container)
        layout = self.opposing_container.layout()

        for party_info in opposing_parties:
            party = party_info['party']

            party_frame = QFrame()
            party_frame.setFrameStyle(QFrame.StyledPanel)
            party_layout = QVBoxLayout(party_frame)
            party_layout.setContentsMargins(4, 4, 4, 4)
            party_layout.setSpacing(4)

            party_label = QLabel("<b>Opposing Party:</b>")
            party_layout.addWidget(party_label)

            party_card = CompactPersonCard(party)
            party_card.edit_clicked.connect(self.edit_person)
            party_card.remove_clicked.connect(self.remove_person)
            party_layout.addWidget(party_card)

            party_person_id = party['person_id']
            party_name = f"{party['first_name']} {party['last_name']}"

            if party_info['attorneys']:
                atty_label = QLabel("<b>Represented by:</b>")
                party_layout.addWidget(atty_label)

                for attorney in party_info['attorneys']:
                    atty_card = CompactPersonCard(attorney, show_add_staff=True)
                    atty_card.edit_clicked.connect(self.edit_person)
                    atty_card.remove_clicked.connect(self.remove_person)
                    atty_card.add_staff_clicked.connect(self.on_add_opposing_staff)
                    party_layout.addWidget(atty_card)

                    for staff in party_info.get('staff', []):
                        if staff.get('represents_person_id') == attorney['person_id']:
                            staff_card = CompactPersonCard(staff)
                            staff_card.edit_clicked.connect(self.edit_person)
                            staff_card.remove_clicked.connect(self.remove_person)
                            party_layout.addWidget(staff_card)

            party_btn_layout = QHBoxLayout()
            add_counsel_btn = QPushButton("Add Attorney")
            add_counsel_btn.setFixedWidth(100)
            add_counsel_btn.clicked.connect(
                lambda checked, pid=party_person_id, pname=party_name:
                self.add_person('opposing_counsel', represents_person_id=pid, represents_name=pname)
            )
            party_btn_layout.addWidget(add_counsel_btn)

            party_btn_layout.addStretch()
            party_layout.addLayout(party_btn_layout)

            layout.addWidget(party_frame)

    def on_add_opposing_staff(self, attorney_person_id: int, attorney_name: str):
        self.add_person('opposing_staff', represents_person_id=attorney_person_id, represents_name=attorney_name)

    def change_client(self):
        if not self.current_case_id:
            return

        reply = QMessageBox.question(
            self, "Change Client",
            "Changing the client will not change the matter number.\n\n"
            "Are you sure you want to change the client for this matter?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        is_litigation = self.current_case and self.current_case.is_litigation

        dialog = AddPersonToCaseDialog(
            self,
            person_queries=self.person_queries,
            case_id=self.current_case_id,
            role='client',
            is_litigation=is_litigation
        )

        if dialog.exec():
            person = dialog.get_person()

            if dialog.is_creating_new():
                person_id = self.person_queries.create(person)
            else:
                person_id = person.id

            case_person = dialog.get_case_person(person_id)
            self.case_person_queries.update_client(
                self.current_case_id, 
                person_id, 
                case_person.party_designation
            )

            self.refresh()
            self.case_updated.emit()

    def add_person(self, role: str, represents_person_id: int = None, represents_name: str = None):
        if not self.current_case_id:
            return

        existing_parties = []
        if role == 'opposing_counsel' and not represents_person_id:
            parties = self.case_person_queries.get_by_role(self.current_case_id, 'opposing_party')
            existing_parties = parties

        if role == 'judge_staff':
            judge = self.case_person_queries.get_by_role(self.current_case_id, 'judge')
            if judge:
                represents_person_id = judge[0]['person_id']
                represents_name = f"{judge[0]['first_name']} {judge[0]['last_name']}"
            else:
                QMessageBox.warning(self, "Warning", "Please set a judge before adding judge's staff.")
                return

        is_litigation = self.current_case and self.current_case.is_litigation

        dialog = AddPersonToCaseDialog(
            self,
            person_queries=self.person_queries,
            case_id=self.current_case_id,
            role=role,
            represents_person_id=represents_person_id,
            represents_name=represents_name,
            existing_parties=existing_parties,
            is_litigation=is_litigation
        )

        if dialog.exec():
            person = dialog.get_person()

            if dialog.is_creating_new():
                person_id = self.person_queries.create(person)
            else:
                person_id = person.id

            case_person = dialog.get_case_person(person_id)
            self.case_person_queries.add_person_to_case(case_person)

            if role == 'opposing_counsel' and case_person.represents_person_id:
                self.case_person_queries.clear_pro_se_for_party(
                    self.current_case_id, 
                    case_person.represents_person_id
                )

            self.refresh()
            self.case_updated.emit()

    def edit_person(self, person_id: int):
        person = self.person_queries.get_by_id(person_id)
        if not person:
            return

        dialog = PersonDialog(self, self.person_queries, person)
        if dialog.exec():
            updated_person = dialog.get_person()
            updated_person.id = person_id
            self.person_queries.update(updated_person)
            self.refresh()
            self.case_updated.emit()

    def remove_person(self, case_person_id: int):
        reply = QMessageBox.question(
            self, "Confirm Remove",
            "Remove this person from the matter? (This does not delete the person from the system.)",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.case_person_queries.remove_person_from_case(case_person_id)
            self.refresh()
            self.case_updated.emit()