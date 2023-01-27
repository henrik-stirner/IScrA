import logging

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, WebDriverException

from datetime import datetime

# ----------
# logger
# ----------


logger = logging.getLogger(__name__)


# ----------
# messenger room
# ----------


class MessengerRoom:
    """represents an IServ messenger room"""
    def __init__(self, remote_location: str, webdriver: WebDriver, timeout: float = 5.0) -> None:
        self._timeout = timeout

        self.remote_location = None
        self.token = None

        self.owner = None

        self.is_group = None
        self.members = None

        self.name = None

        self.last_use_date = None

        self._load(remote_location, webdriver)

    def _load(self, remote_location: str, webdriver: WebDriver) -> None:
        """fetches the data of a messenger room from the corresponding IServ page"""
        self.remote_location = remote_location
        self.token = remote_location.split('/')[-1]

        # TODO

        pass

    def fetch_messages(self, webdriver: WebDriver, number_of_messages: int) -> list:
        """fetches the last number_of_messages that have been sent in a messenger room"""
        # TODO
        pass

    def send_message(self, webdriver: WebDriver, message: str) -> None:
        """sends a message in a messenger room"""
        # TODO
        pass

    def __eq__(self, other) -> bool:
        """
        messenger rooms are compared based on specific aspects
        to ensure that recordings of the same messenger room at different points in time
        can represent the same messenger room
        """
        assert isinstance(other, MessengerRoom)

        return self.token == other.token and self.owner == other.owner and self.is_group == other.is_group and \
            self.name == other.name

    def __repr__(self) -> str:
        return f'<IScrA.webdriver.element.MessengerRoom.MessengerRoom (token="{self.token}", owner="{self.owner}", ' \
               f'is_group="{self.is_group}", name="{self.name}">'
