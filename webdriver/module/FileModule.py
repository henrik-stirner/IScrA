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

    def list_directory(self) -> {}:
        """returns a list of all subdirectories and files in the current directory"""
        if not self._webdriver.current_url == f'{self.remote_location}/{self.relative_path}':
            self._webdriver.get(f'{self.remote_location}/{self.relative_path}')

        directory_contents = {}

        # TODO: somehow not all subdirectories or files have valid links and are not fetched correctly...
        directory_content_table_row_links = WebDriverWait(self._webdriver, self._timeout).until(
            expected_conditions.presence_of_all_elements_located((
                By.XPATH, '//tbody/tr[not(contains(@class, "hasThumbnails"))]/td[contains(@class, "files-name")]/a')))

        for directory_content_table_row_link in directory_content_table_row_links:
            # name: remote_location
            directory_contents[
                directory_content_table_row_link.text
            ] = directory_content_table_row_link.get_attribute('href')

        return directory_contents

    def create_directory(self, directory_name: str) -> str:
        """creates a directory with the given name in the current location and returns its relative_path"""
        if not self._webdriver.current_url == f'{self.remote_location}/{self.relative_path}':
            self._webdriver.get(f'{self.remote_location}/{self.relative_path}')

        add_options_dropdown_button = WebDriverWait(self._webdriver, self._timeout).until(
            expected_conditions.presence_of_element_located((By.ID, 'dropdownAdd')))
        add_options_dropdown_button.click()

        add_folder_button = WebDriverWait(self._webdriver, self._timeout).until(
            expected_conditions.presence_of_element_located((By.ID, 'file-add-folder')))
        add_folder_button.click()

        # TODO
        # Adding a new folder sends a post request with some kind of encoded header to /iserv/file/add/folder.
        # I do not know yet how exactly the request is encoded or the path transmitted.
        # Maybe try x-www-urlencoded?

        folder_name_input = WebDriverWait(self._webdriver, self._timeout).until(
            expected_conditions.presence_of_element_located((By.ID, 'file_factory_item_name')))
        folder_name_input.send_keys(directory_name)

        create_new_folder_button = WebDriverWait(self._webdriver, self._timeout).until(
            expected_conditions.presence_of_element_located((By.ID, 'file_factory_submit')))
        create_new_folder_button.click()

        return f'{self.relative_path}/{directory_name}'

    def upload_file(self, path_to_file):
        """uploads a local file and adds it to the current directory"""
        if not self._webdriver.current_url == f'{self.remote_location}/{self.relative_path}':
            self._webdriver.get(f'{self.remote_location}/{self.relative_path}')
        # TODO: see line 82 <- how find files reliably?
        pass

    def remove(self, name) -> None:
        """
        constantly removes the directory or file with the given name in the current directory
        directories and their contents will be removed recursively
        """
        if not self._webdriver.current_url == f'{self.remote_location}/{self.relative_path}':
            self._webdriver.get(f'{self.remote_location}/{self.relative_path}')

        # TODO: see line 82 <- how to find files reliably?
