import logging

from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

from datetime import datetime
import time


# ----------
# logger
# ----------


logger = logging.getLogger(__name__)


# ----------
# messenger room
# ----------


class MessengerRoom:
    """represents an IServ messenger room"""
    def __init__(self, remote_location: str, webdriver: WebDriver, timeout: float = 5.0) -> None:
        self._timeout = timeout

        self.remote_location = None
        self.token = None

        self.name = None

        self.last_use_date = None

        self.is_group = None
        self.owners = None
        self.members = None  # members includes owners -> owners is element of members

        self._load(remote_location, webdriver)

    def _load(self, remote_location: str, webdriver: WebDriver) -> None:
        """fetches the data of a messenger room from the corresponding IServ page"""
        self.remote_location = remote_location
        self.token = remote_location.split('/')[-1]

        webdriver.get(self.remote_location)

        try:
            # the info section might be already opened
            show_room_info_button = WebDriverWait(webdriver, self._timeout).until(
                # TODO: only works if the language is set to German ('Rauminformationen öffnen')
                expected_conditions.presence_of_element_located(
                    (By.XPATH, '//span[@title="Rauminformationen öffnen"]')))
            show_room_info_button.click()
        except TimeoutException:
            pass

        # open property accordion in order to load the group member names
        property_accordion_buttons = WebDriverWait(webdriver, self._timeout).until(
            expected_conditions.presence_of_all_elements_located((By.CLASS_NAME, 'property-accordion')))

        if len(property_accordion_buttons) > 1:
            # property_accordion_buttons[1].click()  # expanded by default

            member_name_divs = WebDriverWait(webdriver, self._timeout).until(
                    expected_conditions.presence_of_all_elements_located((By.CLASS_NAME, 'member-name')))

            self.members = [div.text for div in member_name_divs]
            # members where there is a label
            # which indicates that they are a group owner, because the is no other labels
            self.owners = [div.text for div in member_name_divs if len(div.find_elements(By.XPATH, '../*')) > 1]
            self.is_group = True

        else:
            self.is_group = False

        self.name = webdriver.find_element(By.CLASS_NAME, 'room-info').text

        self.last_use_date = WebDriverWait(webdriver, self._timeout).until(
            expected_conditions.presence_of_all_elements_located((By.CLASS_NAME, 'date-container')))[-1].text

    def fetch_messages(self, webdriver: WebDriver, number_of_messages: int) -> [(datetime, str, str)]:
        """fetches the last number_of_messages that have been sent in a messenger room"""
        if not webdriver.current_url == self.remote_location:
            webdriver.get(self.remote_location)

        message_chat_bubble_divs = WebDriverWait(webdriver, self._timeout).until(
            expected_conditions.presence_of_all_elements_located((
                By.XPATH, '//div[contains(@class, "chat-bubble")]')))

        if len(message_chat_bubble_divs) > number_of_messages:
            message_chat_bubble_divs = message_chat_bubble_divs[-number_of_messages:]

        chat_messages = []
        for message_chat_bubble_div in message_chat_bubble_divs:
            chat_messages.append((
                datetime.strptime(
                    message_chat_bubble_div.find_elements(By.XPATH, './div/div[2]/div/div')[-1].find_element(
                        By.TAG_NAME, 'span').get_attribute('title'),
                    '%d.%m.%Y, %H:%M:%S'
                ),
                message_chat_bubble_div.find_element(By.XPATH, './div/div[2]/div/div[1]/div').text,
                message_chat_bubble_div.find_element(By.XPATH, './div/div[2]/div/div[2]/div').text
            ))

        return chat_messages

    def send_messages(self, webdriver: WebDriver, messages: list) -> None:
        """sends a message in a messenger room"""
        if not webdriver.current_url == self.remote_location:
            webdriver.get(self.remote_location)

        message_input = WebDriverWait(webdriver, self._timeout).until(expected_conditions.presence_of_element_located(
            (By.XPATH, '//textarea[@id="chat-input"]')))
        maximal_message_length = int(message_input.get_attribute('maxlength'))
        print(maximal_message_length)

        for message in messages:
            message = str(message)

            if len(message) > maximal_message_length:
                logger.exception('Was not able to send a message to a messenger room '
                                 'because it exceeded the maximum length.')
                raise ValueError('Was not able to send a message to a messenger room '
                                 'because it exceeded the maximum length.')

            message_input.send_keys(message)
            message_input.send_keys(Keys.ENTER)

            time.sleep(0.125)  # just for good measure

    def __eq__(self, other) -> bool:
        """
        messenger rooms are compared based on specific aspects
        to ensure that recordings of the same messenger room at different points in time
        can represent the same messenger room
        """
        assert isinstance(other, MessengerRoom)

        return self.token == other.token and self.owners == other.owners and self.is_group == other.is_group \
            and self.name == other.name

    def __repr__(self) -> str:
        return f'<IScrA.webdriver.element.MessengerRoom.MessengerRoom (token="{self.token}", ' \
               f'owners="{self.owners}", is_group="{self.is_group}", name="{self.name}">'
