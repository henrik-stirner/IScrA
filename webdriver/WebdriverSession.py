import logging
from configparser import ConfigParser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, WebDriverException


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
# webdriver
# ----------


class WebdriverSession:
    """a webdriver to automate the usage of IServ using Firefox"""
    def __init__(self, iserv_username: str, iserv_password: str, timeout: float = 5.0) -> None:
        self.timeout = timeout

        self._webdriver_options = webdriver.FirefoxOptions()
        # TODO: only for debugging
        # self._webdriver_options.headless = True  # no ui

        self._webdriver = webdriver.Firefox(options=self._webdriver_options)

        try:
            self._login(iserv_username, iserv_password)
        except WebDriverException as e:
            self._webdriver.quit()
            logger.exception(e)
            raise e

    def _login(self, iserv_username: str, iserv_password: str) -> bool:
        self._webdriver.get(f'https://{config["server"]["domain"]}{config["domain_extension"]["login"]}')
        assert 'IServ' in self._webdriver.title

        # enter username and password
        username_input = WebDriverWait(self._webdriver, self.timeout).until(
            expected_conditions.presence_of_element_located((By.XPATH, '//input[@name="_username"]')))
        password_input = WebDriverWait(self._webdriver, self.timeout).until(
            expected_conditions.presence_of_element_located((By.XPATH, '//input[@name="_password"]')))

        username_input.send_keys(iserv_username)
        password_input.send_keys(iserv_password)

        # press submit button
        login_button = WebDriverWait(self._webdriver, self.timeout).until(
            expected_conditions.presence_of_element_located((By.XPATH, '//button[@type="submit"]')))

        login_button.click()

        try:
            WebDriverWait(self._webdriver, self.timeout).until(expected_conditions.presence_of_element_located(
                (By.XPATH, f'//a[@class="btn btn-success" and @href="https://{config["server"]["domain"]}/iserv"]')
            ))
            self._webdriver.get(f'https://{config["server"]["domain"]}/iserv')
            assert 'IServ' in self._webdriver.title
        except TimeoutException:
            logger.exception('Failed trying to log into IServ. The username or password is invalid.')
            raise ValueError('The username or password is invalid.')

        return True

    def _logout(self) -> None:
        self._webdriver.get(f'https://{config["server"]["domain"]}{config["domain_extension"]["logout"]}')

    def shutdown(self) -> None:
        """makes this instance of IServWebdriver logout of IServ and shut the webdriver down"""
        self._logout()
        self._webdriver.quit()
