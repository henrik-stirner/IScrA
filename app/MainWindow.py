import logging
from configparser import ConfigParser

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QMenuBar, QTabWidget, QLabel,
    QPushButton, QSizePolicy, QStyle
)

from app.QtExt import util
from app.QtExt.QSeparationLine import QHSeparationLine

from app.AboutDialog import AboutDialog
from app.ComposeMailWindow import ComposeMailWindow
from app.DisplayMailWindow import DisplayMailWindow
from app.DisplayExerciseWindow import DisplayExerciseWindow

import mail
import scraper
import webdriver


# ----------
# logging
# ----------


logger = logging.getLogger(__name__)


# ----------
# config
# ----------


config = ConfigParser()
config.read('./app/config/MainWindow.ini', encoding='utf-8')


# ----------
# MainWindow
# ----------


class MainWindow(QMainWindow):
    def __init__(self, iserv_username: str, iserv_password: str) -> None:
        super().__init__()

        # ----------
        # IServ
        # ----------

        self._iserv_username = iserv_username
        self._iserv_password = iserv_password

        self._mail_receiver = None
        self._mail_transmitter = None

        self._webdriver_session = None

        # if we do not keep a reference to our windows, they will be closed immediately
        self.compose_mail_window = None
        self.display_mail_window = None
        self.display_exercise_window = None

        # ----------
        # window setting
        # ----------

        self.setWindowTitle('IScrA')
        self.setGeometry(
            int(config['position']['x']),
            int(config['position']['y']),
            int(config['size']['w']),
            int(config['size']['h'])
        )

        # ----------
        # actions
        # ----------

        self.exit_action = QAction(QIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarCloseButton)), '&Exit', self)
        self.exit_action.setStatusTip('Closes the application')
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.triggered.connect(QApplication.instance().exit)

        self.about_action = QAction(QIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarContextHelpButton)), '&About', self)
        self.about_action.setStatusTip('Shows some general information about IScrA')
        self.about_action.triggered.connect(self.show_about_dialogue)

        # ----------
        # status bar
        # ----------

        self.statusBar().showMessage('Hello, World!')

        # ----------
        # menu bar
        # ----------

        self.menu_bar = QMenuBar(self)

        # app menu
        self.app_menu = self.menu_bar.addMenu('&App')
        self.app_menu.addAction(self.exit_action)

        # help menu
        self.help_menu = self.menu_bar.addMenu('&Help')
        self.help_menu.addAction(self.about_action)

        # ----------
        # tab widget
        # ----------

        self.tab_widget = QTabWidget(self)

        # mails tab
        self.load_mails_button = QPushButton('Load mails')
        self.load_mails_button.clicked.connect(self.load_mails)

        self.compose_mail_button = QPushButton('Compose new mail')
        self.compose_mail_button.clicked.connect(self.compose_mail)

        self.mails_tab_mails_layout = QVBoxLayout()
        self.mails_tab_mails_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.mails_tab_mails_widget = QWidget()
        self.mails_tab_mails_widget.setLayout(self.mails_tab_mails_layout)

        self.mails_tab_main_layout = QVBoxLayout()
        self.mails_tab_main_layout.addWidget(self.load_mails_button)
        self.mails_tab_main_layout.addWidget(self.compose_mail_button)
        self.mails_tab_main_layout.addWidget(QHSeparationLine(line_width=3))
        self.mails_tab_main_layout.addWidget(self.mails_tab_mails_widget)

        self.mails_tab_widget = QWidget()
        self.mails_tab_widget.setLayout(self.mails_tab_main_layout)

        self.mails_tab_scroll_area = QScrollArea()
        self.mails_tab_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.mails_tab_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mails_tab_scroll_area.setWidgetResizable(True)
        self.mails_tab_scroll_area.setWidget(self.mails_tab_widget)

        self.mails_tab = self.tab_widget.addTab(self.mails_tab_scroll_area, 'Mails')

        # exercises tab
        self.load_exercises_button = QPushButton('Load exercises')
        self.load_exercises_button.clicked.connect(self.load_exercises)

        self.exercises_tab_exercises_layout = QVBoxLayout()
        self.exercises_tab_exercises_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.exercises_tab_exercises_widget = QWidget()
        self.exercises_tab_exercises_widget.setLayout(self.exercises_tab_exercises_layout)

        self.exercises_tab_main_layout = QVBoxLayout()
        self.exercises_tab_main_layout.addWidget(self.load_exercises_button)
        self.exercises_tab_main_layout.addWidget(QHSeparationLine(line_width=3))
        self.exercises_tab_main_layout.addWidget(self.exercises_tab_exercises_widget)

        self.exercises_tab_widget = QWidget()
        self.exercises_tab_widget.setLayout(self.exercises_tab_main_layout)

        self.exercises_tab_scroll_area = QScrollArea()
        self.exercises_tab_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.exercises_tab_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.exercises_tab_scroll_area.setWidgetResizable(True)
        self.exercises_tab_scroll_area.setWidget(self.exercises_tab_widget)

        self.exercises_tab = self.tab_widget.addTab(self.exercises_tab_scroll_area, 'Exercises')

        # ----------
        # main layout
        # ----------

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.menu_bar)
        self.main_layout.addWidget(self.tab_widget)

        # dummy widget for setCentralWidget
        self.dummy_widget = QWidget()
        self.dummy_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.dummy_widget)

        # ----------
        # load mails
        # ----------

        # immediately load the mails because it is quick and handy
        self.load_mails()

    def show_about_dialogue(self) -> None:
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    def compose_mail(self):
        if not self.compose_mail_window:
            if not self._mail_transmitter:
                # create mail receiver if not exists
                self._mail_transmitter = mail.Transmitter(self._iserv_username, self._iserv_password)

            self.compose_mail_window = ComposeMailWindow(self._mail_transmitter)

        self.compose_mail_window.empty_inputs()
        self.compose_mail_window.show()

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

            # horizontal separation line
            self.mails_tab_mails_layout.addWidget(QHSeparationLine(line_width=1))
            # add widgets to the mail tab
            self.mails_tab_mails_layout.addWidget(mail_mail_widget)
            # horizontal separation line
            self.mails_tab_mails_layout.addWidget(QHSeparationLine(line_width=1))

            # for accessing the right mail id
            i += 1

        # load mails button
        self.load_mails_button.setText('Reload mails')
        self.load_mails_button.setDisabled(False)

    def display_exercise(self, exercise: webdriver.element.Exercise) -> None:
        if not self.display_exercise_window:
            self.display_exercise_window = DisplayExerciseWindow(self._webdriver_session)

        self.display_exercise_window.display_exercise(exercise)
        self.display_exercise_window.show()

    def load_exercises(self) -> None:
        # load exercise button
        self.load_exercises_button.setText('Loading exercises...')
        self.load_exercises_button.setDisabled(True)

        if not self._webdriver_session:
            # create webdriver session if not exists
            self._webdriver_session = webdriver.Session(self._iserv_username, self._iserv_password)

        # remove all widgets from the layout
        util.clear_layout(self.exercises_tab_exercises_layout)

        exercises = []
        try:
            exercises = self._webdriver_session.fetch_all_exercises()
        except Exception as exception:
            logger.exception(exception)

        if not exercises:
            self.exercises_tab_exercises_layout.addWidget(QLabel(
                'Currently, there are no exercises pending. Lucky You.'
            ))

        for exercise in exercises:
            exercises_title_label = QLabel(exercise.title)

            if exercise.unseen:
                exercises_title_label.setStyleSheet('QLabel { color: red; font-weight: bold }')
            elif exercise.completed:
                exercises_title_label.setStyleSheet('QLabel { color: green; font-weight: bold }')
            else:
                exercises_title_label.setStyleSheet('QLabel { font-weight: bold }')

            exercise_owner_label = QLabel(exercise.owner)
            exercise_owner_label.setStyleSheet('QLabel { color: grey; }')

            exercise_data_layout = QVBoxLayout()
            exercise_data_layout.addWidget(exercises_title_label)
            exercise_data_layout.addWidget(exercise_owner_label)

            exercise_data_widget = QWidget()
            exercise_data_widget.setLayout(exercise_data_layout)

            display_exercise_button = QPushButton('Display')
            display_exercise_button.clicked.connect(
                lambda state, display_exercise=exercise: self.display_exercise(
                    display_exercise
                )
            )
            display_exercise_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

            exercise_exercise_layout = QHBoxLayout()
            exercise_exercise_layout.addWidget(exercise_data_widget)
            exercise_exercise_layout.addWidget(display_exercise_button)

            exercise_exercise_widget = QWidget()
            exercise_exercise_widget.setSizePolicy(
                QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            exercise_exercise_widget.setLayout(exercise_exercise_layout)

            # horizontal separation line
            self.exercises_tab_exercises_layout.addWidget(QHSeparationLine(line_width=1))
            # add widgets to the mail tab
            self.exercises_tab_exercises_layout.addWidget(exercise_exercise_widget)
            # horizontal separation line
            self.exercises_tab_exercises_layout.addWidget(QHSeparationLine(line_width=1))

        # load exercise button
        self.load_exercises_button.setText('Reload exercises')
        self.load_exercises_button.setDisabled(False)

    def shutdown(self) -> None:
        # log out and close connections
        if self._mail_receiver:
            self._mail_receiver.shutdown()
        if self._mail_transmitter:
            self._mail_transmitter.shutdown()

        if self._webdriver_session:
            self._webdriver_session.shutdown()

        # write size and position of the window to the config file
        config['position']['x'] = str(self.x())
        config['position']['y'] = str(self.y())
        config['size']['w'] = str(self.width())
        config['size']['h'] = str(self.height())

        with open('./app/config/MainWindow.ini', 'w', encoding='utf-8') as config_file:
            config.write(config_file)

    def close(self) -> None:
        super().close()

        # log out, close connections and close the app if this window is closed
        self.shutdown()
