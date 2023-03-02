import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QLabel, QPushButton, QSizePolicy
)

from app.QtExt import util
from app.QtExt.QSeparationLine import QHSeparationLine

from app.window.DisplayTextWindow import DisplayTextWindow

import webdriver


# ----------
# logging
# ----------


logger = logging.getLogger(__name__)


# ----------
# TextsTab
# ----------

class TextsTab(QScrollArea):
    def __init__(self, parent):
        super().__init__()

        # ----------
        # IServ
        # ----------

        # for accessing a shared webdriver session
        self._parent = parent

        # if we do not keep a reference to our windows, they will be closed immediately
        self.display_text_window = None

        # ----------
        # actual layout
        # ----------

        self.load_texts_button = QPushButton('Load texts')
        self.load_texts_button.clicked.connect(self.load_texts)

        self.texts_tab_texts_layout = QVBoxLayout()
        self.texts_tab_texts_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.texts_tab_texts_widget = QWidget()
        self.texts_tab_texts_widget.setLayout(self.texts_tab_texts_layout)

        self.texts_tab_main_layout = QVBoxLayout()
        self.texts_tab_main_layout.addWidget(self.load_texts_button)
        self.texts_tab_main_layout.addWidget(QHSeparationLine(line_width=3))
        self.texts_tab_main_layout.addWidget(self.texts_tab_texts_widget)

        self.texts_tab_widget = QWidget()
        self.texts_tab_widget.setLayout(self.texts_tab_main_layout)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        self.setWidget(self.texts_tab_widget)

    def display_text(self, text: webdriver.element.Text) -> None:
        if not self.display_text_window:
            self.display_text_window = DisplayTextWindow(self._parent.get_webdriver_session())

        self.display_text_window.display_text(text)
        self.display_text_window.show()

    def load_texts(self) -> None:
        # load exercise button
        self.load_texts_button.setText('Loading texts...')
        self.load_texts_button.setDisabled(True)

        # remove all widgets from the layout
        util.clear_layout(self.texts_tab_texts_layout)

        texts = []
        try:
            texts = self._parent.get_webdriver_session().fetch_all_texts()
        except Exception as exception:
            logger.exception(exception)

        if not texts:
            self.texts_tab_texts_layout.addWidget(QLabel(
                'Currently, you do not have access to any texts.'
            ))

        for text in texts:
            texts_title_label = QLabel(text.title)
            texts_title_label.setStyleSheet('QLabel { font-weight: bold }')

            text_owner_label = QLabel(text.owner)
            text_owner_label.setStyleSheet('QLabel { color: grey; }')

            text_data_layout = QVBoxLayout()
            text_data_layout.addWidget(texts_title_label)
            text_data_layout.addWidget(text_owner_label)

            text_data_widget = QWidget()
            text_data_widget.setLayout(text_data_layout)

            display_text_button = QPushButton('Display')
            display_text_button.clicked.connect(
                lambda state, display_text=text: self.display_text(
                    display_text
                )
            )
            display_text_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

            text_text_layout = QHBoxLayout()
            text_text_layout.addWidget(text_data_widget)
            text_text_layout.addWidget(display_text_button)

            text_text_widget = QWidget()
            text_text_widget.setSizePolicy(
                QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            text_text_widget.setLayout(text_text_layout)

            # horizontal separation line
            self.texts_tab_texts_layout.addWidget(QHSeparationLine(line_width=1))
            # add widgets to the mail tab
            self.texts_tab_texts_layout.addWidget(text_text_widget)
            # horizontal separation line
            self.texts_tab_texts_layout.addWidget(QHSeparationLine(line_width=1))

        # load exercise button
        self.load_texts_button.setText('Reload texts')
        self.load_texts_button.setDisabled(False)

    def shutdown(self) -> None:
        # close sub-windows
        if self.display_text_window:
            self.display_text_window.close()

        # log out and close connections
        pass

    def close(self) -> None:
        super().close()

        # log out and close connections
        self.shutdown()
