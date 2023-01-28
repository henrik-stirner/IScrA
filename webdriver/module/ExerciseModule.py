import logging
from configparser import ConfigParser

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, WebDriverException

from webdriver.Session import Session

from webdriver.module.ModuleBase import ModuleBase
from webdriver.element.Exercise import Exercise


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
# exercise module
# ----------

class ExerciseModule(ModuleBase):
    """represents an IServ exercise module"""
    def __init__(self, session: Session, webdriver: WebDriver, module_name: str = 'exercise') -> None:
        super().__init__(session, webdriver, module_name)

        self.remote_exercise_locations = None

        self._load()

    def _load(self) -> None:
        """fetches important data of an exercise module from the corresponding IServ page"""
        # TODO
        self.remote_exercise_locations = None
