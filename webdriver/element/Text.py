import logging
from configparser import ConfigParser

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.remote.webdriver import WebElement

from datetime import datetime
from os import path, mkdir, makedirs
from shutil import rmtree
import json

from webdriver.element.util import make_alphanumeric


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
        self.remote_location_of_actual_etherpad = None  # it is an iframe
        self.location = None

        self.owner = None
        self.shared_with_users = None

        self.tags = None

        self.title = None

        self.creation_date = None
        self.last_modification_date = None

        self._load(from_location, webdriver)

    def _fetch_local(self, location: str) -> None:
        """fetches the data of a text from a directory it has been saved to"""
        self.location = location

        data = json.load(open(
            f'{self.location}{"" if self.location.endswith(".json") else "/data.json"}', 'r', encoding='utf-8'))

        self.remote_location = data['remote_location']
        self.remote_location_of_actual_etherpad = data['remote_location_of_actual_etherpad']
        self.location = data['location']
        self.owner = data['owner']
        self.shared_with_users = data['shared_with_users']
        self.tags = data['tags']
        self.title = data['title']
        self.safe_title = data['safe_title']
        self.creation_date = datetime.strptime(data['creation_date'], '%d.%m.%Y %H:%M'),
        self.last_modification_date = datetime.strptime(data['last_modification_date'], '%d.%m.%Y %H:%M')

    def _fetch_remote(self, webdriver: WebDriver, remote_location: str) -> None:
        """fetches the data of a text from the corresponding IServ page"""
        self.remote_location = remote_location

        webdriver.get(remote_location)

        self.remote_location_of_actual_etherpad = webdriver.find_element(
            By.XPATH, '//iframe[@id="etherpad"]').get_attribute('src')

        # remove hidden attribute to make readable
        webdriver.execute_script(
            'arguments[0].setAttribute("class","");',
            webdriver.find_element(By.XPATH, '//div[@id="etherpad-crud-show" and @class="hidden"]')
        )

        text_data_dd_list = webdriver.find_elements(By.XPATH, '//dd[@class="col-sm-8"]')

        self.owner = text_data_dd_list[0].text
        print("OWNER:", self.owner)

        shared_with_users_li_list = text_data_dd_list[1].find_element(By.TAG_NAME, 'ul').find_elements(
            By.TAG_NAME, 'li')
        # TODO: only works if the language is set to German ('(keine)')
        if not shared_with_users_li_list[0].text == '(keine)':
            self.shared_with_users = {}
            for li in shared_with_users_li_list:
                # self.shared_with_users['username'] = ['granted permission', ...]
                self.shared_with_users[li.text] = [
                    span.get_attribute('title') for span in li.find_elements(By.TAG_NAME, 'span')
                    if span.get_attribute('title')
                ]
        print("SHARED WITH:", self.shared_with_users)

        self.tags = [
            a.text for a in text_data_dd_list[2].find_elements(
                By.XPATH, '//a[@class="label label-info tag-link mr-1"]')
        ]
        print("TAGS:", self.tags)

        # remove hidden attribute to make readable
        webdriver.execute_script(
            'arguments[0].setAttribute("class","");',
            webdriver.find_element(By.ID, 'topbar-title')
        )
        self.title = webdriver.find_element(By.ID, 'topbar-title').find_element(By.TAG_NAME, 'span').text
        self.safe_title = make_alphanumeric(self.title)
        print("TITLE:", self.title, self.safe_title)

        webdriver.get(f'https://{config["server"]["domain"]}{config["domain_extension"]["text"]}')

        # the table takes some time to load correctly for some reason
        WebDriverWait(webdriver, self._timeout).until(expected_conditions.presence_of_element_located(
            (By.TAG_NAME, 'tbody')))

        text_document_rows = webdriver.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')
        for text_document_row in text_document_rows:
            text_document_title_link = text_document_row.find_element(
                    By.XPATH, './/td[2]').find_element(By.TAG_NAME, 'a')
            if (self.title != text_document_title_link.text) and (
                    self.remote_location != text_document_title_link.get_attribute('href')):
                continue

            self.creation_date = datetime.strptime(
                text_document_row.find_element(
                    # second iserv-admin-list-field-datetime field?
                    By.XPATH, '//td[5]').text,
                '%d.%m.%Y %H:%M'
            )
            self.last_modification_date = datetime.strptime(
                text_document_row.find_element(
                    By.XPATH, '//td[4]').text,
                '%d.%m.%Y %H:%M'
            )

            break

        if path.exists(text_directory_location := f'{config["path"]["text"]}/{self.title}'):
            self.location = text_directory_location

    def _load(self, from_location: str, webdriver: WebDriver = None) -> None:
        """loads the data of a text from a given location"""
        if from_location.startswith('https://'):
            if webdriver is None:
                raise ValueError('A webdriver is needed to fetch from a remote location.')
            try:
                self._fetch_remote(webdriver, from_location)
            except Exception as exception:
                print(exception)
        else:
            self._fetch_local(from_location)

    def fetch_content(self, webdriver: WebDriver) -> list[WebElement] or list:
        webdriver.get(self.remote_location)

        # they used an iframe ...
        webdriver.switch_to.frame(webdriver.find_element(By.XPATH, '//iframe[@id="etherpad"]'))

        # ... *pause - waiting for the etherpad to load* ...
        WebDriverWait(webdriver, self._timeout).until(expected_conditions.presence_of_element_located(
            (By.XPATH, '//div[@class="editorcontainer initialized"]')))

        # ... containing an iFrAme ...
        webdriver.switch_to.frame(webdriver.find_element(By.XPATH, '//iframe[@name="ace_outer"]'))
        # ... containing aNoThER iFRaMe
        webdriver.switch_to.frame(webdriver.find_element(By.XPATH, '//iframe[@name="ace_inner"]'))

        ace_lines = webdriver.find_elements(By.XPATH, '//div[@class="ace-line"]')

        return ace_lines

    def save(self, webdriver: WebDriver, override: bool = True, to_location: str = config['path']['text']) -> bool:
        """creates a directory in which the texts content and data are saved in"""
        if self.location is None:
            self.location = f'{to_location}/{self.safe_title}'
            makedirs(self.location)
        elif override:
            rmtree(self.location)
            mkdir(self.location)
        else:
            return False

        with open(f'{self.location}/{self.safe_title}.txt', 'w', encoding='utf-8') as outfile:
            for ace_line in self.fetch_content(webdriver=webdriver):
                outfile.write(f'{ace_line.text}\n')

            outfile.close()

        json.dump({
            'remote_location': self.remote_location,
            'remote_location_of_actual_etherpad': self.remote_location_of_actual_etherpad,
            'location': self.location,
            'owner': self.owner,
            'shared_with_users': self.shared_with_users,
            'tags': self.tags,
            'title': self.title,
            'safe_title': self.safe_title,
            'creation_date': datetime.strftime(self.creation_date, '%d.%m.%Y %H:%M'),
            'last_modification_date': datetime.strftime(self.last_modification_date, '%d.%m.%Y %H:%M')
        }, open(f'{self.location}/data.json', 'w', encoding='utf-8'), indent=4)

    def __eq__(self, other) -> bool:
        """
        texts are compared based on specific aspects
        to ensure that recordings of the same text at different points in time
        can represent the same text
        """
        if not isinstance(other, Text):
            return False

        return self.title == other.title and self.owner == other.owner and self.creation_date == other.creation_date

    def __repr__(self) -> str:
        return f'<IScrA.webdriver.element.Text.Text (title="{self.title}", owner="{self.owner}", ' \
               f'creation_date="{self.creation_date}")>'
