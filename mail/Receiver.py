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

        self._current_selection = None
        self._current_selection_is_readonly = None

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

    def change_selection_if_necessary(self, new_selection: str, readonly: bool = True):
        if (self._current_selection == new_selection) and (self._current_selection_is_readonly == readonly):
            return

        if self._imap_connection.state == 'SELECTED':
            self._imap_connection.close()

        status, response = self._imap_connection.select(new_selection, readonly=readonly)
        self._current_selection, self._current_selection_is_readonly = new_selection, readonly

        if status.lower() != 'ok':
            logger.exception(f'Failed to select mailbox {new_selection}.')

    def get_available_mailboxes(self) -> [(str, str, str)] or []:
        """returns a list of all available mailboxes"""
        status, response = self._imap_connection.list()

        if status.lower() != 'ok':
            logger.exception(f'Failed to list mailboxes.')

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
        self.change_selection_if_necessary(selection, readonly=True)

        status, response = self._imap_connection.search(None, '(UNSEEN)')

        if status.lower() != 'ok':
            logger.exception(f'Failed to search mailbox {selection} for (UNSEEN).')

        mail_ids = []
        for mail_id_block in response:
            mail_ids += mail_id_block.decode().split()

        if max_amount is None:
            # setting the max amount to the number of mails means that all mails will be returned
            max_amount = len(mail_ids)

        # the fetch function of imaplib accepts only strings as message_sets (mail ids)
        # therefore, turn the ids into string
        return selection, mail_ids[0:max_amount]

    def get_ids_of_mails(self, selection: str = 'INBOX', max_amount=None) -> (str, [str] or []):
        """checks the inbox for unread mails and returns a list of their ids"""
        status, response = self._imap_connection.select(selection, readonly=True)
        self._current_selection, self._current_selection_is_readonly = selection, True

        if status.lower() != 'ok':
            logger.exception(f'Failed to select mailbox {selection}.')

        # total number of emails
        number_of_mails = int(response[0])

        if max_amount is None:
            # setting the max amount to the number of mails means that all mails will be returned
            max_amount = number_of_mails

        # the fetch function of imaplib accepts only strings as message_sets (mail ids)
        # therefore, turn the ids into string
        return selection, [str(mail_id) for mail_id in range(number_of_mails, (number_of_mails - max_amount), -1)]

    def minimal_mail_data_by_id(self, selection: str, mail_id: int | str) -> tuple[str, str] | None:
        """gets subject and sender of a mail"""
        self.change_selection_if_necessary(selection, readonly=True)

        status, response = self._imap_connection.fetch(str(mail_id), '(RFC822.HEADER)')  # fetch only the header

        if status.lower() != 'ok':
            logger.exception(f'Failed to fetch mail with id: {mail_id}.')
            return

        # response: [(header, content), closing byte]
        # we only want the tuple
        # skip the header in the tuple as well
        message = message_from_bytes(response[0][1])

        # extract message contents
        # subject
        subject = str(make_header(decode_header(message['subject'])))
        # sender
        from_sender = str(make_header(decode_header(message['from'])))

        return subject, from_sender

    def fetch_mail_content_by_id(
            self, selection: str, mail_id: int | str
    ) -> tuple[str, str, str, str, tuple[str, str], list[tuple[str, str]]] | None:
        """gets information about and text content of a mail by its id"""
        self.change_selection_if_necessary(selection, readonly=True)

        status, response = self._imap_connection.fetch(str(mail_id), '(RFC822)')  # fetch the whole mail

        if status.lower() != 'ok':
            logger.exception(f'Failed to fetch mail with id: {mail_id}.')
            return

        # response: [(header, content), closing byte]
        # we only want the tuple
        # skip the header in the tuple as well
        message = message_from_bytes(response[0][1])

        # extract message contents

        # ----------
        # header
        # ----------

        # date
        date = str(make_header(decode_header(message['date'])))
        # subject
        subject = str(make_header(decode_header(message['subject'])))
        # sender
        from_sender = str(make_header(decode_header(message['from'])))
        # receiver
        to_receiver = str(make_header(decode_header(message['to'])))

        # ----------
        # content
        # ----------

        body = ('', '')

        attachment_data = []

        if not message.is_multipart():
            if content_type := message.get_content_type() == 'text/plain':
                # there is only text for us to extract
                body = (message.get_payload(decode=True).decode().strip(), '')
            elif content_type == 'text/html':
                body = ('', message.get_payload(decode=True).decode().strip())
            else:
                # there is no text for us to extract
                attachment_data.append((message.get_filename(), content_type))

        else:
            body_plaintext = ''
            body_html = ''

            # the message is a multipart and the text parts need to be separated from the rest
            for part in message.walk():

                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition'))

                if ('attachment' in content_disposition) and (attachment_file_name := part.get_filename()):
                    attachment_data.append((attachment_file_name, content_type))

                elif content_type == 'text/plain':
                    body_plaintext += part.get_payload(decode=True).decode()
                elif content_type == 'text/html':
                    body_html += part.get_payload(decode=True).decode()

            body = (body_plaintext, body_html)

        return date, subject, from_sender, to_receiver, body, attachment_data

    def download_mail_attachments_by_id(self, selection: str, mail_id: int | str, to_location: str) -> bool:
        """generator; gets information about and text content of a mail by its id"""
        to_location = to_location.removesuffix('/').removesuffix('\\')

        self.change_selection_if_necessary(selection, readonly=True)

        status, response = self._imap_connection.fetch(str(mail_id), '(RFC822)')  # fetch the whole mail

        if status.lower() != 'ok':
            logger.exception(f'Failed to fetch mail with id: {mail_id}.')
            return False

        # response: [(header, content), closing byte]
        # we only want the tuple
        # skip the header in the tuple as well
        message = message_from_bytes(response[0][1])

        # download attachments
        if not message.is_multipart():
            if message.get_content_type() not in ['text/plain', 'text/html']:
                # there is an attachment for us to download
                open(f'{to_location}/{message.get_filename()}', 'wb').write(message.get_payload(decode=True))

        # the message is a multipart
        for part in message.walk():

            if not ('attachment' in str(part.get('Content-Disposition')) and part.get_filename()):
                continue

            # there is an attachment for us to download
            open(f'{to_location}/{part.get_filename()}', 'wb').write(part.get_payload(decode=True))

        return True

    def mark_as_read_by_id(self, selection: str, mail_id: int | str):
        self.change_selection_if_necessary(selection, readonly=False)

        self._imap_connection.store(str(mail_id), '+FLAGS', '\\SEEN')

    def mark_as_unread_by_id(self, selection: str, mail_id: int | str):
        self.change_selection_if_necessary(selection, readonly=False)

        self._imap_connection.store(str(mail_id), '-FLAGS', '\\SEEN')

    # other flags to store?
    # too unsafe?
    # https://stackoverflow.com/questions/17367611/python-imaplib-mark-email-as-unread-or-unseen

    # TODO: BODYSTRUCTURE
    # fetch and analyse BODYSTRUCTURE and only download what is really needed:
    # status, response = self._imap_connection.fetch(str(mail_id), '(BODYSTRUCTURE)')  # get the mails body structure
