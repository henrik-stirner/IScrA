import logging
from configparser import ConfigParser

from datetime import datetime
from os import walk, remove, path

from requests import Session
from requests.exceptions import RequestException
from bs4 import BeautifulSoup

from contextlib import closing
import csv


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
# scraper
# ----------


class IServScraper:
    """web scraping automations for IServ; NOT AN INTERFACE"""
    def __init__(self, iserv_username: str, iserv_password: str) -> None:
        self._request_session = Session()
        self._csrf_token = None

        # login
        self._login(iserv_username, iserv_password)

    def _login(self, iserv_username: str, iserv_password: str) -> bool:
        """makes this instance of IServScraper login to IServ"""
        # post request
        page = self._request_session.post(
            url=f'https://{config["server"]["domain"]}{config["domain_extension"]["login"]}',
            data=f'_password={iserv_password}&_username={iserv_username}',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )

        if str(page.status_code).startswith(('4', '5')):
            # request failed
            logger.exception('An error occurred while trying to log into IServ.\n'
                             f'Status code: "{page.status_code}"')
            raise RequestException('An error occurred while trying to log into IServ.\n'
                                   f'Status code: "{page.status_code}"')
        # TODO: only works if the language is set to German
        elif 'Anmeldung fehlgeschlagen!' in page.text:  # page.text = page.content in utf-8
            # login failed (German text)
            logger.exception('Failed trying to log into IServ. The username or password is invalid.')
            raise ValueError('The username or password is invalid.')

        return True

    def _logout(self) -> bool:
        """makes this instance of IServScraper logout of IServ"""
        page = self._request_session.get(
            url=f'https://{config["server"]["domain"]}{config["domain_extension"]["logout"]}',
        )

        if str(page.status_code).startswith(('4', '5')):
            # request failed
            logger.exception('An error occurred while trying to log out of IServ.\n'
                             f'Status code: "{page.status_code}"')
            raise RequestException('An error occurred while trying to log out of IServ.\n'
                                   f'Status code: "{page.status_code}"')

        # request succeeded
        return True

    def shutdown(self) -> None:
        """makes this instance of IServScraper logout of IServ and close the request session"""
        self._logout()
        self._request_session.close()

    def get_csrf_token(self) -> bool:
        """gets the csrf token from the IServ mail page"""
        page = self._request_session.get(
            url=f'https://{config["server"]["domain"]}{config["domain_extension"]["mail"]}'
        )

        if str(page.status_code).startswith(('4', '5')):
            # request failed
            logger.exception('An error occurred while trying to get the csrf token from the IServ mil page.\n'
                             f'Status code: "{page.status_code}"')
            raise RequestException('An error occurred while trying to get the csrf token from the IServ mail page.\n'
                                   f'Status code: "{page.status_code}"')

        # main code
        soup = BeautifulSoup(page.text, 'html.parser')
        self._csrf_token = soup.find_all('a')[36].attrs['href'].split('=')[-1]

        # request succeeded
        return True

    def pending_tasks_changed(self) -> str or None:
        """gets currently pending tasks and checks if they have change"""

        # copy pending tasks into a text file
        with closing(self._request_session.get(
                f'https://{config["server"]["domain"]}{config["domain_extension"]["tasks_csv"]}', stream=True)
        ) as tasks_csv_file:
            # lazily read from the stream in order to use less memory
            csv_reader = csv.reader(tasks_csv_file.iter_lines(decode_unicode=True), delimiter=';', quotechar='"')
            # write the tasks to a textfile
            tasks_file = open(f'./data/task/{datetime.now().strftime("%Y-%m-%d_-_%H-%M")}.txt', mode='w')
            for index, csv_row in enumerate(csv_reader):
                # csv_row: ['\ufeff', 'Aufgabe', 'Abgabetermin', 'Rueckmeldungen', 'Tags']
                tasks_file.write(f'{index} | "{csv_row[1]}" ({csv_row[4]}) bis {csv_row[2]}\n')
            tasks_file.close()

        # only keep up to 2 files
        task_files = list(filter(lambda file: file.endswith('.txt'), next(walk('./data/task/'), (None, None, []))[2]))
        if len(task_files) > 2:
            for task_file in task_files[0:len(task_files) - 2]:
                remove(f'./data/task/{task_file}')

        # compare the latest task files
        task_files = task_files[len(task_files) - 2:len(task_files)]

        old_task_file = open(f'./data/task/{task_files[0]}', mode='r')
        new_task_file = open(f'./data/task/{task_files[1]}', mode='r')

        for old_task in old_task_file:
            if old_task != new_task_file.readline():
                old_task_file.close()
                new_task_file.close()

                return path.abspath(f'./data/task/{task_files[1]}')

        old_task_file.close()
        new_task_file.close()

        return
