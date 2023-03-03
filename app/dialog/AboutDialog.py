import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDialog, QDialogButtonBox, QLabel

from app.QtExt.QSeparationLine import QHSeparationLine

from version import __version__, __version_description__, __author__


# ----------
# logging
# ----------


logger = logging.getLogger(__name__)


# ----------
# AboutDialog
# ----------


class AboutDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        
        self.setWindowTitle('About IScrA - IServ Scraping Automations')

        # ----------
        # close dialog buttons
        # ----------
        self.close_button = QDialogButtonBox.StandardButton.Close

        # button box
        self.button_box = QDialogButtonBox(self.close_button)
        self.button_box.setCenterButtons(True)
        self.button_box.clicked.connect(self.accept)

        # ----------
        # description aka. actual content
        # ----------

        # version
        self.version_header_label = QLabel('Version: ')
        self.version_header_label.setStyleSheet('QLabel { font-weight: bold; }')

        self.version_description_label = QLabel(f'{".".join(__version__)} | {" ".join(__version_description__)}')

        self.version_layout = QHBoxLayout()
        self.version_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_layout.addWidget(self.version_header_label)
        self.version_layout.addWidget(self.version_description_label)

        self.version_widget = QWidget()
        self.version_widget.setLayout(self.version_layout)

        # author
        self.author_header_label = QLabel('Author: ')
        self.author_header_label.setStyleSheet('QLabel { font-weight: bold; }')

        self.author_description_label = QLabel('Henrik Stirner')

        self.author_layout = QHBoxLayout()
        self.author_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.author_layout.addWidget(self.author_header_label)
        self.author_layout.addWidget(self.author_description_label)

        self.author_widget = QWidget()
        self.author_widget.setLayout(self.author_layout)

        # main layout
        self.description_layout = QVBoxLayout()
        self.description_layout.addWidget(self.author_widget)
        self.description_layout.addWidget(self.version_widget)

        self.description_widget = QWidget()
        self.description_widget.setLayout(self.description_layout)

        # ----------
        # main layout
        # ----------
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(QHSeparationLine(line_width=1))
        self.layout.addWidget(self.description_widget)
        self.layout.addWidget(QHSeparationLine(line_width=1))
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)
