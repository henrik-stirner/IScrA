![badge: python](https://img.shields.io/badge/Lang-Python-informational?style=for-the-badge&logo=Python&logoColor=white&color=fcd132)

WORK IN PROGRESS

# IScrA - IServ Scraping Automations
<b>Make sure to add the missing dotenv and config files before running.</b>
- ./IScrA/.env
  - username
- ./IScrA/config.ini
  - base domain
  - ports (imap, smtp)
- ./IScrA/subject.ini

The icons in ./IScrA/assets/icon/ are missing. <br/>
You will need to add your own icons (listed in ./IScrA/assets/icon/missing.txt) as they will be used for sending notifications (see ./IScrA/core.py). 

## Features
- <b>webdriver</b>
  - fetching information about and downloading tasks
  - fetching information about and downloading texts
  - fetching information about and downloading files
  - sending messages to and fetching messages from messenger rooms
- <b>mailer</b>
  - sending (scheduled) mails using SMTP
  - fetching received mails using IMAP4
- <b>scraper</b>
  - retrieving the users csrf token
  - fetching pending exercises
  - checking if new exercises have been assigned
