import logging
from configparser import ConfigParser

import re

from email.header import make_header, decode_header
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

    @staticmethod
    def _obtain_message_header_contents(message) -> tuple[str, str, str, str]:
        # date
        date = str(make_header(decode_header(message['date'])))
        # subject
        subject = str(make_header(decode_header(message['subject'])))
        # sender
        from_sender = str(make_header(decode_header(message['from'])))
        # receiver
        to_receiver = str(make_header(decode_header(message['to'])))

        return date, subject, from_sender, to_receiver

    @staticmethod
    def _obtain_message_body_contents(message) -> str:
        if not message.is_multipart():
            if not message.get_content_type() in ['text/plain', 'text/html']:
                # there is no text for us to extract
                return ''

            return message.get_payload(decode=True).decode().strip()

        # the message is a multipart and the text parts need to be separated from the rest
        assert message.is_multipart()

        body = ''

        # get all text parts of the message's payload
        for part in message.get_payload():

            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition'))

            if 'attachment' in content_disposition and part.get_filename():
                # TODO: handle attachments
                # attachment_filename := part.get_filename()
                # open(path, 'wb').write(part.get_payload(decode=True))
                pass

            elif content_type in ['text/plain', 'text/html']:
                body += part.get_payload(decode=True).decode()

        return body

    def extract_mail_content_by_id(self, selection: str, mail_ids: list) -> tuple[str, str, str] | None:
        """generator; gets information about and content of a mail by its id"""
        self._imap_connection.select(selection, readonly=True)

        for mail_id in mail_ids:
            status, response = self._imap_connection.fetch(mail_id, '(RFC822)')

            if status.lower() != 'ok':
                return

            # response: [(header, content), closing byte]
            # we only want the tuple
            # skip the header in the tuple as well
            message = message_from_bytes(response[0][1])

            # extract message contents
            date, subject, from_sender, to_receiver = self._obtain_message_header_contents(message=message)
            body = self._obtain_message_body_contents(message=message)

            yield date, subject, from_sender, to_receiver, body

        # close selection when done extracting content from mails
        self._imap_connection.close()
