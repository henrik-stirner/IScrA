import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)

from app.QtExt import util
from app.QtExt.QSeparationLine import QHSeparationLine

import mail


# ----------
# logging
# ----------


logger = logging.getLogger(__name__)


# ----------
# DisplayMailWindow
# ----------


class DisplayMailWindow(QScrollArea):
    def __init__(self, mail_receiver: mail.Receiver) -> None:
        super().__init__()

        # ----------
        # IServ
        # ----------

        self._mail_receiver = mail_receiver

        self.current_mail_id = None

        # ----------
        # window setting
        # ----------

        self.setWindowTitle('IScrA')

        # ----------
        # actions
        # ----------

        self.exit_action = QAction('Exit', self)
        self.exit_action.setStatusTip('Closes the application')
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.triggered.connect(QApplication.instance().exit)

        # ----------
        # main layout
        # ----------

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)

        self.setWidget(self.main_widget)

    def display_mail(self, selection: str, mail_id: int) -> None:
        if self.current_mail_id == mail_id:
            return

        util.clear_layout(self.main_layout)

        from_user, subject, body = '', '', ''
        for from_user, subject, body in self._mail_receiver.extract_mail_content_by_id(
                selection=selection, mail_ids=[mail_id]):
            # this for loop is needed, because extract_mail_content_by_id() is a generator
            pass

        self.setWindowTitle(subject)

        # subject
        subject_header_label = QLabel('Subject: ')
        subject_header_label.setStyleSheet('QLabel { font-weight: bold; }')

        subject_description_label = QLabel(subject)

        subject_layout = QHBoxLayout()
        subject_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        subject_layout.addWidget(subject_header_label)
        subject_layout.addWidget(subject_description_label)

        subject_widget = QWidget()
        subject_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        subject_widget.setLayout(subject_layout)

        self.main_layout.addWidget(subject_widget)

        # from user
        from_user_header_label = QLabel('From: ')
        from_user_header_label.setStyleSheet('QLabel { color: lightgrey; font-weight: bold; }')

        from_user_description_label = QLabel(from_user)
        from_user_description_label.setStyleSheet('QLabel { color: lightgrey; }')

        from_user_layout = QHBoxLayout()
        from_user_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        from_user_layout.addWidget(from_user_header_label)
        from_user_layout.addWidget(from_user_description_label)

        from_user_widget = QWidget()
        from_user_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        from_user_widget.setLayout(from_user_layout)

        self.main_layout.addWidget(from_user_widget)

        # body
        body_label = QLabel(body)

        body_layout = QVBoxLayout()
        body_layout.addWidget(body_label)

        body_widget = QWidget()
        body_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        body_widget.setLayout(body_layout)

        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(body_widget)

    def shutdown(self) -> None:
        # log out and close connections
        pass

    def close(self) -> None:
        super().close()

        # log out and close connections
        self.shutdown()
