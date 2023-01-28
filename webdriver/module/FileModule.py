import logging
from configparser import ConfigParser

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, WebDriverException

from webdriver.Session import Session

from webdriver.module.ModuleBase import ModuleBase
from webdriver.element.File import File


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
# file module
# ----------

class FileModule(ModuleBase):
    """represents an IServ file module"""
    def __init__(self, session: Session, webdriver: WebDriver, module_name: str = 'file') -> None:
        super().__init__(session, webdriver, module_name)
