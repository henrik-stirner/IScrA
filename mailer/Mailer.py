import logging
from configparser import ConfigParser

from datetime import datetime
from string import Template
import re

from email.header import decode_header
from email import message_from_bytes
from email import encoders
from email.utils import formatdate

import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio

import smtplib
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
# mailer
# ----------


class Mailer:
    """a simple mailer for IServ using smtp and imap"""
    def __init__(self, iserv_username: str, iserv_password: str) -> None:
        self._iserv_mail_address = f'{iserv_username}@{config["server"]["domain"]}'

        # ----------
        # establish connections and login
        # ----------

        # smtp connection
        self._smtp_connection = smtplib.SMTP(host=config["server"]["domain"], port=int(config["port"]["smtp"]))
        self._smtp_connection.starttls()
        self._smtp_connection.login(user=iserv_username, password=iserv_password)

        # imap connection
        self._imap_connection = imaplib.IMAP4(host=config["server"]["domain"], port=int(config["port"]["imap"]))
        self._imap_connection.starttls()
        self._imap_connection.login(user=iserv_username, password=iserv_password)

        # ----------
        # load preambles and epilogues
        # ----------

        with open('./data/mail/extension/plaintext/preamble.txt', mode='r', encoding='utf-8'
                  ) as plaintext_preamble_file:
            self._mail_preamble_plaintext = Template(plaintext_preamble_file.read()).substitute(  # substitutions
                {}
            )
            plaintext_preamble_file.close()

        with open('./data/mail/extension/plaintext/epilogue.txt', mode='r', encoding='utf-8'
                  ) as plaintext_epilogue_file:
            self._mail_epilogue_plaintext = Template(plaintext_epilogue_file.read()).substitute(  # substitutions
                TIMESTAMP=datetime.now().strftime("%Y-%m-%d | %H-%M")
            )
            plaintext_epilogue_file.close()

        with open('./data/mail/extension/html/preamble.html', mode='r', encoding='utf-8') as html_preamble_file:
            self._mail_preamble_html = Template(html_preamble_file.read()).substitute(  # substitutions
                {}
            )
            html_preamble_file.close()

        with open('./data/mail/extension/html/epilogue.html', mode='r', encoding='utf-8') as html_epilogue_file:
            self._mail_epilogue_html = Template(html_epilogue_file.read()).substitute(  # substitutions
                TIMESTAMP=datetime.now().strftime("%Y-%m-%d | %H-%M")
            )
            html_epilogue_file.close()

    def shutdown(self) -> None:
        """makes this instance of IServMailer logout and close all connections"""
        # smtp connection
        self._smtp_connection.quit()

        # imap connection
        if self._imap_connection.state == 'SELECTED':
            # performs the same actions as imaplib.IMAP4.close(),
            # except that no messages are permanently removed from the currently selected mailbox
            self._imap_connection.unselect()

        self._imap_connection.logout()  # includes imaplib.IMAP4.shutdown()

    # ----------
    # sending mails using smtp
    # ----------

    @staticmethod
    def _attach_files(to_message: MIMEMultipart, files_to_attach: list) -> None:
        """attach files to a given MIME multipart"""
        for file_to_attach in files_to_attach:
            content_type, encoding = mimetypes.guess_type(file_to_attach)
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'

            maintype, subtype = content_type.split('/', 1)

            if maintype == 'text':
                attachment_file = open(file_to_attach, 'r')
                attachment = MIMEText(attachment_file.read(), _subtype=subtype)
                attachment_file.close()

            elif maintype == 'image':
                attachment_file = open(file_to_attach, 'rb')
                attachment = MIMEImage(attachment_file.read(), _subtype=subtype)
                attachment_file.close()

            elif maintype == 'audio':
                attachment_file = open(file_to_attach, 'rb')
                attachment = MIMEAudio(attachment_file.read(), _subtype=subtype)
                attachment_file.close()

            else:
                attachment_file = open(file_to_attach, 'rb')
                attachment = MIMEBase(maintype, subtype)
                attachment.set_payload(attachment_file.read())
                attachment_file.close()

                encoders.encode_base64(attachment)

            attachment_file_name = file_to_attach.split('/')[-1]
            attachment.add_header('Content-Disposition', 'attachment', filename=attachment_file_name)
            attachment.add_header('Content-ID', '<{}>'.format(attachment_file_name))

            to_message.attach(attachment)

    def send_mail(self, to_user: str, subject: str, body: str, formatted_body: bool = False, attachments=None) -> None:
        """sends a mail with a body containing plain text or html to another IServ user"""
        if attachments is None:
            attachments = []

        # create the message
        message = MIMEMultipart('alternative')
        message['From'] = self._iserv_mail_address
        # with IServ, you can only send mails to other IServ users
        # turn the given username into a mail address
        message['To'] = f'{to_user}@{config["server"]["domain"]}'
        message['Date'] = formatdate(localtime=True)
        message['Subject'] = subject

        if formatted_body:
            # add the preamble and epilogue to the body of the mail
            body = self._mail_preamble_html + body + self._mail_epilogue_html
            # attach the body to the mail
            message.attach(MIMEText(body, 'html'))
        else:
            body = self._mail_preamble_plaintext + body + self._mail_epilogue_plaintext
            # attach the body to the mail
            message.attach(MIMEText(body, 'plain'))

        # attachments
        self._attach_files(message, attachments)

        # send the mail
        self._smtp_connection.send_message(message)
        del message

    def send_mail_template(self, to_user: str, subject: str, template: str, formatted_template=False,
                           substitution_mapping=None, attachments=None) -> None:
        """sends a mail to another IServ user and uses a given plain-text- or html-template as the body of the mail"""
        if substitution_mapping is None:
            substitution_mapping = {}

        # load the mail template and substitute everything listed in the substitution_mapping
        with open(f'./data/mail/template/{"html" if formatted_template else "plaintext"}/{template}',
                  mode='r', encoding='utf-8') as template_file:
            body = Template(template_file.read()).safe_substitute(**substitution_mapping)
            template_file.close()

        # just use the send_mail_plaintext function with the text in the given template as body
        self.send_mail(to_user, subject, body, formatted_template, attachments)

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

    def get_ids_of_unread_mails(self) -> (str, [str] or []):
        """checks the inbox for unread mails and returns a list of their ids"""
        self._imap_connection.select('INBOX', readonly=True)

        status, response = self._imap_connection.search(None, '(UNSEEN)')

        mail_ids = []
        for mail_id_block in response:
            mail_ids += mail_id_block.decode().split()

        # close inbox
        self._imap_connection.close()

        return 'inbox', mail_ids

    def get_ids_of_selected_mails(self, selection: str, amount: int) -> (str, [str] or []):
        """checks the inbox for unread mails and returns a list of their ids"""
        status, response = self._imap_connection.select(selection, readonly=True)
        # total number of emails
        number_of_mails = int(response[0])

        # close selection
        self._imap_connection.close()

        # the fetch function of imaplib accepts only strings as message_sets (mail ids)
        # therefore, turn the ids into string
        return selection, [str(mail_id) for mail_id in range(number_of_mails, number_of_mails-amount, -1)]

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
