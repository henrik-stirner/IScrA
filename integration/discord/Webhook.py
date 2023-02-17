import logging

import requests
import filetype


# ----------
# logger
# ----------


logger = logging.getLogger(__name__)


# ----------
# discord webhook
# ----------


"""
====================================================================================================
----------
JSON DATA EXAMPLE
----------

{
    'username': '',
    'avatar_url': '',
    'content': 'up to 2000 characters',
    'embeds': [
        {
            'author': {
                'name': '',
                'url': '',
                'icon_url': ''
            },
            'title': '',
            'url': '',
            'description': '*italic* **bold** __underline__ ~~strikeout~~ `inline-code` ```code``` '
                           '[hyperlink](https://google.com)',
            'color': int(0xffffff),
            'fields': [
                {
                    'name': '',
                    'value': '',
                    'inline': True
                },
                {
                    'name': "Even more text",
                    'value': "Yup",
                    'inline': True
                },
                {
                    'name': '`\'inline\': True` lets you display two fields in the same line',
                    'value': ''
                }
            ],
            'thumbnail': {
                'url': ''
            },
            'image': {
                'url': ''
            },
            'footer': {
                'text': '',
                'icon_url': ''
            },
            'timestamp': datetime.now().isoformat(sep=' ')
        }
    ]
}

====================================================================================================
"""


class Webhook:
    def __init__(self, webhook_url: str, timeout: float = 5.0, username: str = None, avatar_url: str = None) -> None:
        self._request_session = requests.Session()

        self._url = webhook_url
        self._timeout = timeout

        self.username = username
        self.avatar_url = avatar_url

    def send(self, data: dict, attachment_files: list = None) -> bool:
        attachments = None
        if attachment_files is not None:
            attachments = []
            for file_to_attach in attachment_files:
                attachments.append(
                    ('file', (
                        file_to_attach.split('/')[-1],
                        open(file_to_attach, 'rb'),
                        filetype.guess(file_to_attach).mime
                    ))
                )

        try:
            response = self._request_session.post(
                url=self._url,
                timeout=self._timeout,
                json=data,
                files=attachments
            )

            response.raise_for_status()

            if not 200 <= response.status_code < 300:
                logger.exception(f'Failed trying to post to the discord webhook with url "{self._url}". \n'
                                 f'Status: {response.status_code}, \nResponse:\n{response.json()}')

        except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as exception:
            logger.exception(f'Failed trying to post to the discord webhook with url "{self._url}". \n'
                             f'Reason: {exception}')
            return False

        return True

    def send_simple_message(self, content: str) -> bool:
        data = {
            'username': self.username,
            'content': content
        }

        return self.send(data=data)

    def send_simple_embed(self, title: str, description: str, color: int = 0xffffff) -> bool:
        data = {
            'username': self.username,
            'embeds': [
                {
                    'title': title,
                    'description': description,
                    'color': color
                }
            ]
        }

        return self.send(data=data)
