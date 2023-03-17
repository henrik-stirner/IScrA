import logging
from configparser import ConfigParser

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from webdriver.module.ModuleBase import ModuleBase


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
    def __init__(self, webdriver: WebDriver, module_name: str = 'exercise', timeout: float = 5.0
                 ) -> None:
        super().__init__(webdriver, module_name, timeout)

        self.remote_exercise_locations = None

        self._load()

    def _load(self) -> None:
        """fetches important data of an exercise module from the corresponding IServ page"""
        self._webdriver.get(self.remote_location)

        exercise_table = WebDriverWait(self._webdriver, self._timeout).until(
            expected_conditions.presence_of_element_located((By.TAG_NAME, 'tbody')))
        exercise_table_rows = exercise_table.find_elements(By.XPATH, '//tr[@class!="group success"]')

        exercise_link_relative_path = './td[2]/a' if self.remote_location.endswith('/past/exercise') else './td[1]/a'

        self.remote_exercise_locations = {}
        for exercise_table_row in exercise_table_rows:
            exercise_link = exercise_table_row.find_element(By.XPATH, exercise_link_relative_path)
            # name: remote_location
            self.remote_exercise_locations[exercise_link.text] = exercise_link.get_attribute('href')
