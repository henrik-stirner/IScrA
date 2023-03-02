import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QLabel, QPushButton, QLineEdit, QSizePolicy
)

from app.QtExt import util
from app.QtExt.QSeparationLine import QHSeparationLine

from app.window.DisplayMailWindow import DisplayMailWindow
from app.window.ComposeMailWindow import ComposeMailWindow
from app.window.MailScheduleWindow import MailScheduleWindow

import mail


# ----------
# logging
# ----------


logger = logging.getLogger(__name__)


# ----------
# MailsTab
# ----------

class MailsTab(QScrollArea):
    def __init__(self, iserv_username: str, iserv_password: str):
        super().__init__()

        # ----------
        # IServ
        # ----------

        self._iserv_username = iserv_username
        self._iserv_password = iserv_password

        self._mail_receiver = None
        self._mail_transmitter = None

        # if we do not keep a reference to our windows, they will be closed immediately
        self.display_mail_window = None
        self.compose_mail_window = None
        self.edit_mail_schedule_window = None

        # ----------
        # actual layout
        # ----------

        self.load_mails_button = QPushButton('Load mails')
        self.load_mails_button.clicked.connect(self.load_mails)

        self.compose_mail_button = QPushButton('Compose new mail')
        self.compose_mail_button.clicked.connect(self.compose_mail)

        self.edit_mail_schedule_button = QPushButton('Edit mail schedule')
        self.edit_mail_schedule_button.clicked.connect(self.edit_mail_schedule)

        self.filter_mails_header = QLabel('Filter: ')
        self.filter_mails_header.setStyleSheet('QLabel { font-weight: bold; }')
        self.filter_mails_header.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.filter_mails_entry = QLineEdit()
        self.filter_mails_entry.setPlaceholderText('prompt')
        self.filter_mails_entry.textChanged.connect(self.filter_mails)
        self.filter_mails_entry.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)

        # self.execute_filter_mails_button = QPushButton('Apply Filter')
        # self.execute_filter_mails_button.clicked.connect(self.filter_mails)
        # self.execute_filter_mails_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.filter_mails_layout = QHBoxLayout()
        self.filter_mails_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.filter_mails_layout.addWidget(self.filter_mails_header)
        self.filter_mails_layout.addWidget(self.filter_mails_entry)
        # self.filter_mails_layout.addWidget(self.execute_filter_mails_button)

        self.filter_mails_widget = QWidget()
        self.filter_mails_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        self.filter_mails_widget.setLayout(self.filter_mails_layout)

        self.mails_tab_mails_layout = QVBoxLayout()
        self.mails_tab_mails_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.mails_tab_mails_widget = QWidget()
        self.mails_tab_mails_widget.setLayout(self.mails_tab_mails_layout)

        self.mails_tab_main_layout = QVBoxLayout()
        self.mails_tab_main_layout.addWidget(self.load_mails_button)
        self.mails_tab_main_layout.addWidget(self.compose_mail_button)
        self.mails_tab_main_layout.addWidget(self.edit_mail_schedule_button)
        self.mails_tab_main_layout.addWidget(QHSeparationLine(line_width=3))
        self.mails_tab_main_layout.addWidget(self.filter_mails_widget)
        self.mails_tab_main_layout.addWidget(self.mails_tab_mails_widget)

        self.mails_tab_widget = QWidget()
        self.mails_tab_widget.setLayout(self.mails_tab_main_layout)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        self.setWidget(self.mails_tab_widget)

        # ----------
        # load mails
        # ----------

        # immediately load the mails because it is quick and handy
        self.load_mails()

    def display_mail(self, selection: str, mail_id: int) -> None:
        if not self.display_mail_window:
            self.display_mail_window = DisplayMailWindow(self._mail_receiver)

        self.display_mail_window.display_mail(selection, mail_id)
        self.display_mail_window.show()

    def load_mails(self) -> None:
        # load mails button
        self.load_mails_button.setText('Loading mails...')
        self.load_mails_button.setDisabled(True)

        if not self._mail_receiver:
            # create mail receiver if not exists
            self._mail_receiver = mail.Receiver(self._iserv_username, self._iserv_password)

        # remove all widgets from the layout
        util.clear_layout(self.mails_tab_mails_layout)

        selection, mail_ids = self._mail_receiver.get_ids_of_unread_mails()

        if not mail_ids:
            self.mails_tab_mails_layout.addWidget(QLabel(
                'Currently, there are no unread mails in your inbox.'
            ))

        # there are unread mails, add the new widgets
        i = 0
        for from_user, subject, body in self._mail_receiver.extract_mail_content_by_id(selection, mail_ids):
            # widget with vertical layout containing labels with mail specific data
            mail_subject_label = QLabel(subject)
            mail_subject_label.setStyleSheet('QLabel { font-weight: bold }')

            mail_from_user_label = QLabel(from_user)
            mail_from_user_label.setStyleSheet('QLabel { color: darkgrey }')

            mail_data_layout = QVBoxLayout()
            mail_data_layout.addWidget(mail_subject_label)
            mail_data_layout.addWidget(mail_from_user_label)

            mail_data_widget = QWidget()
            mail_data_widget.setLayout(mail_data_layout)

            # widget with horizontal layout containing the mail data widget and a button for displaying the mail
            display_mail_button = QPushButton('Display')
            display_mail_button.clicked.connect(
                lambda state, display_mail_selection=selection, display_mail_id=mail_ids[i]: self.display_mail(
                    display_mail_selection,
                    display_mail_id
                )
            )
            display_mail_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

            mail_mail_layout = QHBoxLayout()
            mail_mail_layout.addWidget(mail_data_widget)
            mail_mail_layout.addWidget(display_mail_button)

            mail_mail_widget = QWidget()
            mail_mail_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            mail_mail_widget.setLayout(mail_mail_layout)

            mail_main_layout = QVBoxLayout()
            mail_main_layout.addWidget(QHSeparationLine(line_width=1))
            mail_main_layout.addWidget(mail_mail_widget)
            mail_main_layout.addWidget(QHSeparationLine(line_width=1))

            mail_main_widget = QWidget()
            mail_main_widget.setLayout(mail_main_layout)

            self.mails_tab_mails_layout.addWidget(mail_main_widget)

            # for accessing the right mail id
            i += 1

        # load mails button
        self.load_mails_button.setText('Reload mails')
        self.load_mails_button.setDisabled(False)

    def compose_mail(self):
        if not self.compose_mail_window:
            if not self._mail_transmitter:
                # create mail receiver if not exists
                self._mail_transmitter = mail.Transmitter(self._iserv_username, self._iserv_password)

            self.compose_mail_window = ComposeMailWindow(self._mail_transmitter)

        self.compose_mail_window.empty_inputs()
        self.compose_mail_window.show()

    def edit_mail_schedule(self):
        if not self.edit_mail_schedule_window:
            self.edit_mail_schedule_window = MailScheduleWindow()

        self.edit_mail_schedule_window.load_mail_schedule()
        self.edit_mail_schedule_window.show()

    def filter_mails(self):
        prompt = self.filter_mails_entry.text().lower()

        for i in range(self.mails_tab_mails_layout.count()):
            child = self.mails_tab_mails_layout.itemAt(i).widget()

            if not isinstance(child, QWidget):
                # skip
                continue

            if prompt not in util.get_text_of_child_labels(child).lower():
                # hide
                child.hide()
            elif child.isHidden():
                # show
                child.show()

    def shutdown(self) -> None:
        # close sub-windows
        if self.display_mail_window:
            self.display_mail_window.close()

        # log out and close connections
        if self._mail_receiver:
            self._mail_receiver.shutdown()
        if self._mail_transmitter:
            self._mail_transmitter.shutdown()

    def close(self) -> None:
        super().close()

        # log out and close connections
        self.shutdown()
