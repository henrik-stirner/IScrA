import logging
from configparser import ConfigParser

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, WebDriverException

from webdriver.Session import Session

from webdriver.module.ModuleBase import ModuleBase
from webdriver.element.MessengerRoom import MessengerRoom


# ----------
# logger
# ----------


logger = logging.getLogger(__name__)


# ----------
# config
# ----------


config = ConfigParser()
config.read('config.ini', encoding='utf-8')


# ----------
# messenger room module
# ----------

class MessengerModule(ModuleBase):
    """represents an IServ messenger module"""
    def __init__(self, session: Session, webdriver: WebDriver, module_name: str = 'messenger') -> None:
        super().__init__(session, webdriver, module_name)

        self.remote_messenger_room_locations = None

    def _load(self) -> None:
        """fetches important data of a messenger module from the corresponding IServ page"""
        # TODO
        self.remote_messenger_room_locations = None
