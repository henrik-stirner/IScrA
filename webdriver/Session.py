import logging
import os.path
from configparser import ConfigParser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, WebDriverException

import requests

from webdriver.element import Exercise, Text, File, MessengerRoom


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


class Session:
    """a webdriver to automate the usage of IServ using Firefox"""
    def __init__(self, iserv_username: str, iserv_password: str, timeout: float = 5.0) -> None:
        self._timeout = timeout

        self._webdriver_options = webdriver.FirefoxOptions()
        # self._webdriver_options.headless = True  # no ui  # TODO: only False for debugging
        self._webdriver_options.set_preference("browser.preferences.instantApply", True)
        self._webdriver_options.set_preference("browser.download.folderList", 0)
        self._webdriver_options.set_preference("browser.download.manager.showWhenStarting", False)
        self._webdriver_options.set_preference("browser.helperApps.alwaysAsk.force", False)
        self._webdriver_options.set_preference(
            'browser.helperApps.neverAsk.saveToDisk',
            'application/csv, application/xml, application/excel, application/octet-stream, application/binary, '
            'text/plain, text/comma-separated-values, text/csv, text/xml'
        )

        self._webdriver = webdriver.Firefox(options=self._webdriver_options)

        try:
            self._login(iserv_username, iserv_password)
        except WebDriverException as e:
            self._webdriver.quit()
            logger.exception(e)
            raise e

        # for downloading files independently
        self._request_session = None

    def _login(self, iserv_username: str, iserv_password: str) -> bool:
        """makes this instance of WebdriverSession login to IServ"""
        self._webdriver.get(f'https://{config["server"]["domain"]}{config["domain_extension"]["login"]}')
        assert 'IServ' in self._webdriver.title

        # enter username and password
        username_input = WebDriverWait(self._webdriver, self._timeout).until(
            expected_conditions.presence_of_element_located((By.XPATH, '//input[@name="_username"]')))
        password_input = WebDriverWait(self._webdriver, self._timeout).until(
            expected_conditions.presence_of_element_located((By.XPATH, '//input[@name="_password"]')))

        username_input.send_keys(iserv_username)
        password_input.send_keys(iserv_password)

        # press submit button
        login_button = WebDriverWait(self._webdriver, self._timeout).until(
            expected_conditions.presence_of_element_located((By.XPATH, '//button[@type="submit"]')))

        login_button.click()

        try:
            WebDriverWait(self._webdriver, self._timeout).until(expected_conditions.presence_of_element_located(
                (By.XPATH, f'//a[@class="btn btn-success" and @href="https://{config["server"]["domain"]}/iserv"]')
            ))
            self._webdriver.get(f'https://{config["server"]["domain"]}/iserv')
            assert 'IServ' in self._webdriver.title
        except TimeoutException:
            logger.exception('Failed trying to log into IServ. The username or password is invalid.')
            raise ValueError('The username or password is invalid.')

        return True

    def _logout(self) -> None:
        """makes this instance of WebdriverSession logout from IServ"""
        self._webdriver.get(f'https://{config["server"]["domain"]}{config["domain_extension"]["logout"]}')

    def shutdown(self) -> None:
        """makes this instance of WebdriverSession logout from IServ and shut down the webdriver"""
        self._logout()
        self._webdriver.quit()

    def navigate(self, to_remote_location: str) -> None:
        """makes the webdriver navigate to a given remote location"""
        self._webdriver.get(to_remote_location)

    @staticmethod
    def _remote_location_from_module_name(module_name: str) -> str:
        """
        creates an url (remote location) from a module name
        using the domain and domain extensions given in the config
        """
        return f'https://{config["server"]["domain"]}{config["domain_extensions"][module_name]}'

    def navigate_to_module(self, module_name: str) -> None:
        """makes the webdriver navigate to the remote location of a given module"""
        self.navigate(self._remote_location_from_module_name(module_name))

    def fetch_downloadable(self, from_remote_location: str, to_location=None) -> bool or bytes:
        """downloads a file from a remote location by sending a request while not using the webdriver"""
        if not self._request_session:
            self._request_session = requests.Session()

        # get webdriver cookies needed in order to send a valid requests
        relevant_webdriver_cookies = {}
        for webdriver_cookie in self._webdriver.get_cookies():
            if webdriver_cookie['secure'] or not webdriver_cookie['httpOnly']:
                relevant_webdriver_cookies[webdriver_cookie['name']] = webdriver_cookie['value']

        # fetch the data from the remote_location
        data = self._request_session.get(url=from_remote_location, cookies=relevant_webdriver_cookies,
                                         allow_redirects=True)

        downloadable = 'attachment' in data.headers.get('Content-Disposition')
        if not downloadable:
            return False

        # return fetched data if location is None
        if to_location is None:
            return data.content

        # save the fetched data in location
        if os.path.isdir(to_location):
            to_location = f'{to_location}{"" if to_location.endswith("/") else "/"}' \
                       f'{data.headers.get("Content-Disposition").split("=")[-1]}'

        open(to_location, 'wb').write(data.content)

        return True
