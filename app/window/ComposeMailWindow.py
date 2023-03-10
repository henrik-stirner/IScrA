import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QLineEdit,
    QTextEdit, QFileDialog
)

from app.QtExt.QSeparationLine import QHSeparationLine

from app.dialog.WarnDialog import WarnDialog

import mail


# ----------
# logging
# ----------


logger = logging.getLogger(__name__)


# ----------
# ComposeMailWindow
# ----------


class ComposeMailWindow(QScrollArea):
    def __init__(self, mail_transmitter: mail.Transmitter) -> None:
        super().__init__()

        # ----------
        # IServ
        # ----------

        self._mail_transmitter = mail_transmitter

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
        # compose mail layout
        # ----------

        # to user
        self.to_user_info_label = QLabel('To user: ')
        self.to_user_info_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.to_user_info_label.setStyleSheet('QLabel { font-weight: bold; }')

        self.to_user_input = QLineEdit()
        self.to_user_input.setPlaceholderText('user.name')
        self.to_user_input.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)

        self.to_user_layout = QHBoxLayout()
        self.to_user_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.to_user_layout.addWidget(self.to_user_info_label)
        self.to_user_layout.addWidget(self.to_user_input)

        self.to_user_widget = QWidget()
        self.to_user_widget.setLayout(self.to_user_layout)

        # subject
        self.subject_info_label = QLabel('Subject: ')
        self.subject_info_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.subject_info_label.setStyleSheet('QLabel { font-weight: bold; }')

        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText('Subject')
        self.subject_input.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)

        self.subject_layout = QHBoxLayout()
        self.subject_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.subject_layout.addWidget(self.subject_info_label)
        self.subject_layout.addWidget(self.subject_input)

        self.subject_widget = QWidget()
        self.subject_widget.setLayout(self.subject_layout)

        # clear button
        self.clear_inputs_button = QPushButton('Clear')
        self.clear_inputs_button.clicked.connect(self.empty_inputs)
        self.clear_inputs_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # load template button
        self.load_mail_template_button = QPushButton('Load mail template')
        self.load_mail_template_button.clicked.connect(self.load_mail_template)
        self.load_mail_template_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # body
        self.body_input = QTextEdit()
        self.body_input.setAcceptRichText(False)
        self.body_input.setPlaceholderText('Dear John, \n'
                                           'I wanted to ask you if...')
        self.body_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # send button
        self.send_mail_button = QPushButton('Send')
        self.send_mail_button.clicked.connect(self.send_mail)
        self.send_mail_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # ----------
        # main layout
        # ----------

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.to_user_widget)
        self.main_layout.addWidget(self.subject_widget)
        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(self.clear_inputs_button)
        self.main_layout.addWidget(self.load_mail_template_button)
        self.main_layout.addWidget(self.body_input)
        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(self.send_mail_button)

        self.main_widget = QWidget()
        self.main_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        self.main_widget.setLayout(self.main_layout)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)

        self.setWidget(self.main_widget)

    def load_mail_template(self):
        path_to_template = QFileDialog.getOpenFileName(
            self,
            caption='Select Text File',
            directory='./data/mail/template/plaintext/',
            filter='*.txt'
        )[0]

        try:
            with open(path_to_template, 'r', encoding='utf-8') as template_file:
                self.body_input.setText(template_file.read())
        except Exception as exception:
            logger.exception(exception)

    def empty_inputs(self) -> None:
        self.to_user_input.setText('')
        self.subject_input.setText('')
        self.body_input.setText('')

    def show_warn_dialog(self, caption: str, title: str, description: str):
        warn_dialog = WarnDialog(self, title=title, description=description, caption=caption)
        warn_dialog.show()

    def send_mail(self) -> None:
        # check if all the fields have been filled in correctly
        to_user = self.to_user_input.text()
        mandatory_substrings = ['.']
        forbidden_substrings = [' ', '@']
        if (
                not to_user or
                any(mandatory_substring not in to_user for mandatory_substring in mandatory_substrings) or
                any(forbidden_substring in to_user for forbidden_substring in forbidden_substrings)
        ):
            self.show_warn_dialog(
                caption='Warning',
                title='The mail has not been sent. ',
                description='Please enter a valid username. (for example: john.doe)\n'
                            'The rest of the mail address will be appended automatically. \n'
                            'You can not send mails to external mail servers. '
            )

            return

        # try to send the mail
        try:
            self._mail_transmitter.send_mail(
                to_user=self.to_user_input.text(),
                subject=self.subject_input.text(),
                body=self.body_input.toPlainText(),
                formatted_body=False)

            self.empty_inputs()
            self.close()

        except Exception as exception:
            logger.exception(exception)

            self.show_warn_dialog(
                caption='Error',
                title='Was not able to send the mail.',
                description='Something went wrong while trying to send this mail. \n'
                            'Please verify your input and try again.'
            )

    def shutdown(self) -> None:
        # log out and close connections
        pass

    def close(self) -> None:
        super().close()

        # log out and close connections
        self.shutdown()
