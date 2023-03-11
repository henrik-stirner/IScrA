import logging

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication, QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QFileDialog
)

from app.QtExt import util
from app.QtExt.QSeparationLine import QHSeparationLine

import webdriver


# ----------
# logging
# ----------


logger = logging.getLogger(__name__)


# ----------
# DisplayTextWindow
# ----------


class DisplayTextWindow(QScrollArea):
    def __init__(self, webdriver_session: webdriver.Session) -> None:
        super().__init__()

        # ----------
        # IServ
        # ----------

        self._webdriver_session = webdriver_session

        self.current_text = None

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

    def save_text(self, text: webdriver.element.Text):
        save_path = str(QFileDialog.getExistingDirectory(self, 'Select Location'))
        self._webdriver_session.save_text(text=text, override=False, to_location=save_path)

    def display_text(self, text: webdriver.element.Text) -> None:
        if self.current_text == text:
            return

        if self.main_layout.count():
            util.clear_layout(self.main_layout)

        self.setWindowTitle(str(text.title))

        # title
        title_header_label = QLabel('Title: ')
        title_header_label.setStyleSheet('QLabel { font-weight: bold; }')

        title_description_label = QLabel(str(text.title))

        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title_layout.addWidget(title_header_label)
        title_layout.addWidget(title_description_label)

        title_widget = QWidget()
        title_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        title_widget.setLayout(title_layout)

        self.main_layout.addWidget(title_widget)

        # owner
        owner_header_label = QLabel('Owner: ')
        owner_header_label.setStyleSheet('QLabel { color: lightgrey; font-weight: bold; }')

        owner_description_label = QLabel(str(text.owner))
        owner_description_label.setStyleSheet('QLabel { color: lightgrey; }')

        owner_layout = QHBoxLayout()
        owner_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        owner_layout.addWidget(owner_header_label)
        owner_layout.addWidget(owner_description_label)

        owner_widget = QWidget()
        owner_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        owner_widget.setLayout(owner_layout)

        self.main_layout.addWidget(owner_widget)

        # access
        if text.shared_with_users:
            shared_with_users_header_label = QLabel('Access: ')

            shared_with_users_layout = QHBoxLayout()
            shared_with_users_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            shared_with_users_layout.addWidget(shared_with_users_header_label)

            for user, granted_permissions in text.shared_with_users.items():
                shared_with_user_label = QLabel(f'{user} | {": ".join(granted_permissions)}')
                shared_with_user_label.setStyleSheet(
                    'QLabel { background-color: lightgrey; padding: 2px 5px; border-radius: 5px }')
                shared_with_users_layout.addWidget(shared_with_user_label)

            shared_with_users_widget = QWidget()
            shared_with_users_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            shared_with_users_widget.setLayout(shared_with_users_layout)

            self.main_layout.addWidget(shared_with_users_widget)

        # creation date
        creation_date_header_label = QLabel('Date of creation: ')

        creation_date_description_label = QLabel(datetime.strftime(text.creation_date, '%d.%m.%Y %H:%M'))

        creation_date_layout = QHBoxLayout()
        creation_date_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        creation_date_layout.addWidget(creation_date_header_label)
        creation_date_layout.addWidget(creation_date_description_label)

        creation_date_widget = QWidget()
        creation_date_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        creation_date_widget.setLayout(creation_date_layout)

        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(creation_date_widget)

        # last modification date
        last_modification_date_header_label = QLabel('Date of last modification: ')

        last_modification_date_description_label = QLabel(datetime.strftime(
            text.last_modification_date, '%d.%m.%Y %H:%M'))

        last_modification_date_layout = QHBoxLayout()
        last_modification_date_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        last_modification_date_layout.addWidget(last_modification_date_header_label)
        last_modification_date_layout.addWidget(last_modification_date_description_label)

        last_modification_date_widget = QWidget()
        last_modification_date_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        last_modification_date_widget.setLayout(last_modification_date_layout)

        self.main_layout.addWidget(last_modification_date_widget)

        # tags
        if text.tags:
            tags_header_label = QLabel('Tags: ')

            tags_layout = QHBoxLayout()
            tags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            tags_layout.addWidget(tags_header_label)

            for tag in text.tags:
                tag_label = QLabel(str(tag))
                tag_label.setStyleSheet('QLabel { background-color: lightgrey; padding: 2px 5px; border-radius: 5px }')

                tags_layout.addWidget(tag_label)

            tags_widget = QWidget()
            tags_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            tags_widget.setLayout(tags_layout)

            self.main_layout.addWidget(QHSeparationLine(line_width=1))
            self.main_layout.addWidget(tags_widget)

        # text
        body_layout = QVBoxLayout()
        body_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        body_label = QLabel()
        # text should be selectable
        body_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        for ace_line in self._webdriver_session.fetch_text_content(text=text):
            body_label.setText(f'{body_label.text()}\n{ace_line.text}')
        body_layout.addWidget(body_label)

        body_widget = QWidget()
        body_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        body_widget.setLayout(body_layout)

        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(body_widget)

        # save button
        save_button = QPushButton('Save this text')
        save_button.clicked.connect(lambda this_text=text: self.save_text(text))
        save_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(save_button)

    def shutdown(self) -> None:
        # log out and close connections
        pass

    def close(self) -> None:
        # log out and close connections
        self.shutdown()

        super().close()
