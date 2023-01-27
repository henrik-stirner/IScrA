import logging
from configparser import ConfigParser

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException

from datetime import datetime
from os import path, mkdir
from shutil import rmtree
import json

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
# subject keywords
# ----------


def get_subject_keywords():
    subject = ConfigParser()
    subject.read('subject.ini', encoding='utf-8')

    subject_keywords = {}
    for subject_name, keyword_string in subject['keywords'].items():
        subject_keywords[subject_name] = keyword_string.split('/')

    return subject_keywords


subjectKeywords = get_subject_keywords()


# ----------
# exercise
# ----------


class Exercise:
    """represents an IServ exercise"""
    def __init__(self, from_location: str, webdriver: WebDriver = None, timeout: float = 5.0) -> None:
        self._timeout = timeout

        self.remote_location = None
        self.location = None

        self.owner = None

        self.subject = None
        self.tags = None

        self.title = None
        self.description = None
        self.attachments = None

        self.start_date = None
        self.deadline = None

        self.unseen = True
        self.completed = False

        self._load(from_location, webdriver)

    def _fetch_local(self, location: str) -> None:
        """fetches the data of an exercise from a directory it has been saved to"""
        self.location = location

        data = json.load(open(
            f'{self.location}{"" if self.location.endswith(".json") else "/data.json"}', 'r', encoding='utf-8'))

        self.remote_location = data['remote_location']
        self.owner = data['owner']
        self.subject = data['subject']
        self.tags = data['tags']
        self.title = data['title']
        self.description = data['description']
        self.attachments = data['attachments']
        self.start_date = datetime.strptime(data['start_date'], '%d.%m.%Y %H:%M')
        self.deadline = datetime.strptime(data['deadline'], '%d.%m.%Y %H:%M')
        self.unseen = data['unseen']
        self.completed = data['completed']

    @staticmethod
    def search_for_subject_hint(to_be_searched: str) -> list:
        """takes a rough guess at which subjects are recognizable in a string"""
        potential_subjects = []
        for subject, keywords in subjectKeywords.items():
            if any(keyword in to_be_searched for keyword in keywords):
                potential_subjects.append(subject)

        return potential_subjects if potential_subjects else ['unknown']

    def _fetch_remote(self, webdriver: WebDriver, remote_location: str) -> None:
        """fetches the data of an exercise from the corresponding IServ page"""
        self.remote_location = remote_location

        webdriver.get(remote_location)

        self.owner = webdriver.find_element(By.XPATH, '//a[@class="mailto"]').text

        self.tags = [a.text for a in webdriver.find_elements(By.XPATH, '//a[@class="label label-info exercise-tag"]')]

        self.title = webdriver.find_element(By.XPATH, '//h3[@class="panel-title"]').text
        self.description = '\n'.join([
            p.text for p in webdriver.find_element(By.XPATH, '//div[@class="text-break-word pb-0"]'
                                                   ).find_elements(By.TAG_NAME, 'p')
        ])
        self.attachments = [
            a.get_attribute('href') for a in webdriver.find_elements(By.XPATH, '//a[@class="text-break-word"]')
        ]

        fs_disp_url = f'https://{config["server"]["domain"]}{config["domain_extension"]["filesystem_display"]}'
        fs_down_url = f'https://{config["server"]["domain"]}{config["domain_extension"]["filesystem_download"]}'
        for index, attachment in enumerate(self.attachments):
            if attachment.startswith(fs_disp_url):
                # this is necessary for the attachments to be downloadable (Content-Disposition header)
                self.attachments[index] = attachment.replace(fs_disp_url, fs_down_url)

        date_td_list = webdriver.find_elements(By.XPATH, '//td[@class="bt0 pt-0"]')
        self.start_date = datetime.strptime(date_td_list[0].text, '%d.%m.%Y %H:%M')
        self.deadline = datetime.strptime(
            date_td_list[1].find_element(By.TAG_NAME, 'ul').find_element(By.TAG_NAME, 'li').text,
            '%d.%m.%Y %H:%M'
        )

        try:
            # TODO: what if there are files submitted? Is there still an alert?
            WebDriverWait(webdriver, self._timeout).until(expected_conditions.presence_of_element_located(
                (By.XPATH, '//div[@class="alert alert-success"]')))
            self.completed = True
            self.unseen = False
        except TimeoutException:
            self.completed = False

        if self.tags:
            self.subject = self.search_for_subject_hint(' '.join(self.tags).lower())
        if (not self.tags or self.subject == ['unknown']) and (self.title or self.description):
            # search in title and description if they exist and
            # if there are no tags or no subject was recognized in them
            self.subject = self.search_for_subject_hint(f'{self.title.lower()}\n\n{self.description.lower()}')

        if path.exists(exercise_directory_location := f'{config["path"]["exercise"]}/{self.title}'):
            self.location = exercise_directory_location

    def _load(self, from_location: str, webdriver: WebDriver = None) -> None:
        """loads the data of an exercise from a given location"""
        if from_location.startswith('https://'):
            if webdriver is None:
                raise ValueError('A webdriver is needed to fetch from a remote location.')
            self._fetch_remote(webdriver, from_location)
        else:
            self._fetch_local(from_location)

    def save(self, session: Session, override: bool = True, to_location: str = config["path"]["exercise"]) -> bool:
        """creates a directory in which the exercises content, attachments and data are saved in (in subdirectories)"""
        if self.location is None:
            self.location = f'{to_location}/{self.title}'
            mkdir(self.location)
        elif override:
            rmtree(self.location)
            mkdir(self.location)
        else:
            return False

        # json
        json.dump({
            'remote_location': self.remote_location,
            'location': self.location,
            'owner': self.owner,
            'subject': self.subject,
            'tags': self.tags,
            'title': self.title,
            'description': self.description,
            'attachments': self.attachments,
            'start_date': datetime.strftime(self.start_date, '%d.%m.%Y %H:%M'),
            'deadline': datetime.strftime(self.deadline, '%d.%m.%Y %H:%M'),
            'unseen': self.unseen,
            'completed': self.completed
        }, open(f'{self.location}/data.json', 'w', encoding='utf-8'), indent=4)

        # text file for humans - nice and readable
        with open(f'{self.location}/{self.title}.txt', 'w', encoding='utf-8') as outfile:
            outfile.write(
                f'{"=" * 100}\n'
                f'{self.title}\n'
                f'----------\n'
                f'START DATE: \t{datetime.strftime(self.start_date, "%d.%m.%Y %H:%M")}\n'
                f'DEADLINE: \t\t{datetime.strftime(self.deadline, "%d.%m.%Y %H:%M")}\n'
                f'COMPLETED: \t\t{self.completed}\n'
                f'----------\n\n'
                f'{self.description}\n\n'
                f'{"=" * 100}\n'
            )

        if not self.attachments:
            return True

        attachment_directory = f'{self.location}/attachments'
        mkdir(attachment_directory)

        for remote_attachment_location in self.attachments:
            session.fetch_downloadable(
                from_remote_location=remote_attachment_location,
                to_location=f'{attachment_directory}/{remote_attachment_location.split("/")[-1]}'
            )

        return True

    def __eq__(self, other) -> bool:
        """
        exercises are compared based on specific aspects
        to ensure that recordings of the same exercise at different points in time
        can represent the same exercise
        """
        assert isinstance(other, Exercise)

        return self.title == other.title and self.subject == other.subject and self.owner == other.owner and \
            self.start_date == other.start_date and self.deadline == other.deadline

    def __repr__(self) -> str:
        return f'<IScrA.webdriver.element.Exercise.Exercise (title="{self.title}", owner="{self.owner}", ' \
               f'subject="{self.subject}", start_date="{self.start_date}", deadline="{self.deadline}")>'
