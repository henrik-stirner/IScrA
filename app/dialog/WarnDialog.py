import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QDialog, QDialogButtonBox, QLabel

from app.QtExt.QSeparationLine import QHSeparationLine


# ----------
# logging
# ----------


logger = logging.getLogger(__name__)


# ----------
# AboutDialog
# ----------


class WarnDialog(QDialog):
    def __init__(self, parent, title: str, description: str, caption: str = 'Warning') -> None:
        super().__init__(parent)

        self.setWindowTitle(caption)

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

        # actual warning (message)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet('QLabel { color: red; font-weight: bold; }')
        self.description_label = QLabel(description)

        # ----------
        # main layout
        # ----------
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(QHSeparationLine(line_width=1))
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.description_label)
        self.layout.addWidget(QHSeparationLine(line_width=1))
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)
