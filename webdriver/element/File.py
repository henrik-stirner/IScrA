import logging
from configparser import ConfigParser

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By

from datetime import datetime
from os import path, mkdir, makedirs
from shutil import rmtree
import json

from webdriver.element.util import make_alphanumeric

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
# file
# ----------


class File:
    """represents an IServ file"""
    def __init__(self, from_location: str, webdriver: WebDriver = None, timeout: float = 5.0) -> None:
        self._timeout = timeout

        self.relative_remote_location = None
        self.remote_locations = None
        self.directory_location = None

        self.owner = None

        self.type = None

        self.name = None
        self.size = None

        self.last_modification_date = None

        self._load(from_location, webdriver)

    def _fetch_local(self, directory_location: str) -> None:
        """fetches the data of a file from a directory it has been saved to"""
        self.directory_location = directory_location

        data = json.load(open(
            f'{self.directory_location}{"" if self.directory_location.endswith(".json") else "/data.json"}',
            'r', encoding='utf-8'))

        self.relative_remote_location = data['relative_remote_location']
        self.safe_relative_remote_location = data['safe_relative_remote_location']
        self.remote_locations = data['remote_locations']
        self.owner = data['owner']
        self.type = data['type']
        self.name = data['name']
        self.safe_name = data['safe_name']
        self.size = data['size']
        self.last_modification_date = datetime.strptime(data['last_modification_date'], '%d.%m.%Y %H:%M')

    def _remote_locations_from_single_remote_location(self, remote_location: str) -> None:
        files_url = f'https://{config["server"]["domain"]}{config["domain_extension"]["files"]}'
        fs_disp_url = f'https://{config["server"]["domain"]}{config["domain_extension"]["filesystem_display"]}'
        fs_down_url = f'https://{config["server"]["domain"]}{config["domain_extension"]["filesystem_download"]}'
        fs_disp_local_url = f'{fs_disp_url}{config["domain_extension"]["filesystem_local_ext"]}'
        fs_down_local_url = f'{fs_down_url}{config["domain_extension"]["filesystem_local_ext"]}'

        if remote_location.endswith(config['domain_extension']['files_show_page_ext']):
            remote_location = remote_location.removesuffix(config['domain_extension']['files_show_page_ext'])

        if remote_location.startswith(files_url):
            self.relative_remote_location = remote_location.removeprefix(files_url)
            self.remote_locations = {
                'show': f'{remote_location}{config["domain_extension"]["files_show_page_ext"]}',
                'display': f'{fs_disp_local_url}{self.relative_remote_location}',
                'download': f'{fs_down_local_url}{self.relative_remote_location}'
            }

        elif remote_location.startswith(fs_disp_url):
            if remote_location.startswith(fs_disp_local_url):
                self.relative_remote_location = remote_location.removeprefix(fs_disp_local_url)
                self.remote_locations = {
                    'show': f'{files_url}'
                            f'{self.relative_remote_location}{config["domain_extension"]["files_show_page_ext"]}',
                    'display': remote_location,
                    'download': f'{fs_down_local_url}{self.relative_remote_location}'
                }
            else:
                self.relative_remote_location = remote_location.removeprefix(fs_disp_url)
                self.remote_locations = {
                    'show': None,
                    'display': remote_location,
                    'download': f'{fs_down_url}{self.relative_remote_location}'
                }

        elif remote_location.startswith(fs_down_url):
            if remote_location.startswith(fs_down_local_url):
                self.relative_remote_location = remote_location.removeprefix(fs_down_local_url)
                self.remote_locations = {
                    'show': f'{files_url}'
                            f'{self.relative_remote_location}{config["domain_extension"]["files_show_page_ext"]}',
                    'display': f'{fs_disp_local_url}{self.relative_remote_location}',
                    'download': remote_location
                }
            else:
                self.relative_remote_location = remote_location.removeprefix(fs_down_url)
                self.remote_locations = {
                    'show': None,
                    'display': f'{fs_disp_url}{self.relative_remote_location}',
                    'download': remote_location
                }

        self.safe_relative_remote_location = ''.join(
            char if char not in '\"*<>?\\|' else '_' for char in self.relative_remote_location)

    def _fetch_remote(self, webdriver: WebDriver, remote_location: str) -> None:
        """fetches the data of a file from the corresponding IServ page"""
        self._remote_locations_from_single_remote_location(remote_location)

        self.name = self.relative_remote_location.split('/')[-1]
        self.safe_name = make_alphanumeric(self.name)

        self.type = f'.{self.name.split(".")[-1]}'

        if path.exists(file_directory_location :=
                       f'{config["path"]["filesystem"]}{self.relative_remote_location.removesuffix(self.type)}'):
            self.directory_location = file_directory_location

        if self.remote_locations['show'] is None:
            return

        webdriver.get(self.remote_locations['show'])

        file_data_div_list = webdriver.find_element(
            By.XPATH, '//div[@class="file-data"]').find_elements(By.XPATH, '//div[@class="mb-2"]')
        self.last_modification_date = datetime.strptime(file_data_div_list[-1].text.split('\n')[-1], '%d.%m.%Y %H:%M')
        self.owner = file_data_div_list[-2].text.split('\n')[-1]
        self.size = file_data_div_list[-3].text.split('\n')[-1]

    def _load(self, from_location: str, webdriver: WebDriver = None) -> None:
        """loads the data of a file from a given location"""
        if from_location.startswith('https://'):
            if webdriver is None:
                raise ValueError('A webdriver is needed to fetch from a remote location.')
            self._fetch_remote(webdriver, from_location)
        else:
            self._fetch_local(from_location)

    def save(self, session: Session, override: bool = True, to_location: str = config['path']['filesystem']) -> bool:
        """creates a directory in which the files content and data are saved in"""
        if self.directory_location is None:
            self.directory_location = f'{to_location}{self.safe_relative_remote_location.removesuffix(self.type)}'
            makedirs(self.directory_location)
        elif override:
            rmtree(self.directory_location)
            mkdir(self.directory_location)
        else:
            return False

        json.dump({
            'relative_remote_location': self.relative_remote_location,
            'safe_relative_remote_location': self.safe_relative_remote_location,
            'remote_locations': self.remote_locations,
            'directory_location': self.directory_location,
            'owner': self.owner,
            'type': self.type,
            'name': self.name,
            'safe_name': self.safe_name,
            'size': self.size,
            'last_modification_date': datetime.strftime(self.last_modification_date, '%d.%m.%Y %H:%M')
        }, open(f'{self.directory_location}/data.json', 'w', encoding='utf-8'), indent=4)

        session.fetch_downloadable(
            from_remote_location=self.remote_locations['download'],
            to_location=f'{self.directory_location}/{self.safe_name}'
        )

        return True

    def __eq__(self, other) -> bool:
        """
        files are compared based on specific aspects
        to ensure that recordings of the same file at different points in time
        canNOT represent the same file
        """
        if not isinstance(other, File):
            return False

        return self.name == other.name and self.owner == other.owner and self.type == other.type and \
            self.remote_locations == other.remote_locations and self.size == other.size

    def __repr__(self) -> str:
        return f'<IScrA.webdriver.element.File.File (name="{self.name}", owner="{self.owner}", type="{self.type}", ' \
               f'remote_location="{self.remote_locations}", size="{self.size}")>'
