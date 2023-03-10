import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QFileDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

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
        self.main_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        self.main_widget.setLayout(self.main_layout)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)

        self.setWidget(self.main_widget)

    def download_mail_attachments(self, selection: str, mail_id: int | str):
        save_path = str(QFileDialog.getExistingDirectory(self, 'Select Directory'))
        self._mail_receiver.download_mail_attachments_by_id(selection=selection, mail_id=mail_id, to_location=save_path)

    def display_mail(self, selection: str, mail_id: int | str) -> None:
        if self.current_mail_id == mail_id:
            return

        util.clear_layout(self.main_layout)

        # get mail data
        date, subject, from_sender, to_receiver, body, attachment_data = self._mail_receiver.fetch_mail_content_by_id(
            selection=selection, mail_id=str(mail_id))

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
        from_user_header_label.setStyleSheet('QLabel { color: darkgrey; font-weight: bold; }')

        from_user_description_label = QLabel(from_sender)
        from_user_description_label.setStyleSheet('QLabel { color: darkgrey; }')

        from_user_layout = QHBoxLayout()
        from_user_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        from_user_layout.addWidget(from_user_header_label)
        from_user_layout.addWidget(from_user_description_label)

        from_user_widget = QWidget()
        from_user_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        from_user_widget.setLayout(from_user_layout)

        self.main_layout.addWidget(from_user_widget)

        # to user
        to_user_header_label = QLabel('To: ')
        to_user_header_label.setStyleSheet('QLabel { color: darkgrey; font-weight: bold; }')

        to_user_description_label = QLabel(to_receiver)
        to_user_description_label.setStyleSheet('QLabel { color: darkgrey; }')

        to_user_layout = QHBoxLayout()
        to_user_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        to_user_layout.addWidget(to_user_header_label)
        to_user_layout.addWidget(to_user_description_label)

        to_user_widget = QWidget()
        to_user_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        to_user_widget.setLayout(to_user_layout)

        self.main_layout.addWidget(to_user_widget)

        # date
        date_header_label = QLabel('Date: ')
        date_header_label.setStyleSheet('QLabel { color: darkgrey; font-weight: bold; }')

        date_description_label = QLabel(date)
        date_description_label.setStyleSheet('QLabel { color: darkgrey; }')

        date_layout = QHBoxLayout()
        date_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        date_layout.addWidget(date_header_label)
        date_layout.addWidget(date_description_label)

        date_widget = QWidget()
        date_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        date_widget.setLayout(date_layout)

        self.main_layout.addWidget(date_widget)

        # body
        body_widget = None
        if body_html := body[1]:
            # html (preferred)
            body_widget = QWebEngineView()
            body_widget.setHtml(body_html)
        elif body_plaintext := body[0]:
            # plaintext
            body_widget = QLabel(body_plaintext)
            # text should be selectable
            body_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        else:
            body_widget = QLabel('This mail does not contain any text parts.')
            body_widget.setStyleSheet('QLabel { color: lightgrey; font-weight: 100; font-style: italic; }')
            # text should be selectable
            body_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        body_layout = QVBoxLayout()
        body_layout.addWidget(body_widget)

        body_widget = QWidget()
        body_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        body_widget.setLayout(body_layout)

        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(body_widget)

        # attachment file names
        if not attachment_data:
            # if there are no attachment files the following code is unnecessary
            return

        attachment_data_layout = QVBoxLayout()

        for attachment in attachment_data:
            attachment_data_layout.addWidget(QLabel(f'{attachment[0]} ({attachment[1]})'))

        attachment_data_widget = QWidget()
        attachment_data_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        attachment_data_widget.setLayout(attachment_data_layout)

        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(attachment_data_widget)

        # download attachments button
        download_attachments_button = QPushButton('Download attachments')
        download_attachments_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        download_attachments_button.clicked.connect(lambda state: self.download_mail_attachments(
            selection=selection, mail_id=mail_id))

        self.main_layout.addWidget(download_attachments_button)

    def shutdown(self) -> None:
        # log out and close connections
        pass

    def close(self) -> None:
        super().close()

        # log out and close connections
        self.shutdown()
