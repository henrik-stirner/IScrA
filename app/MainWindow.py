import logging
from configparser import ConfigParser

import os

from PyQt6.QtCore import QObject, QThreadPool, QRunnable, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QMenuBar, QTabWidget, QStyle
)

from app.tab import MailsTab
from app.tab import ExercisesTab
from app.tab import TextsTab

from app.dialog.AboutDialog import AboutDialog

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
# Webdriver Launcher
# ----------


class WebdriverLauncherSignals(QObject):
    webdriver_launched = pyqtSignal(webdriver.Session)


class WebdriverLauncher(QRunnable):
    def __init__(self, iserv_username: str, iserv_password: str) -> None:
        super().__init__()

        self.signals = WebdriverLauncherSignals()

        self._iserv_username = iserv_username
        self._iserv_password = iserv_password

    def run(self) -> None:
        webdriver_session = webdriver.Session(self._iserv_username, self._iserv_password)
        self.signals.webdriver_launched.emit(webdriver_session)


# ----------
# MainWindow
# ----------


class MainWindow(QMainWindow):
    def __init__(self, iserv_username: str, iserv_password: str) -> None:
        super().__init__()

        # ----------
        # application settings
        # ----------

        self.setWindowTitle('IScrA - Mails')

        # window icon
        self.setWindowIcon(QIcon('./assets/icon/iscra.ico'))

        # stylesheet
        QApplication.instance().setStyleSheet(f'file:///./app/style/{config["settings"]["stylesheet"]}')
        # QApplication.instance().setStyle('Windows')  # does not look that good to me

        # shutdown
        QApplication.instance().aboutToQuit.connect(self.shutdown)

        # ----------
        # IServ
        # ----------

        self._iserv_username = iserv_username
        self._iserv_password = iserv_password

        # this wille be used by multiple modules and should only exist once, so it is defined here
        self._webdriver_session = None

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
        
        if int(config['view']['full screen']):
            self.showFullScreen()
        elif int(config['view']['maximized']):
            self.showMaximized()
        elif int(config['view']['minimized']):
            self.showMinimized()

        # ----------
        # actions
        # ----------

        self.exit_action = QAction(QIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarCloseButton)), '&Exit', self)
        self.exit_action.setStatusTip('Closes the application')
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.triggered.connect(QApplication.instance().exit)

        self.show_full_screen_action = QAction(QIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarMaxButton)), '&Full &screen', self)
        self.show_full_screen_action.setStatusTip('Toggles full screen mode')
        self.show_full_screen_action.setShortcut('F11')
        self.show_full_screen_action.triggered.connect(
            lambda state: self.showFullScreen() if not self.isFullScreen() else self.showNormal())

        self.show_maximized_action = QAction(QIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarNormalButton)), '&Maximize', self)
        self.show_maximized_action.setStatusTip('Toggles maximized mode')
        self.show_maximized_action.setShortcut('Alt++')
        self.show_maximized_action.triggered.connect(
            lambda state: self.showMaximized() if not self.isMaximized() else self.showNormal())

        self.show_minimized_action = QAction(QIcon(self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarMinButton)), '&Minimize', self)
        self.show_minimized_action.setStatusTip('Toggles minimized mode')
        self.show_minimized_action.setShortcut('Alt+-')
        self.show_minimized_action.triggered.connect(
            lambda state: self.showMinimized() if not self.isMaximized() else self.showNormal())

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
        self.app_menu.addAction(
            self.exit_action
        )

        # settings menu
        self.settings_menu = self.menu_bar.addMenu('&Settings')
        self.style_menu = self.settings_menu.addMenu('&Style')

        self.set_style_actions = []
        for file in os.listdir('./app/style/'):
            if not file.endswith('.qss'):
                continue

            set_style_action = QAction(f'&{file.removesuffix(".qss")}', self)
            set_style_action.setStatusTip(f'Sets the applications style sheet to <{file}>')
            set_style_action.triggered.connect(
                lambda state, stylesheet=file: self._set_stylesheet(stylesheet=stylesheet)
            )

            self.set_style_actions.append(set_style_action)

        self.style_menu.addActions(self.set_style_actions)

        # view menu
        self.view_menu = self.menu_bar.addMenu('&View')
        self.view_menu.addActions([
            self.show_full_screen_action,
            self.show_maximized_action,
            self.show_minimized_action
        ])

        # help menu
        self.help_menu = self.menu_bar.addMenu('&Help')
        self.help_menu.addAction(
            self.about_action
        )

        # ----------
        # tab widget
        # ----------

        self.tab_widget = QTabWidget(self)
        self.tab_widget.currentChanged.connect(lambda current_index: self.setWindowTitle(
            f'IScrA - {self.tab_widget.tabText(current_index)}'))

        # mails tab
        self.mails_tab = MailsTab(self._iserv_username, self._iserv_password)
        self.tab_bar_mails_tab = self.tab_widget.addTab(self.mails_tab, 'Mails')

        # exercises tab
        self.exercises_tab = ExercisesTab(self)
        self.tab_bar_exercises_tab = self.tab_widget.addTab(self.exercises_tab, 'Exercises')

        # texts tab
        self.texts_tab = TextsTab(self)
        self.tab_bar_texts_tab = self.tab_widget.addTab(self.texts_tab, 'Texts')

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
    
    def showFullScreen(self) -> None:
        super().showFullScreen()
        
        config['view']['full screen'] = '1'
        config['view']['maximized'] = '0'
        config['view']['minimized'] = '0'
    
    def showMaximized(self) -> None:
        super().showMaximized()
        
        config['view']['full screen'] = '0'
        config['view']['maximized'] = '1'
        config['view']['minimized'] = '0'
    
    def showMinimized(self) -> None:
        super().showMinimized()
        
        config['view']['full screen'] = '0'
        config['view']['maximized'] = '0'
        config['view']['minimized'] = '1'

    @staticmethod
    def _set_stylesheet(stylesheet: str):
        QApplication.instance().setStyleSheet(f'file:///./app/style/{stylesheet}')
        config['settings']['stylesheet'] = stylesheet

    @pyqtSlot()
    def show_about_dialogue(self) -> None:
        about_dialog = AboutDialog(self)
        about_dialog.exec()

    @pyqtSlot(webdriver.Session)
    def _set_webdriver_session(self, new_webdriver_session: webdriver.Session) -> None:
        self._webdriver_session = new_webdriver_session

    def get_webdriver_session(self) -> tuple[webdriver.Session | None, pyqtSignal | None]:
        if not self._webdriver_session:
            webdriver_launcher = WebdriverLauncher(
                self._iserv_username,
                self._iserv_password
            )
            webdriver_launcher.signals.webdriver_launched.connect(self._set_webdriver_session)

            QThreadPool.globalInstance().start(webdriver_launcher)

            return None, webdriver_launcher.signals.webdriver_launched

        return self._webdriver_session, None

    def shutdown(self) -> None:
        # log out and close connections; close sub-windows
        self.mails_tab.shutdown()
        self.exercises_tab.shutdown()
        self.texts_tab.shutdown()

        if self._webdriver_session:
            self._webdriver_session.shutdown()

        # write size and position of the window to the config file
        screen_resolution = QApplication.instance().primaryScreen().availableGeometry()
        screen_width, screen_height = screen_resolution.width(), screen_resolution.height()

        config['position']['x'] = str(self.x()) if self.x() >= 0 else '0'  # to make sure the window appears on screen
        config['position']['y'] = str(self.y()) if self.y() >= 0 else '0'  # ^^^
        config['size']['w'] = str(self.width()) if self.width() <= screen_width - self.x() else str(
            screen_width - self.x())
        config['size']['h'] = str(self.height()) if self.height() <= screen_height - self.y() else str(
            screen_height - self.y())

        config['view']['full screen'] = '1' if self.isFullScreen() else '0'
        config['view']['maximized'] = '1' if self.isMaximized() else '0'
        config['view']['minimized'] = '1' if self.isMinimized() else '0'

        with open('./app/config/MainWindow.ini', 'w', encoding='utf-8') as config_file:
            config.write(config_file)

    def close(self) -> None:
        # log out, close connections and close the app if this window is closed
        self.shutdown()

        super().close()
