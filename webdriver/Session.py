import logging
import os.path
from configparser import ConfigParser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, WebDriverException

import requests

from webdriver.module import ExerciseModule, TextModule, FileModule, MessengerModule
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

        # each module should be present in each session only once,
        # because for each IServ user each module exists only once
        self._exercise_module = None
        self._text_module = None
        self._file_module = None
        self._messenger_module = None

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
        return f'https://{config["server"]["domain"]}{config["domain_extension"][module_name]}'

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

    # ----------
    # the actually useful part
    # ----------

    # even more boilerplate code...

    # modules
    def exercise_module(self, domain_extension_config_key=None) -> ExerciseModule:
        """access point for this sessions exercise module"""
        if domain_extension_config_key is None:
            domain_extension_config_key = 'exercise'

        if self._exercise_module is None:
            self._exercise_module = ExerciseModule(
                webdriver=self._webdriver,
                module_name=domain_extension_config_key,
                timeout=self._timeout
            )

        return self._exercise_module

    def text_module(self, domain_extension_config_key=None) -> TextModule:
        """access point for this sessions text module"""
        if domain_extension_config_key is None:
            domain_extension_config_key = 'text'

        if self._text_module is None:
            self._text_module = TextModule(
                webdriver=self._webdriver,
                module_name=domain_extension_config_key,
                timeout=self._timeout
            )

        return self._text_module

    def file_module(self, domain_extension_config_key=None) -> FileModule:
        """access point for this sessions files module"""
        if domain_extension_config_key is None:
            domain_extension_config_key = 'files'

        if self._file_module is None:
            self._file_module = FileModule(
                webdriver=self._webdriver,
                module_name=domain_extension_config_key,
                timeout=self._timeout
            )

        return self._file_module

    def messenger_module(self, domain_extension_config_key=None) -> MessengerModule:
        """access point for this sessions messenger module"""
        if domain_extension_config_key is None:
            domain_extension_config_key = 'messenger'

        if self._messenger_module is None:
            self._messenger_module = MessengerModule(
                webdriver=self._webdriver,
                module_name=domain_extension_config_key,
                timeout=self._timeout
            )

        return self._messenger_module

    # now it actually gets interesting (for real) (I swear)

    # exercises
    def fetch_all_exercises(self) -> list:
        """returns a list of all exercises (webdriver.element.Exercise.Exercise) in this session's ExerciseModule"""
        self.exercise_module()

        return [Exercise(
            from_location=remote_location,
            webdriver=self._webdriver,
            timeout=self._timeout
        ) for remote_location in self._exercise_module.remote_exercise_locations.values()]

    def fetch_exercises_by_keywords(self, keywords: list) -> list:
        """
        returns a list of all texts (webdriver.element.Text.Text) in this session's TextModule
        which have a title that contains at least one of the given keywords
        """
        self.exercise_module()

        return [Exercise(
            from_location=remote_location,
            webdriver=self._webdriver,
            timeout=self._timeout
        ) for name, remote_location in self._exercise_module.remote_exercise_locations.items() if any(
            keyword in name for keyword in keywords)]

    def save_all_exercises(self, override: bool = True, to_location: str = config['path']['exercise']) -> None:
        """saves all exercises (webdriver.element.Exercise.Exercise) in this session's ExerciseModule"""
        for exercise in self.fetch_all_exercises():
            exercise.save(session=self, override=override, to_location=to_location)

    def save_exercise(self, exercise: Exercise, override: bool = True, to_location: str = config['path']['exercise']
                      ) -> None:
        """saves an exercise (webdriver.element.Exercise.Exercise) from this session's ExerciseModule"""
        exercise.save(session=self, override=override, to_location=to_location)

    # texts
    def fetch_all_texts(self) -> list:
        """returns a list of all texts (webdriver.element.Text.Texts) in this session's TextModule"""
        self.text_module()

        return [Text(
            from_location=remote_location,
            webdriver=self._webdriver,
            timeout=self._timeout
        ) for remote_location in self._text_module.remote_text_locations.values()]

    def fetch_texts_by_keywords(self, keywords: list) -> list:
        """
        returns a list of all texts (webdriver.element.Text.Text) in this session's TextModule
        which have a title that contains at least one of the given keywords
        """
        self.text_module()

        return [Text(
            from_location=remote_location,
            webdriver=self._webdriver,
            timeout=self._timeout
        ) for name, remote_location in self._text_module.remote_text_locations.items() if any(
            keyword.lower() in name.lower() for keyword in keywords)]

    def save_all_texts(self, override: bool = True, to_location: str = config['path']['text']) -> None:
        """saves all texts (webdriver.element.Text.Text) in this session's TextModule"""
        for text in self.fetch_all_texts():
            text.save(webdriver=self._webdriver, override=override, to_location=to_location)

    def save_text(self, text: Text, override: bool = True, to_location: str = config['path']['text']
                  ) -> None:
        """saves an exercise (webdriver.element.Exercise.Exercise) from this session's ExerciseModule"""
        text.save(webdriver=self._webdriver, override=override, to_location=to_location)

    # files
    # TODO: files

    # messenger rooms
    def get_all_messenger_rooms(self) -> list:
        """
        returns a list of all messenger rooms (webdriver.element.MessengerRoom.MessengerRoom)
        in this session's MessengerModule
        """
        self.messenger_module()

        return [MessengerRoom(
            remote_location=remote_location,
            webdriver=self._webdriver,
            timeout=self._timeout
        ) for remote_location in self._messenger_module.remote_messenger_room_locations.values()]

    def get_messenger_rooms_by_keywords(self, keywords: list) -> list:
        """
        returns a list of all texts (webdriver.element.Text.Text) in this session's TextModule
        which have a title that contains at least one of the given keywords
        """
        self.messenger_module()

        return [MessengerRoom(
            remote_location=remote_location,
            webdriver=self._webdriver,
            timeout=self._timeout
        ) for name, remote_location in self._messenger_module.remote_messenger_room_locations.items() if any(
            keyword in name for keyword in keywords)]

    def fetch_messages(self, messenger_room: MessengerRoom, number_of_messages: int) -> list:
        """fetches the last number_of_messages that have been sent in a messenger room"""
        return messenger_room.fetch_messages(webdriver=self._webdriver, number_of_messages=number_of_messages)

    def send_messages(self, messenger_room: MessengerRoom, messages: list) -> None:
        """sends the given messages to a messenger room"""
        messenger_room.send_messages(webdriver=self._webdriver, messages=messages)
