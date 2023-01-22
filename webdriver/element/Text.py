import logging
from configparser import ConfigParser

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, WebDriverException

from datetime import datetime
from os import path, mkdir
from shutil import rmtree
import json

from webdriver import Session


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
# text
# ----------


class Text:
    """represents an IServ text"""
    def __init__(self, from_location: str, webdriver: WebDriver = None, timeout: float = 5.0) -> None:
        self._timeout = timeout

        self.remote_location = None
        self.location = None

        self.owner = None

        self.tags = None

        self.title = None

        self.creation_date = None
        self.last_modification_date = None

        self._load(from_location, webdriver)

    def _fetch_local(self, location: str) -> None:
        """fetches the data of a text from a directory it has been saved to"""
        self.location = location

        # TODO
        self.remote_location = None

        self.owner = None

        self.tags = None

        self.title = None

        self.creation_date = None
        self.last_modification_date = None

    def _fetch_remote(self, webdriver: WebDriver, remote_location: str) -> None:
        """fetches the data of a text from the corresponding IServ page"""
        self.remote_location = remote_location

        webdriver.get(remote_location)

        # TODO
        self.location = None

        self.owner = None

        self.tags = None

        self.title = None

        self.creation_date = None
        self.last_modification_date = None

    def _load(self, from_location: str, webdriver: WebDriver = None) -> None:
        """loads the data of a text from a given location"""
        if from_location.startswith('https://'):
            if webdriver is None:
                raise ValueError('A webdriver is needed to fetch from a remote location.')
            self._fetch_remote(webdriver, from_location)
        else:
            self._fetch_local(from_location)

    def save(self, session: Session, to_location: str = config["path"]["exercise"]) -> bool:
        """creates a directory in which the texts content and data are saved in"""
        # TODO
        pass

    def __eq__(self, other) -> bool:
        """
        texts are compared based on specific aspects
        to ensure that recordings of the same text at different points in time
        can represent the same text
        """
        assert isinstance(other, Text)

        return self.title == other.title and self.owner == other.owner and self.creation_date == other.creation_date

    def __repr__(self) -> str:
        return f'<IScrA.webdriver.element.Text.Text (title="{self.title}", owner="{self.owner}", ' \
               f'creation_date="{self.creation_date}")>'
