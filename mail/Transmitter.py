import logging
from configparser import ConfigParser

from time import time
from datetime import datetime
from string import Template

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
# smtp - transmitter
# ----------


class Transmitter:
    """a simple mailer for IServ using smtp and imap"""
    def __init__(self, iserv_username: str, iserv_password: str) -> None:
        self._iserv_mail_address = f'{iserv_username}@{config["server"]["domain"]}'

        # establish connections and login
        self._smtp_connection = smtplib.SMTP(host=config["server"]["domain"], port=int(config["port"]["smtp"]))
        self._smtp_connection.starttls()
        self._smtp_connection.login(user=iserv_username, password=iserv_password)
        # an imap connection is needed as well to push mails to INBOX/Sent when sending
        self._imap_connection = imaplib.IMAP4(host=config["server"]["domain"], port=int(config["port"]["imap"]))
        self._imap_connection.starttls()
        self._imap_connection.login(user=iserv_username, password=iserv_password)

        # load preambles and epilogues
        self._mail_preamble_plaintext = None
        self._mail_epilogue_plaintext = None
        self._mail_preamble_html = None
        self._mail_epilogue_html = None

        self.load_extensions()

    def shutdown(self) -> None:
        """close all connections and terminate the smtp and imap session"""
        self._smtp_connection.quit()

        if self._imap_connection.state == 'SELECTED':
            self._imap_connection.unselect()  # close election safely

        self._imap_connection.logout()

    def load_extensions(self) -> None:
        """loads mail preambles and epilogues and overwrites the currently used ones"""
        with open(f'{config["path"]["mail_extension_plaintext"]}/preamble.txt', mode='r', encoding='utf-8'
                  ) as plaintext_preamble_file:
            self._mail_preamble_plaintext = Template(plaintext_preamble_file.read()).substitute(
                # substitutions
                TIMESTAMP=datetime.now().strftime("%Y-%m-%d | %H-%M")
            )
            plaintext_preamble_file.close()

        with open(f'{config["path"]["mail_extension_plaintext"]}/epilogue.txt', mode='r', encoding='utf-8'
                  ) as plaintext_epilogue_file:
            self._mail_epilogue_plaintext = Template(plaintext_epilogue_file.read()).substitute(
                # substitutions
                TIMESTAMP=datetime.now().strftime("%Y-%m-%d | %H-%M")
            )
            plaintext_epilogue_file.close()

        with open(f'{config["path"]["mail_extension_html"]}/preamble.html', mode='r', encoding='utf-8'
                  ) as html_preamble_file:
            self._mail_preamble_html = Template(html_preamble_file.read()).substitute(
                # substitutions
                TIMESTAMP=datetime.now().strftime("%Y-%m-%d | %H-%M")
            )
            html_preamble_file.close()

        with open(f'{config["path"]["mail_extension_html"]}/epilogue.html', mode='r', encoding='utf-8'
                  ) as html_epilogue_file:
            self._mail_epilogue_html = Template(html_epilogue_file.read()).substitute(
                # substitutions
                TIMESTAMP=datetime.now().strftime("%Y-%m-%d | %H-%M")
            )
            html_epilogue_file.close()

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

        # append the mail to the INBOX/Sent folder
        self._imap_connection.append(
            mailbox='INBOX/Sent',
            flags='\\SEEN',
            date_time=imaplib.Time2Internaldate(time()),
            message=message.as_string().encode('utf-8')
        )

        del message

    def send_mail_template(self, to_user: str, subject: str, template: str, formatted_template=False,
                           substitution_mapping=None, attachments=None) -> None:
        """sends a mail to another IServ user and uses a given plain-text- or html-template as the body of the mail"""
        if substitution_mapping is None:
            substitution_mapping = {}

        # load the mail template and substitute everything listed in the substitution_mapping
        with open(f'{config["path"]["mail_template"]}/{"html" if formatted_template else "plaintext"}/{template}',
                  mode='r', encoding='utf-8') as template_file:
            body = Template(template_file.read()).safe_substitute(**substitution_mapping)
            template_file.close()

        # just use the send_mail_plaintext function with the text in the given template as body
        self.send_mail(to_user, subject, body, formatted_template, attachments)
