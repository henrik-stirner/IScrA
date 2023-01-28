import logging
from configparser import ConfigParser

from selenium.webdriver.firefox.webdriver import WebDriver


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
    def __init__(self, webdriver: WebDriver, module_name: str, timeout: float = 5.0) -> None:
        self._webdriver = webdriver
        self._timeout = timeout

        self.name = module_name
        self.remote_location = f'https://{config["server"]["domain"]}{config["domain_extension"][module_name]}'
