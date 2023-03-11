import logging

from PyQt6.QtCore import Qt, QObject, QThreadPool, QRunnable, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QLabel, QPushButton, QLineEdit, QSizePolicy, QComboBox, QCheckBox,
    QSpinBox
)

from app.QtExt import util
from app.QtExt.QSeparationLine import QVSeparationLine, QHSeparationLine

from app.window.DisplayMailWindow import DisplayMailWindow
from app.window.ComposeMailWindow import ComposeMailWindow
from app.window.MailScheduleWindow import MailScheduleWindow

import mail


# ----------
# logging
# ----------


logger = logging.getLogger(__name__)


# ----------
# Mail Loader
# ----------


class MailLoaderSignals(QObject):
    mail_loaded = pyqtSignal(str, str, str, str)
    finished = pyqtSignal()


class MailLoader(QRunnable):
    def __init__(self, mail_receiver: mail.Receiver, selection: str, unread_only: bool, maximum_mail_amount: int
                 ) -> None:
        super().__init__()

        self.signals = MailLoaderSignals()

        self._mail_receiver = mail_receiver
        self._selection = selection
        self._unread_only = unread_only
        self._maximum_mail_amount = maximum_mail_amount

    def run(self) -> None:
        if self._unread_only:
            selection, mail_ids = self._mail_receiver.get_ids_of_unread_mails(
                selection=self._selection,
                max_amount=self._maximum_mail_amount
            )
        else:
            selection, mail_ids = self._mail_receiver.get_ids_of_mails(
                selection=self._selection,
                max_amount=self._maximum_mail_amount
            )

        # if there are no mails to display
        if not mail_ids:
            return

        # there are unread mails, add the new widgets
        for mail_id in mail_ids:
            subject, from_sender = self._mail_receiver.minimal_mail_data_by_id(
                selection=self._selection, mail_id=mail_id
            )

            self.signals.mail_loaded.emit(
                self._selection,
                mail_id,
                subject,
                from_sender
            )

        self.signals.finished.emit()


# ----------
# MailsTab
# ----------

