import logging
from configparser import ConfigParser

from datetime import datetime
from os import walk, remove, path

from requests import Session
from requests.exceptions import RequestException
from bs4 import BeautifulSoup

from contextlib import closing
import csv

import json


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


class Scraper:
    """web scraping automations for IServ"""
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

    def get_pending_exercises(self) -> None:
        """gets currently pending exercises and copies them into a textfile"""

        # copy pending exercises into a text file
        with closing(self._request_session.get(
                f'https://{config["server"]["domain"]}{config["domain_extension"]["exercise_csv"]}', stream=True)
        ) as exercise_csv_file:
            # lazily read from the stream in order to use less memory
            csv_reader = csv.reader(exercise_csv_file.iter_lines(decode_unicode=True), delimiter=';', quotechar='"')
            # write the exercises to a textfile
            new_exercise_file = open(f'./data/task/{datetime.now().strftime("%Y-%m-%d_-_%H-%M")}.txt', mode='w')
            for index, csv_row in enumerate(csv_reader):
                # csv_row: ['\ufeff', 'Aufgabe', 'Abgabetermin', 'Rueckmeldungen', 'Tags']
                new_exercise_file.write(f'{index} | "{csv_row[1]}" ({csv_row[4]}) bis {csv_row[2]}\n')
            new_exercise_file.close()

        # only keep up to 2 files
        exercise_files = list(filter(
            lambda file: file.endswith('.txt'), next(walk('./data/task/'), (None, None, []))[2]))
        if len(exercise_files) > 2:
            for exercise_file in exercise_files[0:len(exercise_files) - 2]:
                remove(f'./data/task/{exercise_file}')

    def pending_exercises_changed(self) -> str or None:
        """gets currently pending exercises and checks if they have change"""
        self.get_pending_exercises()

        exercise_files = list(filter(
            lambda file: file.endswith('.txt'), next(walk('./data/task/'), (None, None, []))[2]))

        # compare the latest exercise files
        exercise_files = exercise_files[len(exercise_files) - 2:len(exercise_files)]

        old_exercise_file = open(f'./data/task/{exercise_files[0]}', mode='r')
        new_exercise_file = open(f'./data/task/{exercise_files[1]}', mode='r')

        for old_exercise in old_exercise_file:
            if old_exercise != new_exercise_file.readline():
                old_exercise_file.close()
                new_exercise_file.close()

                return path.abspath(f'./data/task/{exercise_files[1]}')

        old_exercise_file.close()
        new_exercise_file.close()

        return

    def get_global_videoconference_system_load(self) -> dict:
        """gets the current load of iserv's global videoconference system"""
        return self._request_session.get(
            f'https://{config["server"]["domain"]}{config["domain_extension"]["videoconference_load"]}'
        ).json()
