import logging
from configparser import ConfigParser

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, WebDriverException

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
# file module
# ----------


class FileModule(ModuleBase):
    """represents an IServ file module"""
    def __init__(self, webdriver: WebDriver, module_name: str = 'files', timeout: float = 5.0,
                 base_directory: str = None) -> None:
        super().__init__(webdriver, module_name, timeout)

        self.remote_location = self.remote_location.removeprefix('/').removesuffix('/')
        if base_directory:
            base_directory = base_directory.removeprefix('/').removesuffix('/')
            self.remote_location += f'/{base_directory}'

        self.relative_path = ''

        self._load()

    def _load(self) -> None:
        """switches to the base directories location"""
        self._webdriver.get(self.remote_location)

    def change_directory(self, path: str) -> None:
        """
        changes the directory based on the given path
        you cannot leave the root directory (remote_location/base_directory)
        """
        path = path.removeprefix('/').removesuffix('/')
        self.relative_path = self.relative_path.removeprefix('/').removesuffix('/')

        if path.startswith('../'):
            while path.startswith('../'):
                self.relative_path = '/'.join(self.relative_path.split('/')[:-1])
                path.removeprefix('../')

        elif path.startswith('./'):
            path.removeprefix('./')
            self.relative_path += f'/{path}'

        else:
            self.relative_path = path

        self._webdriver.get(f'{self.remote_location}/{self.relative_path}')

    def list_subdirectories(self) -> []:
        """returns a list of all subdirectories of the current directory"""
        if not self._webdriver.current_url == f'{self.remote_location}/{self.relative_path}':
            self._webdriver.get(f'{self.remote_location}/{self.relative_path}')

        subdirectories = []
        # TODO

        return subdirectories

    def list_files(self) -> []:
        """returns a list of all files in the current directory"""
        if not self._webdriver.current_url == f'{self.remote_location}/{self.relative_path}':
            self._webdriver.get(f'{self.remote_location}/{self.relative_path}')

        files = []
        # TODO

        return files

    def create_directory(self, directory_name) -> str:
        """creates a directory with the given name in the current location and returns its relative_path"""
        if not self._webdriver.current_url == f'{self.remote_location}/{self.relative_path}':
            self._webdriver.get(f'{self.remote_location}/{self.relative_path}')

        # TODO

        return f'{self.relative_path}/{directory_name}'

    def remove(self, name) -> None:
        """
        constantly removes the directory or file with the given name in the current directory
        directories and their contents will be removed recursively
        """
        if not self._webdriver.current_url == f'{self.remote_location}/{self.relative_path}':
            self._webdriver.get(f'{self.remote_location}/{self.relative_path}')

        # TODO
