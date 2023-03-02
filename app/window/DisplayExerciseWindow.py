import logging

from datetime import datetime
import webbrowser

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
# DisplayExerciseWindow
# ----------


class DisplayExerciseWindow(QScrollArea):
    def __init__(self, webdriver_session: webdriver.Session) -> None:
        super().__init__()

        # ----------
        # IServ
        # ----------

        self._webdriver_session = webdriver_session

        self.current_exercise = None

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

    def save_exercise(self, exercise: webdriver.element.Exercise):
        save_path = str(QFileDialog.getExistingDirectory(self, 'Select Directory'))
        self._webdriver_session.save_exercise(exercise=exercise, override=False, to_location=save_path)

    def display_exercise(self, exercise: webdriver.element.Exercise) -> None:
        if self.current_exercise == exercise:
            return

        if self.main_layout.count():
            util.clear_layout(self.main_layout)

        self.setWindowTitle(str(exercise.title))

        # title
        title_header_label = QLabel('Title: ')
        title_header_label.setStyleSheet('QLabel { font-weight: bold; }')

        title_description_label = QLabel(str(exercise.title))

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

        owner_description_label = QLabel(str(exercise.owner))
        owner_description_label.setStyleSheet('QLabel { color: lightgrey; }')

        owner_layout = QHBoxLayout()
        owner_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        owner_layout.addWidget(owner_header_label)
        owner_layout.addWidget(owner_description_label)

        owner_widget = QWidget()
        owner_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        owner_widget.setLayout(owner_layout)

        self.main_layout.addWidget(owner_widget)

        # start date
        start_date_header_label = QLabel('Start Date: ')

        start_date_description_label = QLabel(datetime.strftime(exercise.start_date, '%d.%m.%Y %H:%M'))

        start_date_layout = QHBoxLayout()
        start_date_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        start_date_layout.addWidget(start_date_header_label)
        start_date_layout.addWidget(start_date_description_label)

        start_date_widget = QWidget()
        start_date_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        start_date_widget.setLayout(start_date_layout)

        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(start_date_widget)

        # deadline
        deadline_header_label = QLabel('Deadline: ')

        deadline_description_label = QLabel(datetime.strftime(exercise.deadline, '%d.%m.%Y %H:%M'))

        deadline_layout = QHBoxLayout()
        deadline_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        deadline_layout.addWidget(deadline_header_label)
        deadline_layout.addWidget(deadline_description_label)

        deadline_widget = QWidget()
        deadline_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        deadline_widget.setLayout(deadline_layout)

        self.main_layout.addWidget(deadline_widget)

        # subject
        subject_header_label = QLabel('Subject hint: ')

        subject_description_label = QLabel(" | ".join([subject.capitalize() for subject in exercise.subject]))

        subject_layout = QHBoxLayout()
        subject_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        subject_layout.addWidget(subject_header_label)
        subject_layout.addWidget(subject_description_label)

        subject_widget = QWidget()
        subject_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        subject_widget.setLayout(subject_layout)

        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(subject_widget)

        # tags
        if exercise.tags:
            tags_header_label = QLabel('Tags: ')

            tags_layout = QHBoxLayout()
            tags_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            tags_layout.addWidget(tags_header_label)

            for tag in exercise.tags:
                tag_label = QLabel(str(tag))
                tag_label.setStyleSheet('QLabel { background-color: lightgrey; padding: 2px 5px; border-radius: 5px }')

                tags_layout.addWidget(tag_label)

            tags_widget = QWidget()
            tags_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            tags_widget.setLayout(tags_layout)

            self.main_layout.addWidget(tags_widget)

        # description
        description_label = QLabel(str(exercise.description))

        description_layout = QVBoxLayout()
        description_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        description_layout.addWidget(description_label)

        description_widget = QWidget()
        description_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        description_widget.setLayout(description_layout)

        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(description_widget)

        # attachments
        attachments_layout = QVBoxLayout()
        attachments_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for attachment in exercise.attachments:
            attachment_file_name_label = QLabel(attachment.split('/')[-1])

            open_attachment_button = QPushButton('OPEN')
            open_attachment_button.clicked.connect(lambda attachment_to_open=attachment: webbrowser.open(
                attachment, new=2))
            open_attachment_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

            attachment_data_layout = QHBoxLayout()
            attachment_data_layout.addWidget(attachment_file_name_label)
            attachment_data_layout.addWidget(open_attachment_button)

            attachment_data_widget = QWidget()
            attachment_data_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
            attachment_data_widget.setLayout(attachment_data_layout)

            attachments_layout.addWidget(attachment_data_widget)

        attachments_widget = QWidget()
        attachments_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        attachments_widget.setLayout(attachments_layout)

        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(attachments_widget)

        # save button
        save_button = QPushButton('Save this exercise')
        save_button.clicked.connect(lambda this_exercise=exercise: self.save_exercise(this_exercise))
        save_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.main_layout.addWidget(QHSeparationLine(line_width=1))
        self.main_layout.addWidget(save_button)

    def shutdown(self) -> None:
        # log out and close connections
        pass

    def close(self) -> None:
        super().close()

        # log out and close connections
        self.shutdown()
