import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QLabel, QPushButton, QSizePolicy
)

from app.QtExt import util
from app.QtExt.QSeparationLine import QHSeparationLine

from app.window.DisplayExerciseWindow import DisplayExerciseWindow

import webdriver


# ----------
# logging
# ----------


logger = logging.getLogger(__name__)


# ----------
# ExercisesTab
# ----------

class ExercisesTab(QScrollArea):
    def __init__(self, parent):
        super().__init__()

        # ----------
        # IServ
        # ----------

        # for accessing a shared webdriver session
        self._parent = parent

        # if we do not keep a reference to our windows, they will be closed immediately
        self.display_exercise_window = None

        # ----------
        # actual layout
        # ----------

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

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        self.setWidget(self.exercises_tab_widget)

    def display_exercise(self, exercise: webdriver.element.Exercise) -> None:
        if not self.display_exercise_window:
            self.display_exercise_window = DisplayExerciseWindow(self._parent.get_webdriver_session())

        self.display_exercise_window.display_exercise(exercise)
        self.display_exercise_window.show()

    def load_exercises(self) -> None:
        # load exercise button
        self.load_exercises_button.setText('Loading exercises...')
        self.load_exercises_button.setDisabled(True)

        # remove all widgets from the layout
        util.clear_layout(self.exercises_tab_exercises_layout)

        exercises = []
        try:
            exercises = self._parent.get_webdriver_session().fetch_all_exercises()
        except Exception as exception:
            logger.exception(exception)

        if not exercises:
            self.exercises_tab_exercises_layout.addWidget(QLabel(
                'Currently, there are no exercises pending for you.'
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
        # close sub-windows
        if self.display_exercise_window:
            self.display_exercise_window.close()

        # log out and close connections
        pass

    def close(self) -> None:
        super().close()

        # log out and close connections
        self.shutdown()