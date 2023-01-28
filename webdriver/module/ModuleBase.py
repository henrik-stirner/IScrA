import logging
from configparser import ConfigParser

from selenium.webdriver.firefox.webdriver import WebDriver

from webdriver.Session import Session


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
# module base class
# ----------

class ModuleBase:
    """
    base class for all modules

    modules save their session and webdriver as attributes; elements do not
    -> different Sessions can work with the same elements, compare them, and so on
    -> each module should be present in each session only once, because for each IServ user each module exists only once
    """
    def __init__(self, session: Session, webdriver: WebDriver, module_name: str) -> None:
        self.name = module_name

        self._session = session
        self._session.navigate_to_module(self.name)

        self._webdriver = webdriver
