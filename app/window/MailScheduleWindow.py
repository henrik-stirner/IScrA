import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication, QScrollArea, QWidget, QVBoxLayout, QPushButton, QSizePolicy, QTextEdit
)

from app.QtExt.QSeparationLine import QHSeparationLine


# ----------
# logging
# ----------


logger = logging.getLogger(__name__)


# ----------
# MailScheduleWindow
# ----------


class MailScheduleWindow(QScrollArea):
    def __init__(self) -> None:
        super().__init__()

        # ----------
        # window settings
        # ----------

        self.setWindowTitle('Mail Schedule')

        # ----------
        # actions
        # ----------

        self.exit_action = QAction('Exit', self)
        self.exit_action.setStatusTip('Closes the application')
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.triggered.connect(QApplication.instance().exit)

        # ----------
        # schedule mail layout
        # ----------

        # reload button
        self.reload_mail_schedule_button = QPushButton('Reload mail schedule')
        self.reload_mail_schedule_button.clicked.connect(self.load_mail_schedule)
        self.reload_mail_schedule_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # mail schedule
        self.mail_schedule_input = QTextEdit()
        self.mail_schedule_input.setAcceptRichText(False)
        self.mail_schedule_input.setPlaceholderText(
            'Europe/Berlin | dd-mm-yyyy_-_hh-mm-ss | user.name | subject | plaintext/plaintext-template-name.txt | '
            'once | C:/absolute/path/to/an/attachment.filetype | ./relative/path/to/an/attachment.filetype | ...\n'
            'Europe/Berlin | dd-mm-yyyy_-_hh-mm-ss | user.name | subject | plaintext/plaintext-template-name.txt | '
            'once | C:/absolute/path/to/an/attachment.filetype | ./relative/path/to/an/attachment.filetype | ...\n'
            '...'
        )
        self.mail_schedule_input.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        # save button
        self.save_mail_schedule_button = QPushButton('Save mail schedule')
        self.save_mail_schedule_button.clicked.connect(self.save_mail_schedule)
        self.save_mail_schedule_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # ----------
        # main layout
        # ----------

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.reload_mail_schedule_button)
        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(self.mail_schedule_input)
        self.main_layout.addWidget(self.save_mail_schedule_button)

        self.main_widget = QWidget()
        self.main_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        self.main_widget.setLayout(self.main_layout)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)

        self.setWidget(self.main_widget)

        # ----------
        # load mail schedule
        # ----------

        self.load_mail_schedule()

    def load_mail_schedule(self) -> None:
        with open('./data/mail/schedule/schedule.txt', 'r', encoding='utf-8') as mail_schedule_file:
            self.mail_schedule_input.setText(mail_schedule_file.read())
            mail_schedule_file.close()

    def save_mail_schedule(self) -> None:
        with open('./data/mail/schedule/schedule.txt', 'w', encoding='utf-8') as mail_schedule_file:
            mail_schedule_file.write(self.mail_schedule_input.toPlainText())
            mail_schedule_file.close()

    def shutdown(self) -> None:
        # log out and close connections
        pass

    def close(self) -> None:
        super().close()

        # log out and close connections
        self.shutdown()
