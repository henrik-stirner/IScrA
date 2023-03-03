import logging
from configparser import ConfigParser

import re

from email.header import decode_header
from email import message_from_bytes
import imaplib


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
# imap - receiver
# ----------


class Receiver:
    """a simple mailer for IServ using smtp and imap"""
    def __init__(self, iserv_username: str, iserv_password: str) -> None:
        # establish connections and login
        self._imap_connection = imaplib.IMAP4(host=config["server"]["domain"], port=int(config["port"]["imap"]))
        self._imap_connection.starttls()
        self._imap_connection.login(user=iserv_username, password=iserv_password)

    def shutdown(self) -> None:
        """close all connections and logout"""
        if self._imap_connection.state == 'SELECTED':
            # performs the same actions as imaplib.IMAP4.close(),
            # except that no messages are permanently removed from the currently selected mailbox
            self._imap_connection.unselect()

        self._imap_connection.logout()  # includes imaplib.IMAP4.shutdown()

    # ----------
    # receiving mails using imap
    # ----------

    def get_available_mailboxes(self) -> [(str, str, str)] or []:
        """returns a list of all available mailboxes"""
        status, response = self._imap_connection.list()

        if not response:
            return []

        list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')

        mailboxes = []
        for line in response:
            flags, delimiter, mailbox_name = list_response_pattern.match(line.decode()).groups()
            mailbox_name = mailbox_name.strip('"')
            mailboxes.append((flags, delimiter, mailbox_name))

        return mailboxes

    def get_ids_of_unread_mails(self, selection: str = 'INBOX', max_amount=None) -> (str, [str] or []):
        """checks the inbox for unread mails and returns a list of their ids"""
        self._imap_connection.select(selection, readonly=True)

        status, response = self._imap_connection.search(None, '(UNSEEN)')

        mail_ids = []
        for mail_id_block in response:
            mail_ids += mail_id_block.decode().split()

        # close selection
        self._imap_connection.close()

        number_of_mails = len(mail_ids)

        if max_amount is None:
            # setting the max amount to the number of mails means that all mails will be returned
            max_amount = number_of_mails

        # the fetch function of imaplib accepts only strings as message_sets (mail ids)
        # therefore, turn the ids into string
        return selection, [str(mail_id) for mail_id in range(number_of_mails, number_of_mails - max_amount, -1)]

    def get_ids_of_mails(self, selection: str = 'INBOX', max_amount=None) -> (str, [str] or []):
        """checks the inbox for unread mails and returns a list of their ids"""
        status, response = self._imap_connection.select(selection, readonly=True)
        # total number of emails
        number_of_mails = int(response[0])

        # close selection
        self._imap_connection.close()

        if max_amount is None:
            # setting the max amount to the number of mails means that all mails will be returned
            max_amount = number_of_mails

        # the fetch function of imaplib accepts only strings as message_sets (mail ids)
        # therefore, turn the ids into string
        return selection, [str(mail_id) for mail_id in range(number_of_mails, number_of_mails - max_amount, -1)]

    def extract_mail_content_by_id(self, selection: str, mail_ids: list) -> (str, str, str):
        """generator; gets information about and content of a mail by its id"""
        self._imap_connection.select(selection, readonly=True)

        for mail_id in mail_ids:
            from_user, subject, body = '', '', ''

            status, response = self._imap_connection.fetch(mail_id, '(RFC822)')

            # data: a list with a tuple with header, content, and the closing byte b')'
            for chunk in response:
                if not isinstance(chunk, tuple):
                    continue

                # skip the header
                message = message_from_bytes(chunk[1])

                # decode subject
                subject, encoding = decode_header(message['subject'])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else 'utf-8').strip()

                # decode sender
                from_user, encoding = decode_header(message.get('from', '<unknown>'))[0]
                if isinstance(from_user, bytes):
                    # TODO: failing to successfully decode special characters and symbols
                    from_user = from_user.decode(encoding if encoding else 'utf-8').strip()

                # if the message is a multipart, the text needs to be separated
                if message.is_multipart():
                    # get all text parts of the message payload
                    for part in message.get_payload():
                        if part.get_content_type() == 'text/plain':
                            body += part.get_payload(decode=True).decode()
                else:
                    if message.get_content_type() in ['text/plain', 'text/html']:
                        body = message.get_payload(decode=True).decode().strip()

            yield from_user, subject, body

        # close selection when done extracting content from mails
        self._imap_connection.close()
