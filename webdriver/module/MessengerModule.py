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
# messenger room module
# ----------


class MessengerModule(ModuleBase):
    """represents an IServ messenger module"""
    def __init__(self, webdriver: WebDriver, module_name: str = 'messenger', timeout: float = 5.0
                 ) -> None:
        super().__init__(webdriver, module_name, timeout)

        self.remote_messenger_room_locations = None

        self._load()

    def _load(self) -> None:
        """fetches important data of a messenger module from the corresponding IServ page"""
        self._webdriver.get(self.remote_location)

        messenger_room_buttons = WebDriverWait(self._webdriver, self._timeout).until(
            expected_conditions.presence_of_all_elements_located((
                By.XPATH, '//div[contains(@class, "chat-select-button")]')))

        self.remote_messenger_room_locations = {}
        for messenger_room_button in messenger_room_buttons:
            messenger_room_button.click()
            # name = remote_location
            self.remote_messenger_room_locations[
                messenger_room_button.find_element(By.XPATH, './div[2]/div[1]/b').text
            ] = self._webdriver.current_url
