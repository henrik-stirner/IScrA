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
# text module
# ----------


class TextModule(ModuleBase):
    """represents an IServ text module"""
    def __init__(self, webdriver: WebDriver, module_name: str = 'text', timeout: float = 5.0
                 ) -> None:
        super().__init__(webdriver, module_name, timeout)

        self.remote_text_locations = None

        self._load()

    def _load(self) -> None:
        """fetches important data of a text module from the corresponding IServ page"""
        self._webdriver.get(self.remote_location)

        text_table = WebDriverWait(self._webdriver, self._timeout).until(
            expected_conditions.presence_of_element_located((By.TAG_NAME, 'tbody')))
        text_table_rows = text_table.find_elements(By.TAG_NAME, 'tr')

        self.remote_text_locations = {}
        for text_table_row in text_table_rows:
            try:
                text_link = text_table_row.find_element(By.XPATH, './td[2]/a')
                # name: remote_location
                self.remote_text_locations[text_link.text] = text_link.get_attribute('href')
            except Exception as exception:
                logger.info(exception)