class MailsTab(QScrollArea):
    def __init__(self, iserv_username: str, iserv_password: str):
        super().__init__()

        # ----------
        # IServ
        # ----------

        self._iserv_username = iserv_username
        self._iserv_password = iserv_password

        # this is not too expensive, so it can be executed by the Main Thread without the window freezing
        self._mail_receiver = mail.Receiver(self._iserv_username, self._iserv_password)
        self._mail_transmitter = None

        # if we do not keep a reference to our windows, they will be closed immediately
        self.display_mail_window = None
        self.compose_mail_window = None
        self.edit_mail_schedule_window = None

        # ----------
        # actual layout
        # ----------

        self.mail_selection_combo_box = QComboBox()
        self.mail_selection_combo_box.addItems(
            [element[2] for element in self._mail_receiver.get_available_mailboxes()])
        self.mail_selection_combo_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.unread_only_check_box = QCheckBox('Unread only')
        self.unread_only_check_box.setChecked(True)
        self.unread_only_check_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.max_amount_spin_box = QSpinBox()
        self.max_amount_spin_box.setRange(1, 999999999)
        self.max_amount_spin_box.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.max_amount_spin_box.setEnabled(False)

        self.max_amount_check_box = QCheckBox('Max amount')
        self.max_amount_check_box.setChecked(False)
        self.max_amount_check_box.clicked.connect(
            lambda state: self.max_amount_spin_box.setEnabled(self.max_amount_check_box.isChecked()))
        self.max_amount_check_box.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.mail_selection_layout = QHBoxLayout()
        self.mail_selection_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mail_selection_layout.addWidget(self.mail_selection_combo_box)
        self.mail_selection_layout.addWidget(QVSeparationLine(line_width=1))
        self.mail_selection_layout.addWidget(self.unread_only_check_box)
        self.mail_selection_layout.addWidget(QVSeparationLine(line_width=1))
        self.mail_selection_layout.addWidget(self.max_amount_check_box)
        self.mail_selection_layout.addWidget(self.max_amount_spin_box)

        self.mail_selection_widget = QWidget()
        self.mail_selection_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.mail_selection_widget.setLayout(self.mail_selection_layout)

        self.load_mails_button = QPushButton('Load mails')
        self.load_mails_button.clicked.connect(self.load_mails)

        self.compose_mail_button = QPushButton('Compose new mail')
        self.compose_mail_button.clicked.connect(self.compose_mail)

        self.edit_mail_schedule_button = QPushButton('Edit mail schedule')
        self.edit_mail_schedule_button.clicked.connect(self.edit_mail_schedule)

        self.filter_mails_header = QLabel('Filter: ')
        self.filter_mails_header.setStyleSheet('QLabel { font-weight: bold; }')
        self.filter_mails_header.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.filter_mails_entry = QLineEdit()
        self.filter_mails_entry.setPlaceholderText('prompt')
        self.filter_mails_entry.textChanged.connect(self.filter_mails)
        self.filter_mails_entry.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)

        # self.execute_filter_mails_button = QPushButton('Apply Filter')
        # self.execute_filter_mails_button.clicked.connect(self.filter_mails)
        # self.execute_filter_mails_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.filter_mails_layout = QHBoxLayout()
        self.filter_mails_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.filter_mails_layout.addWidget(self.filter_mails_header)
        self.filter_mails_layout.addWidget(self.filter_mails_entry)
        # self.filter_mails_layout.addWidget(self.execute_filter_mails_button)

        self.filter_mails_widget = QWidget()
        self.filter_mails_widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        self.filter_mails_widget.setLayout(self.filter_mails_layout)

        self.mails_tab_mails_layout = QVBoxLayout()
        self.mails_tab_mails_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.mails_tab_mails_widget = QWidget()
        self.mails_tab_mails_widget.setLayout(self.mails_tab_mails_layout)

        self.mails_tab_main_layout = QVBoxLayout()
        self.mails_tab_main_layout.addWidget(self.mail_selection_widget)
        self.mails_tab_main_layout.addWidget(self.load_mails_button)
        self.mails_tab_main_layout.addWidget(self.compose_mail_button)
        self.mails_tab_main_layout.addWidget(self.edit_mail_schedule_button)
        self.mails_tab_main_layout.addWidget(QHSeparationLine(line_width=3))
        self.mails_tab_main_layout.addWidget(self.filter_mails_widget)
        self.mails_tab_main_layout.addWidget(self.mails_tab_mails_widget)

        self.mails_tab_widget = QWidget()
        self.mails_tab_widget.setLayout(self.mails_tab_main_layout)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        self.setWidget(self.mails_tab_widget)

        # ----------
        # load mails
        # ----------

        # immediately load the mails because it is quick and handy
        self.load_mails()

    def display_mail(self, selection: str, mail_id: int | str) -> None:
        if not self.display_mail_window:
            self.display_mail_window = DisplayMailWindow(self._mail_receiver)

        self.display_mail_window.display_mail(selection, mail_id)
        self.display_mail_window.show()

    @pyqtSlot()
    def toggle_load_mails_button_loading_state(self) -> None:
        if self.load_mails_button.isEnabled():
            self.load_mails_button.setText('Loading mails...')
            self.load_mails_button.setEnabled(False)
        else:
            self.load_mails_button.setText('Reload mails')
            self.load_mails_button.setEnabled(True)

    @pyqtSlot(str, str, str, str)
    def append_loaded_mail_to_layout(self, selection: str, mail_id: int | str, subject: str, from_sender: str) -> None:
        # widget with vertical layout containing labels with mail specific data
        mail_subject_label = QLabel(subject)
        mail_subject_label.setStyleSheet('QLabel { font-weight: bold }')

        mail_from_user_label = QLabel(from_sender)
        mail_from_user_label.setStyleSheet('QLabel { color: darkgrey }')

        mail_data_layout = QVBoxLayout()
        mail_data_layout.addWidget(mail_subject_label)
        mail_data_layout.addWidget(mail_from_user_label)

        mail_data_widget = QWidget()
        mail_data_widget.setLayout(mail_data_layout)

        # widget with horizontal layout containing the mail data widget and a button for displaying the mail
        display_mail_button = QPushButton('Display')
        display_mail_button.clicked.connect(
            lambda state, display_mail_selection=selection, display_mail_id=mail_id: self.display_mail(
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

        mail_main_layout = QVBoxLayout()
        mail_main_layout.addWidget(QHSeparationLine(line_width=1))
        mail_main_layout.addWidget(mail_mail_widget)
        mail_main_layout.addWidget(QHSeparationLine(line_width=1))

        mail_main_widget = QWidget()
        mail_main_widget.setLayout(mail_main_layout)

        self.mails_tab_mails_layout.addWidget(mail_main_widget)

    def load_mails(self) -> None:
        self.toggle_load_mails_button_loading_state()  # load mails button
        self.filter_mails_widget.setEnabled(False)
        util.clear_layout(self.mails_tab_mails_layout)

        # load data
        mail_loader = MailLoader(
            self._mail_receiver,
            self.mail_selection_combo_box.currentText(),
            self.unread_only_check_box.isChecked(),
            self.max_amount_spin_box.value() if self.max_amount_check_box.isChecked() else None
        )
        mail_loader.signals.mail_loaded.connect(self.append_loaded_mail_to_layout)
        # pressing a display mail button would crash the receiver
        mail_loader.signals.mail_loaded.connect(lambda: self.mails_tab_mails_widget.setEnabled(False))

        mail_loader.signals.finished.connect(self.toggle_load_mails_button_loading_state)  # load mails button
        mail_loader.signals.finished.connect(lambda: self.mails_tab_mails_widget.setEnabled(True))
        mail_loader.signals.finished.connect(lambda: self.filter_mails_widget.setEnabled(True))

        QThreadPool.globalInstance().start(mail_loader)

    def compose_mail(self) -> None:
        if not self.compose_mail_window:
            if not self._mail_transmitter:
                # create mail receiver if not exists
                self._mail_transmitter = mail.Transmitter(self._iserv_username, self._iserv_password)

            self.compose_mail_window = ComposeMailWindow(self._mail_transmitter)

        self.compose_mail_window.empty_inputs()
        self.compose_mail_window.show()

    def edit_mail_schedule(self) -> None:
        if not self.edit_mail_schedule_window:
            self.edit_mail_schedule_window = MailScheduleWindow()

        self.edit_mail_schedule_window.load_mail_schedule()
        self.edit_mail_schedule_window.show()

    def filter_mails(self) -> None:
        prompt = self.filter_mails_entry.text().lower()

        for i in range(self.mails_tab_mails_layout.count()):
            child = self.mails_tab_mails_layout.itemAt(i).widget()

            if not isinstance(child, QWidget):
                # skip
                continue

            if prompt not in util.get_text_of_child_labels(child).lower():
                # hide
                child.hide()
            elif child.isHidden():
                # show
                child.show()

    def shutdown(self) -> None:
        # close sub-windows
        if self.display_mail_window:
            self.display_mail_window.close()

        if self.compose_mail_window:
            self.compose_mail_window.close()

        if self.edit_mail_schedule_window:
            self.compose_mail_window.close()

        # log out and close connections
        if self._mail_receiver:
            self._mail_receiver.shutdown()
        if self._mail_transmitter:
            self._mail_transmitter.shutdown()

    def close(self) -> None:
        # log out and close connections
        self.shutdown()

        super().close()
